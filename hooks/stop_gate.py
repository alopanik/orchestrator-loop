#!/usr/bin/env python3
"""Fail-closed Stop gate for orchestrator-loop (PRD-004).

Registered as a Claude Code `Stop` hook. It refuses to let a turn end while a declared gate's
scriptable checks are failing — turning the framework's advisory gates into enforced ones.

Hook mode (no args, Stop-event JSON on stdin):
  * no active gate manifest            -> exit 0  (NEVER block a normal turn)
  * active gate, all checks exit 0     -> exit 0  (allow the stop)
  * active gate, any check fails/missing/errors, or a corrupt manifest
                                       -> exit 2  (BLOCK; stderr explains why — Claude reads it)

Fail-closed: a missing or erroring check counts as a FAILURE, never a silent pass.

Management (used by the loop):
  stop_gate.py set <PRD-ID> "<cmd>" ["<cmd>" ...]   declare the gate's checks (activates it)
  stop_gate.py clear                                 deactivate the gate
  stop_gate.py status                                print the manifest
  stop_gate.py check                                 run the checks now, print pass/fail (exit 0/1)

Loop safety: the Stop event carries `stop_hook_active`; we surface it but still block while
checks fail. The escapes from a genuinely stuck gate are `clear` and Claude Code's documented
consecutive-block cap (CLAUDE_CODE_STOP_HOOK_BLOCK_CAP, default 8) — the gate cannot trap a
session forever, but it also can't be bypassed by simply trying to stop again.
"""
import json
import os
import subprocess
import sys

MANIFEST_REL = os.path.join(".orchestrator", "gate.json")
CHECK_TIMEOUT = 180


def project_dir(stdin_obj=None):
    d = os.environ.get("CLAUDE_PROJECT_DIR")
    if d:
        return d
    if stdin_obj and stdin_obj.get("cwd"):
        return stdin_obj["cwd"]
    return os.getcwd()


def manifest_path(pdir):
    return os.path.join(pdir, MANIFEST_REL)


def load_manifest(pdir):
    """Return (state, manifest). state in {'none','corrupt','inactive','active'}."""
    p = manifest_path(pdir)
    if not os.path.exists(p):
        return "none", None
    try:
        with open(p) as f:
            m = json.load(f)
    except Exception:
        return "corrupt", None
    if not m.get("active"):
        return "inactive", m
    return "active", m


def run_checks(pdir, checks):
    """Run each check command in pdir. Return list of (name, ok, detail). Fail-closed."""
    results = []
    for c in checks:
        name = c.get("name") or c.get("cmd", "?")
        cmd = c.get("cmd")
        if not cmd:
            results.append((name, False, "no command"))
            continue
        try:
            proc = subprocess.run(cmd, shell=True, cwd=pdir, capture_output=True,
                                  text=True, timeout=CHECK_TIMEOUT)
            ok = proc.returncode == 0
            detail = "ok" if ok else f"exit {proc.returncode}: {(proc.stderr or proc.stdout).strip()[:160]}"
        except subprocess.TimeoutExpired:
            ok, detail = False, f"timed out after {CHECK_TIMEOUT}s"
        except Exception as e:  # missing interpreter, etc. — fail closed
            ok, detail = False, f"error running check: {e}"
        results.append((name, ok, detail))
    return results


def hook_mode():
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    try:
        stdin_obj = json.loads(raw) if raw.strip() else {}
    except Exception:
        stdin_obj = {}
    pdir = project_dir(stdin_obj)
    stop_active = bool(stdin_obj.get("stop_hook_active"))

    state, m = load_manifest(pdir)
    if state == "none" or state == "inactive":
        return 0  # nothing to enforce — never block a normal turn
    if state == "corrupt":
        sys.stderr.write("orchestrator-loop gate: .orchestrator/gate.json is unparseable — "
                         "fail-closed (blocking). Fix or `stop_gate.py clear`.\n")
        return 2

    results = run_checks(pdir, m.get("checks", []))
    failed = [(n, d) for (n, ok, d) in results if not ok]
    if not failed:
        return 0  # all green — allow the stop

    lines = [f"orchestrator-loop gate BLOCKED end of turn — {m.get('prd','gate')} checks not green:"]
    for n, d in failed:
        lines.append(f"  ✗ {n}: {d}")
    lines.append("Fix the failing check(s) and try again. (Override: `stop_gate.py clear`.)")
    if stop_active:
        lines.append("(stop_hook_active=true — still blocking; the block-cap is the hard escape.)")
    sys.stderr.write("\n".join(lines) + "\n")
    return 2


def slug(cmd):
    base = cmd.strip().split()
    # take the last path-ish token or a flag as the name hint
    for tok in reversed(base):
        if tok.startswith("--"):
            return tok.lstrip("-")
    return os.path.basename(base[0]) if base else "check"


def cmd_set(args):
    if len(args) < 2:
        print("usage: stop_gate.py set <PRD-ID> \"<cmd>\" [\"<cmd>\" ...]", file=sys.stderr)
        return 2
    prd, cmds = args[0], args[1:]
    pdir = project_dir()
    os.makedirs(os.path.join(pdir, ".orchestrator"), exist_ok=True)
    manifest = {"prd": prd, "active": True,
                "checks": [{"name": slug(c), "cmd": c} for c in cmds]}
    with open(manifest_path(pdir), "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"gate set for {prd}: {len(cmds)} check(s) — {[c['name'] for c in manifest['checks']]}")
    return 0


def cmd_clear():
    pdir = project_dir()
    os.makedirs(os.path.join(pdir, ".orchestrator"), exist_ok=True)
    with open(manifest_path(pdir), "w") as f:
        json.dump({"active": False}, f, indent=2)
        f.write("\n")
    print("gate cleared (inactive)")
    return 0


def cmd_status():
    pdir = project_dir()
    state, m = load_manifest(pdir)
    print(f"gate state: {state}")
    if m:
        print(json.dumps(m, indent=2))
    return 0


def cmd_check():
    pdir = project_dir()
    state, m = load_manifest(pdir)
    if state in ("none", "inactive"):
        print("no active gate — nothing to check")
        return 0
    if state == "corrupt":
        print("gate manifest corrupt — fail-closed", file=sys.stderr)
        return 1
    results = run_checks(pdir, m.get("checks", []))
    for n, ok, d in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {n}: {d}")
    return 0 if all(ok for _, ok, _ in results) else 1


def main(argv):
    if not argv:
        return hook_mode()
    sub = argv[0]
    if sub == "set":
        return cmd_set(argv[1:])
    if sub == "clear":
        return cmd_clear()
    if sub == "status":
        return cmd_status()
    if sub == "check":
        return cmd_check()
    print(f"unknown subcommand: {sub}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
