<div align="center">

<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/hero.svg" alt="orchestrator-loop — set one goal, get a verified result, stop babysitting" width="100%">

<p>
  <img src="https://img.shields.io/badge/version-0.6.0-2f81f7?style=flat-square" alt="version 0.6.0">
  <img src="https://img.shields.io/badge/license-MIT-3fb950?style=flat-square" alt="MIT license">
  <img src="https://img.shields.io/badge/Claude%20Code%20%C2%B7%20Cowork-d97757?style=flat-square" alt="Claude Code and Cowork">
  <img src="https://img.shields.io/badge/tests-40%2F40-3fb950?style=flat-square" alt="40 of 40 tests passing">
  <img src="https://img.shields.io/badge/plugin%20validate-passing-3fb950?style=flat-square" alt="claude plugin validate passing">
</p>

<p>
  <a href="#why-it-exists">Why</a> &nbsp;•&nbsp;
  <a href="#the-team-in-one-command">The team</a> &nbsp;•&nbsp;
  <a href="#how-it-works">How it works</a> &nbsp;•&nbsp;
  <a href="#the-proof">The proof</a> &nbsp;•&nbsp;
  <a href="#quick-start">Quick start</a> &nbsp;•&nbsp;
  <a href="#execution-modes">Modes</a> &nbsp;•&nbsp;
  <a href="#architecture">Architecture</a>
</p>

</div>

**orchestrator-loop turns Claude into a disciplined engineering team you delegate to.** You set one
goal. It refines the goal into testable requirements, decomposes it into numbered PRDs, builds each
one, and then **verifies its own work like an adversary** — looping across as many PRDs as the goal
needs and stopping only when the work is *proven* done. You review evidence, not diffs.

```text
$ /orchestrator-loop:go   "ship per-org rate limiting, verified against the live DB"

◆ refine     one-line ask → testable definition of done   (3 questions, then autonomous)
◆ roadmap    PRD-001 schema · PRD-002 middleware · PRD-003 dashboard
◇ PRD-001    draft → architect-review ✓ → build → verify ✓        committed
◇ PRD-002    draft → architect-review ✓ → build → verify ✗
             reproduced: limiter off-by-one on burst → fixed → verify ✓   committed
◇ PRD-003    draft → architect-review ✓ → build → verify ✓        renders · network 200 · rows match
■ 3/3 PRDs verified against the live system · every gate decision logged to the ledger
  paused at the one boundary that's yours — the production deploy. Recommendation attached.
```

<div align="center"><sub>One goal in. A chain of independently verified PRDs out. No “want me to continue?”.</sub></div>

<br/>

## Why it exists

AI coding agents are a revelation — but you only save real time by **delegating**, not by
micromanaging. The bottleneck stopped being *writing* code; it's *trusting* it. Most agent loops
hand you a confident "done" you still have to babysit, re-run, and second-guess.

orchestrator-loop removes the babysitting by making the agent **prove** its work:

- **One goal, not a hundred prompts.** State the outcome; the loop refines it, plans it, and drives
  it to completion across multiple PRDs without check-ins.
- **A verifier that's an adversary, not a cheerleader.** Every "done" is a claim, re-established
  against reality — the deployed path, the real numbers, per-partition — by a fresh agent that
  never saw the build reasoning.
- **Gates that fail closed.** A turn *cannot* end on a self-asserted "done." Tests can't be edited
  green. The orchestrator can't quietly write the code it's supposed to review.
- **Evidence, not vibes.** Every gate decision and its proof is logged; you read the ledger, not
  the diff.

The planning half of this is now commodity. The **verifier is the moat** — it's what makes
autonomous delegation trustworthy enough to walk away from.

<br/>

## The team in one command

A real change normally moves through five people. orchestrator-loop runs all five — and *enforces*
each hand-off so none can be skipped or faked:

| Role on a team | The hand-off it removes | Skill | Enforced by | Lives in |
|---|---|---|---|---|
| **Product / PM** — turns a vague ask into testable requirements | the spec round-trip | `/go` refinement | requirements must be testable before any code | `skills/go` |
| **Architect** — catches layering & forks before code | the design review meeting | `/architect-review` | five structural questions answered *in* the PRD | `skills/architect-review` |
| **Engineer** — writes the code | "who's free to build this?" | `/handoff-to-executor` | one PRD in flight; executor wired to the *right* project (preflight) | `skills/handoff-to-executor` · `hooks/enforce_executor.py` |
| **QA** — tries to break it | the back-and-forth on "is it really done?" | `/verify-handback` | a context-isolated adversary reproduces the numbers | `skills/verify-handback` · `test/harness/check_isolation.py` |
| **Release gatekeeper** — won't let unproven work ship | the merge argument | the fail-closed Stop gate | the turn can't end while checks are red; every decision logged | `hooks/stop_gate.py` |

