> **Operating under orchestrator-loop — the plugin's `GUARDRAILS.md` is always in effect; read
> it first.** (This blockquote MUST be the very first content in the file — above the title —
> because it is what keeps the guardrails on in Cowork, where SessionStart hooks don't reliably
> fire. Do not put a heading or anything else above it.)

# App profile — <YOUR APP NAME>

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
~~ci              = <e.g. GitHub Actions — workflow that runs the migration lint + tests>
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

## Sanity bounds / impossible values
<The framework's core skepticism rule — "a surprising good result is a data bug until proven"
— needs YOUR numbers to know what "surprising" means. Declare them here so the orchestrator
can recognize a too-good-to-be-true result on sight:
- The theoretical ceiling / plausible range for each key metric (e.g. "sustainable <metric>
  is X–Y; above Y on N≥… is corruption first, signal second").
- The "this should be ≈0 (or slightly negative)" canaries and the band they must stay in,
  checked PER partition not just in aggregate.
- Any value that is structurally impossible (a probability outside [0,1], an error score
  below the random-chance floor, a both-sides payoff that nets positive).
If you don't have these yet, the `draft-prd` and `verify-handback` skills will help you
derive them from first principles.>

## Constitution / source of truth
<Pointer to the doc that declares your canonical tables/modules/surfaces. The framework
enforces "extend it, don't fork it" against this. If you don't have one, the `roadmap` +
`draft-prd` skills will help you create one.>

## Roadmap
<Pointer to your roadmap doc (produced by the `roadmap` skill). Numbered; lowest ships first.>

## Where PRDs live
<The directory PRDs are written to, e.g. `docs/prd/` or `_cowork_docs/`.>
