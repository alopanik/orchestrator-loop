# Constitution — orchestrator-loop

Every canonical component, its one purpose, its one home, and who reads it. **If it isn't in
this file, it doesn't exist.** Architect-review enforces "extend it, don't fork it" against this
list — no `_v2 / _new / _copy` siblings of anything below.

## Method (the framework)

| Component | One purpose | Home | Readers |
|---|---|---|---|
| Operating method (full) | The complete rules + war stories | `GUARDRAILS.md` | every session (by reference), every skill |
| Startup stub | The always-true core injected at session start | `STARTUP.md` *(PRD-002)* | SessionStart hook |
| Hooks | Session lifecycle wiring | `hooks/hooks.json` | Claude Code runtime |
| Stop gate | Fail-closed turn-end enforcement | `hooks/stop_gate.py` + `.orchestrator/gate.json` *(PRD-004)* | Claude Code `Stop` hook; loop writes the manifest |
| Stage skills | One skill per loop stage | `skills/<stage>/SKILL.md` (+ `references/`) | the orchestrator |

**Invariant:** rule text lives once, in `GUARDRAILS.md`. `STARTUP.md` and skills point at it;
they never duplicate it. Connectors are referenced by `~~category` only — no product names in
the framework.

## Test kit (the regression signal)

| Component | One purpose | Home | Writers / readers |
|---|---|---|---|
| Scenario data (SSoT) | The scenarios + machine-scorable rubric | `test/scenarios.json` *(PRD-001)* | written by hand; read by the harness |
| Scenario narrative | Human-readable companion of the above | `test/scenarios.md` | derived from / kept in sync with the JSON |
| Harness | Run scenarios → score → catch-rate | `test/harness/` *(PRD-001)* | one entry point: `run.py` |
| Verifier-isolation guard | Assert a verifier bundle leaks no build context | `test/harness/check_isolation.py` *(PRD-003)* | `run.py --check-isolation` |
| Decision ledger | Append-only record of gate decisions | `test/ledger.jsonl` *(PRD-008)* | one writer: the gate script |

**Invariant:** one scenarios SSoT (`scenarios.json`); the `.md` is a view of it, never a second
source. One writer to the ledger.

## Distribution

| Component | One purpose | Home |
|---|---|---|
| Plugin manifest | Plugin identity + version | `.claude-plugin/plugin.json` |
| Marketplace manifest | Distribution + version | `.claude-plugin/marketplace.json` |
| Publishing guide | How a release ships | `PUBLISHING.md` |

**Invariant:** `version` is identical in both manifests, always.

## Docs

| Component | One purpose | Home |
|---|---|---|
| App-profile (this repo) | The plugin-as-app profile | `CLAUDE.md` |
| App-profile template | The `CLAUDE.md` an installer fills in | `app-profile.template.md` |
| Connector catalog | The `~~category` list | `CONNECTORS.md` |
| Roadmap | Numbered PRD sequence | `ROADMAP.md` |
| Public README | Value prop + catch-rate + how to use | `README.md` |
