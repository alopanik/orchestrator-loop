#!/usr/bin/env python3
"""Tests for gated-migration choreography (PRD-023): draft -> approve -> apply -> verify, with
apply gated on owner review and a bare destructive migration blocked. Self-contained.

Run: python3 test/harness/test_migration_gate.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MIGRATE = os.path.join(HERE, "migrate.py")
PY = sys.executable

_passed = 0
_failed = 0


def check(name, cond, detail=""):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  [PASS] {name}")
    else:
        _failed += 1
        print(f"  [FAIL] {name}: {detail}")


def tmp():
    d = tempfile.mkdtemp(prefix="ol-mig-")
    os.makedirs(os.path.join(d, ".orchestrator"), exist_ok=True)
    return d


def run(argv, d, actor="tester"):
    return subprocess.run([PY, MIGRATE, *argv], cwd=d, capture_output=True, text=True,
                          env=dict(os.environ, CLAUDE_PROJECT_DIR=d, OL_ACTOR=actor))


def rec(d, name):
    p = os.path.join(d, ".orchestrator", "migrations", f"{name}.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def test_draft_records():
    d = tmp()
    r = run(["draft", "m1", "--sql", "CREATE TABLE t(id int)"], d)
    o = rec(d, "m1")
    check("AT-1 draft records a drafted migration", r.returncode == 0 and o.get("state") == "drafted", str(o))
    check("AT-1 non-destructive flagged correctly", o.get("destructive") is False, str(o))
    check("AT-1 status lists it", "m1" in run(["status"], d).stdout)


def test_apply_gated_on_review():
    d = tmp()
    run(["draft", "m1", "--sql", "CREATE TABLE t(id int)"], d)
    r = run(["apply", "m1"], d)
    check("AT-2 apply fails closed without approval (mandatory pause)", r.returncode != 0)
    check("AT-2 names the missing review", "approv" in (r.stdout + r.stderr).lower())


def test_approve_unlocks_apply():
    d = tmp()
    run(["draft", "m1", "--sql", "CREATE TABLE t(id int)"], d)
    ra = run(["approve", "m1", "--by", "alice"], d)
    approved_state = rec(d, "m1").get("state")  # capture BEFORE apply advances it
    rp = run(["apply", "m1"], d)
    check("AT-3 approve sets state approved", ra.returncode == 0 and approved_state == "approved", approved_state)
    check("AT-3 apply succeeds after approval", rp.returncode == 0 and rec(d, "m1").get("state") == "applied", rp.stderr)


def test_bare_destructive_blocked():
    d = tmp()
    run(["draft", "m2", "--sql", "DROP TABLE users"], d)
    check("AT-4 destructive flagged at draft", rec(d, "m2").get("destructive") is True, str(rec(d, "m2")))
    run(["approve", "m2", "--by", "alice"], d)
    r = run(["apply", "m2"], d)
    check("AT-4 bare destructive apply fails closed", r.returncode != 0)
    check("AT-4 names the 2-stage requirement", "stage" in (r.stdout + r.stderr).lower() or "destructive" in (r.stdout + r.stderr).lower())
    # the staged variant is allowed
    run(["draft", "m3", "--sql", "DROP TABLE users", "--staged"], d)
    run(["approve", "m3", "--by", "alice"], d)
    r2 = run(["apply", "m3"], d)
    check("AT-4 staged destructive apply is allowed", r2.returncode == 0, r2.stderr)


def test_audit_trail():
    d = tmp()
    run(["draft", "m1", "--sql", "CREATE TABLE t(id int)"], d, actor="drafter")
    run(["approve", "m1", "--by", "reviewer"], d)
    run(["apply", "m1"], d, actor="applier")
    hist = rec(d, "m1").get("history", [])
    states = {h.get("state"): h.get("by") for h in hist}
    check("AT-5 history records drafted/approved/applied with who",
          states.get("drafted") == "drafter" and states.get("approved") == "reviewer"
          and states.get("applied") == "applier", str(hist))


def test_full_lifecycle():
    d = tmp()
    run(["draft", "m1", "--sql", "CREATE TABLE t(id int)"], d)
    run(["approve", "m1", "--by", "alice"], d)
    run(["apply", "m1"], d)
    rv = run(["verify", "m1"], d)
    check("AT-6 verify advances to verified", rv.returncode == 0 and rec(d, "m1").get("state") == "verified", rv.stderr)
    check("AT-6 status reflects final state", "verified" in run(["status"], d).stdout)


def main():
    print("PRD-023 gated-migration choreography — acceptance tests")
    test_draft_records()
    test_apply_gated_on_review()
    test_approve_unlocks_apply()
    test_bare_destructive_blocked()
    test_audit_trail()
    test_full_lifecycle()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
