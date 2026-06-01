# orchestrator-loop — Requirements

## Context

The planning loop (refine → decompose → PRD → handoff) is now commodity — Superpowers, Deep
Trilogy, and others ship it. The one differentiated thing this plugin has is **forensic
verification against deployed reality** (per-partition, lying-instrument, verified-deploy
checks, war-story-backed rules). The goal of this work is to harden that moat, make it
measurable, and stop competing on the commodity half.

Build these in order. Each is independent enough to ship on its own.

## Requirements (priority order)

1. **Make the loop measurable.** Turn `test/scenarios.md` (the 11 scenarios) into a runnable
   harness that scores whether the loop catches each planted defect and prints a single
   catch-rate number. *Done when:* one command outputs the catch-rate + per-scenario pass/fail,
   and deliberately breaking the verifier makes the number drop (if it doesn't, the harness is
   measuring nothing). Everything below is validated against this.

2. **Stop loading the whole rulebook every session.** The SessionStart hook currently cats all
   of `GUARDRAILS.md` (~449 lines) into every session, which dilutes adherence. Inject a small
   always-true stub on start; move the conditional rules and war stories into the skills that
   need them, loaded on demand. *Done when:* startup injection is a fraction of today's size and
   the catch-rate from #1 does not drop.

3. **Make the verifier independent.** `verify-handback` should run as a fresh subagent that sees
   only the diff and the acceptance criteria — never the planning or build reasoning that
   produced the change. *Done when:* the verifier provably has no build-context access and the
   catch-rate holds or improves.

4. **Make the hard gates fail closed.** Today the gates are advisory markdown; a turn can end on
   a self-asserted "done". Convert the scriptable verify checks into a Stop hook that blocks the
   turn from ending until they pass. *Done when:* a planted failing check prevents turn-end, and
   a missing/erroring check counts as a failure, not a pass.

5. **Guard the tests.** Require acceptance tests committed (and failing) before implementation,
   and have the verifier confirm the tests weren't edited to go green. *Done when:* a handback
   where tests were altered to pass is rejected.

6. **Don't let the verifier over-report.** Scope its findings to correctness and the stated
   acceptance criteria, not style or speculative completeness — an over-eager adversary drives
   over-engineering. *Done when:* sound work returns zero blocking findings while genuinely
   broken work still gets blocked (checked against #1).

7. **Add an escape hatch for trivial changes.** A one-line, reversible, single-file change
   shouldn't go through the full ceremony — but it must still hit the verify gate. *Done when:* a
   trivial change takes the fast path with the gate intact, and a migration/schema change can't.

8. **Record what the loop catches.** Append every gate decision (what was checked, pass/block,
   the evidence) to a simple ledger, with a one-line summary surface. *Done when:* every block
   from #1 shows up in the ledger with its evidence.

## Later / bigger (only after 1–8 are solid)

- **Self-improving rules:** when the verifier catches a failure with no matching rule, auto-draft
  a candidate `Seen:` war story for human approval (never auto-commit it).
- **Agent Teams mode:** run the verifier as a standing team member auditing every handback, with
  subagent fallback when Agent Teams isn't available.
- **Standalone verifier:** package `verify-handback` so an external planner can call it with just
  a diff + criteria + app-profile, no orchestrator-loop planning required. (This is the adoption
  play — pull it earlier if adoption matters more than your own use.)
- **README:** lead with the verifier moat and the published catch-rate, not the rule count.

## Notes for the agent

- Gather the actual proof from the repo before building each item — measure the current token
  injection, reproduce a slipped "done", etc. Don't take the descriptions above as established
  facts; confirm them.
- Don't pull the three "Later / bigger" items forward — they can fork the architecture if the
  verifier internals (#3, #4) aren't hardened first.
