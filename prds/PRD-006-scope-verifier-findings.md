# PRD-006 — Don't let the verifier over-report

**User-visible-surface impact:** Yes — `verify-handback` is scoped to block only on correctness
vs. the stated acceptance criteria; style/speculative findings become non-blocking notes. A new
scenario (S12) guards it.

## 1. Problem (with proof)

PRD-001 through PRD-005 sharpen the verifier into an adversary — which creates the *opposite*
failure: an over-eager adversary that blocks sound work over things the PRD never asked for.
`verify-handback/SKILL.md` today says "Report ❌ for every miss" and "Walk EVERY user journey …
plus downstream effects" with **no scope limit** — so "the naming could be cleaner," "you didn't
test this edge case" (even when it's an explicit non-goal), or "I'd have structured it
differently" all read as blocking findings. An adversary with no scope drives over-engineering
and erodes trust in the gate (if everything is a blocker, nothing is). The framework hardened
"catch real defects" without bounding "don't invent fake ones."

## 2. Root cause

The verifier's findings have no declared *scope*. "Be comprehensive" is stated; "block only on
correctness against the stated acceptance criteria" is not. Without that boundary, thoroughness
silently becomes nitpicking, and the binary accept/block verdict has no rule for sorting a real
defect from a preference.

## 3. Scope

- **`GUARDRAILS.md` (Verification discipline):** add the scoping rule — *block only on
  correctness against the stated acceptance criteria, sanity bounds, freshness, and security;
  style, speculative completeness, and explicit non-goals are at most non-blocking notes, never
  blockers.* (Canonical, with its why.)
- **`verify-handback/SKILL.md`:** a "Scope your findings" section making the two-bucket rule
  explicit (blocking = fails a stated criterion / breaks reality / security or freshness regress;
  non-blocking note = everything else), and "if acceptance is met and reality agrees, the verdict
  is accept — don't manufacture blockers."
- **`STARTUP.md`:** one compressed line in the verification bullet (stay within the ≤60-line
  budget the PRD-002 guard enforces).
- **`test/scenarios.json` (SSoT):** add **S12 — the over-eager adversary**. Sound work that meets
  all acceptance tests, with only style nits + an explicit-non-goal edge case + a personal
  structural preference. Pass = accept / scope those as non-blocking; Fail = block on them.
  Regenerate `scenarios.md`; bump count to 12, target to 11.
- **Fixtures** `good/S12.txt` + `bad/S12.txt` for the self-test.

## 4. Non-goals

- Not softening the real checks (three signals, per-partition, freshness, tamper) — those stay
  blocking. This only reclassifies *out-of-scope* findings.
- Not removing thoroughness — the verifier still surfaces notes; it just doesn't *block* on them.

## 5. Acceptance tests (un-gameable)

- **AT-1 (sound work → zero blocking findings):** in the harness, a verifier operating under the
  scoping rule, given work that meets the criteria with only style/non-goal nits, **accepts**
  (S12 passes). Demonstrated live: a guardrailed verifier accepts; an explicitly nitpicky/
  completionist verifier **over-blocks** and S12 fails for it — proving the rule changes behavior
  and the rubric detects over-blocking.
- **AT-2 (broken work still blocked):** the existing catch scenarios (S1–S11) still pass — scoping
  findings did not make the verifier credulous. Self-test stays green; the credulous transcripts
  still score 0.
- **AT-3 (self-test discriminates S12):** `--self-test` passes `good/S12` (accepts, notes nits)
  and fails `bad/S12` (blocks on style/non-goal).
- **AT-4 (count/target):** `scenarios.json` has 12 scenarios; `--check-sync` green; target = 11.

## 6. Architect review

1. **Removal.** Removes the unbounded "report every miss as a blocker"; replaces with a scoped
   two-bucket verdict.
2. **SSoT.** The scoping rule lives once in `GUARDRAILS.md`; the SKILL + STARTUP reference/compress
   it; the scenario lives in `scenarios.json` (the test SSoT). No forked rule text.
3. **Layering.** Edits the verifier rule + the scenario set in place; no parallel verifier.
4. **Migration debt.** Rule + skill + primer + scenario + fixtures ship together.
5. **Constitution diff.** No new component; extends existing Method + Test-kit entries. Count
   bumps 11→12 (the CLAUDE.md sanity bound already anticipates this).

## 7. Execution

Commit to `master` as `PRD-006` once AT-1…AT-4 pass. No push.
