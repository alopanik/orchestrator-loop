#!/usr/bin/env python3
"""Tests for bootstrap-cicd (PRD-016): scaffold.py generator + hooks/ci_gate.py engine +
the ratchet baseline-trust guard. Self-contained; uses throwaway target repos in /tmp.

Run: python3 test/harness/test_scaffold.py
Exit 0 iff every acceptance assertion (AT-1 .. AT-6) passes.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCAFFOLD = os.path.join(REPO, "skills", "bootstrap-cicd", "scaffold.py")
CI_GATE = os.path.join(REPO, "hooks", "ci_gate.py")
SKILL_MD = os.path.join(REPO, "skills", "bootstrap-cicd", "SKILL.md")
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


def run(cmd, cwd=None):
    env = dict(os.environ)
    if cwd:
        env["CLAUDE_PROJECT_DIR"] = cwd  # pin to the temp repo (robust to an ambient CLAUDE_PROJECT_DIR)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


def make_target():
    """A throwaway target repo: a CLAUDE.md with content that must survive, plus helper checks."""
    d = tempfile.mkdtemp(prefix="ol-cicd-")
    os.makedirs(os.path.join(d, ".orchestrator"), exist_ok=True)
    with open(os.path.join(d, "CLAUDE.md"), "w") as f:
        f.write("# App profile\n\nUNIQUE-EXISTING-CONTENT-must-survive\n")
    with open(os.path.join(d, "ok.sh"), "w") as f:
        f.write("exit 0\n")
    with open(os.path.join(d, "bad.sh"), "w") as f:
        f.write("echo boom >&2; exit 1\n")
    return d


def write_ci_gate(d, checks):
    with open(os.path.join(d, ".orchestrator", "ci-gate.json"), "w") as f:
        json.dump({"checks": checks}, f, indent=2)


def test_install_idempotent_and_artifacts():
    d = make_target()
    r1 = run([PY, SCAFFOLD, "install", "--ci", "github", "--vcs", "git", "--repo", d])
    check("install exits 0", r1.returncode == 0, r1.stderr)
    claude = open(os.path.join(d, "CLAUDE.md")).read()
    after1 = claude
    run([PY, SCAFFOLD, "install", "--ci", "github", "--vcs", "git", "--repo", d])
    after2 = open(os.path.join(d, "CLAUDE.md")).read()
    # AT-3
    check("AT-3 CLAUDE.md block byte-identical on re-run", after1 == after2)
    check("AT-3 exactly one managed block",
          after2.count("ORCHESTRATOR-LOOP:CI:BEGIN") == 1, f"count={after2.count('ORCHESTRATOR-LOOP:CI:BEGIN')}")
    check("AT-3 pre-existing content preserved", "UNIQUE-EXISTING-CONTENT-must-survive" in after2)
    # AT-1
    wf = os.path.join(d, ".github", "workflows", "orchestrator-gate.yml")
    check("AT-1 github workflow emitted", os.path.exists(wf))
    wf_txt = open(wf).read() if os.path.exists(wf) else ""
    check("AT-1 workflow calls the single entry point", "ci_gate.py" in wf_txt)
    check("AT-1 workflow has NO inline check list",
          re.search(r"self-test|check-startup|check-sync|pytest", wf_txt) is None,
          "found a re-listed check command in the workflow")
    # vendored engine present in target
    check("vendors ci_gate.py into target", os.path.exists(os.path.join(d, "hooks", "ci_gate.py")))
    # AT-6 hook installed
    hook = os.path.join(d, ".githooks", "pre-push")
    check("AT-6 pre-push hook installed", os.path.exists(hook))
    if os.path.exists(hook):
        check("AT-6 pre-push runs the fast gate", "--fast" in open(hook).read())


def test_parameterization_and_app_agnostic():
    d = make_target()
    run([PY, SCAFFOLD, "install", "--ci", "generic", "--vcs", "git", "--repo", d])
    # AT-4: generic emits a portable shell template, not a github workflow
    check("AT-4 generic emits portable template",
          os.path.exists(os.path.join(d, "orchestrator-gate.sh")))
    check("AT-4 generic does NOT emit a github workflow",
          not os.path.exists(os.path.join(d, ".github", "workflows", "orchestrator-gate.yml")))
    # AT-4: the SKILL prose names no concrete product (app-agnostic domain rule)
    if os.path.exists(SKILL_MD):
        skill = open(SKILL_MD).read().lower()
        check("AT-4 SKILL.md names no hardcoded product",
              re.search(r"github|vercel|supabase|gitlab|circleci", skill) is None,
              "SKILL.md must refer to ~~ci/~~vcs only")
    else:
        check("AT-4 SKILL.md exists", False, "missing skills/bootstrap-cicd/SKILL.md")


def test_ci_gate_enforces():
    d = make_target()
    # healthy
    write_ci_gate(d, [{"name": "ok", "cmd": "sh ok.sh", "fast": True}])
    r = run([PY, CI_GATE], cwd=d)
    check("AT-2 healthy tree passes", r.returncode == 0, r.stderr)
    # add a failing (non-fast) check
    write_ci_gate(d, [{"name": "ok", "cmd": "sh ok.sh", "fast": True},
                      {"name": "bad", "cmd": "sh bad.sh"}])
    r = run([PY, CI_GATE], cwd=d)
    check("AT-2 a red check fails the gate", r.returncode != 0)
    check("AT-2 failing check is named", "bad" in (r.stdout + r.stderr))
    led = os.path.join(d, ".orchestrator", "ledger.jsonl")
    led_txt = open(led).read() if os.path.exists(led) else ""
    check("AT-2 decision recorded to ledger with source ci-gate", "ci-gate" in led_txt)
    # --fast skips the non-fast failing check
    r = run([PY, CI_GATE, "--fast"], cwd=d)
    check("AT-2 --fast runs only fast checks", r.returncode == 0, r.stderr)


def test_ratchet_baseline_trust():
    # discriminating: signal passes, control fails -> they differ -> baseline allowed
    d = make_target()
    r = run([PY, SCAFFOLD, "ratchet-baseline", "--signal", "sh ok.sh",
             "--control", "sh bad.sh", "--repo", d])
    check("AT-5 discriminating signal is baselined", r.returncode == 0, r.stderr)
    check("AT-5 baseline file written",
          os.path.exists(os.path.join(d, ".orchestrator", "ci-baseline.json")))
    # non-discriminating: signal and control both pass -> no delta -> refuse
    d2 = make_target()
    r = run([PY, SCAFFOLD, "ratchet-baseline", "--signal", "sh ok.sh",
             "--control", "sh ok.sh", "--repo", d2])
    check("AT-5 non-discriminating signal is REFUSED", r.returncode != 0)
    check("AT-5 no baseline written on refusal",
          not os.path.exists(os.path.join(d2, ".orchestrator", "ci-baseline.json")))


def test_gitignore_keeps_config_committable():
    # If the target ignores .orchestrator/, install must un-ignore the CI config SSoT,
    # or a clean CI runner checks out the repo without any checks to run.
    d = make_target()
    with open(os.path.join(d, ".gitignore"), "w") as f:
        f.write("__pycache__/\n.orchestrator/\n")
    run([PY, SCAFFOLD, "install", "--ci", "github", "--vcs", "git", "--repo", d])
    gi = open(os.path.join(d, ".gitignore")).read()
    check("install keeps ci-gate.json committable past .gitignore",
          "!.orchestrator/ci-gate.json" in gi,
          "scaffold must add a .gitignore exception for the CI config")


def test_pre_push_blocks_bad_push():
    d = make_target()
    run([PY, SCAFFOLD, "install", "--ci", "github", "--vcs", "git", "--repo", d])
    # a failing FAST check must make the pre-push hook refuse the push
    write_ci_gate(d, [{"name": "bad", "cmd": "sh bad.sh", "fast": True}])
    hook = os.path.join(d, ".githooks", "pre-push")
    r = run(["sh", hook], cwd=d)
    check("AT-6 pre-push refuses when a fast check is red", r.returncode != 0)


def main():
    print("PRD-016 bootstrap-cicd — acceptance tests")
    test_install_idempotent_and_artifacts()
    test_parameterization_and_app_agnostic()
    test_ci_gate_enforces()
    test_ratchet_baseline_trust()
    test_gitignore_keeps_config_committable()
    test_pre_push_blocks_bad_push()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
