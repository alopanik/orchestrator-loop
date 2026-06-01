---
name: go
description: >
  THE single entry point for an orchestrator-loop session. Orients on the project, sets ONE
  session goal, REFINES it into fully-covered requirements (probing questions; garbage in,
  garbage out), then autonomously drives the whole rules→roadmap→PRD→handoff→verify loop across
  as many PRDs as the goal needs — looping until the goal is met and independently verified. Use
  when the user says "go", "start", "run the roadmap", "continue",
  "pick up where we left off", "session goal: …", or invokes /orchestrator-loop:go. The user
  normally only ever needs this skill; it calls the six stage skills internally.
---

# go — the session driver

This is the one skill a user runs to start a session. They set ONE goal; you **refine it into
full requirements**, then drive the entire loop to completion. Do not make them juggle the six
stage skills — you invoke those internally. Operate under GUARDRAILS.md throughout, especially
**Refine before you drive** (garbage in, garbage out) and **Session-completion discipline** (the
unit of completion is the GOAL, not a single PRD).

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

## 3. Refine the goal into full requirements — BEFORE driving

This gate is non-negotiable: **garbage in, garbage out.** An autonomous driver is most dangerous
when it confidently builds the wrong thing from an under-specified goal. So before any PRD is
drafted, run a short **refinement pass** that turns the one-line goal into requirements covered
at *both* levels — and surface what you don't know rather than guessing it.

- **Probe the unknowns.** Ask the user focused, batched questions to close the gaps that would
  change what gets built — scope edges, the *integration surface* (where this must plug into the
  existing app — routes, data model, who reads/writes it), success criteria + how each is
  measured, non-goals, constraints, and the sanity bounds for any number that defines "done."
  Prefer a few high-signal questions over an interrogation. (Use the host's structured-question
  UI if available.)
- **Cover every level.** Decompose until each requirement is concrete enough to write an
  un-gameable acceptance test for — high-level outcomes *and* the low-level nuts and bolts
  (schema, the exact surfaces, edge cases, failure modes, migration/deploy needs). A requirement
  you can't yet test isn't refined enough.
- **State assumptions; let the user correct cheaply.** For anything you must assume, write it
  down explicitly so a wrong assumption is caught now, not after three PRDs.
- **You may be abstract, and you may skip — deliberately.** If the goal is already crisp, or the
  user says "just go / don't ask," compress this to a one-line restatement of the requirements
  and proceed — but note that you skipped refinement, so a gap surfaced mid-drive is expected,
  not a surprise. Skipping is a choice you name, not a step you silently drop.
- **Output a brief requirements spec** (the definition of done, now itemized: every requirement
  with its acceptance check + the integration points), confirmed with the user in one pass. THIS
  becomes what the roadmap decomposes and every PRD's acceptance traces back to.

Only with requirements fully covered do you proceed to drive. (The cost of a question now is one
message; the cost of building the wrong thing is the whole session.)

## 4. Drive the loop to completion

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

## 5. Stop only on a real boundary

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
