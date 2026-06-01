# Verifier bundle — PRD-141 (LEAKY)

## Diff under review
```diff
+ # score written only by score_writer_batch
```

## Acceptance criteria
- AT-1: calibration max gap <= 0.06.

## Root cause
The trigger read inputs.final_value which is NULL at insert; why it works now is that we moved
the write to the batch. As I built this, my reasoning was that the convex weight amplified it.

## App-profile facts / sanity bounds
- Accuracy below the chance floor is impossible.

## Build log
The executor reports: implemented the batch writer, deleted the trigger, all green.
