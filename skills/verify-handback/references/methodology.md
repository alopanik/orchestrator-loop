# Verify the handback — methodology + worked example

The `SKILL.md` gives the spine. This is the forensic method. Verification is role 2 (QA) and
it is the role most often done shallowly. The executor's "done" is a *claim*. Your job is to
re-establish every claim yourself, against reality — as an adversary, not a co-author hoping
it worked.

A three-bullet "renders + 200 + DB" checklist is the *floor*, not the method. The method is
an investigation: reproduce the exact number, read the path that runs in production, trace
the data to its source, and disbelieve any instrument that tells you a story that's too good.

## The mindset

**You are trying to break the claim, not confirm it.** If you go in wanting it to pass, you
will find reasons it passed. Go in assuming a specific failure mode and try to trigger it.
The verification that matters is the one that *could have* returned ❌.

And: **a surprising good result is a data bug until proven otherwise.** If the handback
reports a number that's better than expected, that is not a moment to relax — it's the moment
to dig hardest. Reproduce it, trace it, and find the contamination before you report it as a
win.

## The forensic ladder — climb all of it for any non-trivial claim

### 1. Reproduce the exact number yourself

Don't accept "the metric improved to 0.92." Re-run the query/test and get **0.92 yourself**.
If you get a different number, the claim is already false. If you can't reproduce it at all,
it isn't true yet. Quote *your* number in the report, not the executor's: "verified 0.92 via
`<query>`," never "executor reports 0.92."

### 2. Read the code path that actually runs

Confirm the change is on the live path, not an adjacent function, a dead branch, or a
helper that nothing calls. Trace the data from where it enters to where it's displayed. A
"fixed" function that production doesn't call is not a fix.

*Real failure this catches:* a handback claimed "0 references to the dropped column in the
source." Trusted, it shipped. The *deployed bundle* still queried the column — the DB drop
succeeded, the frontend was never deployed, and every request 400'd the moment the page
opened. Reading the deployed path (not just the source grep) is what catches this.

### 3. Distrust the instrument

If a monitor/dashboard/test reports an *impossible* value — an error score below the random-
chance floor, an accuracy that beats the theoretical ceiling, a should-net-zero metric that's
strongly positive — the instrument is reading a contaminated or leaked source. Do not report
its number. Find why the instrument lies, then fix or quarantine it.

*Real failure this catches:* a model-vs-benchmark monitor showed the model winning with an
impossible error score; it was reading an in-sample (leaked) table and would have green-lit
shipping a model that actually loses to the benchmark.

### 4. Trace performance to its mechanism

If something is slow or timing out, read the **query plan / profile** before accepting any
"fix." Raising a timeout is a symptom-patch that hides the mechanism.

*Real failure this catches:* a nightly job had failed for days on a timeout. The real cause
was a deep-offset scan over a large table plus stale planner statistics — fixed with an index
and fresh stats, not a bigger timeout. A verification that just confirmed "it ran this time"
would have shipped a job that fails again next week.

### 5. Gate per partition, not just in aggregate

A global average can be healthy while one partition is broken — aggregate hides local. For
anything locally contaminable, re-run the integrity check **per partition** (per day/group,
min N).

*Real failure this catches:* a corpus-wide canary at ≈ −5 (healthy) passed while one day's
slice sat at +57 — a real re-contamination diluted into invisibility by the clean majority.
The per-slice check is what turns it red.

### 6. The three signals (all required for a UI-affecting change)

1. **It renders.** Walk the affected routes via `~~browser-qa`. No console errors; real
   content, not a skeleton, not "ERROR." **Read the actionable counter first** — the headline
   "today / pending / status" indicator. A "today: 0" *is* the report, not the big KPI above
   it.
2. **The network is green.** The calls the page makes return success (2xx), not silent empty
   fallbacks or 4xx/5xx on the changed surfaces.
3. **The datastore reflects it.** Query `~~database` directly — counts, values, schema match
   what the PRD promised.

