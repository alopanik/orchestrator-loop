#!/usr/bin/env python3
"""bootstrap-cicd scaffolder (PRD-016).

Drops the repo's EXISTING orchestrator-loop gate into a repo as `~~ci`: a CI workflow + a
pre-push hook that both invoke the one standing-checks engine (`hooks/ci_gate.py`) — never a
re-listed check set — plus an idempotent managed block in `CLAUDE.md`. App-agnostic: the only
provider knowledge is the `--ci` / `--vcs` binding; everything the loop runs is data in
`.orchestrator/ci-gate.json`.

  scaffold.py install --ci <github|generic> --vcs <git> [--repo DIR]
  scaffold.py ratchet-baseline --signal "<cmd>" --control "<cmd>" [--name N] [--repo DIR]

`ratchet-baseline` enforces baseline-trust: it refuses to record a floor for a signal the
ablation control does not move (you cannot ratchet a number you have not proven is real).
"""
import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANONICAL_ENGINE = os.path.join(PLUGIN_ROOT, "hooks", "ci_gate.py")

BEGIN = "<!-- ORCHESTRATOR-LOOP:CI:BEGIN (managed by bootstrap-cicd — edits here are overwritten) -->"
END = "<!-- ORCHESTRATOR-LOOP:CI:END -->"
BLOCK_RE = re.compile(r"<!-- ORCHESTRATOR-LOOP:CI:BEGIN.*?-->.*?<!-- ORCHESTRATOR-LOOP:CI:END -->\n?",
                      re.DOTALL)

GITHUB_WORKFLOW = """\
name: orchestrator-loop gate
on: [push, pull_request]
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - name: orchestrator-loop standing gate
        run: python3 hooks/ci_gate.py
"""

GENERIC_TEMPLATE = """\
#!/bin/sh
# orchestrator-loop standing gate — portable runner for any ~~ci provider.
# Point your CI at:  sh orchestrator-gate.sh
# It runs the checks declared once in .orchestrator/ci-gate.json — do not re-list them here.
set -e
python3 hooks/ci_gate.py
"""

PRE_PUSH = """\
#!/bin/sh
# orchestrator-loop pre-push fast gate (PRD-016).
# Runs the FAST subset of .orchestrator/ci-gate.json before every push; a red check refuses it.
exec python3 hooks/ci_gate.py --fast
"""

STARTER_CI_GATE = {
    "checks": [
        {"name": "example", "cmd": "echo 'replace with your real checks (see CLAUDE.md)'", "fast": True}
    ]
}

CLAUDE_BLOCK_BODY = """\
## CI gate (orchestrator-loop)

This repo's loop gate also runs as `~~ci`. The standing checks live **once**, as data, in
`.orchestrator/ci-gate.json`; the CI workflow and the pre-push hook both invoke
`python3 hooks/ci_gate.py` (fast subset on pre-push). Add or remove checks by editing
`ci-gate.json` — never re-list them in the workflow (that would fork the source of truth).
Enable the local fast gate with: `git config core.hooksPath .githooks`."""


