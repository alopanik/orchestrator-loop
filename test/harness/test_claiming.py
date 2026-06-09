#!/usr/bin/env python3
"""Tests for PRD claiming/ownership (PRD-019): atomic O_EXCL claim, release, stale reclaim,
branch binding. Self-contained; real parallel processes for the concurrency test.

Run: python3 test/harness/test_claiming.py
"""
import json
import os
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
PRD_STATE = os.path.join(HERE, "prd_state.py")
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
    d = tempfile.mkdtemp(prefix="ol-claim-")
    os.makedirs(os.path.join(d, ".orchestrator", "prds"), exist_ok=True)
    return d


def run(argv, d):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=d)
    return subprocess.run([PY, PRD_STATE, *argv], capture_output=True, text=True, env=env)


def claim_file(d, pid):
    return os.path.join(d, ".orchestrator", "prds", f"{pid}.claim")


def _read_claim(d, pid):
    p = claim_file(d, pid)
    if not os.path.exists(p):
        return {}
    try:
        return json.load(open(p))
    except Exception:
        return {}


def test_exactly_one_winner():
    d = tmp()
    results = []
    lock = threading.Lock()

    def claimer(i):
        r = run(["claim", "PRD-100", "--by", f"op{i}", "--branch", f"b{i}"], d)
        with lock:
            results.append(r.returncode)
    threads = [threading.Thread(target=claimer, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    winners = sum(1 for rc in results if rc == 0)
    check("AT-1 exactly one of 10 concurrent claims wins", winners == 1, f"winners={winners}")


def test_release_frees():
    d = tmp()
    run(["claim", "PRD-101", "--by", "a", "--branch", "b"], d)
    run(["release", "PRD-101"], d)
    r = run(["claim", "PRD-101", "--by", "c", "--branch", "d"], d)
    check("AT-2 release frees the claim", r.returncode == 0, r.stderr)


def test_identity_and_branch_recorded():
    d = tmp()
    run(["claim", "PRD-102", "--by", "alice", "--branch", "prd-102-foo"], d)
    obj = _read_claim(d, "PRD-102")
    listing = run(["claims"], d).stdout
    check("AT-3 claim records by+branch",
          obj.get("by") == "alice" and obj.get("branch") == "prd-102-foo", str(obj))
    check("AT-3 claims lists it", "alice" in listing and "prd-102-foo" in listing, listing)


def test_live_claim_not_stealable():
    d = tmp()
    run(["claim", "PRD-103", "--by", "alice", "--branch", "b1"], d)
    r1 = run(["claim", "PRD-103", "--by", "mallory", "--branch", "b2"], d)
    r2 = run(["claim", "PRD-103", "--by", "mallory", "--branch", "b2", "--force"], d)
    held_by = _read_claim(d, "PRD-103").get("by")
    check("AT-4 a fresh claim cannot be stolen", r1.returncode != 0 and r2.returncode != 0,
          f"r1={r1.returncode} r2={r2.returncode}")
    check("AT-4 original holder unchanged", held_by == "alice", f"held_by={held_by}")


def test_stale_reclaim():
    d = tmp()
    # fabricate a stale claim (ts well in the past)
    os.makedirs(os.path.dirname(claim_file(d, "PRD-104")), exist_ok=True)
    with open(claim_file(d, "PRD-104"), "w") as f:
        json.dump({"by": "ghost", "branch": "old", "ts": "2000-01-01T00:00:00"}, f)
    r = run(["claim", "PRD-104", "--by", "newbie", "--branch", "fresh", "--force"], d)
    held_by = _read_claim(d, "PRD-104").get("by")
    check("AT-5 a stale claim is reclaimable with --force", r.returncode == 0, r.stderr)
    check("AT-5 new holder recorded", held_by == "newbie", f"held_by={held_by}")


def test_claim_sets_state():
    d = tmp()
    run(["claim", "PRD-105", "--by", "a", "--branch", "b"], d)
    st = run(["get", "PRD-105"], d).stdout.strip()
    check("AT-6 a successful claim sets state to claimed", st == "claimed", f"state={st!r}")


def main():
    print("PRD-019 claiming — acceptance tests")
    test_exactly_one_winner()
    test_release_frees()
    test_identity_and_branch_recorded()
    test_live_claim_not_stealable()
    test_stale_reclaim()
    test_claim_sets_state()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
