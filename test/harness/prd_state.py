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
import sys

STATES = ["planned", "claimed", "building", "verifying", "shipped"]


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
    obj = {"id": _norm(pid), "status": status,
           "ts": datetime.datetime.now().isoformat(timespec="seconds")}
    p = _path(d, pid)
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


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("set")
    s.add_argument("id")
    s.add_argument("status")
    g = sub.add_parser("get")
    g.add_argument("id")
    sub.add_parser("list")
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
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
