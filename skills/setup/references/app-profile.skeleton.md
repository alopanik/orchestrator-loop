# App profile — <YOUR APP NAME>

> **Operating under orchestrator-loop — the plugin's `GUARDRAILS.md` is always in effect; read
> it first.** (Keep this line at the very top — it is what keeps the guardrails on in Cowork,
> where SessionStart hooks don't always fire.)

This file is YOUR app's input to the orchestrator-loop framework. The framework (guardrails +
the rules→roadmap→PRD→handoff→verify loop) lives in the plugin and is frozen. Everything below
is yours to fill in. Keep this as the repo's `CLAUDE.md` (or whatever file the orchestrator reads
first each session). Be concrete.

## What this app is
<2–4 sentences: the product(s), the stack, where active development happens.>

## Connector mappings
Map each category to the concrete tool you use (drop the ones you don't):
```
~~executor        = <Tier 1: this Cowork agent (writes code directly) | Tier 2: a coding CLI via a shell MCP>
~~vcs             = <e.g. GitHub — org/repo>
~~ci              = <e.g. GitHub Actions — runs build, tests, migration lint>
~~database        = <e.g. Postgres / Supabase — project ref>
~~hosting         = <e.g. a PaaS — what triggers deploys>
~~dns             = <e.g. Cloudflare — or none>
~~browser-qa      = <e.g. Claude-in-Chrome / Playwright>
~~project-tracker = <e.g. Linear — or none>
```

## Infrastructure
<Vendors, project refs, dashboards, the deploy mechanism, what a push triggers, secrets location.>

## Domain rules (the things an agent must NOT get wrong)
<Your invariants: config knobs + allowed values, business rules, conventions, and the "things
that look fine but aren't". The app-specific equivalent of the framework's guardrails.>

## Sanity bounds / impossible values
<The numbers that tell the orchestrator a result is "too good to be true" for THIS app: the
plausible range/ceiling for each key metric; the should-be-≈0 canaries and their allowed band
(checked per partition, not just in aggregate); any structurally impossible value (a probability
outside [0,1], an error score below the chance floor, a both-sides payoff that nets positive).>

## Constitution / source of truth
<Pointer to the doc that declares your canonical tables/modules/surfaces + invariants (one
concept→one store, one write-path per store, no fork views). The framework enforces "extend it,
don't fork it" against this. If you don't have one, the roadmap + draft-prd skills help create it.>

## Roadmap
<Pointer to your roadmap doc (produced by the `roadmap` skill). Numbered; lowest ships first.>

## Where PRDs live
<The directory PRDs are written to, e.g. `docs/prd/`.>
