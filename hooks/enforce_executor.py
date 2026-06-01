#!/usr/bin/env python3
"""Enforce the executor boundary (PRD-011) — a Claude Code PreToolUse hook.

In power mode (`~~executor = claude-code`), the orchestrator plans and verifies; it must NOT
edit files itself. This hook denies file-mutation tools to the orchestrator session and allows
them only to the executor process (launched with env OL_ROLE=executor). In `self` mode
(zero-setup / solo) it allows everything — the separation there is temporal, not enforced.

PreToolUse contract: read the event JSON on stdin; exit 0 to allow, exit 2 to DENY (stderr is
fed back to Claude). Fail-OPEN on internal error or unknown mode (we never want this hook to
brick a session) — the mode must be explicitly `claude-code` to deny.

  enforce_executor.py            # hook mode (PreToolUse JSON on stdin)
  enforce_executor.py mode self|claude-code   # set mode
  enforce_executor.py status
"""
import json
import os
import sys

MUTATION_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
MODE_REL = os.path.join(".orchestrator", "mode.json")


def pdir(stdin_obj=None):
    d = os.environ.get("CLAUDE_PROJECT_DIR")
    if d:
        return d
    if stdin_obj and stdin_obj.get("cwd"):
        return stdin_obj["cwd"]
    return os.getcwd()


def get_mode(pdir_):
    p = os.path.join(pdir_, MODE_REL)
    if not os.path.exists(p):
        return "self"  # default: zero-setup/solo allows
    try:
        return json.load(open(p)).get("executor", "self")
    except Exception:
        return "self"  # fail-open: a broken mode file must not brick edits


def hook_mode():
    try:
        raw = sys.stdin.read()
        obj = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # fail-open
    tool = obj.get("tool_name") or obj.get("tool") or ""
    if tool not in MUTATION_TOOLS:
        return 0
    mode = get_mode(pdir(obj))
    if mode != "claude-code":
        return 0  # self/solo: allowed
    if os.environ.get("OL_ROLE") == "executor":
        return 0  # this IS the executor process
    sys.stderr.write(
        "orchestrator-loop: power mode (~~executor = claude-code) — the orchestrator plans and "
        f"verifies; it does not edit files. Dispatch this {tool} to the executor instead "
        "(handoff-to-executor). [enforce_executor]\n")
    return 2  # DENY


def cmd_mode(argv):
    if not argv or argv[0] not in ("self", "claude-code"):
        print("usage: enforce_executor.py mode self|claude-code", file=sys.stderr)
        return 2
    d = pdir()
    os.makedirs(os.path.join(d, ".orchestrator"), exist_ok=True)
    with open(os.path.join(d, MODE_REL), "w") as f:
        json.dump({"executor": argv[0]}, f, indent=2)
        f.write("\n")
    print(f"executor mode set: {argv[0]}")
    return 0


def cmd_status():
    print(f"executor mode: {get_mode(pdir())}  (OL_ROLE={os.environ.get('OL_ROLE','<unset>')})")
    return 0


def main(argv):
    if not argv:
        return hook_mode()
    if argv[0] == "mode":
        return cmd_mode(argv[1:])
    if argv[0] == "status":
        return cmd_status()
    print(f"unknown subcommand: {argv[0]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
