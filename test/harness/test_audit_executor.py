#!/usr/bin/env python3
"""Tests for audit_executor.py (PRD-013) — temp git repos, no network, stdlib only."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = HERE / "audit_executor.py"


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)


def make_repo():
    d = Path(tempfile.mkdtemp(prefix="ol-audit-"))
    git(d, "init")
    git(d, "config", "user.email", "t@t")
    git(d, "config", "user.name", "t")
    (d / "seed.txt").write_text("seed\n")
    git(d, "add", "-A")
    git(d, "commit", "-m", "seed")
    return d


def set_mode(repo, mode):
    o = repo / ".orchestrator"
    o.mkdir(exist_ok=True)
    (o / "mode.json").write_text(json.dumps({"executor": mode}) + "\n")


def set_status(repo, text):
    o = repo / ".orchestrator"
    o.mkdir(exist_ok=True)
    (o / "executor.status").write_text(text + "\n")


def dirty(repo):
    (repo / "code.py").write_text("print('change')\n")


def run_check(repo, env_extra=None):
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(repo)
    env.pop("OL_ROLE", None)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run([sys.executable, str(AUDIT), "check"],
                          capture_output=True, text=True, env=env)
    return proc.returncode, (proc.stdout + proc.stderr)


class AuditTests(unittest.TestCase):
    def test_self_mode_change_allowed(self):  # AT-5
        r = make_repo(); set_mode(r, "self"); dirty(r)
        rc, out = run_check(r)
        self.assertEqual(rc, 0, out)

    def test_claude_code_change_no_dispatch_blocks(self):  # AT-3 (headline)
        r = make_repo(); set_mode(r, "claude-code"); dirty(r)
        rc, out = run_check(r)
        self.assertEqual(rc, 2, out)
        self.assertIn("dispatch", out.lower())

    def test_claude_code_change_with_dispatch_allowed(self):  # AT-4
        r = make_repo(); set_mode(r, "claude-code"); dirty(r); set_status(r, "exited 0")
        rc, out = run_check(r)
        self.assertEqual(rc, 0, out)

    def test_claude_code_clean_allowed(self):
        r = make_repo(); set_mode(r, "claude-code")  # no working-tree change
        rc, out = run_check(r)
        self.assertEqual(rc, 0, out)

    def test_default_mode_absent_is_self(self):
        r = make_repo(); dirty(r)  # no mode.json => defaults to self => dormant
        rc, out = run_check(r)
        self.assertEqual(rc, 0, out)

    def test_executor_role_bypass(self):
        r = make_repo(); set_mode(r, "claude-code"); dirty(r)
        rc, out = run_check(r, {"OL_ROLE": "executor"})
        self.assertEqual(rc, 0, out)

    def test_running_status_not_attributable(self):  # mid-flight != a completed dispatch
        r = make_repo(); set_mode(r, "claude-code"); dirty(r); set_status(r, "running")
        rc, out = run_check(r)
        self.assertEqual(rc, 2, out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
