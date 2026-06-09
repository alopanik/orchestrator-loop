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
| Executor enforcement | Block orchestrator file-writes in power mode | `hooks/enforce_executor.py` + `.orchestrator/mode.json` *(PRD-011)* | Claude Code `PreToolUse` hook |
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
| Tests guard | Tests-first baseline + tamper/green check | `test/harness/check_tests.py` + `.orchestrator/tests.json` *(PRD-005)* | `baseline` writes; the gate runs `verify` |
| Change classifier | Decide trivial-fast-path eligibility (gate still applies) | `test/harness/classify_change.py` *(PRD-007)* | `go` / `draft-prd` |
| Connector preflight | Verify executor is wired to the declared project; fail closed | `test/harness/preflight.py` + `.orchestrator/connectors.json` *(PRD-010)* | `handoff-to-executor` / the gate |
| Executor dispatch | Launch executor live-streamed + logged; stamp OL_ROLE; bound runtime (`--timeout`) + record a structured outcome | `test/harness/dispatch.py` + `.orchestrator/executor.{log,status,outcome.json}` *(PRD-012; timeout + outcome PRD-017)* | `handoff-to-executor` |
| Executor audit | Cowork-side fail-closed detection: in power mode, block a handback whose tree changed with no recorded dispatch | `test/harness/audit_executor.py` *(PRD-013)* | `verify-handback` / the gate |
| Executor outcome gate | Fail closed unless the last dispatch finished clean (`ok`); a stale `running` with a dead pid is a crash, not "done" | `test/harness/check_executor.py` *(PRD-017)* | `verify-handback` / the gate |
| Decision ledger | Append-only record of gate decisions | `.orchestrator/ledger.jsonl` *(PRD-008)* | many atomic appenders — `stop_gate.py` (turn-end) + `ci_gate.py` (CI/pre-push), across operators; each a single O_APPEND write *(PRD-016/018)* |

**Invariant:** one scenarios SSoT (`scenarios.json`); the `.md` is a view of it, never a second
source. The ledger is one append-only log with **many atomic appenders** (PRD-018 retired the old
"one writer" rule): each writer does a single O_APPEND write (kernel-atomic for a line ≤ PIPE_BUF),
and `check_ledger.py` is the torn-line canary.

## Shared state (collaborator-safe)

Per-PRD status as its own file (no single contended document); the ROADMAP status is a generated
view. This is the substrate the claim protocol (019) and provenance (020) build on.

| Component | One purpose | Home | Writers / readers |
|---|---|---|---|
| Per-PRD state | One file per PRD = its status; atomic writes (temp + `os.replace`) | `.orchestrator/prds/<PRD-ID>.json` *(PRD-018)* | `prd_state.py` writes; `roadmap_status.py` + the claim protocol read |
| Per-PRD state CLI | set / get / list a PRD's status | `test/harness/prd_state.py` *(PRD-018)* | `go` / `handoff` / `verify` |
| ROADMAP status view | Generate the status block from state files; `--check` guards drift | `test/harness/roadmap_status.py` *(PRD-018)* | a standing CI check |
| Ledger canary | Fail on any torn / unparseable ledger line | `test/harness/check_ledger.py` *(PRD-018)* | a standing CI check |

**Invariant:** per-PRD status SSoT = one file per PRD (one owner-at-a-time); the ROADMAP status is
a generated *view*, never hand-edited. Different PRDs never contend; same-PRD writes are atomic.

## Scaffolding (bootstrap-cicd)

The gate, relocated so it runs where the turn-end hook can't: on a remote and at pre-push. The
checks live once as data; the workflow and hook are thin callers.

| Component | One purpose | Home | Writers / readers |
|---|---|---|---|
| CI engine | Run the standing checks (fail-closed, ledgered) on a clean runner | `hooks/ci_gate.py` *(PRD-016)* | invoked by the generated workflow + pre-push hook; reads `ci-gate.json` |
| Standing checks (SSoT) | The repo's always-on gate checks, as data | `.orchestrator/ci-gate.json` *(PRD-016)* | written by hand / `scaffold.py`; read by `ci_gate.py` |
| Ratchet baseline | A metric floor set only if the ablation control discriminates | `.orchestrator/ci-baseline.json` *(PRD-016)* | `scaffold.py ratchet-baseline` writes; `ci_gate.py` enforces |
| CI scaffolder | Emit the workflow + pre-push hook + managed `CLAUDE.md` block, parameterized by `~~ci`/`~~vcs` | `skills/bootstrap-cicd/scaffold.py` *(PRD-016)* | the `bootstrap-cicd` skill |
| Version check | Assert `version` identical across both manifests | `test/harness/check_version.py` *(PRD-016)* | a standing check in `ci-gate.json` |

**Invariant:** the checks live once, as data, in `.orchestrator/ci-gate.json`; the workflow and
the pre-push hook are thin callers of `ci_gate.py` and never re-list checks. The engine is
standalone (no plugin imports) so it can be vendored into any repo and run on a clean CI runner.

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
