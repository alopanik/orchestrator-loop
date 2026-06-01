#!/usr/bin/env python3
"""Guard the tests (PRD-005) — tests-first + tamper detection.

The easiest way to game an "un-gameable" acceptance test is to edit it green. This guards
against that by pinning a baseline: the test must be committed FAILING before implementation,
and at handback it must be (a) unchanged since that baseline and (b) actually green.

  check_tests.py baseline --cmd "<test cmd>" --tests <glob> [--tests <glob> ...]
      Assert the test cmd fails NOW (red). Record HEAD + globs + cmd to .orchestrator/tests.json.
      Errors if the cmd already passes (a test that never failed is not a guard).

  check_tests.py verify
      Read the manifest and enforce BOTH:
        - no tamper: git diff of the test globs from baseline -> working tree is empty
        - green now: the test cmd passes
      Exit 0 only if untampered AND now-green; nonzero otherwise (composed into the PRD-004 gate).
"""
import argparse
import json
import os
import subprocess
import sys

MANIFEST_REL = os.path.join(".orchestrator", "tests.json")


def pdir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def mpath(d):
    return os.path.join(d, MANIFEST_REL)


def git(d, *args):
    return subprocess.run(["git", "-C", d, *args], capture_output=True, text=True)


def run_cmd(d, cmd):
    return subprocess.run(cmd, shell=True, cwd=d, capture_output=True, text=True)


def cmd_baseline(args):
    d = pdir()
    res = run_cmd(d, args.cmd)
    if res.returncode == 0:
        sys.stderr.write("check_tests baseline: the test command PASSES already — tests must be "
                         "committed FAILING before implementation. Write a real (red) test first.\n")
        return 1
    head = git(d, "rev-parse", "HEAD")
    if head.returncode != 0:
        sys.stderr.write("check_tests baseline: not a git repo / no HEAD.\n")
        return 1
    ref = head.stdout.strip()
    os.makedirs(os.path.join(d, ".orchestrator"), exist_ok=True)
    manifest = {"prd": args.prd, "baseline_ref": ref, "test_globs": args.tests, "test_cmd": args.cmd}
    with open(mpath(d), "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"tests baseline recorded at {ref[:9]} (red ✓) — globs={args.tests}")
    return 0


def cmd_verify(_args):
    d = pdir()
    p = mpath(d)
    if not os.path.exists(p):
        print("check_tests verify: no tests manifest — nothing to guard")
        return 0
    try:
        m = json.load(open(p))
    except Exception:
        sys.stderr.write("check_tests verify: tests manifest corrupt — fail-closed.\n")
        return 1
    ref, globs, cmd = m.get("baseline_ref"), m.get("test_globs", []), m.get("test_cmd")
    # (a) tamper: any change to the test files since the failing baseline?
    diff = git(d, "diff", "--name-only", ref, "--", *globs)
    if diff.returncode != 0:
        sys.stderr.write(f"check_tests verify: git diff failed: {diff.stderr.strip()}\n")
        return 1
    changed = [x for x in diff.stdout.splitlines() if x.strip()]
    if changed:
        sys.stderr.write("check_tests verify: TESTS ALTERED since the failing baseline — reject:\n")
        for c in changed:
            sys.stderr.write(f"   ✗ {c}\n")
        sys.stderr.write("A handback that edits its own tests to pass is not done.\n")
        return 1
    # (b) green now
    res = run_cmd(d, cmd)
    if res.returncode != 0:
        sys.stderr.write("check_tests verify: tests are UNCHANGED but still RED at HEAD — not done.\n")
        sys.stderr.write((res.stderr or res.stdout).strip()[:200] + "\n")
        return 1
    print(f"check_tests verify: tests untampered since {ref[:9]} and green ✓")
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="sub", required=True)
    b = sub.add_parser("baseline")
    b.add_argument("--cmd", required=True)
    b.add_argument("--tests", action="append", required=True)
    b.add_argument("--prd", default="")
    sub.add_parser("verify")
    args = ap.parse_args(argv)
    if args.sub == "baseline":
        return cmd_baseline(args)
    return cmd_verify(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
