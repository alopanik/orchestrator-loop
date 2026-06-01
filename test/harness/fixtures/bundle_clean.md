# Verifier bundle — PRD-141 (isolated)

## Diff under review
```diff
- score = trigger_compute(inputs)   # on-write trigger
+ # score is now written only by score_writer_batch; NULL when inputs incomplete
```
This is the only thing the verifier may read about what changed. Note: a comment here may say
"root cause" or "rationale" and that is fine — diff bodies are exempt.

## Acceptance criteria
- AT-1: max |recorded - actual| across buckets (n>=500) <= 0.06.
- AT-2 (per partition): for every day in the last 30 (n>=100), the should-net-zero canary in [-10, 0].
- AT-3: exactly one write-path to items.score (grep + trigger list).

## App-profile facts / sanity bounds
- A should-be-balanced A/B more than 55/45 out of balance has an assignment bug.
- Model accuracy below the random-chance floor is impossible (leaked source).
- One concept -> one table; one write-path per table.
