#!/usr/bin/env python3
"""Tests for check_tests.py (PRD-005). Builds throwaway git repos in /tmp and exercises:
  - baseline errors if the test is already green (must be red first)
  - happy path: red baseline -> impl makes it green, test untouched -> verify PASS
  - tamper path: test file edited after baseline -> verify FAIL
Run: python3 test/harness/test_check_tests.py
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "check_tests.py")
PY = sys.executable


def sh(d, *cmd):
    return subprocess.run(cmd, cwd=d, capture_output=True, text=True)


def git(d, *args):
    return sh(d, "git", *args)


def check(d, *args):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=d)
    return subprocess.run([PY, CHECK, *args], cwd=d, env=env, capture_output=True, text=True)


def init_repo(d, f_returns):
    git(d, "init", "-q")
    git(d, "config", "user.email", "t@t")
    git(d, "config", "user.name", "t")
    open(os.path.join(d, "impl.py"), "w").write(f"def f():\n    return {f_returns}\n")
    # the test passes only when impl.f() == 42
    open(os.path.join(d, "test_impl.py"), "w").write(
        "import impl, sys\nsys.exit(0 if impl.f() == 42 else 1)\n")
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "initial")


CASES = []
def case(n):
    def deco(fn): CASES.append((n, fn)); return fn
    return deco


@case("baseline errors when tests already pass (must be red first)")
def _(d):
    init_repo(d, 42)  # already green
    r = check(d, "baseline", "--cmd", f"{PY} test_impl.py", "--tests", "test_impl.py")
    return r.returncode != 0, f"baseline exit {r.returncode} (want nonzero)"


@case("happy path: red baseline -> impl fixes it, test untouched -> verify PASS")
def _(d):
    init_repo(d, 0)  # red
    r = check(d, "baseline", "--cmd", f"{PY} test_impl.py", "--tests", "test_impl.py")
    if r.returncode != 0:
        return False, f"baseline should pass on red, got {r.returncode}: {r.stderr}"
    # implement the fix WITHOUT touching the test
    open(os.path.join(d, "impl.py"), "w").write("def f():\n    return 42\n")
    v = check(d, "verify")
    return v.returncode == 0, f"verify exit {v.returncode} (want 0): {v.stderr}"


@case("tamper path: test edited after baseline -> verify FAIL")
def _(d):
    init_repo(d, 0)  # red
    check(d, "baseline", "--cmd", f"{PY} test_impl.py", "--tests", "test_impl.py")
    # cheat: rewrite the test to always pass instead of fixing impl
    open(os.path.join(d, "test_impl.py"), "w").write("import sys\nsys.exit(0)\n")
    v = check(d, "verify")
    return v.returncode != 0 and "test_impl.py" in v.stderr, f"verify exit {v.returncode}; stderr={v.stderr!r}"


@case("untampered but still red -> verify FAIL")
def _(d):
    init_repo(d, 0)  # red
    check(d, "baseline", "--cmd", f"{PY} test_impl.py", "--tests", "test_impl.py")
    # do nothing — impl still wrong, test untouched
    v = check(d, "verify")
    return v.returncode != 0, f"verify exit {v.returncode} (want nonzero)"


def main():
    passed = failed = 0
    for name, fn in CASES:
        with tempfile.TemporaryDirectory() as d:
            try:
                ok, detail = fn(d)
            except Exception as e:
                ok, detail = False, f"raised {e}"
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}  ({detail})")
        passed += ok; failed += not ok
    print()
    if failed:
        print(f"check_tests tests FAILED: {failed}/{len(CASES)}", file=sys.stderr)
        return 1
    print(f"check_tests tests PASSED: {passed}/{len(CASES)} ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
