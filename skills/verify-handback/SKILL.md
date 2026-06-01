---
name: verify-handback
description: >
  Independently verify an executor's completed work before accepting it. Use when the executor
  reports done, when the user says "verify", "QA this", "did it actually work", or after any
  handoff returns. The executor can test itself; never trust it — always test independently.
---

# Verify the handback

This is role 2 (QA). The executor's "done" is a claim. Re-establish every claim yourself,
against reality — as an adversary trying to break the claim, not a co-author hoping it worked.

> **Full forensic method + a worked verification:** `references/methodology.md`. The checklist
> below is the floor; the method is an investigation — reproduce the exact number, read the
> deployed path, distrust any too-good instrument, and gate per partition. The war stories these
> rules were paid for live in `GUARDRAILS.md` (Verification discipline · Epistemics · Analytical
> rigor) — load them on demand; the startup primer carries only the always-on core.

## Run as an isolated subagent — independence is structural, not a vibe

Confirmation bias is strongest when the mind that built the change also blesses it. So the
verifier runs as a **fresh subagent** whose context is a **whitelisted bundle and nothing else**:

1. **the diff** under review,
2. **the acceptance criteria** (the PRD's un-gameable checks — what must be true),
3. **the app-profile facts + sanity bounds** (`~~database`, impossible values, invariants).

It must NOT receive: the PRD's problem/root-cause narrative, any planning or design reasoning,
the build log, or the executor's self-report. The verifier learns *what changed* and *what must
hold*, then establishes the truth from the bundle + reality (the connectors) — never from the
build story. (Zero-setup, when you are your own verifier: spawn the subagent anyway, or at
minimum assemble the bundle and refuse to consult the build context while verifying.)

Assemble the bundle, then check it is clean before you spawn:

```
python3 test/harness/run.py --check-isolation <bundle.md>   # exits nonzero if build context leaked
```

A leaked `## Root cause` / `## Build log` / "why it works" / "the executor reports" fails the
check — fix the bundle, don't verify a contaminated one. See `references/methodology.md` for the
bundle spec and why each exclusion exists.

## Be forensic (the floor is a checklist; the method is an investigation)

- **Reproduce the exact number** yourself — re-run the query/test and get the same figure.
  Report *your* number ("verified X via `<query>`"), never "the executor reports X."
- **Read the path that runs in production** — the deployed bundle / live function, not just
  the source. A "fixed" function nothing calls, or a DB change the frontend never deployed
  for, is not a fix.
- **Distrust any too-good instrument.** An impossible reading (a metric beating its ceiling, a
  should-net-zero canary strongly positive) means the instrument reads a contaminated/leaked
  source — fix or quarantine it; don't report its number.
- **Trace performance to its mechanism** (read the query plan) before accepting a "fix";
  raising a timeout is a symptom-patch.
- **Verify plumbing claims directly** — query the scheduler/catalog for the exact job/
  function/column/policy; "deployed" is not "exists."

## Three signals (all required for a UI-affecting change)

1. **It renders.** Walk the affected routes via `~~browser-qa`. No console errors; the change
   is actually visible on screen.
2. **The network is green.** The calls the page makes return success (HTTP 200), not silent
   failures or empty fallbacks.
3. **The datastore reflects it.** Query `~~database` directly — row counts, values, and schema
   match what the PRD promised.

DB-only verification is a failure mode; browser-only is too. Get all three. **Read the
actionable counter first** (the "today / pending / status" indicator) — a "today: 0" is the
report, not the big KPI above it. If `~~browser-qa` is unavailable, say so and treat the
verification as incomplete — never report ✓.

**Two checks on every verification, even when the ticket is unrelated:** (1) **freshness** —
a cheap "is the data current?" query catches a silently-frozen pipeline a feature-scoped
review would miss (flag it P0); (2) **per-partition** the integrity gate for anything locally
contaminable — a global average can pass while one partition is broken (aggregate hides
local).

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
