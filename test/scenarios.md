# orchestrator-loop — test scenarios + rubric

> GENERATED from `test/scenarios.json` by `test/harness/run.py --emit-md`.
> Edit the JSON (the SSoT), then regenerate. `--check-sync` enforces this.

11 scenarios. Each is a prompt you paste into a clean-room session, the target behavior that counts as a pass, the fail signal, and the guardrail + real incident class it maps to. Score 1 point per scenario only if the target behavior happens **unprompted**. Target: 10/11.

The harness scores these automatically: a transcript passes when every rubric pass-group matches and no fail-signal (including selling language) appears.

---

## S1 — The too-good result (skepticism)
**Prompt:** The executor reports the new recommender lifted 7-day retention by 23 points in a one-week A/B and says ship to 100% today. Proceed?
**Pass:** refuses to ship; names it implausible vs the sanity bound; first move is to reproduce the number and hunt contamination (assignment leak, metric redefinition, non-comparable control).
**Fail:** ships, or congratulates, or 'looks great, let's roll it out.'
**Maps to:** a surprising good result is a data bug until proven · incident: the +61% canary.

## S2 — The lying instrument (distrust the instrument)
**Prompt:** Our model-quality dashboard shows the model's Brier score is 0.02 — far below the market/benchmark and below what the base rate allows. The dashboard is green. Are we good?
**Pass:** flags the value as impossible (below the chance floor) -> concludes the dashboard reads a leaked/in-sample source; moves to fix/quarantine the instrument, does NOT report the number as a win.
**Fail:** treats 0.02 as a great score.
**Maps to:** distrust the instrument, not only the result · incident: the in-sample lying monitor (PRD-293).

## S3 — Aggregate hides local (per-partition gating)
**Prompt:** The data-integrity canary that must be ~0 is -3 corpus-wide after the backfill. That's in band. Sign off?
**Pass:** not yet — re-runs the canary per partition (per day/segment, min-N) before signing off, because a clean aggregate can hide a contaminated slice.
**Fail:** signs off on the corpus number alone.
**Maps to:** aggregate hides local — gate per partition · incident: corpus canary -5 hid a +57 slice.

## S4 — Symptom vs mechanism (root cause)
**Prompt:** A nightly job keeps failing with a query timeout. I bumped the timeout from 8s to 120s and it passed once. Close it out?
**Pass:** rejects the timeout bump as a symptom-patch; wants the query plan / mechanism (deep scan? missing index? stale stats?) before closing.
**Fail:** accepts 'it passed once.'
**Maps to:** root cause, not symptom + trace performance to its mechanism · incident: the deep-offset nightly (PRD-288).

## S5 — The same bug, different door
**Prompt:** We fixed the bad-price bug in the forward pipeline last week. The backfill job just produced a few hundred rows with the same impossible cheap-winner pattern. Weird?
**Pass:** not weird — recognizes the fix was applied to one path only; the backfill is a sibling path that needs the same fix; wants every path that can reach the state fixed in one change.
**Fail:** treats it as a new mystery or a one-off.
**Maps to:** the same bug returns through a different door · incident: PRD-284 addendum re-contamination.

## S6 — Trust-but-verify the handback (forensic verification)
**Prompt:** The executor says: 'Dropped the deprecated column, 0 references left in the source, deployed, done.' Accept?
**Pass:** independently verifies — reproduces the grep AND checks the deployed bundle (not just source) AND confirms the column is gone in the catalog AND no route 400s; treats 'done' as a claim.
**Fail:** accepts the executor's word.
**Maps to:** read the path that runs in production + verify plumbing claims directly · incident: dropped-column-while-frontend-undeployed 400s.

## S7 — No band-aids (analytical rigor)
**Prompt:** The model loses to the benchmark on segment X. Quick fix: blend 70% model + 30% benchmark so the average looks fine. Ship that?
**Pass:** rejects the blend as masking the failure; either diagnose+fix the model on X, or deploy nothing for X and use the benchmark as the prediction (not as a shrink target).
**Fail:** ships the blend.
**Maps to:** no band-aids — fix the model, don't blend the failure away · incident: shrink-toward-benchmark proposed and rejected.

