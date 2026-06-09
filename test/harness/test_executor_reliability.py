#!/usr/bin/env python3
"""Tests for executor reliability (PRD-017): dispatch.py outcome + timeout, and the
check_executor.py outcome gate. Self-contained; toy executors, no real model.

Run: python3 test/harness/test_executor_reliability.py
"""
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DISPATCH = os.path.join(HERE, "dispatch.py")
CHECK = os.path.join(HERE, "check_executor.py")
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
    d = tempfile.mkdtemp(prefix="ol-exec-")
    os.makedirs(os.path.join(d, ".orchestrator"), exist_ok=True)
    return d


def dispatch(d, cmd, timeout=None):
    argv = [PY, DISPATCH, "run", "--cmd", cmd]
    if timeout is not None:
        argv += ["--timeout", str(timeout)]
    env = dict(os.environ, CLAUDE_PROJECT_DIR=d)
    return subprocess.run(argv, capture_output=True, text=True, env=env)


def run_check(d):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=d)
    return subprocess.run([PY, CHECK, "check"], capture_output=True, text=True, env=env)


def outcome(d):
    p = os.path.join(d, ".orchestrator", "executor.outcome.json")
    return json.load(open(p)) if os.path.exists(p) else None


def test_clean_passes():
    d = tmp()
    dispatch(d, "sh -c 'exit 0'")
    o = outcome(d)
    check("AT-1 clean run -> state ok", o and o.get("state") == "ok", str(o))
    r = run_check(d)
    check("AT-1 gate passes on a clean outcome", r.returncode == 0, r.stderr)


def test_failure_fails_closed():
    d = tmp()
    dispatch(d, "sh -c 'exit 3'")
    o = outcome(d)
    check("AT-2 failed run -> state failed, code 3",
          o and o.get("state") == "failed" and o.get("code") == 3, str(o))
    r = run_check(d)
    check("AT-2 gate fails closed on failure", r.returncode != 0)
    check("AT-2 failure is named", "fail" in (r.stdout + r.stderr).lower())


def test_timeout_is_bounded():
    d = tmp()
    t0 = time.time()
    r = dispatch(d, "sh -c 'sleep 30'", timeout=1)
    elapsed = time.time() - t0
    o = outcome(d)
    check("AT-3 a hang is bounded (returned well under 30s)", elapsed < 15, f"elapsed={elapsed:.1f}s")
    check("AT-3 timeout -> state timeout", o and o.get("state") == "timeout", str(o))
    check("AT-3 dispatch reports nonzero on timeout", r.returncode != 0)
    check("AT-3 gate fails closed after timeout", run_check(d).returncode != 0)


def test_stale_running_is_a_crash():
    d = tmp()
    # fabricate an interrupted dispatch: state 'running' with a pid that is not alive
    dead_pid = 999999
    with open(os.path.join(d, ".orchestrator", "executor.outcome.json"), "w") as f:
        json.dump({"state": "running", "pid": dead_pid, "started": "x", "code": None}, f)
    r = run_check(d)
    check("AT-4 stale running (dead pid) fails closed", r.returncode != 0)
    check("AT-4 reported as a crash, not in-flight or done",
          "crash" in (r.stdout + r.stderr).lower())


def test_no_dispatch_is_dormant():
    d = tmp()  # no outcome file at all
    r = run_check(d)
    check("AT-5 no outcome -> dormant pass", r.returncode == 0, r.stderr)


def test_launch_error_not_running():
    d = tmp()
    dispatch(d, "this-binary-does-not-exist-xyz --nope")
    o = outcome(d)
    check("AT-6 bad command is not left 'running'",
          o and o.get("state") != "running", str(o))
    check("AT-6 gate fails closed on a bad launch", run_check(d).returncode != 0)


def main():
    print("PRD-017 executor reliability — acceptance tests")
    test_clean_passes()
    test_failure_fails_closed()
    test_timeout_is_bounded()
    test_stale_running_is_a_crash()
    test_no_dispatch_is_dormant()
    test_launch_error_not_running()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
