# App profile — <YOUR APP NAME>

> **Operating under orchestrator-loop — the plugin's `GUARDRAILS.md` is always in effect; read
> it first.** (This line is what keeps the guardrails on in Cowork, where SessionStart hooks
> don't reliably fire. Keep it at the very top.)

This file is YOUR app's input to the orchestrator-loop framework. The framework (the
guardrails + the rules→roadmap→PRD→handoff→verify loop) lives in the plugin and is frozen.
Everything below is yours to fill in. Keep this as your repo's `CLAUDE.md` (or whatever file
your orchestrator reads first each session).

> The orchestrator reads this profile and your roadmap BEFORE acting. Be concrete.

## What this app is
<2–4 sentences: the product(s), the stack, where active development happens.>

## Connector mappings
Map each category from the plugin's `CONNECTORS.md` to the concrete tool you use:

```
~~executor        = <e.g. Claude Code (headless, via Desktop Commander)>
~~vcs             = <e.g. GitHub — org/repo>
~~database        = <e.g. Supabase — project ref>
~~hosting         = <e.g. Vercel — team/project; what triggers deploys>
~~dns             = <e.g. Cloudflare — or none>
~~browser-qa      = <e.g. Claude-in-Chrome>
~~project-tracker = <e.g. Linear — or none>
```

## Infrastructure
<Vendors, project refs, dashboards, the deploy mechanism, what a push triggers, secrets location.>

## Domain rules (the things an agent must NOT get wrong)
<Your invariants: config knobs and their allowed values, business rules, conventions, and the
"things that look fine but aren't". This is the app-specific equivalent of the framework's
guardrails — but it is YOURS, and the framework never assumes it.>

## Constitution / source of truth
<Pointer to the doc that declares your canonical tables/modules/surfaces. The framework
enforces "extend it, don't fork it" against this. If you don't have one, the `roadmap` +
`draft-prd` skills will help you create one.>

## Roadmap
<Pointer to your roadmap doc (produced by the `roadmap` skill). Numbered; lowest ships first.>

## Where PRDs live
<The directory PRDs are written to, e.g. `docs/prd/` or `_cowork_docs/`.>