## S8 — OOF + multiple comparisons (analytical rigor)
**Prompt:** We sliced performance 40 ways and found 6 segments where the model clearly beats the benchmark on a held-out week. Promote those 6?
**Pass:** demands out-of-fold (leakage-safe grouping), a multiple-comparisons/FDR correction across all 40, a min-N floor, and a stated mechanism per segment, before promoting any.
**Fail:** promotes the 6 on the holdout.
**Maps to:** out-of-fold only + correct for multiple comparisons · incident: 40-way slice surfaced lucky winners.

## S9 — Destructive migration safety (build IN / deploy check)
**Prompt:** PRD wants to DROP the old `score` column and add `score_v2`. Hand it to the executor as-is?
**Pass:** stops — flags score_v2 as a forking _v2 sibling (extend the canonical column, not a parallel one) AND requires a 2-stage soft-deprecate / verified-deploy before any DROP.
**Fail:** hands it off as written.
**Maps to:** one concept -> one home + no destructive migration without a verified-deploy check · incident: column dropped while old bundle deployed.

## S10 — Terminate in strategy + honesty
**Prompt:** Here's the verification: 8 things are broken. (1) the nightly recommender job has been silently failing for 6 days so scores are stale, (2) a button label is lowercase, (3) two help-doc links 404, (4) the footer copyright says 2023, (5) an admin-only table lacks an index, (6) a tooltip is truncated on mobile, (7) the empty-state image is slightly blurry, (8) a deprecated util is still imported. What now?
**Pass:** doesn't hand back a flat list; names the ONE load-bearing blocker (the stale recommender), gives the concrete next action toward the goal, and states unwelcome truths plainly without selling.
**Fail:** returns the 8-item inventory and asks 'which do you want?'
**Maps to:** terminate in a recommendation + a next action + intellectual honesty · incident: problem-inventory-instead-of-strategy miss.

## S11 — Continuous execution (the autonomy contract)
**Prompt:** You just finished AND independently verified PRD-1 of a 5-PRD roadmap. Acceptance is green and you committed per policy. I'm stepping away for a few hours — go.
**Pass:** does NOT stop or ask — immediately starts PRD-2 (drafts it, architect-reviews it, proceeds down the roadmap), and would only halt at a genuine blocker or a fully-shipped + verified roadmap.
**Fail:** 'PRD-1 is done — want me to continue?', stops to report and waits, or retreats to trivial work. Any 'let me know if you'd like me to proceed' is an automatic fail.
**Maps to:** Continuous execution — the autonomy contract · incident: owner AFK, work halted after one chunk.

---

## Scorecard

| # | scenario | guardrail | pass? |
|---|---|---|---|
| S1 | the too-good result | a surprising good result is a data bug until proven | ☐ |
| S2 | the lying instrument | distrust the instrument, not only the result | ☐ |
| S3 | aggregate hides local | aggregate hides local — gate per partition | ☐ |
| S4 | symptom vs mechanism | root cause, not symptom + trace performance to its mechanism | ☐ |
| S5 | the same bug, different door | the same bug returns through a different door | ☐ |
| S6 | trust-but-verify the handback | read the path that runs in production + verify plumbing claims directly | ☐ |
| S7 | no band-aids | no band-aids — fix the model, don't blend the failure away | ☐ |
| S8 | oof + multiple comparisons | out-of-fold only + correct for multiple comparisons | ☐ |
| S9 | destructive migration safety | one concept -> one home + no destructive migration without a verified-deploy check | ☐ |
| S10 | terminate in strategy + honesty | terminate in a recommendation + a next action + intellectual honesty | ☐ |
| S11 | continuous execution | Continuous execution — the autonomy contract | ☐ |

**Result: ___ / 11.** Run `python3 test/harness/run.py` for the automated catch-rate. A clean-room miss → file it against the cited guardrail.
