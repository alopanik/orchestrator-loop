#!/usr/bin/env python3
"""Multi-hand release gate (PRD-022) — a release requires a recorded OWNER sign-off.

The app-profile says "a push to the remote is a RELEASE — owner sign-off required, never
autonomous." With multiple committers that needs teeth: anyone can bump the version, but a release
is only valid if an AUTHORIZED OWNER has signed off on that exact version. `check` fails closed
otherwise. Owners derive from `.orchestrator/release-policy.json` `{"owners":[…]}` if present,
else the marketplace manifest's `owner.name` — no new hardcoded identity.

  release.py signoff --by <owner> [--version V]   # record owner sign-off (refuses a non-owner)
  release.py check                                 # 0 iff current version is signed off by an owner
  release.py status                                # version · signed-off · owners
"""
import argparse
import datetime
import json
import os
import subprocess
import sys


def pdir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _plugin(d):
    return os.path.join(d, ".claude-plugin", "plugin.json")


def _market(d):
    return os.path.join(d, ".claude-plugin", "marketplace.json")


def _signoff_path(d):
    return os.path.join(d, ".orchestrator", "release-signoff.json")


def _policy(d):
    return os.path.join(d, ".orchestrator", "release-policy.json")


def version(d):
    try:
        return json.load(open(_plugin(d))).get("version")
    except Exception:
        return None


def owners(d):
    p = _policy(d)
    if os.path.exists(p):
        try:
            o = json.load(open(p)).get("owners")
            if o:
                return list(o)
        except Exception:
            pass
    try:
        name = json.load(open(_market(d))).get("owner", {}).get("name")
        return [name] if name else []
    except Exception:
        return []


def _commit(d):
    try:
        c = subprocess.run(["git", "-C", d, "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True)
        return c.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def signoff(d, by, ver):
    v = ver or version(d)
    if v is None:
        sys.stderr.write("release: no version in plugin.json\n")
        return 2
    owl = owners(d)
    if by not in owl:
        sys.stderr.write(f"release: {by!r} is not an authorized owner {owl} — sign-off REFUSED.\n")
        return 1
    os.makedirs(os.path.join(d, ".orchestrator"), exist_ok=True)
    rec = {"version": v, "by": by,
           "ts": datetime.datetime.now().isoformat(timespec="seconds"), "commit": _commit(d)}
    with open(_signoff_path(d), "w") as f:
        json.dump(rec, f, indent=2)
        f.write("\n")
    print(f"release: {v} signed off by {by} (commit {rec['commit']})")
    return 0


def check(d):
    v = version(d)
    if v is None:
        sys.stderr.write("release: no version in plugin.json — FAIL CLOSED. [release]\n")
        return 2
    owl = owners(d)
    try:
        rec = json.load(open(_signoff_path(d)))
    except Exception:
        rec = {}
    if rec.get("version") == v and rec.get("by") in owl:
        print(f"release: version {v} signed off by {rec.get('by')} ✓")
        return 0
    if rec.get("version") == v:
        sys.stderr.write(f"release: version {v} signoff by {rec.get('by')!r} is NOT an authorized "
                         f"owner {owl} — FAIL CLOSED. [release]\n")
        return 2
    sys.stderr.write(f"release: version {v} is NOT signed off by an authorized owner "
                     f"(last signoff: {rec.get('version')!r} by {rec.get('by')!r}). A release "
                     "needs owner sign-off. FAIL CLOSED. [release]\n")
    return 2


def status(d):
    try:
        rec = json.load(open(_signoff_path(d)))
    except Exception:
        rec = {}
    print(f"release: version={version(d)}  signed_off={rec.get('version')} by={rec.get('by')}  "
          f"owners={owners(d)}")
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("signoff")
    s.add_argument("--by", required=True)
    s.add_argument("--version", default=None)
    sub.add_parser("check")
    sub.add_parser("status")
    args = ap.parse_args(argv)
    d = pdir()
    if args.cmd == "signoff":
        return signoff(d, args.by, args.version)
    if args.cmd == "check":
        return check(d)
    if args.cmd == "status":
        return status(d)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
