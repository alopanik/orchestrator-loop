# Roadmap — harden the verifier moat

Source: `REQUIREMENTS.md`. The planning loop is commodity; the moat is **forensic verification
against deployed reality.** This roadmap hardens that moat, makes it measurable, and stops
competing on the commodity half. Lowest number ships first; the number IS the execution order.

| # | scope (one line) | depends-on | user-visible? | risk |
|---|---|---|---|---|
| 001 | Make the loop measurable — scenario harness prints a catch-rate; breaking the verifier drops it | — | dev-facing (new `test/harness`) | med |
| 002 | Stop loading the whole rulebook each session — small startup stub, rest on demand | 001 | yes (startup behavior) | med |
| 003 | Make the verifier independent — fresh subagent sees only diff + criteria | 001 | yes (verify-handback) | med |
| 004 | Make the hard gates fail closed — Stop hook blocks turn-end until checks pass | 001 | yes (new Stop hook) | high |
| 005 | Guard the tests — tests committed failing first; verifier rejects tampered tests | 001, 004 | yes (verify + handoff) | med |
| 006 | Don't let the verifier over-report — findings scoped to correctness + criteria | 001, 003 | yes (verify-handback) | med |
| 007 | Escape hatch for trivial changes — fast path, gate still enforced | 004 | yes (go / draft-prd) | med |
| 008 | Record what the loop catches — append-only ledger + one-line surface | 004 | yes (new ledger) | low |
| 009 | README rewrite — lead with delegation value prop + published catch-rate; refresh visuals | 001–008 | yes (README) | low |

## Later / bigger (NOT in this session — do not pull forward)
Forking risk if the verifier internals (003, 004) aren't hardened first.

- Self-improving rules: verifier catches a failure with no matching rule → auto-draft a candidate
  `Seen:` war story for human approval (never auto-commit).
- Agent Teams mode: verifier as a standing team member auditing every handback; subagent fallback.
- Standalone verifier: package `verify-handback` so an external planner can call it with just a
  diff + criteria + app-profile (the adoption play).

## Status
- [x] 001 · [x] 002 · [x] 003 · [ ] 004 · [ ] 005 · [ ] 006 · [ ] 007 · [ ] 008 · [ ] 009

001 shipped (80e60c9): one-command catch-rate; AT-3 proven (Haiku 5/5 guarded → 0/5 credulous;
Opus saturated). Evidence: test/harness/AT3-evidence.md.
002 shipped (ef3d47e): startup injection 449→48 lines (29KB→3.3KB); Haiku primer-only 5/5
(== full); guard run.py --check-startup keeps GUARDRAILS.md the SSoT.
003 shipped (7103e3b): verify-handback = fresh subagent fed only diff+criteria+facts;
run.py --check-isolation guard; isolated verifier caught a planted defect from the bundle alone.
