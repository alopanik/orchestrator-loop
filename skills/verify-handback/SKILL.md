---
name: verify-handback
description: >
  Independently verify an executor's completed work before accepting it. Use when the executor
  reports done, when the user says "verify", "QA this", "did it actually work", or after any
  handoff returns. The executor can test itself; never trust it — always test independently.
---

# Verify the handback

This is role 2 (QA). The executor's "done" is a claim. Re-establish every claim yourself,
against reality.

## Three signals (all required for a UI-affecting change)

1. **It renders.** Walk the affected routes via `~~browser-qa`. No console errors; the change
   is actually visible on screen.
2. **The network is green.** The calls the page makes return success (HTTP 200), not silent
   failures or empty fallbacks.
3. **The datastore reflects it.** Query `~~database` directly — row counts, values, and schema
   match what the PRD promised.

DB-only verification is a failure mode; browser-only is too. Get all three.

## Comprehensive, not feature-local

- Walk EVERY user journey the change could touch, click-by-click — not just the one feature.
- Check downstream effects: jobs/crons, server functions, derived views/materializations — did
  they update too?
- Re-run each acceptance test from the PRD against reality. Report ❌ for every miss with
  quoted evidence (the query, the response, the screenshot).

## Mission-level

Step back: does the app still serve its mission after this change, or did it drift? A change
that passes its own tests but moves the product away from its purpose fails review.

## Terminate in strategy

End with a verdict — accept / fix-list / redesign — and the concrete next action. Never a bare
problem list. If it fails, the fix becomes a PRD (or a PRD addendum), not a chat instruction.
