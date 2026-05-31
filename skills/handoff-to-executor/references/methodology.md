# Handoff to executor — methodology + worked example

The `SKILL.md` gives the rules. This is the anatomy of a brief that an executor can build
from *alone*, the commit discipline that keeps the repo clean, and a worked example.

You plan and verify; `~~executor` writes the code. The handoff is the contract between those
two roles. A weak handoff produces a weak diff and a verification full of surprises — the
quality of what comes back is set here.

## The core property: self-contained

The executor must be able to build from the brief alone. That cuts two ways depending on
what `~~executor` can see:

- **If the executor can read the repo and your docs** (a coding agent with filesystem
  access): the brief is a short prompt that points to the PRD file path + the branch name.
  Keep it short *because* the PRD is the spec — don't re-summarize it and risk drift.
- **If the executor cannot read your docs** (a sandboxed or remote agent): inline the
  **entire** PRD body in the message. Never hand it a path it can't open, and never a half
  reference ("see the PRD") with no PRD attached — that's a brief the executor never actually
  received.

The test: could someone with zero prior context and only this message produce the right
diff? If not, it's not self-contained yet.

## Commit discipline — state it every time

Commit policy is **explicit in every brief**, never assumed:

- **Default for a completed PRD with green acceptance: commit + push.** A finished, verified
  unit of work shouldn't wait on a permission round-trip — that's friction with no safety
  gain.
- **Speculative / ad-hoc / exploratory work waits for sign-off.** If the change isn't a
  PRD with passing gates, it doesn't auto-commit.
- **The executor commits and pushes — the owner does not.** Never end a handoff by telling
  the owner to push the branch; the executor's job includes the push. (Telling the owner to
  push is a workflow violation, not a courtesy.)

## Forbid out-of-scope commits — explicitly, every time

A global "don't commit unrelated changes" rule **does not auto-propagate to a sub-agent.**
The executor starts fresh; if you don't say it, it isn't bound. So every brief states: *do
not commit anything outside this PRD's scope; do not auto-commit beyond what the Execution
section authorizes.* This one sentence prevents the executor from sweeping unrelated working-
tree changes into the commit.

## Sequencing — one in flight

One PRD per handoff, in numbered order (lowest first). **Do not stack the next brief while
one is in flight** — wait for the handback. Stacking work on a busy executor makes
coordination harder and invites half-merged states. If the owner signals an executor is
already working ("pasting the next one now," "it's on it"), stop drafting new briefs and wait
for the handback.

## What every brief restates

Even when it points to the PRD, the brief restates the *operational* essentials so they can't
be missed:

- **Branch name** (explicit).
- **The acceptance tests**, and the instruction to run them and report **before/after
  numbers** — not "done," but the actual figures.
- **Commit policy** for this specific handoff.
- **The no-out-of-scope-commit line.**
- **What to report back** (the AT results as a table; the canary number first if there is
  one).

## Worked example — executor can read the repo

```
Execute PRD-141 (score integrity). Spec: _docs/prd/PRD-141-score-integrity.md — build
from it; it is self-contained.

Branch: prd-141-score-integrity (create from main).

Acceptance — run all and report before/after as a table, canary first:
  AT-1 calibration max|recorded−actual| ≤ 0.06 (today 0.27)
  AT-2 should-net-zero canary in [−10,0] (today +61)
  AT-2b SAME canary PER day, last 30 days, n≥100 each — all in [−10,0]
  AT-3 exactly one write-path to items.score
  AT-4 no item score < 0.10 without finalized, verifiable inputs

Commit policy: commit + push ONLY when AT-1, AT-2, AND AT-2b are green. Do not commit
partial or speculative work. Do NOT commit anything outside PRD-141's scope. You commit
and push the branch — do not ask me to push.

Report back: the AT table, plus the row count of items whose score changed.
```

Note: short, because the PRD carries the spec — but it pins the branch, restates the gates
(including the per-partition AT-2b), sets the commit policy, forbids out-of-scope commits,
and asks for numbers, not a "done."

## After dispatch

Wait for the handback. Do not start the next PRD. When the executor reports done, do **not**
accept it — run `verify-handback`. The executor's "done" is a claim to be tested, not
trusted; the next skill is how you test it.
