#!/usr/bin/env python3
"""Per-PRD state files (PRD-018) — de-contend the loop.

Each PRD's status lives in its OWN file, `.orchestrator/prds/<PRD-ID>.json`, so two operators
working different PRDs never touch the same file (no lost update), and same-PRD writes are atomic
(write a temp + `os.replace`, a single atomic rename on POSIX). This is the substrate the claim
protocol (PRD-019) builds on; here it is just state.

  prd_state.py set <PRD-ID> <status>     # status in {planned,claimed,building,verifying,shipped}
  prd_state.py get <PRD-ID>              # prints the status (exit 1 if unknown)
  prd_state.py list                       # prints every PRD's state
"""
import argparse
import datetime
import json
import os
import subprocess
import sys

STATES = ["planned", "claimed", "building", "verifying", "shipped"]


def _actor(d):
    """The principal effecting a transition (PRD-020/021): $OL_ACTOR -> git user -> $USER."""
    actor = os.environ.get("OL_ACTOR")
    if not actor:
        try:
            actor = subprocess.run(["git", "-C", d, "config", "user.name"],
                                   capture_output=True, text=True).stdout.strip()
        except Exception:
            actor = ""
    return actor or os.environ.get("USER") or "unknown"


def pdir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _dir(d):
    return os.path.join(d, ".orchestrator", "prds")


def _norm(pid):
    pid = pid.strip()
    if pid.upper().startswith("PRD-"):
        rest = pid[4:]
        return f"PRD-{int(rest):03d}" if rest.isdigit() else f"PRD-{rest}"
    if pid.isdigit():
        return f"PRD-{int(pid):03d}"
    return pid


def _path(d, pid):
    return os.path.join(_dir(d), f"{_norm(pid)}.json")


def set_state(d, pid, status):
    os.makedirs(_dir(d), exist_ok=True)
    p = _path(d, pid)
    by = _actor(d)
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    prev = get_state(d, pid) or {}
    history = list(prev.get("history", []))
    history.append({"status": status, "by": by, "ts": ts})  # who effected each transition (PRD-021)
    obj = {"id": _norm(pid), "status": status, "by": by, "ts": ts, "history": history}
    tmp = f"{p}.tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")
    os.replace(tmp, p)  # atomic rename — no torn file even under concurrent writers
    return obj


def get_state(d, pid):
    p = _path(d, pid)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except Exception:
        return None


def list_states(d):
    dd = _dir(d)
    out = []
    if os.path.isdir(dd):
        for f in sorted(os.listdir(dd)):
            if f.endswith(".json"):
                try:
                    out.append(json.load(open(os.path.join(dd, f))))
                except Exception:
                    pass
    return out


DEFAULT_TTL = 86400  # a claim older than this (no heartbeat) is stale and reclaimable (PRD-019)


def _claim_path(d, pid):
    return os.path.join(_dir(d), f"{_norm(pid)}.claim")


def _age_seconds(ts):
    try:
        return (datetime.datetime.now() - datetime.datetime.fromisoformat(ts)).total_seconds()
    except Exception:
        return float("inf")  # unparseable/absent ts = treat as very old (stale)


def claim(d, pid, by, branch, ttl=DEFAULT_TTL, force=False):
    """Atomically acquire a PRD. O_EXCL guarantees exactly one creator wins (PRD-019)."""
    os.makedirs(_dir(d), exist_ok=True)
    p = _claim_path(d, pid)
    payload = (json.dumps({"id": _norm(pid), "by": by, "branch": branch,
                           "ts": datetime.datetime.now().isoformat(timespec="seconds")}) + "\n")
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, payload.encode())
        finally:
            os.close(fd)
        set_state(d, pid, "claimed")
        return 0, f"claimed {_norm(pid)} by {by} on {branch}"
    except FileExistsError:
        try:
            existing = json.load(open(p))
        except Exception:
            existing = {}
        age = _age_seconds(existing.get("ts", ""))
        if force and age > ttl:  # --force overrides ONLY a stale claim, never a live owner
            tmp = f"{p}.tmp.{os.getpid()}"
            with open(tmp, "w") as f:
                f.write(payload)
            os.replace(tmp, p)
            set_state(d, pid, "claimed")
            return 0, f"reclaimed stale {_norm(pid)} (was {existing.get('by')!r}, age {int(age)}s) by {by}"
        who = existing.get("by", "?")
        why = "" if force else " (use --force only if it is stale)"
        return 1, f"DENIED: {_norm(pid)} is held by {who!r} (age {int(age)}s, ttl {ttl}s){why}"


def release(d, pid):
    p = _claim_path(d, pid)
    if os.path.exists(p):
        try:
            os.replace(p, p + ".released")  # rename-aside (virtiofs-safe), not unlink
        except Exception:
            open(p, "w").write("")
    return 0


def list_claims(d):
    dd = _dir(d)
    out = []
    if os.path.isdir(dd):
        for f in sorted(os.listdir(dd)):
            if f.endswith(".claim"):
                try:
                    o = json.load(open(os.path.join(dd, f)))
                    out.append(f"{o.get('id')}  by={o.get('by')}  branch={o.get('branch')}  "
                               f"age={int(_age_seconds(o.get('ts', '')))}s")
                except Exception:
                    pass
    return out


def claim_check(d, pid, branch):
    p = _claim_path(d, pid)
    if not os.path.exists(p):
        return 1, f"{_norm(pid)} is unclaimed"
    try:
        o = json.load(open(p))
    except Exception:
        return 1, "claim unreadable"
    if o.get("branch") == branch:
        return 0, f"branch {branch} matches the claim on {_norm(pid)}"
    return 1, f"branch {branch!r} != claimed branch {o.get('branch')!r} for {_norm(pid)}"


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("set")
    s.add_argument("id")
    s.add_argument("status")
    g = sub.add_parser("get")
    g.add_argument("id")
    sub.add_parser("list")
    c = sub.add_parser("claim")
    c.add_argument("id")
    c.add_argument("--by", required=True)
    c.add_argument("--branch", required=True)
    c.add_argument("--ttl", type=int, default=DEFAULT_TTL)
    c.add_argument("--force", action="store_true")
    rl = sub.add_parser("release")
    rl.add_argument("id")
    sub.add_parser("claims")
    cc = sub.add_parser("claim-check")
    cc.add_argument("id")
    cc.add_argument("--branch", required=True)
    args = ap.parse_args(argv)
    d = pdir()
    if args.cmd == "set":
        if args.status not in STATES:
            print(f"invalid status {args.status!r}; one of {STATES}", file=sys.stderr)
            return 2
        o = set_state(d, args.id, args.status)
        print(f"{o['id']}: {o['status']}")
        return 0
    if args.cmd == "get":
        o = get_state(d, args.id)
        if not o:
            print("unknown", file=sys.stderr)
            return 1
        print(o["status"])
        return 0
    if args.cmd == "list":
        for o in list_states(d):
            print(f"{o.get('id')}: {o.get('status')}")
        return 0
    if args.cmd == "claim":
        rc, msg = claim(d, args.id, args.by, args.branch, args.ttl, args.force)
        print(msg, file=sys.stderr if rc else sys.stdout)
        return rc
    if args.cmd == "release":
        release(d, args.id)
        print(f"released {_norm(args.id)}")
        return 0
    if args.cmd == "claims":
        for line in list_claims(d):
            print(line)
        return 0
    if args.cmd == "claim-check":
        rc, msg = claim_check(d, args.id, args.branch)
        print(msg, file=sys.stderr if rc else sys.stdout)
        return rc
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
