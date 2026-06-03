#!/usr/bin/env python3
"""Audit the executor boundary in Cowork (PRD-013) — a fail-closed DETECTIVE control.

The preventive guard (`hooks/enforce_executor.py`, a Claude Code PreToolUse hook) blocks the
orchestrator's writes in power mode — but only where Claude Code fires PreToolUse. The
orchestrator usually runs in **Cowork**, where that deny is not guaranteed. This check is the
Cowork-side complement: at verify time, in `claude-code` mode, it FAILS CLOSED if the working
tree changed but no executor dispatch is recorded — i.e. the orchestrator coded instead of
dispatching to the executor.

It is a detective (after-the-fact), not preventive, control, and does not defeat a deliberate
actor (see PRD-013 non-goals). In `self`/solo mode it is dormant (always passes). The mode is
read through the one canonical reader, `enforce_executor.get_mode` — no second source of truth.

  audit_executor.py check     # exit 0 = clean / dormant; nonzero = boundary violation
  audit_executor.py status    # print mode + what the audit currently sees
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "hooks"))
import enforce_executor  # canonical mode reader — one source of truth for the mode  # noqa: E402

STATUS_REL = os.path.join(".orchestrator", "executor.status")


def pdir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _porcelain_path(line):
    """Path from a `git status --porcelain` v1 line ('XY <path>', rename 'XY <old> -> <new>')."""
    p = line[3:] if len(line) > 3 else line
    if " -> " in p:
        p = p.split(" -> ", 1)[1]
    return p.strip().strip('"')


def _git_dirty(d):
    """Return (changed: bool|None, detail). None = could not determine (git missing / not a repo).

    `.orchestrator/` is the loop's OWN runtime state (mode, gate, ledger, executor status/log) —
    not code. Changes there must never count as 'the orchestrator wrote code', or simply running
    the loop (which writes gate.json / ledger.jsonl) would trip the audit. Attribute only changes
    OUTSIDE `.orchestrator/`.
    """
    try:
        proc = subprocess.run(["git", "-C", d, "status", "--porcelain"],
                              capture_output=True, text=True)
    except FileNotFoundError:
        return None, "git not found"
    if proc.returncode != 0:
        return None, f"git error: {(proc.stderr or '').strip()[:120]}"
    code = [ln for ln in proc.stdout.splitlines()
            if ln.strip()
            and not _porcelain_path(ln).startswith(".orchestrator/")
            and _porcelain_path(ln) != ".orchestrator"]
    return (len(code) > 0), "\n".join(code)


def _dispatch_recorded(d):
    """A completed executor dispatch is recorded iff executor.status contains 'exited'.
    (dispatch.py writes 'running' -> 'exited <code>'.)"""
    p = os.path.join(d, STATUS_REL)
    if not os.path.exists(p):
        return False, "no .orchestrator/executor.status"
    try:
        txt = open(p).read().strip()
    except Exception as e:  # pragma: no cover - unreadable status
        return False, f"unreadable status: {e}"
    return ("exited" in txt), (txt or "<empty>")


def check():
    d = pdir()
    mode = enforce_executor.get_mode(d)
    if mode != "claude-code":
        print(f"audit: dormant (mode={mode}) — self/solo writes are legitimate ✓")
        return 0
    if os.environ.get("OL_ROLE") == "executor":
        print("audit: running as the executor — pass ✓")
        return 0
    changed, gdetail = _git_dirty(d)
    if changed is None:
        sys.stderr.write(
            f"audit: power mode but cannot read git state ({gdetail}) — FAIL CLOSED. "
            "[audit_executor]\n")
        return 2
    if not changed:
        print("audit: power mode, working tree clean — nothing to attribute ✓")
        return 0
    recorded, sdetail = _dispatch_recorded(d)
    if recorded:
        print(f"audit: power mode, changes attributable to a recorded executor dispatch "
              f"({sdetail}) ✓")
        return 0
    sys.stderr.write(
        "audit: power mode (~~executor = claude-code) — the working tree changed but NO "
        f"executor dispatch is recorded ({sdetail}). The orchestrator must dispatch to the "
        "executor (handoff-to-executor / dispatch.py), not edit files itself. FAIL CLOSED. "
        "[audit_executor]\n")
    return 2


def status():
    d = pdir()
    mode = enforce_executor.get_mode(d)
    changed, gdetail = _git_dirty(d)
    recorded, sdetail = _dispatch_recorded(d)
    print(f"audit_executor: mode={mode}  working_tree_changed={changed}  "
          f"dispatch_recorded={recorded}  (status={sdetail!r}, "
          f"OL_ROLE={os.environ.get('OL_ROLE', '<unset>')})")
    return 0


def main(argv):
    cmd = argv[0] if argv else "check"
    if cmd == "check":
        return check()
    if cmd == "status":
        return status()
    print(f"usage: audit_executor.py [check|status]  (got {cmd!r})", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