def _write(path, content, executable=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    if executable:
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def merge_claude_block(repo):
    path = os.path.join(repo, "CLAUDE.md")
    block = f"{BEGIN}\n{CLAUDE_BLOCK_BODY}\n{END}\n"
    text = open(path).read() if os.path.exists(path) else ""
    if BLOCK_RE.search(text):
        new = BLOCK_RE.sub(block, text)
    else:
        new = (text.rstrip("\n") + "\n\n" + block) if text.strip() else block
    with open(path, "w") as f:
        f.write(new)


def ensure_gitignore_exception(repo):
    """If the target ignores .orchestrator/, keep the CI config committable so a clean CI runner
    (which has only the checked-out repo) can see the checks."""
    gi = os.path.join(repo, ".gitignore")
    if not os.path.exists(gi):
        return
    txt = open(gi).read()
    ignores_orch = re.search(r"(?m)^\s*\.orchestrator/?\s*$", txt)
    if ignores_orch and "!.orchestrator/ci-gate.json" not in txt:
        with open(gi, "a") as f:
            f.write("\n# bootstrap-cicd: .orchestrator/ is runtime, but the CI config must ship\n"
                    "!.orchestrator/ci-gate.json\n!.orchestrator/ci-baseline.json\n")


def cmd_install(args):
    repo = os.path.abspath(args.repo)
    if args.vcs != "git":
        print(f"unsupported --vcs {args.vcs!r} (only 'git' in v1)", file=sys.stderr)
        return 2

    # 1. vendor the engine if the target doesn't already have it (the plugin's own repo does)
    target_engine = os.path.join(repo, "hooks", "ci_gate.py")
    if not os.path.exists(target_engine):
        os.makedirs(os.path.dirname(target_engine), exist_ok=True)
        shutil.copyfile(CANONICAL_ENGINE, target_engine)

    # 2. the CI workflow — parameterized by ~~ci, NO inline check list
    if args.ci == "github":
        _write(os.path.join(repo, ".github", "workflows", "orchestrator-gate.yml"), GITHUB_WORKFLOW)
    else:
        _write(os.path.join(repo, "orchestrator-gate.sh"), GENERIC_TEMPLATE, executable=True)

    # 3. the pre-push fast gate (opt-in activation via core.hooksPath — never set silently)
    _write(os.path.join(repo, ".githooks", "pre-push"), PRE_PUSH, executable=True)

    # 4. seed the standing-checks manifest if absent
    manifest = os.path.join(repo, ".orchestrator", "ci-gate.json")
    if not os.path.exists(manifest):
        _write(manifest, json.dumps(STARTER_CI_GATE, indent=2) + "\n")
    ensure_gitignore_exception(repo)

    # 5. idempotent managed block in CLAUDE.md
    merge_claude_block(repo)

    where = "github workflow" if args.ci == "github" else "portable orchestrator-gate.sh"
    print(f"bootstrap-cicd installed in {repo}: {where} + .githooks/pre-push + CLAUDE.md block.")
    print("Activate the local fast gate with: git config core.hooksPath .githooks")
    print("CI activates on your next push (a push is the owner's release call).")
    return 0


def _run(cmd, cwd):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)


def cmd_ratchet_baseline(args):
    repo = os.path.abspath(args.repo)
    sig = _run(args.signal, repo)
    ctl = _run(args.control, repo)
    sig_ok = sig.returncode == 0
    ctl_ok = ctl.returncode == 0
    # discriminates iff the real signal passes but the ablated control does NOT (they differ)
    if not (sig_ok and not ctl_ok):
        sys.stderr.write(
            "REFUSED to baseline: the control did not move the signal — "
            f"signal exit={sig.returncode}, control exit={ctl.returncode}. "
            "A ratchet on a non-discriminating signal locks in an unproven number "
            "(see app-profile sanity bound). Fix the signal/control, then re-baseline.\n")
        return 1
    os.makedirs(os.path.join(repo, ".orchestrator"), exist_ok=True)
    with open(os.path.join(repo, ".orchestrator", "ci-baseline.json"), "w") as f:
        json.dump({"signal": {"name": args.name, "cmd": args.signal},
                   "validated_by_control": args.control,
                   "control_exit": ctl.returncode}, f, indent=2)
        f.write("\n")
    print(f"ratchet baseline recorded for {args.name!r}: signal green, control red "
          f"(exit {ctl.returncode}) — discrimination proven. ci_gate.py will now enforce it.")
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="sub", required=True)
    pi = sub.add_parser("install")
    pi.add_argument("--ci", default="github", choices=["github", "generic"])
    pi.add_argument("--vcs", default="git")
    pi.add_argument("--repo", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))
    pr = sub.add_parser("ratchet-baseline")
    pr.add_argument("--signal", required=True)
    pr.add_argument("--control", required=True)
    pr.add_argument("--name", default="signal")
    pr.add_argument("--repo", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))
    args = ap.parse_args(argv)
    if args.sub == "install":
        return cmd_install(args)
    if args.sub == "ratchet-baseline":
        return cmd_ratchet_baseline(args)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
