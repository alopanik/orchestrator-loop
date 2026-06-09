#!/usr/bin/env python3
"""Standing-checks CI engine for orchestrator-loop (PRD-016).

This is the SAME gate as `hooks/stop_gate.py`, relocated so it can run where the turn-end hook
cannot: on a remote CI runner and in a pre-push hook. It runs the repo's STANDING checks from
`.orchestrator/ci-gate.json` (distinct from the per-PRD `.orchestrator/gate.json`) and fails
closed — a missing, erroring, or non-zero check is a FAILURE, never a silent pass.

It is deliberately **standalone** (no import of plugin internals) so `bootstrap-cicd`'s
`scaffold.py` can vendor this one file into any target repo and it will run on a clean CI runner
where the plugin is not installed. The checks themselves live once, as data, in `ci-gate.json` —
the CI workflow and the pre-push hook both invoke this engine and never re-list the checks.

  python3 hooks/ci_gate.py            run every standing check   (exit 0 all green, 1 otherwise)
  python3 hooks/ci_gate.py --fast     run only checks flagged "fast" (the pre-push subset)

Manifest (`.orchestrator/ci-gate.json`):
  {"checks": [{"name": "self-test", "cmd": "python3 test/harness/run.py --self-test", "fast": true},
              {"name": "units",     "cmd": "...", "fast": false}]}
A `.orchestrator/ci-baseline.json` written by `scaffold.py ratchet-baseline` adds its validated
signal as an extra check, so a regression in the ratcheted signal fails CI too.
"""
import datetime
import json
import os
import subprocess
import sys

MANIFEST_REL = os.path.join(".orchestrator", "ci-gate.json")
BASELINE_REL = os.path.join(".orchestrator", "ci-baseline.json")
LEDGER_REL = os.path.join(".orchestrator", "ledger.jsonl")
CHECK_TIMEOUT = 600


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def load_checks(pdir, fast_only):
    p = os.path.join(pdir, MANIFEST_REL)
    if not os.path.exists(p):
        return None, "no .orchestrator/ci-gate.json — nothing to gate (run bootstrap-cicd first)"
    try:
        with open(p) as f:
            manifest = json.load(f)
    except Exception as e:
        return None, f"ci-gate.json unparseable: {e}"
    checks = list(manifest.get("checks", []))
    # fold in the ratcheted signal, if a validated baseline exists
    bp = os.path.join(pdir, BASELINE_REL)
    if os.path.exists(bp):
        try:
            sig = json.load(open(bp)).get("signal", {})
            if sig.get("cmd"):
                checks.append({"name": "ratchet:" + sig.get("name", "signal"),
                               "cmd": sig["cmd"], "fast": False})
        except Exception:
            checks.append({"name": "ratchet", "cmd": None, "fast": False})  # fail closed
    if fast_only:
        checks = [c for c in checks if c.get("fast")]
    return checks, None


def run_checks(pdir, checks):
    results = []
    for c in checks:
        name = c.get("name") or c.get("cmd", "?")
        cmd = c.get("cmd")
        if not cmd:
            results.append((name, False, "no command (fail-closed)"))
            continue
        try:
            proc = subprocess.run(cmd, shell=True, cwd=pdir, capture_output=True,
                                  text=True, timeout=CHECK_TIMEOUT)
            ok = proc.returncode == 0
            detail = "ok" if ok else f"exit {proc.returncode}: {(proc.stderr or proc.stdout).strip()[:200]}"
        except subprocess.TimeoutExpired:
            ok, detail = False, f"timed out after {CHECK_TIMEOUT}s"
        except Exception as e:
            ok, detail = False, f"error running check: {e}"
        results.append((name, ok, detail))
    return results


def append_ledger(pdir, decision, results):
    entry = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
             "prd": "ci", "decision": decision, "source": "ci-gate",
             "checks": [{"name": n, "ok": ok, "detail": d} for (n, ok, d) in results]}
    try:
        os.makedirs(os.path.join(pdir, ".orchestrator"), exist_ok=True)
        line = (json.dumps(entry) + "\n").encode()
        # atomic append (PRD-018): one os.write to an O_APPEND fd interleaves as a whole line
        fd = os.open(os.path.join(pdir, LEDGER_REL), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, line)
        finally:
            os.close(fd)
    except Exception:
        pass  # never let ledger I/O mask the gate result


def main(argv):
    fast_only = "--fast" in argv
    pdir = project_dir()
    checks, err = load_checks(pdir, fast_only)
    if err:
        # No manifest is a no-op (don't block a repo that hasn't opted in); a corrupt one fails closed.
        if "unparseable" in err:
            sys.stderr.write(f"orchestrator-loop ci-gate: {err} — fail-closed.\n")
            return 1
        print(f"orchestrator-loop ci-gate: {err}")
        return 0
    if not checks:
        print("orchestrator-loop ci-gate: no checks to run" + (" (fast subset empty)" if fast_only else ""))
        return 0

    results = run_checks(pdir, checks)
    failed = [(n, d) for (n, ok, d) in results if not ok]
    append_ledger(pdir, "block" if failed else "pass", results)

    scope = "fast " if fast_only else ""
    for n, ok, d in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {n}: {d}")
    if failed:
        sys.stderr.write(f"\norchestrator-loop ci-gate FAILED — {len(failed)} {scope}check(s) red:\n")
        for n, d in failed:
            sys.stderr.write(f"  ✗ {n}: {d}\n")
        return 1
    print(f"\norchestrator-loop ci-gate: all {len(results)} {scope}check(s) green.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
