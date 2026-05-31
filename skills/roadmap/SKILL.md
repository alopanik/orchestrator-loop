---
name: roadmap
description: >
  Translate a mission, vision, or broad request into a sequenced, numbered PRD roadmap.
  Use when the user says "plan the roadmap", "what should we build next", "sequence this
  work", "turn this into PRDs", "map out the project", or hands over a broad/ambiguous goal
  that needs to be decomposed before any code is written.
---

# Roadmap

Turn a broad goal into an ordered set of PRD-sized units of work. This is role 3 (run the
roadmap): requirements arrive broad; you drill in at high AND low level, do discovery, and
produce a sequence the executor can chew through.

## Procedure

1. **Anchor on the mission.** Restate the goal in one sentence and the success condition.
   If the goal is genuinely ambiguous in a way that changes the plan, ask 1–3 focused
   questions — otherwise proceed on the best reading and state it.

2. **Discover the current state before planning.** Read the app-profile. Inspect reality
   through the connectors — query `~~database`, read the repo via `~~vcs`, check what's
   deployed on `~~hosting`. Do not plan against assumptions; plan against what is actually
   there. Write down the gap between current state and the goal.

3. **Decompose top-down, then bottom-up.** Break the goal into subsystems, then into the
   smallest shippable units that each leave the system working. A unit is PRD-sized when it
   has one clear outcome, a verifiable acceptance test, and a bounded blast radius.

4. **Order by dependency and risk.** Lower number ships first — the number IS the
   execution order. Put foundational/plumbing work that everything else needs before the
   features that depend on it. Put reversible/low-risk work before irreversible/high-risk.
   Flag any unit that is gated on another (data migration, a deploy, an external job).

5. **Write the roadmap as a table**, one row per PRD: `# | scope (one line) | depends-on |
   user-visible? | risk`. Keep it to outcomes, not implementation. Save it to the app's
   docs location as a living document and update it as PRDs land.

6. **Reconcile, don't accumulate.** If the new work overlaps existing tables/functions/UI,
   the roadmap must say what gets REMOVED or merged — not just what's added. Layering is the
   failure mode; building IN is the goal.

## Output

A numbered roadmap (lowest = next). Each entry is ready to feed the `draft-prd` skill. Hand
the user the table and name the single next PRD to write. Do not start coding from the
roadmap — each unit still goes through `draft-prd` → `architect-review` → `handoff-to-executor`.
