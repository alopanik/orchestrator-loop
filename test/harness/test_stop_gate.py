#!/usr/bin/env python3
"""Unit tests for hooks/stop_gate.py (PRD-004) — the fail-closed Stop gate.

No live Claude Code needed: we invoke the hook script as a subprocess with a synthetic
CLAUDE_PROJECT_DIR + Stop-event JSON on stdin and assert the exit code (0 = allow stop,
2 = block). Run: python3 test/harness/test_stop_gate.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "..", "..", "hooks", "stop_gate.py")
PY = sys.executable


def run_hook(pdir, stdin_obj):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=pdir)
    p = subprocess.run([PY, GATE], input=json.dumps(stdin_obj), env=env,
                       capture_output=True, text=True)
    return p.returncode, p.stderr


def manage(pdir, *args):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=pdir)
    return subprocess.run([PY, GATE, *args], env=env, capture_output=True, text=True)


def write_manifest(pdir, obj, raw=None):
    os.makedirs(os.path.join(pdir, ".orchestrator"), exist_ok=True)
    p = os.path.join(pdir, ".orchestrator", "gate.json")
    with open(p, "w") as f:
        f.write(raw if raw is not None else json.dumps(obj))


CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


@case("no gate manifest -> allow (exit 0)")
def _(pdir):
    rc, _ = run_hook(pdir, {})
    return rc == 0, f"exit {rc}"


@case("active gate, check passes -> allow (exit 0)")
def _(pdir):
    write_manifest(pdir, {"prd": "T", "active": True, "checks": [{"name": "ok", "cmd": "true"}]})
    rc, _ = run_hook(pdir, {})
    return rc == 0, f"exit {rc}"


@case("active gate, check fails -> BLOCK (exit 2)")
def _(pdir):
    write_manifest(pdir, {"prd": "T", "active": True, "checks": [{"name": "bad", "cmd": "false"}]})
    rc, err = run_hook(pdir, {})
    return rc == 2 and "bad" in err, f"exit {rc}; stderr={err!r}"


@case("fail-closed: missing command -> BLOCK (exit 2)")
def _(pdir):
    write_manifest(pdir, {"prd": "T", "active": True,
                          "checks": [{"name": "missing", "cmd": "this_cmd_does_not_exist_123 --x"}]})
    rc, _ = run_hook(pdir, {})
    return rc == 2, f"exit {rc}"


@case("corrupt manifest -> BLOCK (exit 2)")
def _(pdir):
    write_manifest(pdir, None, raw="{not valid json")
    rc, _ = run_hook(pdir, {})
    return rc == 2, f"exit {rc}"


@case("inactive manifest -> allow (exit 0)")
def _(pdir):
    write_manifest(pdir, {"active": False})
    rc, _ = run_hook(pdir, {})
    return rc == 0, f"exit {rc}"


@case("stop_hook_active=true, check still failing -> BLOCK (exit 2)")
def _(pdir):
    write_manifest(pdir, {"prd": "T", "active": True, "checks": [{"name": "bad", "cmd": "false"}]})
    rc, _ = run_hook(pdir, {"stop_hook_active": True})
    return rc == 2, f"exit {rc}"


@case("clear deactivates a failing gate -> allow (exit 0)")
def _(pdir):
    write_manifest(pdir, {"prd": "T", "active": True, "checks": [{"name": "bad", "cmd": "false"}]})
    manage(pdir, "clear")
    rc, _ = run_hook(pdir, {})
    return rc == 0, f"exit {rc}"


@case("set + check: passing checks -> check exits 0")
def _(pdir):
    manage(pdir, "set", "PRD-X", "true", "true")
    r = manage(pdir, "check")
    return r.returncode == 0, f"check exit {r.returncode}"


@case("set + check: a failing check -> check exits 1")
def _(pdir):
    manage(pdir, "set", "PRD-X", "true", "false")
    r = manage(pdir, "check")
    return r.returncode == 1, f"check exit {r.returncode}"


def read_ledger(pdir):
    p = os.path.join(pdir, ".orchestrator", "ledger.jsonl")
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]


@case("ledger: a block writes a block entry carrying the failing check's evidence")
def _(pdir):
    write_manifest(pdir, {"prd": "L1", "active": True, "checks": [{"name": "bad", "cmd": "false"}]})
    run_hook(pdir, {})
    led = read_ledger(pdir)
    if not led:
        return False, "no ledger entry"
    e = led[-1]
    ok = e.get("decision") == "block" and any(c["name"] == "bad" and not c["ok"] for c in e.get("checks", []))
    return ok, f"last entry={e}"


@case("ledger: a pass writes a pass entry")
def _(pdir):
    write_manifest(pdir, {"prd": "L2", "active": True, "checks": [{"name": "ok", "cmd": "true"}]})
    run_hook(pdir, {})
    led = read_ledger(pdir)
    return bool(led) and led[-1].get("decision") == "pass", f"ledger={led}"


@case("ledger: summary surface renders a line")
def _(pdir):
    write_manifest(pdir, {"prd": "L3", "active": True, "checks": [{"name": "bad", "cmd": "false"}]})
    run_hook(pdir, {})
    r = manage(pdir, "ledger")
    return "BLOCK" in r.stdout and "L3" in r.stdout, f"stdout={r.stdout!r}"


def main():
    passed = failed = 0
    for name, fn in CASES:
        with tempfile.TemporaryDirectory() as d:
            try:
                ok, detail = fn(d)
            except Exception as e:
                ok, detail = False, f"raised {e}"
        mark = "ok " if ok else "FAIL"
        print(f"  [{mark}] {name}  ({detail})")
        passed += ok
        failed += not ok
    print()
    if failed:
        print(f"stop_gate tests FAILED: {failed}/{len(CASES)}", file=sys.stderr)
        return 1
    print(f"stop_gate tests PASSED: {passed}/{len(CASES)} ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
