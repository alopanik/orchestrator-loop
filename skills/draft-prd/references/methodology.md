# Draft a PRD — methodology + worked example

The `SKILL.md` gives the required structure. This is the craft: what makes each section
*load-bearing* instead of ceremonial, and a full worked PRD. A PRD is two things at once —
the design the owner reviews before the diff lands, and the self-contained brief the executor
builds from. Both readers are unforgiving of vagueness.

## The two sections that carry the PRD

Most PRDs live or die on **proof** and **acceptance tests**. Get those right and the rest
follows.

### Problem, with proof — numbers, not adjectives

State the problem and then *prove it with concrete evidence*: a query result, a failing
test, a log line, a screenshot. "Scores feel random" is a complaint; "across 9 score buckets
(n≥500 each), recorded score vs. actual outcome rate diverges by up to 0.27" is a problem.
**No proof, no PRD** — if you can't prove it, you don't yet understand it well enough to
spec the fix.

Apply the epistemics while gathering proof:

- If the problem is a *good* number you distrust, prove the contamination (reproduce it,
  trace it to source) and put the impossible value in the PRD as the canary the fix must
  kill. A surprising good result is a data bug until proven otherwise — the PRD is where you
  prove it.
- Quote the evidence verbatim (the exact query, the exact error string). A PRD that
  paraphrases its evidence invites a fix aimed at the paraphrase.

### Root cause — the mechanism, not the symptom

Name *why* it happens at the level of "this function reads the wrong source," "this column is
two types across these tables," "this query does a deep-offset scan and blows the timeout."
If you can only describe the symptom, the PRD isn't ready — do more discovery. A PRD whose
root cause is "the numbers are off" produces a fix that's also just "off."

Two tells that you've found the *real* root cause:
1. You can explain why the existing patches didn't work (if there were any).
2. You can name every *other* code path that could reproduce the same bug — and the scope
   includes fixing them too (the same bug returns through a different door).

### Acceptance tests — un-gameable, outcome-based, measured against reality

This is the section the executor will (consciously or not) optimize against. Design it so the
*only* way to pass is to actually fix the problem.

- **Outcome-based, against reality.** Tests assert on the datastore / the rendered UX / the
  deploy — never "the code looks right." Each must be something *you can independently re-run
  after the handback.*
- **Un-gameable.** A test the executor can satisfy without fixing the root cause is not
  allowed. "Function returns without error" is gameable; "the canary that was +61 is now in
  [−10, 0], and no record priced < 0.10 exists without a verifiable source" is not.
- **Per-partition where local contamination is possible.** A corpus-wide gate can pass while
  one partition is broken — aggregate hides local. If the failure can be localized, the
  acceptance test must check per partition (per day/group, min N), not just the global
  average. *This is a real, repeated miss:* a global integrity gate at ≈ −5 passed while one
  day's slice sat at +57; the per-slice gate is what would have caught it.
- **Includes the canary that proves the negative.** The best acceptance test is often a
  number that is *structurally impossible* unless the bug is gone (a two-sided payoff that
  must net ≤ 0; a probability that must lie in [0,1]; an error score that can't beat the
  random-chance floor).

## The other sections (each in one tight move)

- **User-visible-surface impact** (one line, in the header): what the user sees change, or
  "none (plumbing)." If a correct fix will make a headline metric look *worse* because the
  old value was inflated, say so here — honestly, as the correct outcome.
- **Scope:** the smallest change that fixes the root cause and leaves the system whole. Name
  the exact files/stores/functions. If it removes or merges something, say so — structural
  change ships its own cleanup.
- **Non-goals:** what this explicitly does NOT do, so scope can't creep.
- **Architect review:** run the `architect-review` skill and record the answers (removal,
  single-source-of-truth, layering, migration debt, constitution-diff). A failed review sends
  the PRD back here, not forward.
- **Execution:** branch name; explicit commit policy; migrations as 2-stage soft-deprecate
  (add → backfill → swap reads → drop), never a bare destructive change, never DDL without a
  verified-deploy/readers check.

## Worked example (app-agnostic, abbreviated)

```
# PRD-141 — Restore integrity of the per-item quality score

**User-visible-surface impact:** None directly; but every ranking and the "top items"
list read these scores. Expect many scores to move sharply (some high scores drop near
zero). That is the correct outcome — the current values are an artifact.

## 1. Problem (with proof)
The stored quality score is not calibrated to outcomes. Bucketing items by recorded
score vs. actual success rate (n≥500/bucket):

| recorded score | actual rate | n |
|---|---|---|
| 0.08 | 0.34 | 1,183 |   <- impossible: a 0.08 score "succeeding" 34% of the time
| 0.50 | 0.49 | 571  |
| 0.91 | 0.64 | 1,189 |

Canary: averaging a should-net-zero reconciliation across all items returns +61 (must be
≈0). Proof of contamination, not signal.

## 2. Root cause
`score_writer_batch` and the on-write trigger both write `items.score` (two write-paths).
The trigger reads `inputs.final_value`, which is NULL at insert and backfilled later, so
the trigger stores a score from incomplete inputs; the batch later disagrees. The cheap-
score errors are amplified by the convex ranking weight. Same class also reachable via the
import path, which calls the trigger.

## 3. Scope
- Remove the on-write trigger; `score_writer_batch` becomes the single write-path.
- Recompute scores only from finalized inputs; NULL the score when inputs are incomplete
  (never guess).
- Fix the import path to enqueue a batch recompute rather than write directly.
Files: `score_writer_batch`, `triggers/on_item_write`, `import/ingest`.

## 4. Non-goals
No new scoring model; no UI change; no change to the ranking weight (separate PRD).

## 5. Acceptance tests (un-gameable)
- AT-1 (calibration): max |recorded − actual| across buckets (n≥500) ≤ 0.06. (Today: 0.27.)
- AT-2 (canary): the should-net-zero reconciliation is in [−10, 0]. (Today: +61.)
- AT-2b (PER PARTITION): for EVERY day in the last 30 (n≥100), the same canary is in
  [−10, 0]. A localized re-contamination must turn this red even if AT-2 passes.
- AT-3 (one write-path): exactly one writer to items.score (grep + DB trigger list).
- AT-4 (no fabricated cheap winners): no item with score < 0.10 unless its inputs are
  finalized and verifiable.

## 6. Architect review
Removal: deletes the second write-path (not a guard on top). SSoT: one writer.
Layering: fix at the writer, not a downstream filter. Migration debt: drops the trigger
in-PRD. Constitution: extends the `items` entry (one write-path invariant); cite it.

## 7. Execution
Branch `prd-141-score-integrity`. Run the AT SQL; commit + push only when AT-1, AT-2, AND
AT-2b pass. Do not commit partial work. Report before/after as a table (the canary first).
```

Note the shape: the proof is numeric and quoted; the root cause names the mechanism *and*
the sibling path; AT-2b exists *because* AT-2 alone can be diluted; the "scores will drop,
that's correct" honesty is in the header where the owner sees it first.

## Discipline reminders

- Build IN, not ON TOP: the PRD fixes the existing path; it never adds a layer above a broken
  thing.
- Keep app-specific facts (store names, infra refs, domain rules, sanity bounds) sourced from
  the app-profile; reference connectors as `~~category`.
- When the PRD is ready, do **not** hand off yet — pass it through `architect-review` first.
