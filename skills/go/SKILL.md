---
name: go
description: >
  THE single entry point for an orchestrator-loop session. Orients on the project, sets ONE
  session goal (definition of done), then autonomously drives the whole rules→roadmap→PRD→
  handoff→verify loop across as many PRDs as the goal needs — looping until the goal is met and
  independently verified. Use when the user says "go", "start", "run the roadmap", "continue",
  "pick up where we left off", "session goal: …", or invokes /orchestrator-loop:go. The user
  normally only ever needs this skill; it calls the six stage skills internally.
---

# go — the session driver

This is the one skill a user runs to start a session. They set ONE goal; you drive the entire
loop to completion. Do not make them juggle the six stage skills — you invoke those internally.
Operate under GUARDRAILS.md throughout, especially **Session-completion discipline**: the unit
of completion is the GOAL, not a single PRD.

> Full orientation checklist + a worked multi-PRD session: `references/driving.md`.

## 1. Orient (always first)

Read the ground truth before saying anything about what's next — never plan from memory:

- the **app-profile** (`CLAUDE.md`): connectors, domain rules, **sanity bounds**, constitution
  + roadmap pointers;
- the **roadmap** doc (numbered; lowest = next);
- the **PRD folder** (what's shipped, what's mid-flight);
- the **task list** and any **memory/notes** the project keeps.

Then report, in a few lines: **last shipped · in-flight · parked · next up.** Ground every claim
in something you just read, not recall.

## 2. Set the goal (one line, confirmed)

- If the user gave a goal, restate it as the session's **definition of done** — concrete enough
  to test "are we there?" — and confirm in one line.
- If they didn't, **propose** one from the roadmap (typically the next numbered chunk through to
  verified) and state it. Don't stall waiting for elaborate input; a goal you can act on now
  beats a perfect one later — proceed on the best reading and say so.
- A good goal names an outcome and its proof (e.g. "X is live and verified by Y"), not a task.

## 3. Drive the loop to completion

Run continuously toward the goal, invoking the stage skills as internal steps:

`roadmap` (only if the goal isn't already decomposed) → for each PRD the goal needs, in order:
`draft-prd` → `architect-review` → `handoff-to-executor` → `verify-handback` → then **start the
next PRD in the same turn.** Do not stop at a per-PRD checkpoint; the PRD is a step, the goal is
the finish line.

- **One PRD in flight at a time** (handoff rule), but the moment a handback verifies, pick up the
  next without checking in.
- **Re-orient cheaply between PRDs** — re-query the live state so each PRD plans against reality,
  not the plan.
- **Carry the epistemics**: a surprising-good result is a data bug until reproduced; verify
  forensically; terminate each PRD in a verdict, not a problem list.

## 4. Stop only on a real boundary

End the session — and surface it plainly — only when one of these is true (see GUARDRAILS
"Session-completion discipline"):

1. **Goal met AND independently verified** (the three signals / per-partition / mission-level).
   Report what shipped against the definition of done.
2. **Genuine blocker or a decision that's truly the user's** — a real fork, a missing
   credential, or **anything irreversible / real-money: a prod deploy, a DB migration, a
   trade/transfer.** Autonomy drives the build; it never runs *past* a decision the user must
   own. Pause, state the decision crisply with your recommendation, and wait.
3. **The user stops it.**

Reporting a milestone and waiting while the goal is unmet and no boundary is hit is THE failure
mode — keep going.

## Output
A session that ends at a real boundary, with a status against the goal's definition of done:
what shipped + verified, what's queued, and (if paused) the one decision needed and your
recommendation.
