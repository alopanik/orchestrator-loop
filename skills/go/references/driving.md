# Driving a session with `go` — method + worked example

`go` is a thin orchestrator over the six stage skills plus the Session-completion guardrail. Its
whole job is to remove the per-step juggling: the user sets ONE goal, you drive everything to
that goal. This file is the full method and a worked multi-PRD session.

## The mindset

A session is not "do a task." It's "reach a definition of done." The PRD is the unit of *work*;
the **goal** is the unit of *session completion*. You loop — PRD after PRD — and you do not hand
the turn back at a milestone. The only legitimate stops are: goal met + verified, a real
user-only decision (especially anything irreversible/real-money), or the user halting you. If you
catch yourself about to write "shipped PRD-N — want me to continue?", that's the failure mode;
start PRD-N+1 instead.

## Step 1 — Orient (the checklist)

Read, don't recall. Concretely:

- **App-profile (`CLAUDE.md`)** — connectors, domain rules, **sanity bounds / impossible
  values**, constitution + roadmap pointers. This is what makes your skepticism numerate for
  *this* app.
- **Roadmap** — the numbered sequence; lowest unshipped = the default next goal.
- **PRD folder** — highest number + statuses tell you what shipped and what's mid-flight.
- **Task list / memory / notes** — in-flight work, parked items, prior decisions.
- **Live state** (if connectors are wired) — a cheap freshness/health query so you plan against
  reality, not the doc. If a monitor shows something implausibly good, distrust it before you
  build on it.

Report: **last shipped · in-flight · parked · next up** — each line backed by something you just
read.

## Step 2 — Set the goal

Restate the user's goal as a testable definition of done, or propose one from the roadmap. Good
goals name an outcome + its proof and often span several PRDs:

- weak: "work on the new scoring feature."
- strong: "a scoring engine exists and its accuracy is proven out-of-fold on held-out data, AND a
  surface renders it in the app (renders + network 200 + datastore), with no irreversible action
  enabled — pause before the first production write."

Confirm in one line, then move to refinement (Step 2.5) — don't drive yet.

## Step 2.5 — Refine into full requirements (garbage in, garbage out)

The single most valuable thing `go` does before building. A crisp-sounding goal almost always
hides decisions that change what gets built. Close them with a short, batched round of questions,
then decompose to testable requirements at every level.

Worked example — goal: *"add a scoring engine + a surface for it."* That's weak. The refinement
pass asks (batched, high-signal):

- **Scope / data:** what's scored, on what inputs, how often? Is there ground truth to measure
  accuracy against, or only proxies?
- **Integration surface (the part agents skip):** which route does the surface live at? which
  table stores scores, and *who is the single writer*? who reads it downstream?
- **Success + sanity bounds:** what accuracy clears the bar, measured how (OOF? per segment)?
  what value would be *too good to be true* (a data-bug signal) for this metric?
- **Non-goals / irreversible steps:** live writes? a migration? — flag the pause points now.

From the answers, emit an itemized **requirements spec** — e.g.:
1. `score_engine` computes X from finalized inputs only; OOF accuracy ≥ baseline, per segment,
   FDR-corrected. *(acceptance: re-run OOF; beats baseline; no value above the plausible ceiling.)*
2. one writer (`score_writer`) → `item_scores`; catalogued in the constitution.
3. read-only surface at `/scores`; three signals (renders + 200 + datastore).
4. non-goals: no production write this session — pause before the first one.

THIS itemized spec is what the roadmap decomposes; every PRD's acceptance traces back to a line
in it. If the user said "just go," you'd instead restate the goal in one line, note "refinement
skipped — gaps will surface mid-drive," and proceed.

## Step 3 — Drive

For each PRD the goal needs, lowest number first:

1. `draft-prd` — proof in numbers, root cause, scope, un-gameable (per-partition) acceptance.
2. `architect-review` — the 5 questions + constitution diff; a bad answer is a redesign.
3. `handoff-to-executor` — one PRD in flight; explicit commit policy; forbid out-of-scope commits.
4. `verify-handback` — reproduce the number, read the deployed path, three signals,
   per-partition, freshness, mission-level. Terminate in a verdict.
5. **Seam:** the instant it verifies, re-orient cheaply and start the next PRD — same turn.

If the goal isn't decomposed yet, run `roadmap` first to produce the numbered sequence, then
drive it.

## Step 4 — The boundary

Stop only at: goal met + independently verified; a genuine blocker / user-only decision; or an
irreversible/real-money action (**prod deploy, DB migration, trade/transfer**) — pause there with
a crisp statement of the decision and your recommendation. Otherwise keep going.

## Worked example (app-agnostic)

**Goal:** "Ship the next roadmap chunk: a working item-scoring capability, proven before it's
trusted and surfaced in the app. Drive it home — don't stop at one PRD."

A `go` session:

1. **Orient.** Read app-profile → sanity bounds say "a score is only trustworthy if it survives
   out-of-fold on held-out data; accuracy above the theoretical ceiling, or below the
   chance floor, is a data bug." Roadmap → next is PRD-42 (scoring engine), then PRD-43 (the UI
   for it). PRD folder → 41 shipped, nothing in flight. Report: *last shipped 41 · in-flight none
   · parked the export feature · next 42 then 43.*
2. **Goal.** Restate: "PRD-42 + PRD-43: a scoring engine whose accuracy is proven out-of-fold,
   plus an integrated surface that renders it (renders + 200 + datastore). Done when both hold,
   verified — no production write enabled yet."
3. **Drive 42.** draft-prd (problem with proof; bar: OOF accuracy beats the baseline,
   per-partition) → architect-review (extends the existing data model? one write-path?) →
   handoff (build it; commit on green) → verify (reproduce the accuracy number myself; is it
   between the chance floor and the ceiling, or implausibly high → a leak?). Verified. **Seam:
   immediately start 43** — don't check in.
4. **Drive 43.** Same five stages for the surface; verify with the three signals (renders +
   network 200 + datastore reflects it) and a journey walk. Verified.
5. **Boundary.** The goal is met and verified, so the session ends here with a status against the
   definition of done. *(If the next step had been flipping on a production write or a migration,
   `go` would instead STOP and ask — stating the decision and a recommendation.)*

Note what `go` did: drove **two** PRDs through all five stages without checking in between,
re-oriented at the seam, kept the skepticism numerate against the app's sanity bounds, and ended
only when the whole goal was verified — not after the first PRD.
