#!/usr/bin/env python3
"""Connector preflight (PRD-010) — verify the executor is wired to the RIGHT project.

Before dispatch, compare each connector's *declared* ref (from CLAUDE.md, recorded in the
manifest) to the *actual* ref the connected tool reports via a probe command. Fail closed on a
mismatch, a missing probe, or a probe that errors — so a change can't run against the wrong
Supabase/Vercel/repo.

Manifest `.orchestrator/connectors.json`:
  [ {"category":"~~database","expected":"abc123","probe":"supabase projects list --output json"} ]

  preflight.py check     # exit 0 only if every probe's output contains its expected ref
  preflight.py status    # print the comparison table
"""
import json
import os
import subprocess
import sys

MANIFEST_REL = os.path.join(".orchestrator", "connectors.json")
PROBE_TIMEOUT = 60


def pdir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def load(pdir_):
    p = os.path.join(pdir_, MANIFEST_REL)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def probe_one(pdir_, c):
    cat = c.get("category", "?")
    expected = str(c.get("expected", "")).strip()
    probe = c.get("probe")
    if not expected:
        return cat, False, "no expected ref declared"
    if not probe:
        return cat, False, "no probe command (fail-closed)"
    try:
        r = subprocess.run(probe, shell=True, cwd=pdir_, capture_output=True,
                           text=True, timeout=PROBE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return cat, False, f"probe timed out; expected {expected!r}"
    except Exception as e:
        return cat, False, f"probe error: {e}"
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        return cat, False, f"probe exited {r.returncode}; expected {expected!r}"
    if expected in out:
        return cat, True, f"actual matches expected {expected!r}"
    actual = out.strip().splitlines()[0][:60] if out.strip() else "(empty)"
    return cat, False, f"MISMATCH: expected {expected!r}, probe reported {actual!r}"


def run(pdir_):
    m = load(pdir_)
    if m is None:
        return None
    return [probe_one(pdir_, c) for c in m]


def cmd_check():
    results = run(pdir())
    if results is None:
        print("preflight: no connectors manifest — nothing to check")
        return 0
    bad = [(c, d) for (c, ok, d) in results if not ok]
    for c, ok, d in results:
        print(f"  [{'OK ' if ok else 'BAD'}] {c}: {d}", file=sys.stderr if not ok else sys.stdout)
    if bad:
        print(f"\npreflight FAILED ({len(bad)}): executor is NOT verified against the declared "
              "project(s) — refusing to dispatch.", file=sys.stderr)
        return 1
    print(f"\npreflight OK: {len(results)} connector(s) verified against CLAUDE.md ✓")
    return 0


def cmd_status():
    results = run(pdir())
    if results is None:
        print("no connectors manifest")
        return 0
    for c, ok, d in results:
        print(f"  {c:<16} {'OK' if ok else 'BAD':<4} {d}")
    return 0


def main(argv):
    sub = argv[0] if argv else "check"
    if sub == "check":
        return cmd_check()
    if sub == "status":
        return cmd_status()
    print(f"unknown subcommand: {sub}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
