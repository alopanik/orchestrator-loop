#!/usr/bin/env python3
"""Tests for the team provenance ledger (PRD-020): every ledger decision records who · commit ·
branch, from both writers, surfaced, and graceful outside git. Self-contained (temp git repos).

Run: python3 test/harness/test_provenance.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CI_GATE = os.path.join(REPO, "hooks", "ci_gate.py")
STOP_GATE = os.path.join(REPO, "hooks", "stop_gate.py")
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


def _git(d, *args):
    return subprocess.run(["git", "-C", d, *args], capture_output=True, text=True)


def git_repo():
    d = tempfile.mkdtemp(prefix="ol-prov-")
    os.makedirs(os.path.join(d, ".orchestrator"), exist_ok=True)
    _git(d, "init", "-q")
    _git(d, "config", "user.name", "Test User")
    _git(d, "config", "user.email", "t@e.com")
    open(os.path.join(d, "f.txt"), "w").write("x")
    _git(d, "add", "-A")
    _git(d, "commit", "-q", "-m", "init")
    with open(os.path.join(d, ".orchestrator", "ci-gate.json"), "w") as f:
        json.dump({"checks": [{"name": "ok", "cmd": "true", "fast": True}]}, f)
    return d


def run(argv, d, env_extra=None):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=d)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(argv, cwd=d, capture_output=True, text=True, env=env)


def newest_entry(d):
    p = os.path.join(d, ".orchestrator", "ledger.jsonl")
    lines = [l for l in open(p).read().splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else {}


def test_fields_present_and_actor_override():
    d = git_repo()
    run([PY, CI_GATE], d, {"OL_ACTOR": "alice"})
    e = newest_entry(d)
    check("AT-1 actor/commit/branch present", all(e.get(k) for k in ("actor", "commit", "branch")), str(e))
    check("AT-2 OL_ACTOR overrides actor", e.get("actor") == "alice", e.get("actor"))


def test_actor_fallback():
    d = git_repo()
    env = dict(os.environ)
    env.pop("OL_ACTOR", None)
    run([PY, CI_GATE], d)  # no OL_ACTOR -> git user.name "Test User"
    e = newest_entry(d)
    check("AT-2 actor falls back to a non-empty value", bool(e.get("actor")) and e.get("actor") != "unknown", e.get("actor"))


def test_commit_is_real():
    d = git_repo()
    run([PY, CI_GATE], d)
    e = newest_entry(d)
    head = _git(d, "rev-parse", "--short", "HEAD").stdout.strip()
    check("AT-3 commit == git HEAD short sha", e.get("commit") == head, f"entry={e.get('commit')} head={head}")


def test_surface_shows_provenance():
    d = git_repo()
    run([PY, CI_GATE], d, {"OL_ACTOR": "carol"})
    out = run([PY, STOP_GATE, "ledger"], d).stdout
    head = _git(d, "rev-parse", "--short", "HEAD").stdout.strip()
    check("AT-4 ledger surface shows actor", "carol" in out, out)
    check("AT-4 ledger surface shows commit", head in out, out)


def test_both_writers():
    d = git_repo()
    run([PY, CI_GATE], d, {"OL_ACTOR": "dave"})           # ci-gate writer
    run([PY, STOP_GATE, "set", "PRD-T", "true"], d)
    # trigger stop_gate hook mode (reads Stop-event JSON on stdin) to append a stop-gate entry
    env = dict(os.environ, CLAUDE_PROJECT_DIR=d, OL_ACTOR="dave")
    subprocess.run([PY, STOP_GATE], cwd=d, input="{}", capture_output=True, text=True, env=env)
    p = os.path.join(d, ".orchestrator", "ledger.jsonl")
    entries = [json.loads(l) for l in open(p).read().splitlines() if l.strip()]
    sources = {e.get("source") for e in entries}
    have_prov = all(e.get("actor") and e.get("commit") for e in entries)
    check("AT-5 both ci-gate and stop-gate decisions recorded", {"ci-gate", "stop-gate"} <= sources, sources)
    check("AT-5 every entry from both writers carries provenance", have_prov, str(entries))


def test_graceful_outside_git():
    d = tempfile.mkdtemp(prefix="ol-nogit-")
    os.makedirs(os.path.join(d, ".orchestrator"), exist_ok=True)
    with open(os.path.join(d, ".orchestrator", "ci-gate.json"), "w") as f:
        json.dump({"checks": [{"name": "ok", "cmd": "true", "fast": True}]}, f)
    r = run([PY, CI_GATE], d)
    e = newest_entry(d)
    check("AT-6 gate still records outside a git repo", e.get("decision") == "pass", str(e))
    check("AT-6 commit degrades to 'unknown' (no crash)", e.get("commit") == "unknown" and r.returncode == 0, str(e))


def main():
    print("PRD-020 team provenance ledger — acceptance tests")
    test_fields_present_and_actor_override()
    test_actor_fallback()
    test_commit_is_real()
    test_surface_shows_provenance()
    test_both_writers()
    test_graceful_outside_git()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
