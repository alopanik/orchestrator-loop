#!/usr/bin/env python3
"""Tests for separation of duties (PRD-021): planner != verifier, enforced when a team opts in,
dormant in solo. Self-contained.

Run: python3 test/harness/test_separation.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PRD_STATE = os.path.join(HERE, "prd_state.py")
CHECK_SEP = os.path.join(HERE, "check_separation.py")
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
    d = tempfile.mkdtemp(prefix="ol-sep-")
    os.makedirs(os.path.join(d, ".orchestrator", "prds"), exist_ok=True)
    return d


def set_status(d, pid, status, actor):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=d, OL_ACTOR=actor)
    return subprocess.run([PY, PRD_STATE, "set", pid, status], capture_output=True, text=True, env=env)


def check_sep(d, pid, require_env=False):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=d)
    env.pop("OL_REQUIRE_SEPARATION", None)
    if require_env:
        env["OL_REQUIRE_SEPARATION"] = "1"
    return subprocess.run([PY, CHECK_SEP, pid], capture_output=True, text=True, env=env)


def state(d, pid):
    num = "".join(c for c in pid if c.isdigit())  # prd_state normalizes PRD-N -> PRD-00N
    norm = f"PRD-{int(num):03d}" if num else pid
    p = os.path.join(d, ".orchestrator", "prds", f"{norm}.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def test_dormant_by_default():
    d = tmp()
    set_status(d, "PRD-1", "building", "alice")
    set_status(d, "PRD-1", "shipped", "alice")
    r = check_sep(d, "PRD-1", require_env=False)
    check("AT-1 dormant by default (solo is legitimate)", r.returncode == 0, r.stderr)


def test_same_principal_blocked():
    d = tmp()
    set_status(d, "PRD-2", "building", "alice")
    set_status(d, "PRD-2", "shipped", "alice")
    r = check_sep(d, "PRD-2", require_env=True)
    check("AT-2 same principal built+blessed -> fail closed", r.returncode != 0)
    check("AT-2 collision named", "alice" in (r.stdout + r.stderr).lower())


def test_distinct_principals_pass():
    d = tmp()
    set_status(d, "PRD-3", "building", "alice")
    set_status(d, "PRD-3", "shipped", "bob")
    r = check_sep(d, "PRD-3", require_env=True)
    check("AT-3 distinct builder/verifier -> pass when required", r.returncode == 0, r.stderr)


def test_history_recorded():
    d = tmp()
    set_status(d, "PRD-4", "building", "alice")
    set_status(d, "PRD-4", "shipped", "bob")
    st = state(d, "PRD-4")
    hist = st.get("history", [])
    bys = [h.get("by") for h in hist]
    check("AT-4 history records each transition's principal",
          len(hist) >= 2 and "alice" in bys and "bob" in bys, str(hist))
    check("AT-4 latest by matches last setter", st.get("by") == "bob", str(st))


def test_policy_file():
    d = tmp()
    with open(os.path.join(d, ".orchestrator", "policy.json"), "w") as f:
        json.dump({"require_separation": True}, f)
    set_status(d, "PRD-5", "building", "alice")
    set_status(d, "PRD-5", "shipped", "alice")
    r = check_sep(d, "PRD-5", require_env=False)  # policy from file, not env
    check("AT-5 policy file enforces separation", r.returncode != 0, r.stdout + r.stderr)


def test_insufficient_history_fails_closed():
    d = tmp()
    set_status(d, "PRD-6", "building", "alice")  # builder only, no independent verifier transition
    r = check_sep(d, "PRD-6", require_env=True)
    check("AT-6 insufficient history fails closed when required", r.returncode != 0)


def main():
    print("PRD-021 separation of duties — acceptance tests")
    test_dormant_by_default()
    test_same_principal_blocked()
    test_distinct_principals_pass()
    test_history_recorded()
    test_policy_file()
    test_insufficient_history_fails_closed()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
