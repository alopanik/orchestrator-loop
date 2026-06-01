#!/usr/bin/env python3
"""Tests for enforce_executor.py (PRD-011). Run: python3 test/harness/test_enforce_executor.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "..", "..", "hooks", "enforce_executor.py")
PY = sys.executable


def set_mode(pdir, mode):
    os.makedirs(os.path.join(pdir, ".orchestrator"), exist_ok=True)
    with open(os.path.join(pdir, ".orchestrator", "mode.json"), "w") as f:
        json.dump({"executor": mode}, f)


def run_hook(pdir, tool, role=None):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=pdir)
    env.pop("OL_ROLE", None)
    if role:
        env["OL_ROLE"] = role
    return subprocess.run([PY, HOOK], input=json.dumps({"tool_name": tool}),
                          env=env, capture_output=True, text=True)


CASES = []
def case(n):
    def deco(fn): CASES.append((n, fn)); return fn
    return deco


@case("power mode + Write + no role -> DENY (exit 2)")
def _(d):
    set_mode(d, "claude-code")
    r = run_hook(d, "Write")
    return r.returncode == 2 and "power mode" in r.stderr, f"exit {r.returncode}"


@case("power mode + Write + OL_ROLE=executor -> allow (exit 0)")
def _(d):
    set_mode(d, "claude-code")
    r = run_hook(d, "Write", role="executor")
    return r.returncode == 0, f"exit {r.returncode}"


@case("self mode + Write -> allow (exit 0)")
def _(d):
    set_mode(d, "self")
    r = run_hook(d, "Write")
    return r.returncode == 0, f"exit {r.returncode}"


@case("no mode file (default self) + Write -> allow")
def _(d):
    r = run_hook(d, "Write")
    return r.returncode == 0, f"exit {r.returncode}"


@case("power mode + non-mutation tool (Bash) -> allow")
def _(d):
    set_mode(d, "claude-code")
    r = run_hook(d, "Bash")
    return r.returncode == 0, f"exit {r.returncode}"


@case("power mode + Edit + no role -> DENY")
def _(d):
    set_mode(d, "claude-code")
    r = run_hook(d, "Edit")
    return r.returncode == 2, f"exit {r.returncode}"


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
        print(f"enforce_executor tests FAILED: {f}/{len(CASES)}", file=sys.stderr); return 1
    print(f"enforce_executor tests PASSED: {p}/{len(CASES)} ✓"); return 0


if __name__ == "__main__":
    sys.exit(main())
