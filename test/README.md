# orchestrator-loop — behavioral test kit

This kit proves the plugin *changes how an agent thinks and verifies* — and now it does so as a
**runnable harness that prints one number**, not a manual checklist. It is the evidence you run
before trusting the plugin to drive real work, and before publishing it.

## The catch-rate in one command

```
python3 test/harness/run.py
```

This runs every scenario in `scenarios.json` through an agent (with the guardrails + the sample
app-profile injected), scores each transcript, and prints per-scenario PASS/FAIL plus:

```
catch-rate: N/11 (XX%)   threshold: 10
```

Exit code is 0 iff the catch-rate meets the threshold, so a Stop hook / CI can gate on it.

### What runs the agent (model-agnostic)

The runner shells out to an agent command — `OL_AGENT_CMD`, default `claude -p --output-format
text`. The command receives the full prompt on stdin and prints the agent's reply to stdout. Any
CLI honoring that contract works; the harness is not tied to one model. You need an
authenticated agent (e.g. a logged-in `claude`, or `ANTHROPIC_API_KEY` in CI).

### How scoring works

`scenarios.json` is the **single source of truth**. Each scenario carries a machine `rubric`:
groups of regex signals that must appear (the target reasoning) and fail-signals that must not
(capitulation / selling language). The judge (`test/harness/judge.py`) is deterministic and
negation-aware — "do *not* ship to 100%" is not counted as "ship it." For higher fidelity than
keywords, set `OL_JUDGE_CMD` to delegate judging to an LLM. `scenarios.md` is **generated** from
the JSON (`--emit-md`); `--check-sync` fails if it drifted.

### Useful flags

```
python3 test/harness/run.py --self-test        # judge sanity check on bundled fixtures (no model)
python3 test/harness/run.py --scenario S1      # one scenario
python3 test/harness/run.py --transcripts DIR  # score recorded transcripts DIR/<id>.txt (no model)
python3 test/harness/run.py --method FILE      # inject FILE as the rulebook (ablation control)
python3 test/harness/run.py --emit-md > test/scenarios.md   # regenerate the human view
python3 test/harness/run.py --check-sync       # enforce scenarios.md == scenarios.json
```

## The control that makes the number meaningful

A catch-rate is only worth publishing if it would *drop* when the agent gets worse. It does — see
[`harness/AT3-evidence.md`](harness/AT3-evidence.md): the same model (Haiku) scores **5/5 with
the guardrails and 0/5 without them**. Two ways to re-establish this yourself:

1. **Deterministic (no model):** `--self-test`. The bundled `bad/*` transcripts are pure
   capitulation and MUST score FAIL; the `good/*` transcripts MUST score PASS. If the judge can't
   tell them apart, it's measuring nothing.
2. **Live ablation:** run once with the full `GUARDRAILS.md` and once with `--method` pointing at
   a copy that has the skepticism/verification sections stripped, and compare.

Honest caveat, recorded in the evidence file: a **frontier** model is already skeptical, so on
Opus these one-shot scenarios are saturated and ablation barely moves them. The guardrails'
one-shot value shows up on a smaller/cheaper executor — which is exactly where you'd want a cheap
agent to behave like a careful one.

## Clean room (still the rule for manual runs)

If you score by hand instead of via the harness, do it in a fresh session in a folder that has
NOTHING but this plugin installed and `sample-app-profile.md` as the app-profile — otherwise you
can't tell whether the *plugin* produced the behavior or ambient memory did. A control is
stronger still: run the same scenario with and without the plugin; it passes if the with-plugin
answer hits the target and the without-plugin answer is visibly more credulous.

## Files

- `scenarios.json` — the SSoT: 11 scenarios, each with prompt, human pass/fail prose, and the
  machine rubric.
- `scenarios.md` — generated human view of the above (`--emit-md`).
- `harness/run.py` — the runner (live, transcripts, self-test, emit/check-sync).
- `harness/judge.py` — the deterministic, negation-aware rubric judge.
- `harness/fixtures/{good,bad}/` — transcripts the self-test scores to prove the judge discriminates.
- `harness/AT3-evidence.md` — the recorded break-the-verifier run.
- `sample-app-profile.md` — a generic B2C SaaS app-profile (the clean-room `CLAUDE.md`).
