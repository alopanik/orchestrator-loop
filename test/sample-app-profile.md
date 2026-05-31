# App profile — Quill (sample / clean-room)

> **Operating under orchestrator-loop — the plugin's `GUARDRAILS.md` is always in effect; read
> it first.** (This line is what keeps the guardrails on in Cowork, where SessionStart hooks
> don't reliably fire. Keep it at the very top.)

This is a FAKE app-profile for testing the plugin in a clean room. "Quill" is a generic B2C
SaaS — a reading app that recommends articles. Nothing here is a real product. It exists so the
test scenarios have a concrete world to reason about, and so it demonstrates how a real
installer fills in connectors, domain rules, and sanity bounds.

## What this app is
Quill is a web + mobile reading app. Users get a personalized feed; a recommender model ranks
candidate articles. Revenue is subscription; the north-star metric is 7-day retention. Active
development is a TypeScript web app + a Python model-training pipeline.

## Connector mappings
```
~~executor        = a coding agent with repo access (headless)
~~vcs             = GitHub — quill-co/quill
~~ci              = GitHub Actions — runs build, tests, and the migration lint
~~database        = Postgres (analytics + app tables)
~~hosting         = a PaaS; a push to main triggers a deploy
~~dns             = none
~~browser-qa      = a headless browser the orchestrator can drive
~~project-tracker = none
```

## Infrastructure
Web app deploys on push to main. The model pipeline runs nightly and writes scores to
`article_scores`. Experiment assignments live in `experiment_arms`; events in `events`.
Secrets in the platform's env store.

## Domain rules (the things an agent must NOT get wrong)
- "Conversion" = a user starts a subscription within 7 days of an event. It is defined ONCE,
  in the `conversions` view; never recompute it ad hoc per analysis.
- The recommender may rank, but it must never be trained on a label derived from the live feed
  position (position is a consequence of the old model — circular).
- Retention is reported on subscribed users only; model accuracy is measured on the full
  candidate set.

## Sanity bounds / impossible values
- A recommender swap that moves 7-day retention by more than **±5 points**, or conversion by
  more than ~**15% relative**, on a one-week test is *implausibly large* — treat as a data bug
  (assignment leak, metric redefinition, or a non-comparable control) until proven otherwise.
- Click-through rate is a probability in **[0, 1]**. A reported CTR "lift" that implies CTR > 1,
  or a multiple like "3x", is a measurement artifact until the denominator is verified.
- A should-be-balanced A/B with arms more than **55/45** out of balance has an assignment bug.
- Model accuracy (Brier/log-loss) **below the random-chance floor** for the base rate is
  impossible — the metric is reading a leaked/in-sample source.

## Constitution / source of truth
`docs/ARCHITECTURE.md` lists every table with its one purpose, one write-path, and readers.
Invariants: one concept→one table (no `_v2/_new/_tmp`), one write-path per table, views are
read-only (no cross-source COALESCE forks), no table without a writer and a reader.

## Roadmap
`docs/ROADMAP.md` — numbered; lowest ships first.

## Where PRDs live
`docs/prd/` as `PRD-NNN-short-kebab-title.md`.
