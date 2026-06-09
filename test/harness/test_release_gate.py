#!/usr/bin/env python3
"""Tests for the multi-hand release gate (PRD-022): owner sign-off recorded + enforced, and the
scaffold emits a release workflow. Self-contained.

Run: python3 test/harness/test_release_gate.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
RELEASE = os.path.join(HERE, "release.py")
SCAFFOLD = os.path.join(REPO, "skills", "bootstrap-cicd", "scaffold.py")
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


def plugin_repo(version="0.7.0", owner="Andrew Lopanik"):
    d = tempfile.mkdtemp(prefix="ol-rel-")
    os.makedirs(os.path.join(d, ".claude-plugin"))
    os.makedirs(os.path.join(d, ".orchestrator"))
    json.dump({"name": "x", "version": version},
              open(os.path.join(d, ".claude-plugin", "plugin.json"), "w"))
    json.dump({"name": "x", "owner": {"name": owner}, "metadata": {"version": version},
               "plugins": [{"name": "x", "version": version}]},
              open(os.path.join(d, ".claude-plugin", "marketplace.json"), "w"))
    subprocess.run(["git", "-C", d, "init", "-q"])
    subprocess.run(["git", "-C", d, "config", "user.name", "t"])
    subprocess.run(["git", "-C", d, "config", "user.email", "t@e.com"])
    open(os.path.join(d, "f"), "w").write("x")
    subprocess.run(["git", "-C", d, "add", "-A"])
    subprocess.run(["git", "-C", d, "commit", "-q", "-m", "i"])
    return d


def run(argv, d):
    return subprocess.run(argv, cwd=d, capture_output=True, text=True,
                          env=dict(os.environ, CLAUDE_PROJECT_DIR=d))


def set_version(d, v):
    for rel in (("plugin.json",), ("marketplace.json",)):
        p = os.path.join(d, ".claude-plugin", rel[0])
        obj = json.load(open(p))
        obj["version"] = v
        if "metadata" in obj:
            obj["metadata"]["version"] = v
        for pl in obj.get("plugins", []):
            pl["version"] = v
        json.dump(obj, open(p, "w"))


def signoff_obj(d):
    p = os.path.join(d, ".orchestrator", "release-signoff.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def test_unsigned_bump_blocked():
    d = plugin_repo("0.7.0")
    set_version(d, "0.8.0")  # bumped, not signed
    r = run([PY, RELEASE, "check"], d)
    check("AT-1 unsigned version bump fails closed", r.returncode != 0)
    check("AT-1 pending version named", "0.8.0" in (r.stdout + r.stderr), r.stdout + r.stderr)


def test_owner_signoff_passes():
    d = plugin_repo("0.7.0")
    set_version(d, "0.8.0")
    rs = run([PY, RELEASE, "signoff", "--by", "Andrew Lopanik"], d)
    rc = run([PY, RELEASE, "check"], d)
    check("AT-2 owner signoff recorded", rs.returncode == 0 and signoff_obj(d).get("version") == "0.8.0", rs.stderr)
    check("AT-2 check passes after owner signoff", rc.returncode == 0, rc.stderr)


def test_non_owner_rejected():
    d = plugin_repo("0.7.0")
    set_version(d, "0.8.0")
    rs = run([PY, RELEASE, "signoff", "--by", "mallory"], d)
    check("AT-3 non-owner signoff is refused", rs.returncode != 0 and not signoff_obj(d), rs.stdout + rs.stderr)
    # fabricated record whose 'by' is not an owner -> check rejects
    json.dump({"version": "0.8.0", "by": "mallory", "ts": "x", "commit": "y"},
              open(os.path.join(d, ".orchestrator", "release-signoff.json"), "w"))
    rc = run([PY, RELEASE, "check"], d)
    check("AT-3 fabricated non-owner signoff rejected by check", rc.returncode != 0)


def test_no_pending_passes():
    d = plugin_repo("0.7.0")  # no bump
    run([PY, RELEASE, "signoff", "--by", "Andrew Lopanik"], d)
    rc = run([PY, RELEASE, "check"], d)
    check("AT-4 no pending release (signed == manifest) passes", rc.returncode == 0, rc.stderr)


def test_scaffold_emits_release_workflow():
    d = tempfile.mkdtemp(prefix="ol-relwf-")
    os.makedirs(os.path.join(d, ".orchestrator"))
    open(os.path.join(d, "CLAUDE.md"), "w").write("# x\n")
    run([PY, SCAFFOLD, "install", "--ci", "github", "--vcs", "git", "--repo", d], REPO)
    wf = os.path.join(d, ".github", "workflows", "orchestrator-release.yml")
    check("AT-5 scaffold emits a release workflow", os.path.exists(wf))
    if os.path.exists(wf):
        txt = open(wf).read()
        check("AT-5 release workflow runs release.py check", "release.py check" in txt, txt)


def test_owners_resolution():
    # policy file wins
    d = plugin_repo("0.8.0", owner="MarketOwner")
    json.dump({"owners": ["PolicyOwner"]}, open(os.path.join(d, ".orchestrator", "release-policy.json"), "w"))
    r1 = run([PY, RELEASE, "signoff", "--by", "PolicyOwner"], d)
    r2 = run([PY, RELEASE, "signoff", "--by", "MarketOwner"], d)
    check("AT-6 policy owners win when present", r1.returncode == 0 and r2.returncode != 0,
          f"policy={r1.returncode} market={r2.returncode}")
    # without policy, marketplace owner is authorized
    d2 = plugin_repo("0.8.0", owner="MarketOwner")
    r3 = run([PY, RELEASE, "signoff", "--by", "MarketOwner"], d2)
    check("AT-6 marketplace owner authorized without a policy file", r3.returncode == 0, r3.stderr)


def main():
    print("PRD-022 multi-hand release gate — acceptance tests")
    test_unsigned_bump_blocked()
    test_owner_signoff_passes()
    test_non_owner_rejected()
    test_no_pending_passes()
    test_scaffold_emits_release_workflow()
    test_owners_resolution()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
