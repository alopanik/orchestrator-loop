---
name: draft-prd
description: >
  Write a single PRD (product/engineering requirements doc) in the house format before any
  code is handed off. Use when the user says "write a PRD", "spec this", "draft PRD for X",
  or when a roadmap entry is the next thing to build. Every non-trivial change gets a PRD first.
---

# Draft a PRD

A PRD is the design the owner reviews before the diff lands, and the self-contained brief
the executor builds from. Write it to a file — **PRDs are pointers, never inline body in chat.**

> **Full method + a complete worked PRD:** `references/methodology.md`. Most PRDs live or die
> on two sections — **proof (numbers, not adjectives)** and **un-gameable acceptance tests**;
> the reference goes deep on both. The PRD-discipline rules + their war stories live in
> `GUARDRAILS.md` (PRD discipline · Design guardrails) — load on demand; the startup primer
> carries only the always-on core.

## File + numbering

- Save to the app's PRD directory as `PRD-NNN-short-kebab-title.md`. Find the next number by
  listing existing `PRD-*.md` and incrementing the highest. Never reuse a number.
- **The number is the execution order** — lower ships first.

## Required structure

```
# PRD-NNN — <title>

**User-visible-surface impact:** <one line — what the user sees change, or "none (plumbing)">.

## 1. Problem (with proof)
State the problem and PROVE it with concrete evidence — a query result, a failing test, a
log line, a screenshot, quoted verbatim. No proof, no PRD. If the problem is a *good* number
you distrust, prove the contamination here (a surprising good result is a data bug until
proven) and capture the impossible value as the canary the fix must kill.

## 2. Root cause
The actual mechanism, not the symptom. If you can't name the root cause, do more discovery.

## 3. Scope
The smallest change that fixes the root cause and leaves the system whole. Name the exact
files/tables/functions touched.

## 4. Non-goals
What this explicitly does NOT do (so scope can't creep).

## 5. Acceptance tests (un-gameable)
Outcome-based, measured against reality (the datastore / the rendered UX / the deploy), not
"the code looks right". Each must be something you can independently re-run after the
handback. A test the executor can satisfy without actually fixing the problem is not allowed.
**Gate per partition where local contamination is possible** — a corpus-wide gate can pass
while one partition is broken (aggregate hides local). Prefer a canary that is structurally
impossible unless the bug is gone.

## 6. Architect review
Run the `architect-review` skill and record the answers here (removal, single-source-of-truth,
layering, migration debt, constitution-diff).

## 7. Execution
Branch/commit/push discipline. State explicitly whether the executor may commit. Migrations
and irreversible steps are 2-stage soft-deprecate (add → backfill → swap reads → drop), never
a bare destructive change, and never ship DDL without a verified deploy/readers check.
```

## Discipline

- Build IN, not ON TOP: the PRD fixes the existing path; it does not add a layer above a
  broken thing.
- If the change removes/merges something, say so in Scope — structural change ships its own
  cleanup in the same PRD.
- Keep app-specific facts (table names, infra refs, domain rules) sourced from the
  app-profile; reference connectors as `~~category`.
- When the PRD is ready, do NOT hand off yet — pass it through `architect-review` first.
- **Trivial-change fast path (PRD-007).** Before writing a full PRD, check eligibility:
  `python3 "${CLAUDE_PLUGIN_ROOT}/test/harness/classify_change.py" --staged`. If it reports
  TRIVIAL (one-line, reversible, single-file, no migration/schema/structural content), skip the
  roadmap + full PRD + architect-review and go straight to make-it-then-verify — but still run the
  verify gate. A migration / multi-file / destructive change is never trivial; write the PRD.