**What that's worth:** the coordination between those five roles collapses into one goal you hand
off. You stop supervising each diff and start reviewing *evidence* — Anthropic now writes
[≈100% of its own code with Claude, with "scaffolds to let the team trust it"](https://www.itpro.com/software/development/anthropic-labs-chief-mike-krieger-claims-claude-is-essentially-writing-itself-and-it-validates-a-bold-prediction-by-ceo-dario-amodei).
orchestrator-loop *is* that trust scaffold.

<br/>

## How it works

<div align="center">

<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/loop.svg" alt="The loop: one goal → go → roadmap → draft-prd → architect-review → handoff → verify → verified done, with reject paths looping back to draft-prd" width="62%">

</div>

The loop is `rules → roadmap → PRD → handoff → verify`, driven from one goal by `/go`. Six
enforcement mechanisms are what make it more than a checklist:

| Mechanism | What it guarantees | File |
|---|---|---|
| **Fail-closed gate** | A `Stop` hook refuses to end the turn while the PRD's scriptable checks are red. Missing or erroring counts as failure — never a silent pass. | `hooks/stop_gate.py` |
| **Independent verifier** | `verify-handback` runs as a fresh subagent fed *only* the diff + acceptance criteria + app facts; a guard rejects any bundle that leaks the build story. | `test/harness/check_isolation.py` |
| **Test tamper-guard** | Acceptance tests are committed **failing first**; a handback that edited its own tests to go green is rejected. | `test/harness/check_tests.py` |
| **Connector preflight** | Before dispatch, each tool is verified to point at the project your `CLAUDE.md` names — a wrong Supabase/Vercel fails closed. | `test/harness/preflight.py` |
| **Scoped findings** | The verifier blocks only on correctness / real regressions / sanity / freshness / security. Style and non-goals are notes — it can't over-engineer. | `GUARDRAILS.md` |
| **Decision ledger** | Every gate decision (pass/block + the evidence) is appended, with a one-line summary surface. | `hooks/stop_gate.py` → `.orchestrator/ledger.jsonl` |

<br/>

## The proof

This isn't a manifesto — it's a test you can run. The kit is 12 clean-room scenarios, each a
planted defect mapped to a guardrail and a real incident.

```bash
# Model-free — proves the harness itself is sound (runs anywhere, no agent needed):
python3 test/harness/run.py --self-test        # the judge discriminates 14/14 good/bad fixtures
python3 test/harness/run.py --check-startup     # the always-on primer stays in budget, canon intact

# Live — the catch-rate, run through your own authenticated agent:
python3 test/harness/run.py                     # 12 scenarios → per-scenario PASS/FAIL + catch-rate
```

Three things hold up under independent re-testing (see [`test/harness/AT3-evidence.md`](test/harness/AT3-evidence.md)):

- **The harness measures something.** A deliberately credulous transcript scores **0**; a skeptical
  one scores full. The judge is not a rubber stamp — 14/14, deterministic.
- **The guardrails cause the catch.** Same small model, same scenarios: **5/5 with the guardrails,
  0/5 without.** Strip the rulebook and the score collapses.
- **It turns a cheap executor into a careful one.** Frontier models already reason this way; the
  guardrails make a smaller, faster, autonomous executor do the same — and you can re-run the proof
  yourself any time.

<div align="center">

<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/gates.svg" alt="Seven fail-closed gates per cycle: refinement, roadmap dependency, draft-PRD proof, architect-review, handoff scope, verify-handback, session completion" width="58%">

</div>

**What it refuses to ship** — each a real incident class, each a scenario in the kit:

| The claim it distrusts | What the loop does instead |
|---|---|
| "+23 pts retention in a one-week A/B — ship to 100%." | Refuses; reproduces the number; finds the assignment leak. *(S1)* |
| "Dashboard's green, error is below the chance floor." | Flags it *structurally impossible* — the monitor reads a leaked table. Quarantine it. *(S2)* |
| "Canary is −3 corpus-wide, healthy." | Re-runs **per partition** — one day's slice sits at +57. *(S3)* |
| "0 references in source, dropped the column, done." | Reads the **deployed** bundle — the live frontend still queries it. *(S6 / S9)* |

<br/>

## Aligned with Anthropic's Claude Code guidance

orchestrator-loop is a deliberate, *enforced* implementation of the patterns Anthropic itself
publishes — it turns "best practice" into "can't skip it":

| Anthropic guidance | How orchestrator-loop enforces it |
|---|---|
| Separate planning from implementation; stop the agent writing code too early | Plan → build → verify are distinct phases; in power mode a hook **blocks** the orchestrator from editing files |
| `CLAUDE.md` as short, explicit production prompts | The app-profile is the single source of facts; the session primer is **50 lines**, full rules on demand |
| Use subagents in isolated context for specialized work | `verify-handback` is a fresh subagent fed only the diff + criteria |
| Writer/Reviewer with **fresh context** so review isn't biased | Two-brain mode + the isolated verifier — the reviewer never sees the build story |
| "Show evidence rather than asserting success" | Reproduce the number yourself; every decision + evidence in the ledger |
| Treat it like a junior engineer you watch, redirect, or step away from | The autonomy contract + a **live-streamed** executor + a fail-closed gate at the key points |

<sub>Sources: <a href="https://code.claude.com/docs/en/best-practices">Claude Code best practices</a> · <a href="https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf">How Anthropic teams use Claude Code</a> · <a href="https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents">Effective context engineering for agents</a>. Cat Wu (Head of Product, Claude Code) and Mike Krieger frame Anthropic's direction as a <b>harness strategy</b> — Chat / Cowork / Code as modes over one capable model. This plugin is an opinionated harness for the engineering loop.</sub>

<br/>

## Quick start

**Cowork** — Settings → Plugins → Add plugin → GitHub → `alopanik/orchestrator-loop`. Then:

```text
/orchestrator-loop:setup     once — wires your repo, services, and executor, writes CLAUDE.md
/orchestrator-loop:go        every session — state one goal, it drives the loop to verified done
```

**Claude Code**

```bash
claude plugin marketplace add alopanik/orchestrator-loop
claude plugin install orchestrator-loop
```

The repo *is* the marketplace (`.claude-plugin/marketplace.json` at root). Fork it for your own
variant — different guardrails, extra skills, a stack-specific profile. See [`PUBLISHING.md`](PUBLISHING.md).

<br/>

## Execution modes

| Mode | Plans & QAs | Writes code | Best for |
|---|---|---|---|
| **Two-brain** &nbsp;`recommended` | Cowork orchestrator | **Claude Code CLI** | Serious, multi-PRD, autonomous runs |
| Cowork-solo | Cowork agent | itself (switches hats) | Zero-setup quick start |
| Code-solo | Claude Code | itself (switches hats) | Terminal-native; strongest enforcement (hooks fire reliably) |

The **two-brain** setup is the recommended default: a Cowork orchestrator that plans and
adversarially verifies, with a separate Claude Code CLI doing the typing. The wins are **leverage**
(a cheaper, parallel executor types while the orchestrator stays in skeptic-mind), **enforcement**
(the fail-closed gate and always-on guardrails fire natively in Claude Code), and
**tamper-resistance** (an independent verifier working from the PRD's original criteria resists
softened or self-edited tests). Both solo modes are first-class — and even solo, the verifier's
isolated subagent keeps most of the independence.

<br/>

## Architecture

The framework knows *method*; your repo supplies *facts*. They meet in one file — `CLAUDE.md`,
scaffolded from [`app-profile.template.md`](app-profile.template.md): connector mappings (each
`~~category` → a concrete tool), infra + deploy mechanics, **domain rules and sanity bounds** (the
values that are structurally impossible, so the verifier can call them out), and pointers to your
roadmap + constitution. Where the two ever conflict, the app-profile wins on facts; the framework
wins on method.

```
orchestrator-loop/
├── GUARDRAILS.md            # the full method — 14 sections · 53 rules · 22 war stories (SSoT)
├── STARTUP.md               # the 50-line always-on primer injected each session
├── ARCHITECTURE.md          # the constitution — every canonical component, one home each
├── CLAUDE.md                # this repo's own app-profile (the plugin dogfoods itself)
├── hooks/
│   ├── hooks.json           # SessionStart → STARTUP.md · Stop → fail-closed gate · PreToolUse → executor guard
│   ├── stop_gate.py         # the fail-closed gate + the decision ledger
│   └── enforce_executor.py  # in power mode, the orchestrator can't write code
├── skills/                  # 7 skills — setup · go · roadmap · draft-prd · architect-review · handoff · verify
├── prds/                    # PRD-NNN-*.md — the specs the loop produces
├── test/
│   ├── scenarios.json       # 12 scenarios — the SSoT for the catch-rate
│   └── harness/             # run.py · judge.py · check_isolation · check_tests · classify_change · preflight · dispatch
│       └── AT3-evidence.md  # the recorded, reproducible proof
└── .claude-plugin/          # plugin.json + marketplace.json (version is the SSoT pair)
```

Every component above is registered in [`ARCHITECTURE.md`](ARCHITECTURE.md) with its one purpose
and one home — *if it isn't in the constitution, it doesn't exist*, and `architect-review` enforces
"extend it, don't fork it" against that file.

<br/>

<div align="center">

**plan with rigor · build with leverage · verify like an adversary · ship the truth**

<sub>MIT © Andrew Lopanik · 7 skills · 53 rules · 22 war stories · 12 scenarios · a catch-rate you can run yourself</sub>

</div>
