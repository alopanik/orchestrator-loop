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

> **Full method, the constitution + CI machinery, and worked catches:**
> `references/methodology.md`. Systems rot one reasonable-looking addition at a time; these
> questions are the ratchet against it. The Design-guardrails rules + their war stories live in
> `GUARDRAILS.md` — load on demand; the startup primer carries only the always-on core.

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

Back the review with machinery so it sticks between reviews: a **constitution doc** (every
store's one purpose / one write-path / readers — *if it isn't in the doc, it doesn't exist*)
and a **`~~ci` guardrail** that fails the build on banned patterns (a `_v2`-style store, a
fork view, a store not in the constitution), scoped to the PR diff. Confirm this change would
pass it. A failed review sends the PRD back to `draft-prd`, not forward to
`handoff-to-executor`.