DB-only verification is a failure mode; browser-only is too. If `~~browser-qa` is
unavailable, say so explicitly and treat the verification as **incomplete** — never report ✓.

*Real failure this catches:* a cache was verified to hold the right rows via SQL and called
done — but the page's hook to read it was broken and the tab rendered blank. DB was right;
the UI was not. Only the browser walk catches that.

### 7. Verify the plumbing claims directly

For every "deployed / shipped / wired / created / live" claim, verify the artifact exists:

- **Scheduled jobs:** query the scheduler's job list for the exact name — empty means it
  doesn't exist, whatever the handback says.
- **Functions / columns / policies / constraints:** query the catalog directly; confirm
  signatures and types, not just names.
- **Deployed code:** confirm it's in the repo *and* actually deployed (the running bundle /
  the live function URL), not just committed.
- **UI controls:** click the button and observe the state change — DOM presence is
  meaningless if the trigger panel is stuck loading.

*Real failure this catches:* two jobs marked "deployed" in a handback did not exist in the
scheduler at all; models had silently been frozen for days. The catalog query is what
surfaces it.

### 8. Always check freshness — even when the ticket is unrelated

Run the cheap "is the data current?" query on **every** verification (e.g. `MAX` of the
freshness column). A silently-frozen pipeline is a P0 that a feature-scoped review sails
right past. This has caught multi-day stale-pipeline regressions discovered only because the
freshness check is unconditional.

## Comprehensive, not feature-local

Walk **every** user journey the change could touch, click-by-click — not just the one
feature. Check downstream effects: jobs/crons, server functions, derived
views/materializations — did they update too? Re-run each acceptance test from the PRD
against reality and report **❌ for every miss with quoted evidence** (the query, the
response, the screenshot).

## Mission level

Step back: does the app still serve its mission after this change, or did it drift? A change
that passes its own tests but moves the product away from its purpose fails review.

## Terminate in strategy — not a problem inventory

This is where verification most often fails the owner even when the *checking* was perfect.
End with:

- **A verdict:** accept / fix-list / redesign.
- **The ONE load-bearing blocker**, named — not eight problems presented as equals.
- **The concrete next action** toward the actual goal, which you then take.

Do not end with a list of findings and "which should I pursue?" — that reads as circles even
when every finding is correct. And never use "ready to ship / want to go live?" framing to
close out: report what's true and let the owner decide. If the gate isn't fully green, you
don't offer the go-live action at all. A failure becomes a PRD (or an addendum), not a chat
instruction.

## Worked example — verifying the score-integrity handback (PRD-141)

The executor reports: "Done. Calibration 0.04, canary −3, one write-path, pushed."

A forensic verification:

1. **Reproduce:** re-run the calibration and canary SQL myself → I get 0.05 and −3.2. Close
   to claimed; ✓ on reproduction.
2. **Per partition (the one that matters):** run AT-2b — the canary per day for 30 days.
   **Day 14 = +49 on n=210.** ❌. The global canary (−3.2) hid it. The backfill path
   re-introduced the bug on one day's data — the same bug, a different door.
3. **Read the path:** confirm `score_writer_batch` is the sole writer (catalog: trigger
   gone ✓) — but the *backfill* script still prices from the wrong source. Root cause not
   fully removed.
4. **Three signals on the UI:** rankings render ✓, network 2xx ✓, but the "items scored
   today" counter reads 0 — the recompute didn't run for today. ❌.
5. **Freshness:** `MAX(scored_at)` is two days stale. ❌ — unrelated-looking but P0.

**Verdict:** reject. **The one blocker:** the backfill path re-contaminates (day 14) — fix
it to use the finalized-input source and null-when-unverifiable, same as the forward path,
then re-run AT-2b for every backfilled day. **Next action:** I'm writing PRD-141-addendum for
the backfill path + the stale recompute; the calibration fix itself is sound and stays.

Note what made it real: the per-partition gate caught what the aggregate hid; reading the
deployed path found the un-fixed sibling; the freshness check surfaced an unrelated P0; and it
ends with one blocker + the next action, not a five-item list.
