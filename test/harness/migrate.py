#!/usr/bin/env python3
"""Gated-migration choreography (PRD-023) — the gate + record state machine.

The framework does NOT execute SQL (`~~database` does). This gates and records the choreography
around the irreversible apply: draft -> (PAUSE for owner review) approve -> apply (gated) ->
connector runs the SQL -> verify. A bare destructive migration (DROP/TRUNCATE/… without a 2-stage
soft-deprecate) is blocked; apply fails closed unless an owner has reviewed it. Every transition
is recorded with who + when.

  migrate.py draft <name> --sql "<sql>|@file" [--staged]   # record a plan; flag destructive
  migrate.py approve <name> --by <reviewer>                 # the owner-review gate (recorded)
  migrate.py apply <name>                                   # gated: needs approval; blocks bare destructive
  migrate.py verify <name>                                  # mark verified after the connector applied + checked
  migrate.py status                                         # list migrations + states
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

DESTRUCTIVE = [
    r"\bDROP\s+(TABLE|COLUMN|INDEX|VIEW|SCHEMA|DATABASE)\b",
    r"\bTRUNCATE\b",
    r"\bALTER\s+TABLE\b.*\bDROP\b",
    r"\bDELETE\s+FROM\b",
    r"\bRENAME\b",
]


def pdir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _dir(d):
    return os.path.join(d, ".orchestrator", "migrations")


def _path(d, name):
    return os.path.join(_dir(d), f"{name}.json")


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _actor(d):
    a = os.environ.get("OL_ACTOR")
    if not a:
        try:
            a = subprocess.run(["git", "-C", d, "config", "user.name"],
                               capture_output=True, text=True).stdout.strip()
        except Exception:
            a = ""
    return a or os.environ.get("USER") or "unknown"


def is_destructive(sql):
    return any(re.search(p, sql, re.I | re.S) for p in DESTRUCTIVE)


def _load(d, name):
    p = _path(d, name)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except Exception:
        return None


def _save(d, name, obj):
    os.makedirs(_dir(d), exist_ok=True)
    p = _path(d, name)
    tmp = f"{p}.tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")
    os.replace(tmp, p)


def _hist(obj, state, by):
    obj.setdefault("history", []).append({"state": state, "by": by, "ts": _now()})


def cmd_draft(d, name, sql, staged):
    if sql.startswith("@"):
        try:
            sql = open(os.path.join(d, sql[1:])).read()
        except Exception as e:
            sys.stderr.write(f"migrate: cannot read sql file {sql[1:]!r}: {e}\n")
            return 2
    by = _actor(d)
    obj = {"name": name, "sql": sql, "destructive": is_destructive(sql), "staged": bool(staged),
           "state": "drafted", "history": [{"state": "drafted", "by": by, "ts": _now()}]}
    _save(d, name, obj)
    note = " [DESTRUCTIVE]" if obj["destructive"] else ""
    note += " (staged 2-stage plan)" if staged else ""
    print(f"migrate: drafted {name}{note}. Next: owner review -> `migrate.py approve {name} --by <owner>`.")
    return 0


def cmd_approve(d, name, by):
    obj = _load(d, name)
    if obj is None:
        sys.stderr.write(f"migrate: no migration {name!r} to approve\n")
        return 2
    obj["state"] = "approved"
    obj["approved_by"] = by
    _hist(obj, "approved", by)
    _save(d, name, obj)
    print(f"migrate: {name} approved by {by}. Apply is now unlocked (`migrate.py apply {name}`).")
    return 0


def cmd_apply(d, name):
    obj = _load(d, name)
    if obj is None:
        sys.stderr.write(f"migrate: no migration {name!r}\n")
        return 2
    if obj.get("state") != "approved":
        sys.stderr.write(
            f"migrate: {name} is '{obj.get('state')}', not approved — the apply is the IRREVERSIBLE "
            f"step and must pause for owner review first. Run `migrate.py approve {name} --by "
            "<owner>`. FAIL CLOSED. [migrate]\n")
        return 2
    if obj.get("destructive") and not obj.get("staged"):
        sys.stderr.write(
            f"migrate: {name} is a BARE DESTRUCTIVE migration — blocked. Use a 2-stage "
            "soft-deprecate (add -> backfill -> swap reads -> drop) and re-draft with --staged, or "
            "confirm the readers are deployed. FAIL CLOSED. [migrate]\n")
        return 2
    obj["state"] = "applied"
    _hist(obj, "applied", _actor(d))
    _save(d, name, obj)
    print(f"migrate: {name} authorized to apply. The ~~database connector may now run the SQL with "
          f"your go; then `migrate.py verify {name}`.")
    return 0


def cmd_verify(d, name):
    obj = _load(d, name)
    if obj is None:
        sys.stderr.write(f"migrate: no migration {name!r}\n")
        return 2
    obj["state"] = "verified"
    _hist(obj, "verified", _actor(d))
    _save(d, name, obj)
    print(f"migrate: {name} verified.")
    return 0


def cmd_status(d):
    dd = _dir(d)
    if not os.path.isdir(dd):
        print("migrate: no migrations recorded")
        return 0
    for f in sorted(os.listdir(dd)):
        if f.endswith(".json"):
            o = _load(d, f[:-5]) or {}
            flag = " [DESTRUCTIVE]" if o.get("destructive") else ""
            flag += " staged" if o.get("staged") else ""
            print(f"  {o.get('name'):<16} {o.get('state'):<10}{flag}")
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    dft = sub.add_parser("draft")
    dft.add_argument("name")
    dft.add_argument("--sql", required=True)
    dft.add_argument("--staged", action="store_true")
    apv = sub.add_parser("approve")
    apv.add_argument("name")
    apv.add_argument("--by", required=True)
    apl = sub.add_parser("apply")
    apl.add_argument("name")
    vfy = sub.add_parser("verify")
    vfy.add_argument("name")
    sub.add_parser("status")
    args = ap.parse_args(argv)
    d = pdir()
    if args.cmd == "draft":
        return cmd_draft(d, args.name, args.sql, args.staged)
    if args.cmd == "approve":
        return cmd_approve(d, args.name, args.by)
    if args.cmd == "apply":
        return cmd_apply(d, args.name)
    if args.cmd == "verify":
        return cmd_verify(d, args.name)
    if args.cmd == "status":
        return cmd_status(d)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
