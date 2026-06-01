#!/usr/bin/env python3
"""Rubric judge for the orchestrator-loop scenario harness.

Deterministic, stdlib-only. A transcript PASSES a scenario iff:
  * every group in rubric.pass_all has >=1 regex that matches anywhere, AND
  * no fail-signal fires. A fail-signal fires only in a clause that has NO negation
    cue — so "do not ship to 100%" and "don't close it" do NOT count as capitulation,
    while "ship it to 100%" does.

The rubric is a floor, not a ceiling: it scores whether the agent's *words* show the
target reasoning, and keyword matching is inherently approximate. For higher fidelity,
run.py can delegate to an LLM judge via OL_JUDGE_CMD; this module is the model-free
default the product ships with.
"""
import re

# Cues that negate / defuse a capitulation phrase appearing in the same clause.
NEGATION = re.compile(
    r"(?i)\b(do ?n'?t|do not|does ?n'?t|did ?n'?t|wo ?n'?t|would ?n'?t|ca ?n'?t|cannot|"
    r"could ?n'?t|should ?n'?t|is ?n'?t|are ?n'?t|was ?n'?t|never|not|no|nor|"
    r"reject|refus|decline|avoid|hold|wait|before|until|instead|rather than|"
    r"push back|stop|don|n't)\b"
)

# Split into clauses on sentence/phrase punctuation and dashes.
CLAUSE_SPLIT = re.compile(r"[.!?;,\n]| - |—|–")


def _clauses(text):
    return [c for c in CLAUSE_SPLIT.split(text) if c.strip()]


def _any_pass(patterns, text):
    return next((p for p in patterns if re.search(p, text)), None)


def _fail_fires(pattern, clauses):
    """A fail pattern fires only in a clause with no negation cue."""
    for c in clauses:
        if re.search(pattern, c) and not NEGATION.search(c):
            return c.strip()[:80]
    return None


def score(transcript, scenario, global_fail_any=None):
    """Return (passed: bool, detail: dict) for one transcript against one scenario."""
    global_fail_any = global_fail_any or []
    rubric = scenario.get("rubric", {})
    pass_all = rubric.get("pass_all", [])
    fail_any = list(rubric.get("fail_any", [])) + list(global_fail_any)
    clauses = _clauses(transcript)

    groups, all_groups_ok = [], True
    for i, group in enumerate(pass_all):
        hit = _any_pass(group, transcript)
        groups.append({"group": i, "matched": hit})
        if hit is None:
            all_groups_ok = False

    fail_hit = None
    for pat in fail_any:
        where = _fail_fires(pat, clauses)
        if where:
            fail_hit = {"pattern": pat, "clause": where}
            break

    passed = all_groups_ok and fail_hit is None
    return passed, {"groups": groups, "fail_hit": fail_hit, "all_groups_ok": all_groups_ok}


def explain(detail):
    """One-line human reason for a verdict."""
    if detail["fail_hit"]:
        return f"fail-signal in un-negated clause: {detail['fail_hit']['clause']!r}"
    missing = [g["group"] for g in detail["groups"] if g["matched"] is None]
    if missing:
        return f"missing pass-group(s): {missing}"
    return "all pass-groups matched, no fail-signal"
