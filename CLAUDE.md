> **Operating under orchestrator-loop — the plugin's `GUARDRAILS.md` is always in effect; read
> it first.** (This line is what keeps the guardrails on in Cowork, where SessionStart hooks
> don't reliably fire. Keep it at the very top, above the title.)

# App profile — orchestrator-loop (the plugin developing itself)

This repo *is* the orchestrator-loop plugin. When we work here, the "app" under development is
the framework itself, so the plugin dogfoods its own loop. The framework (GUARDRAILS.md + the
six stage skills) is the method; this file is the app-specific input.

## What this app is
A Claude plugin (Cowork & Code) — Markdown skills, hooks, and a behavioral test kit. There is
no runtime service, database, or UI: the "product" is the set of skills + guardrails an agent
loads, and the "build artifacts" are Markdown, JSON manifests, hook configs, and shell/Python
test tooling. Active development happens in this repo on the `master` branch.

## Connector mappings
```
~~executor        = self (Cowork orchestrator, zero-setup tier — plan/build/verify as separate phases)
~~vcs             = git (local). Remote = github.com/alopanik/orchestrator-loop.
                    A push to the remote is a RELEASE — user sign-off required, never autonomous.
~~ci              = the scenario harness (test/harness/run.py) + the Stop-hook gate
~~database        = none (no datastore)
~~hosting         = none (distributed as repo-is-marketplace; see PUBLISHING.md)
~~dns             = none
~~browser-qa      = none (no UI to walk; the "three signals" reduce to: harness runs, score reproduces, ledger reflects)
~~project-tracker = ROADMAP.md + the session task list
```

## Infrastructure
Distribution is repo-as-marketplace (`.claude-plugin/marketplace.json` at root). Installers add
the GitHub repo; a version bump in BOTH `.claude-plugin/plugin.json` and `marketplace.json` plus
a push to the remote is what ships a new version to installers. Version is the SSoT pair in those
two manifests and must always match.

## Domain rules (the things an agent must NOT get wrong)
- `GUARDRAILS.md` is the single source of truth for the operating method. The startup stub and
  the skills REFERENCE it; they never copy rule text (copying forks the truth).
- The framework stays **app-agnostic**: never hardcode a specific product/tool in GUARDRAILS.md
  or the skills — refer to connectors by `~~category` only. App-specific facts live here.
- PRDs are pointers (files in `prds/`), never an inline body in chat.
- `version` in `plugin.json` and `marketplace.json` must be identical, every change.
- The behavioral test kit is the plugin's only real regression signal — a change to guardrails
  or skills is not "done" until the catch-rate is re-run.

## Sanity bounds / impossible values
- **The durable regression signal is the deterministic self-test + the ablation delta — NOT a
  single absolute catch-rate number.** `run.py --self-test` must stay green (the judge discriminates
  the good/bad fixtures; bad ones FAIL); and guarded must beat credulous on the core scenarios.
  Absolute live catch-rate is **model-dependent**: a frontier model saturates (~12/12 with or
  without the rules), a small model is variable (~6–10/12 run-to-run). A self-test regression, or a
  collapsed guarded-vs-credulous delta, after a guardrails/skill change IS a regression.
- **A *rising* catch-rate after we SHRINK the guardrails (PRD-002) is "too good" until proven** —
  first hypothesis is the judge got more lenient or is keyword-matching the scenario prompt
  itself, not the agent's reasoning. Reproduce with the ablation control before believing it.
- **A perfect board from the rubric judge is suspect**: confirm the judge actually fails a
  deliberately-broken agent (the ablation must drop the score) before trusting it.
- Startup-injection budget (PRD-002): the SessionStart stub stays **≤ 60 lines / ≤ 4 KB**.
  Achieved: `STARTUP.md` is **50 lines / 3.3 KB** (was 449 / 29 KB); `run.py --check-startup`
  enforces the budget + that `GUARDRAILS.md` remains the intact canonical source.

## Constitution / source of truth
`ARCHITECTURE.md` — lists every canonical component (its one purpose, one home, who reads it).
The framework enforces "extend it, don't fork it" against that file.

## Roadmap
`ROADMAP.md` — numbered; lowest ships first.

## Where PRDs live
`prds/` as `PRD-NNN-short-kebab-title.md`.
