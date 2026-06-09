#!/usr/bin/env python3
"""Ledger integrity canary (PRD-018) — the concurrency safety net.

The ledger is append-only and now has multiple writers (stop_gate at turn-end, ci_gate in
CI/pre-push, across operators/machines). Each writer appends one whole line with a single
`os.write` to an `O_APPEND` fd, which the kernel guarantees atomic for a line ≤ PIPE_BUF — so
concurrent appends interleave as whole lines, never torn. This check is the canary that proves
it: every line must be parseable JSON. A torn/garbled line fails closed.

  check_ledger.py check    # 0 = every line well-formed (or no ledger yet); 1 = a torn line
"""
import json
import os
import sys

LEDGER_REL = os.path.join(".orchestrator", "ledger.jsonl")


def pdir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def main(argv):
    d = pdir()
    p = os.path.join(d, LEDGER_REL)
    if not os.path.exists(p):
        print("check_ledger: no ledger yet — ok")
        return 0
    torn = 0
    n = 0
    for i, ln in enumerate(open(p), 1):
        ln = ln.rstrip("\n")
        if not ln.strip():
            continue
        n += 1
        try:
            json.loads(ln)
        except Exception:
            torn += 1
            sys.stderr.write(f"check_ledger: torn/unparseable line {i}: {ln[:80]!r}\n")
    if torn:
        sys.stderr.write(f"check_ledger: {torn}/{n} torn line(s) — FAIL CLOSED [check_ledger]\n")
        return 1
    print(f"check_ledger: {n} line(s), all well-formed ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
