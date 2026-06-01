#!/usr/bin/env python3
"""Tests for preflight.py (PRD-010). Run: python3 test/harness/test_preflight.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PF = os.path.join(HERE, "preflight.py")
PY = sys.executable


def check(pdir, manifest):
    os.makedirs(os.path.join(pdir, ".orchestrator"), exist_ok=True)
    with open(os.path.join(pdir, ".orchestrator", "connectors.json"), "w") as f:
        json.dump(manifest, f)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=pdir)
    return subprocess.run([PY, PF, "check"], env=env, capture_output=True, text=True)


CASES = []
def case(n):
    def deco(fn): CASES.append((n, fn)); return fn
    return deco


@case("match -> pass (exit 0)")
def _(d):
    r = check(d, [{"category": "~~database", "expected": "abc123", "probe": "echo project=abc123"}])
    return r.returncode == 0, f"exit {r.returncode}"


@case("mismatch -> block (exit 1, names it)")
def _(d):
    r = check(d, [{"category": "~~database", "expected": "abc123", "probe": "echo project=WRONG999"}])
    return r.returncode == 1 and "MISMATCH" in (r.stdout + r.stderr), f"exit {r.returncode}"


@case("fail-closed: missing probe -> block")
def _(d):
    r = check(d, [{"category": "~~hosting", "expected": "vercel-xyz"}])
    return r.returncode == 1, f"exit {r.returncode}"


@case("fail-closed: probe errors -> block")
def _(d):
    r = check(d, [{"category": "~~vcs", "expected": "org/repo", "probe": "exit 3"}])
    return r.returncode == 1, f"exit {r.returncode}"


@case("multiple connectors, one wrong -> block")
def _(d):
    r = check(d, [
        {"category": "~~database", "expected": "db1", "probe": "echo db1"},
        {"category": "~~hosting", "expected": "host1", "probe": "echo host2"},
    ])
    return r.returncode == 1, f"exit {r.returncode}"


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
        print(f"preflight tests FAILED: {f}/{len(CASES)}", file=sys.stderr); return 1
    print(f"preflight tests PASSED: {p}/{len(CASES)} ✓"); return 0


if __name__ == "__main__":
    sys.exit(main())
