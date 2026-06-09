#!/usr/bin/env python3
"""Separation of duties (PRD-021) — planner != verifier, enforced when a team opts in.

The moat is that the verifier is an adversary, not a co-author. This makes it an invariant rather
than a hope: when separation is REQUIRED, the principal who moved a PRD into a builder status
(claimed/building) must not be the one who moved it into a verifier status (verifying/shipped).
Solo/self mode legitimately has one principal, so this is OPT-IN and dormant by default (like
audit_executor). It reads the per-PRD state `history` written by prd_state.py (PRD-021), whose
`by` field is the recorded principal from provenance (PRD-020).

  check_separation.py <PRD-ID>     # 0 = separated or dormant; nonzero = same principal / unprovable
"""
import json
import os
import sys

BUILDER = {"claimed", "building"}
VERIFIER = {"verifying", "shipped"}


def pdir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _norm(pid):
    pid = pid.strip()
    if pid.upper().startswith("PRD-"):
        rest = pid[4:]
        return f"PRD-{int(rest):03d}" if rest.isdigit() else f"PRD-{rest}"
    if pid.isdigit():
        return f"PRD-{int(pid):03d}"
    return pid


def required(d):
    if str(os.environ.get("OL_REQUIRE_SEPARATION", "")).lower() in ("1", "true", "yes"):
        return True
    p = os.path.join(d, ".orchestrator", "policy.json")
    if os.path.exists(p):
        try:
            return bool(json.load(open(p)).get("require_separation"))
        except Exception:
            return False
    return False


def main(argv):
    if not argv:
        print("usage: check_separation.py <PRD-ID>", file=sys.stderr)
        return 2
    d = pdir()
    pid = _norm(argv[0])
    if not required(d):
        print("check_separation: separation not required (policy off) — dormant ✓")
        return 0
    p = os.path.join(d, ".orchestrator", "prds", f"{pid}.json")
    if not os.path.exists(p):
        sys.stderr.write(f"check_separation: no state for {pid} — cannot prove separation. "
                         "FAIL CLOSED. [check_separation]\n")
        return 2
    try:
        st = json.load(open(p))
    except Exception:
        sys.stderr.write("check_separation: state unreadable — FAIL CLOSED. [check_separation]\n")
        return 2
    hist = st.get("history", [])
    builders = {h.get("by") for h in hist if h.get("status") in BUILDER}
    verifiers = {h.get("by") for h in hist if h.get("status") in VERIFIER}
    if not builders or not verifiers:
        sys.stderr.write(
            f"check_separation: {pid} lacks both a builder and an independent verifier transition "
            f"(builders={sorted(builders)} verifiers={sorted(verifiers)}) — cannot prove "
            "separation. FAIL CLOSED. [check_separation]\n")
        return 2
    overlap = builders & verifiers
    if overlap:
        sys.stderr.write(
            f"check_separation: the SAME principal built and blessed {pid}: {sorted(overlap)}. "
            "The planner must not be the verifier. FAIL CLOSED. [check_separation]\n")
        return 2
    print(f"check_separation: {pid} builder(s) {sorted(builders)} != verifier(s) {sorted(verifiers)} ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
