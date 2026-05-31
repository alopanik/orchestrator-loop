---
name: architect-review
description: >
  Run the architect review on a PRD before it is handed to the executor. Use when a PRD is
  drafted and about to ship, when the user says "review this design", "architect review", or
  before any structural change. Catches layering and forking before any code is written.
---

# Architect review

Before any PRD is handed off, answer these five questions in the PRD's review section. A bad
answer is a redesign, not a warning.

1. **Removal.** What is being REMOVED in this change? If nothing, why? A change that only
   adds — while touching an existing concept — is usually layering. Find what it replaces.

2. **Single source of truth.** What is the SSoT for the concept this PRD touches, and is the
   PRD writing through that one source's one owner (one writer per table/value/rule)?

3. **Layering.** Are we adding a layer on top of an existing concept, or editing the existing
   one? Choose editing unless there is a clear, stated case for a new layer.

4. **Migration debt.** What gets cleaned up IN this PRD? Structural change ships its own
   cleanup — the change that adds the canonical thing also drops what it supersedes.

5. **Constitution diff.** Does this EXTEND the canonical model the app declares (its
   architecture/constitution doc), or FORK it? If it forks, stop and redesign. Cite the
   constitution entry it touches.

If a CI guardrail exists (a migration/structure linter), confirm this change would pass it.
A failed review sends the PRD back to `draft-prd`, not forward to `handoff-to-executor`.
