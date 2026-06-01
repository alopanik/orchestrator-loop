#!/usr/bin/env python3
"""Tests for dispatch.py (PRD-012). Run: python3 test/harness/test_dispatch.py"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DISP = os.path.join(HERE, "dispatch.py")
PY = sys.executable


def run(pdir, *args):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=pdir)
    env.pop("OL_ROLE", None)  # the dispatcher must set it, not us
    return subprocess.run([PY, DISP, *args], env=env, capture_output=True, text=True)


def logtext(pdir):
    p = os.path.join(pdir, ".orchestrator", "executor.log")
    return open(p).read() if os.path.exists(p) else ""


def statustext(pdir):
    p = os.path.join(pdir, ".orchestrator", "executor.status")
    return open(p).read() if os.path.exists(p) else ""


CASES = []
def case(n):
    def deco(fn): CASES.append((n, fn)); return fn
    return deco


@case("AT-1 live+logged: executor output is streamed and logged")
def _(d):
    r = run(d, "run", "--cmd", 'printf "line1\\nline2\\n"')
    streamed = "line1" in r.stdout and "line2" in r.stdout
    logged = "line1" in logtext(d) and "line2" in logtext(d)
    return streamed and logged, f"streamed={streamed} logged={logged}"


@case("AT-2 role stamped: executor sees OL_ROLE=executor")
def _(d):
    r = run(d, "run", "--cmd", 'echo role=$OL_ROLE')
    return "role=executor" in (r.stdout + logtext(d)), f"out={r.stdout!r}"


@case("AT-3 status records the real exit code; dispatch returns it")
def _(d):
    r = run(d, "run", "--cmd", "exit 7")
    return r.returncode == 7 and "exited 7" in statustext(d), f"rc={r.returncode} status={statustext(d)!r}"


@case("AT-3b success path: exit 0 recorded")
def _(d):
    r = run(d, "run", "--cmd", "true")
    return r.returncode == 0 and "exited 0" in statustext(d), f"rc={r.returncode}"


@case("AT-4 watch reads the log")
def _(d):
    run(d, "run", "--cmd", 'echo hello-watch')
    r = run(d, "watch")
    return "hello-watch" in r.stdout, f"watch out={r.stdout!r}"


@case("brief is delivered on stdin")
def _(d):
    r = run(d, "run", "--cmd", "cat", "--brief", "BRIEF-PAYLOAD-123")
    return "BRIEF-PAYLOAD-123" in (r.stdout + logtext(d)), f"out={r.stdout!r}"


def main():
    p = f = 0
    for name, fn in CASES:
        with tempfile.TemporaryDirectory() as d:
            try:
                ok, detail = fn(d)
            except Exception as e:
                ok, detail = False, f"raised {e}"
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}  ({detail})")
        p += ok; f += not ok
    print()
    if f:
        print(f"dispatch tests FAILED: {f}/{len(CASES)}", file=sys.stderr); return 1
    print(f"dispatch tests PASSED: {p}/{len(CASES)} ✓"); return 0


if __name__ == "__main__":
    sys.exit(main())
