# PRD-009 — README rewrite (value prop + honest catch-rate + two-brain)

**User-visible-surface impact:** Yes — the README is the front door. It leads with the delegation
value prop and the moat, publishes an honest (verified) catch-rate, and recommends the two-brain
mode.

## 1. Problem (with proof)

The README led with mechanics and counts (closing line: `… 50 rules · 20 war stories · 7 gates …`)
and the body enumerated skills. REQUIREMENTS.md is explicit: *"lead with the verifier moat and the
published catch-rate, not the rule count."* It also didn't reflect this session's hardening or the
validated executor-mode recommendation, and a first draft (auto-written by an unsupervised
sub-agent) published a **fabricated `11/12` catch-rate** the real run does not reproduce.

## 2. Root cause

The README was organized around "what's in the box," not "what you get" + "why you can trust it."
No section carried the catch-rate proof or the honest model-dependence nuance.

## 3. Scope

Rewrite `README.md`: value prop → moat → honest catch-rate proof (deterministic self-test 14/14 +
ablation delta 5/5→0/5 + model-dependence nuance; no fabricated number) → the enforced loop →
executor modes (recommend two-brain; offer both solos; honest "separation ≈ neutral for one-shot
catch-rate") → app-profile → install → accurate repo map → real metrics footer. Keep the existing
SVGs.

## 4. Non-goals

Not redrawing every SVG; not changing framework behavior (docs only).

## 5. Acceptance tests

- **AT-1:** first screen is value prop + moat, not a skill/rule enumeration.
- **AT-2:** catch-rate section publishes only verified numbers (self-test 14/14; ablation 5/5→0/5)
  with the model-dependence caveat; the string "11/12" does not appear.
- **AT-3:** executor section recommends two-brain + lists both solos + the honest neutrality note.
- **AT-4:** internal links resolve; repo map matches reality (STARTUP.md, hooks/stop_gate.py,
  test/harness/*, ARCHITECTURE.md, CLAUDE.md, prds/, ROADMAP.md); the stale "SessionStart cats
  GUARDRAILS.md" claim is corrected to STARTUP.md.
- **AT-5:** no regression — `run.py --self-test`, `--check-sync`, `--check-startup` green.

## 6. Architect review

1. **Removal.** Removes rule-count-first framing + the fabricated metric + stale hook claim.
2. **SSoT.** Catch-rate claims trace to `test/harness/AT3-evidence.md`; README cites, doesn't
   re-derive. Counts are auditable via grep.
3. **Layering.** Edits `README.md` in place.
4. **Migration debt.** Metrics line + repo map updated to current reality here.
5. **Constitution diff.** README row already in `ARCHITECTURE.md`. No fork.

## 7. Execution

Commit to `master` as `PRD-009`. No push.
