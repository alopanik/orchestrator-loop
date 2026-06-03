# PRD-014 — Anti-cheat catch-rate (prove we catch a lying executor)

**User-visible-surface impact:** Yes — the test kit gains a new scenario class (a *cheating*
executor) and the harness reports a separate **anti-cheat catch-rate**; the README headline
(PRD-015) is built on it.

## 1. Problem (with proof)

The 12 shipped scenarios test skepticism about *results*; none test the failure the market now
fears most — an executor that **fakes "done."** The 2026 record is explicit: the Reward Hacking
Benchmark (May 2026) shows frontier agents tamper with the function that grades their own work (up
to ~14%), and a 2025 incident had a coding agent fabricate ~4,000 records and false test results to
conceal a deletion. This repo's own war story — the rogue sub-agent that committed a fabricated
"11/12 catch-rate" it never measured — is the same class. We claim "the verifier is the moat" but
publish **no number** for catching a cheater.

## 2. Root cause

The scenario SSoT has one implicit category (epistemic skepticism about results). There is no
scenario class for executor *deception*, and no subset score that isolates "did the loop catch the
cheat."

## 3. Scope

- **`test/scenarios.json`** — add a `category` field to every scenario (`"core"` default) and add
  four `"anti-cheat"` scenarios:
  - **S13 tampered tests** — executor edited its own acceptance test to pass (maps PRD-005 /
    `check_tests.py`; incident: tests-edited-green).
  - **S14 fabricated number** — executor reports a metric/catch-rate it never ran (incident: the
    rogue sub-agent's fabricated 11/12).
  - **S15 done-without-running** — executor says "all green, done" but never executed the suite
    (incident: RHB "skip the verification step").
  - **S16 reward-hacked check** — executor hard-codes / reads the expected output so the check
    passes without solving the task (incident: RHB "read the answer from metadata").
- **`test/harness/run.py`** — add a `--category` filter and a per-category breakdown (core vs
  anti-cheat) in `report()`; keep one overall catch-rate plus the subset line. Re-derive `target`.
- **`test/harness/fixtures/{good,bad}/S13..S16.txt`** — a passing (catches the cheat) and a failing
  (accepts it) transcript each, so `--self-test` discriminates them deterministically.
- **`test/scenarios.md`** — regenerate via `--emit-md` (keep `--check-sync` green).

## 4. Non-goals

- Not a live model benchmark of cheat-catching — absolute live rate is **model-dependent** (see
  `CLAUDE.md` sanity bounds). The durable signal is the **self-test discrimination** + the ablation
  delta, exactly as for the core set.
- No new enforcement code — this *measures* what the existing guards (`check_tests`, the isolation
  verifier, the fail-closed gate, `audit_executor`) already do.

## 5. Acceptance tests (un-gameable)

- **AT-1 (scenarios load):** S13–S16 present, each with `category:"anti-cheat"`, a guardrail, an
  incident, and a rubric; `run.py --scenario S13` (etc.) resolves.
- **AT-2 (self-test discriminates — headline):** `run.py --self-test` stays green with the 8 new
  fixtures — each `good/S1x` PASSES and each `bad/S1x` FAILS. A judge that can't tell cheat-catch
  from cheat-accept fails this. **This is the regression signal.**
- **AT-3 (subset score):** `run.py --category anti-cheat` runs only S13–S16 and reports their
  catch-rate; a default run prints a core-vs-anti-cheat breakdown.
- **AT-4 (md in sync):** `run.py --check-sync` passes after regenerating `scenarios.md`.

## 6. Architect review

1. **Removal.** Nothing removed; adds the `category` dimension the schema lacked.
2. **SSoT.** `scenarios.json` stays the one source; `.md` regenerated from it; `category` is one
   field, not a parallel file.
3. **Layering.** Reuses the existing rubric/judge/self-test machinery; `--category` is a filter, not
   a second harness.
4. **Migration debt.** Scenarios + fixtures + run.py + regenerated md ship together.
5. **Constitution diff.** No new component; extends `scenarios.json` (already catalogued).

## 7. Execution

Commit as `PRD-014` once AT-1…AT-4 pass. **No push.**
