#!/usr/bin/env python3
"""Tests for the shared-state restructure (PRD-018): per-PRD state files, the generated ROADMAP
status view, and the concurrency-safe ledger. Self-contained.

Run: python3 test/harness/test_shared_state.py
"""
import json
import os
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
PRD_STATE = os.path.join(HERE, "prd_state.py")
ROADMAP_STATUS = os.path.join(HERE, "roadmap_status.py")
CHECK_LEDGER = os.path.join(HERE, "check_ledger.py")
CI_GATE = os.path.join(os.path.dirname(os.path.dirname(HERE)), "hooks", "ci_gate.py")  # hooks/, not test/harness/
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
    d = tempfile.mkdtemp(prefix="ol-state-")
    os.makedirs(os.path.join(d, ".orchestrator"), exist_ok=True)
    return d


def run(argv, d):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=d)
    return subprocess.run([PY, *argv], capture_output=True, text=True, env=env)


def test_different_prds_dont_contend():
    d = tmp()
    ids = [f"PRD-1{i:02d}" for i in range(10)]

    def setter(i):
        run([PRD_STATE, "set", ids[i], "shipped"], d)
    threads = [threading.Thread(target=setter, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    landed = 0
    for i in ids:
        p = os.path.join(d, ".orchestrator", "prds", f"{i}.json")
        if os.path.exists(p) and json.load(open(p)).get("status") == "shipped":
            landed += 1
    check("AT-1 10 concurrent sets on distinct PRDs all land", landed == 10, f"landed={landed}/10")


def test_same_prd_is_atomic():
    d = tmp()
    vals = ["planned", "claimed", "building", "verifying", "shipped"]

    def setter(v):
        for _ in range(5):
            run([PRD_STATE, "set", "PRD-SAME", v], d)
    threads = [threading.Thread(target=setter, args=(v,)) for v in vals]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    p = os.path.join(d, ".orchestrator", "prds", "PRD-SAME.json")
    try:
        obj = json.load(open(p))
        ok = obj.get("status") in vals
    except Exception as e:
        ok = False
        obj = str(e)
    check("AT-2 concurrent same-PRD writes never tear the file", ok, str(obj))


def _seed(d, shipped, planned):
    for i in shipped:
        run([PRD_STATE, "set", f"PRD-{i}", "shipped"], d)
    for i in planned:
        run([PRD_STATE, "set", f"PRD-{i}", "planned"], d)


def test_status_generated_and_drift_guarded():
    d = tmp()
    with open(os.path.join(d, "ROADMAP.md"), "w") as f:
        f.write("# Roadmap\n\n## Status\n\n## Notes\nhand-written history stays.\n")
    _seed(d, ["016", "017"], ["018", "019"])
    r = run([ROADMAP_STATUS, "render"], d)
    check("AT-3 render exits 0", r.returncode == 0, r.stderr)
    rm = open(os.path.join(d, "ROADMAP.md")).read()
    check("AT-3 managed status block written", "ORCHESTRATOR-LOOP:STATUS:BEGIN" in rm)
    check("AT-3 --check passes right after render", run([ROADMAP_STATUS, "--check"], d).returncode == 0)
    check("AT-3 hand-written history preserved", "hand-written history stays." in rm)
    # hand-edit the generated block -> drift -> --check fails
    tampered = rm.replace("016", "999")
    with open(os.path.join(d, "ROADMAP.md"), "w") as f:
        f.write(tampered)
    check("AT-3 --check fails on a hand-edited (stale) block",
          run([ROADMAP_STATUS, "--check"], d).returncode != 0)


def test_ledger_atomic_under_concurrency():
    d = tmp()
    with open(os.path.join(d, ".orchestrator", "ci-gate.json"), "w") as f:
        json.dump({"checks": [{"name": "ok", "cmd": "true", "fast": True}]}, f)

    def appender():
        subprocess.run([PY, CI_GATE], cwd=d, capture_output=True, text=True,
                       env=dict(os.environ, CLAUDE_PROJECT_DIR=d))
    threads = [threading.Thread(target=appender) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    led = os.path.join(d, ".orchestrator", "ledger.jsonl")
    if not os.path.exists(led):
        check("AT-4 20 concurrent appends produce 20 well-formed lines", False, "no ledger written")
        return
    lines = [ln for ln in open(led).read().splitlines() if ln.strip()]
    torn = 0
    for ln in lines:
        try:
            json.loads(ln)
        except Exception:
            torn += 1
    check("AT-4 20 concurrent appends produce 20 well-formed lines",
          len(lines) == 20 and torn == 0, f"lines={len(lines)} torn={torn}")
    check("AT-4 check_ledger passes on a clean ledger", run([CHECK_LEDGER, "check"], d).returncode == 0)
    with open(led, "a") as f:
        f.write('{"torn": tru')  # deliberately corrupt, no newline
    check("AT-4 check_ledger fails on a torn line", run([CHECK_LEDGER, "check"], d).returncode != 0)


def test_migration_complete_and_faithful():
    # The real repo migration is asserted against the real repo's state dir.
    repo = os.path.dirname(HERE)  # test/  -> repo via two dirs up below
    repo = os.path.dirname(os.path.dirname(HERE))
    prds_dir = os.path.join(repo, ".orchestrator", "prds")
    have = set()
    if os.path.isdir(prds_dir):
        have = {f[:-5] for f in os.listdir(prds_dir) if f.endswith(".json")}
    expected = {f"PRD-{i:03d}" for i in list(range(1, 18)) + list(range(18, 24))}
    missing = expected - have
    check("AT-5 every PRD 001-023 has a state file", not missing, f"missing={sorted(missing)}")
    # faithfulness: 016,017 shipped; 018 not shipped
    def status_of(pid):
        p = os.path.join(prds_dir, f"{pid}.json")
        return json.load(open(p)).get("status") if os.path.exists(p) else None
    # Faithful to the pre-migration truth, and stable as 018+ ship: 001-017 were shipped; the
    # late collaborator PRDs (023) start planned. (018's own status transitions as it ships, so
    # it is deliberately not pinned here.)
    all_17 = all(status_of(f"PRD-{i:03d}") == "shipped" for i in range(1, 18))
    check("AT-5 001-017 shipped and 023 not-yet (faithful to pre-migration truth)",
          all_17 and status_of("PRD-023") != "shipped",
          f"all 001-017 shipped={all_17}  023={status_of('PRD-023')}")


def test_constitution_invariant_retired():
    repo = os.path.dirname(os.path.dirname(HERE))
    arch = open(os.path.join(repo, "ARCHITECTURE.md")).read()
    check("AT-6 ARCHITECTURE no longer claims a single ledger writer",
          "One writer to the ledger." not in arch,
          "stale 'one writer' invariant still present")


def main():
    print("PRD-018 shared-state restructure — acceptance tests")
    test_different_prds_dont_contend()
    test_same_prd_is_atomic()
    test_status_generated_and_drift_guarded()
    test_ledger_atomic_under_concurrency()
    test_migration_complete_and_faithful()
    test_constitution_invariant_retired()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
