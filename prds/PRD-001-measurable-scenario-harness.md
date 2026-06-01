# PRD-001 — Make the loop measurable (scenario harness + catch-rate)

**User-visible-surface impact:** Dev-facing. New `test/harness/` + a machine-readable
`test/scenarios.json`; `test/scenarios.md` becomes a generated view. One command prints a
catch-rate. No change to the shipped skills/guardrails behavior.

## 1. Problem (with proof)

The behavioral test kit is **documentation, not a test.** `test/` contains only prose:

```
$ ls test/
README.md  sample-app-profile.md  scenarios.md
```

`scenarios.md` instructs a human to paste 11 prompts into clean-room sessions and hand-tally a
scorecard of checkboxes:

```
| S1 | too-good result | skepticism | ☐ |
...
**Result: ___ / 11.**
```

Consequences, each load-bearing for everything below in the roadmap:
- **No single number.** "Catch-rate" is a manual, subjective tally — not reproducible, not
  CI-able.
- **No regression signal.** Nothing detects whether a change to `GUARDRAILS.md` or a skill made
  the agent *more credulous*. REQUIREMENTS.md says every item below "is validated against this"
  — there is currently nothing to validate against.
- **Unfalsifiable.** There is no way to show the plugin measures anything, because deliberately
  breaking the verifier produces no observable drop.

## 2. Root cause

The kit was authored as human-run documentation: the scenarios, their pass/fail criteria, and
the scorecard live as prose in `scenarios.md`, with no machine-readable scenario data and no
scorer. "Catch-rate" therefore can't be computed, only estimated by a person.

## 3. Scope

Smallest change that makes the catch-rate a reproducible number, while keeping the 11 scenarios'
substance identical:

- **`test/scenarios.json`** — the SSoT. One object per scenario: `id`, `title`, `guardrail`,
  `incident`, `prompt` (the clean-room prompt verbatim), `pass_desc`, `fail_desc`, and a
  machine `rubric` (`pass_all`: groups of regex where each group needs ≥1 match; `fail_any`:
  regex that force a fail). A global `fail_any` (selling language) applies to every scenario.
- **`test/harness/run.py`** (Python 3, stdlib only) — loads the SSoT, for each scenario builds
  the agent input (method file + `sample-app-profile.md` + the prompt), invokes a **pluggable
  agent command** (`OL_AGENT_CMD`, default `claude -p`), captures the transcript, scores it via
  the judge, prints per-scenario PASS/FAIL + `catch-rate: N/M (XX%)`, exits nonzero below
  threshold. Flags: `--method PATH` (which method file to inject — enables ablation),
  `--scenario ID`, `--transcripts DIR` (score recorded transcripts; no model needed),
  `--self-test` (judge fixtures), `--emit-md`, `--check-sync`, `--json`.
- **`test/harness/judge.py`** — the rubric scorer (deterministic, no network). Optional
  `OL_JUDGE_CMD` swaps in an LLM judge for fidelity.
- **`test/harness/fixtures/`** — a `good`/`bad` transcript per a few scenarios, for `--self-test`.
- **`test/scenarios.md`** — regenerated from the JSON via `--emit-md` (now a view, not a source).
- **`test/README.md`** — document `run.py` (run, ablation, self-test).

## 4. Non-goals

- Not changing the scenarios' substance (port the existing prose verbatim into JSON).
- Not hardcoding a model — the runner is agent-agnostic; the rubric judge is model-free.
- Not building CI config (the fail-closed gate is PRD-004).
- Not slimming the guardrails (PRD-002).

## 5. Acceptance tests (un-gameable)

- **AT-1 (judge discriminates):** `run.py --self-test` passes every `good` fixture and fails
  every `bad` fixture, exit 0. A judge that can't tell a credulous transcript from a skeptical
  one measures nothing.
- **AT-2 (SSoT enforced):** `run.py --check-sync` — `scenarios.md` equals `--emit-md` output.
  Editing the prose without the JSON fails this.
- **AT-3 (break-the-verifier — load-bearing):** catch-rate with full `GUARDRAILS.md` (`C_full`)
  vs. with an ablated method file that has the skepticism + verification sections removed
  (`C_ablated`): **`C_ablated` < `C_full`** by a clear margin. Measured with a real agent. If
  breaking the rules does not drop the number, the harness is measuring nothing — this AT is the
  whole point of the PRD.
- **AT-4 (one command, one number):** a single invocation prints each scenario PASS/FAIL and
  `catch-rate: N/M (XX%)`, and returns nonzero when below a `--threshold`.
- **AT-5 (coverage):** JSON has exactly 11 scenarios; each has a non-empty `prompt` and `rubric`;
  count equals the scorecard rows.

> Sandbox note: `claude -p` is not logged in *in this dev sandbox*, so the live AT-3 is run via
> real Claude subagents (the orchestrator's available agent transport) with full vs. ablated
> method text; the shipped default remains `claude -p` for the user's authenticated env/CI. The
> judge ATs (AT-1/2/4/5) are model-free and run anywhere.

## 6. Architect review

1. **Removal.** Deletes the hand-maintained checkbox scorecard and the manual tally;
   `scenarios.md` stops being a source and becomes generated output.
2. **SSoT.** `scenarios.json` is the single source for scenario data; `scenarios.md` is emitted
   from it (one writer: `--emit-md`); the rubric lives *with* each scenario.
3. **Layering.** Edits the test kit in place under `test/` — no parallel kit. The `.md` is a
   view, not a fork.
4. **Migration debt.** Regenerates `scenarios.md` from JSON within this PRD and adds
   `--check-sync` to prevent future drift; nothing deferred.
5. **Constitution diff.** Extends the "Test kit" rows already declared in `ARCHITECTURE.md`
   (scenarios.json SSoT, scenarios.md as view, `test/harness/` home). No fork.

## 7. Execution

Commit to `master` locally as `PRD-001` once AT-1, AT-2, AT-4, AT-5 pass and AT-3 shows a live
drop. No push (release boundary). Stdlib only; no new dependencies.
