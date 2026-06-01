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

- weak: "work on market-making."
- strong: "a paper market-making engine exists and its edge is proven out-of-sample on the clean
  corpus, AND a `/…/mm` surface renders it in the app (renders + network 200 + datastore), with
  no real-money path enabled — pause before any live order."

Confirm in one line, then move. Don't gold-plate the goal; act on the best reading.

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

**Goal:** "Two reliable revenue methods live in the app, each proven before it's trusted; ship
the UI for both. Method 1 already shipped. Drive Method 2 (market-making) home."

A `go` session:

1. **Orient.** Read app-profile → sanity bounds say "edge is only real if it survives
   out-of-fold on the clean corpus; >X return on N≥… is a data bug." Roadmap → next is PRD-300
   (market-making). PRD folder → 299 shipped, nothing in flight. Report: *last shipped 299 ·
   in-flight none · parked the categories idea · next 300 (MM).*
2. **Goal.** Restate: "PRD-300: a paper MM engine whose edge is proven OOS, + an integrated
   `/mm` surface (renders + 200 + datastore), no live orders. Done when both hold, verified."
3. **Drive 300.** draft-prd (problem: is there MM edge? proof bar: OOS spread-capture minus
   fees/adverse-selection, per-partition) → architect-review (extends the existing pricing
   store? one write-path?) → handoff (build the paper engine; commit on green) → verify
   (reproduce the edge number myself; is it above the sanity floor? does the surface render with
   live data?). Edge proven on paper, surface integrated, verified.
4. **Boundary.** The next step would be enabling **real orders** — irreversible/real-money.
   STOP. Report: "Method 2 paper-proven and surfaced, verified; going live needs your
   go/no-go — recommend a capped live pilot only after N days of paper tracking holds the
   edge." Wait.

Note what `go` did: drove a whole PRD through all five stages without checking in, re-oriented at
the seam, kept the skepticism numerate against the app's sanity bounds, and stopped exactly at
the real-money line — not before, not after.
