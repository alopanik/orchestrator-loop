# AT-3 evidence — the catch-rate responds to agent quality

PRD-001's load-bearing acceptance test: *deliberately breaking the verifier must drop the
number; if it doesn't, the harness is measuring nothing.* This file records the run that proved
it, so the published catch-rate is auditable rather than asserted.

Run date: 2026-06-01. Agent transport: Claude subagents (the dev sandbox's `claude -p` is not
logged in; the shipped default is `claude -p`). Scoring: the bundled rubric judge
(`test/harness/judge.py`), the same one that ships. Scenarios: the 5 core epistemic scenarios
(S1 too-good result, S2 lying instrument, S3 per-partition, S4 root cause, S6 forensic verify).

## Headline

| condition | model | rulebook | catch-rate (core 5) |
|---|---|---|---|
| guarded | Haiku | full `GUARDRAILS.md` | **5 / 5** |
| **broken** (credulous, ship-fast persona) | Haiku | **none** | **0 / 5** |
| guarded | Opus | full `GUARDRAILS.md` | 5 / 5 |
| ablated (skepticism/verification/rigor sections removed) | Opus | partial | 4 / 5 |

**The drop is real and large on a model that needs the rules: Haiku goes 5/5 → 0/5 when the
guardrails are removed and the agent is told to move fast.** That is the proof the harness
measures something.

## The honest nuance (why we report Haiku, not Opus, as the proof)

A frontier model is **already skeptical** — Opus scored 5/5 *with* the full rulebook, 4/5 with
the skepticism/verification sections ablated, and (separately tested) still refused to ship even
when explicitly role-played as a reckless "ship-fast" engineer. On Opus these one-shot scenarios
are **saturated**: removing the guardrail text barely moves the answer, because the model
supplies the skepticism itself.

So the guardrails' measurable, one-shot value shows up where it matters in practice — on a
smaller/cheaper executor. Under the rulebook, Haiku reasons like a careful senior engineer
("this is a data bug until proven," "gate per partition," "a code search is not a runtime
proof"); without it, the same model says "Ship it — get it to 100% today," "−3 is noise, good to
go," "zero refs, we're good." The plugin makes a cheap executor behave like a frontier one on
engineering judgment, and the harness quantifies that.

(The structural half of the moat — fail-closed gates, the independent verifier, the decision
ledger — is what a base model does *not* do by default and what later PRDs add; the scenario
catch-rate only measures the one-shot epistemics.)

## Representative quotes

Haiku, **with** guardrails:
- S1: "No. Stop. A 23-point lift … is implausibly large … This is a data bug until proven …
  reproduce the exact number … audit the experiment assignment for an assignment leak."
- S6: "'0 references left in the source' is a code search, not a runtime proof … read the
  deployed schema … I verify against reality, not against what the code claims."

Haiku, **credulous / no guardrails**:
- S1: "Ship it. A 23-point lift … is huge … Get it to 100% today."
- S3: "Ship it. −3 is noise … good to go."
- S6: "Ship it. If the executor ran the scan and there are zero refs, we're good — no point
  second-guessing."

## Reproduce

```
# guarded (the user's authenticated env):
python3 test/harness/run.py                      # uses claude -p by default

# break it (ablation control kept gitignored as a .junk file):
python3 test/harness/run.py --method <stripped-rulebook>

# deterministic proof the judge is not a rubber stamp (no model needed):
python3 test/harness/run.py --self-test          # bad transcripts MUST score FAIL
```

---

## PRD-002 addendum — the slim primer preserves behavior

PRD-002 shrank the SessionStart injection from `GUARDRAILS.md` (449 lines / 29 KB) to
`STARTUP.md` (48 lines / 3.3 KB — 11% of the size). Acceptance required the catch-rate not to
drop. Same model (Haiku), same 5 core scenarios:

| injected rulebook | size | catch-rate (core 5) |
|---|---|---|
| full `GUARDRAILS.md` | 29 KB | 5 / 5 |
| **slim `STARTUP.md` primer only** | **3.3 KB** | **5 / 5** |
| none (credulous) | 0 | 0 / 5 |

The primer alone reproduces the guarded behavior ("implausibly large … data bug … in-sample
leakage … won't put it live"; "symptom patch … EXPLAIN ANALYZE"; "trust vs verification … halt
the handback"). No regression — `run.py --check-startup` enforces the size budget and that
`GUARDRAILS.md` remains the intact canonical source.
