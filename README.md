<div align="center">

<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/loop.svg" alt="orchestrator-loop: one goal in, verified result out. Six skills run top to bottom, with reject paths looping back from architect-review and verify." width="100%">

</div>

<br/>

# orchestrator-loop

**Set one goal. Get a verified result. Stop babysitting.**

AI coding agents are a revelation — but you only save real time by *delegating*, not by
micromanaging. orchestrator-loop turns Claude into a disciplined engineering lead: you state a
single session goal; it refines that goal with you into fully-covered requirements, decomposes
it into numbered PRDs, builds each one, and then **verifies its own work like an adversary** —
looping across as many PRDs as the goal needs, without stopping to ask *"want me to continue?"*

App-agnostic by design: the framework knows *how to work*; you supply *what your app is* through
a one-time `CLAUDE.md` app-profile.

<br/>

## The moat: forensic verification, not process theater

The planning half of this loop (refine → decompose → spec → hand off) is now commodity — lots of
tools ship it. The differentiated, asymmetric part is the **verifier**: the thing that makes
autonomous delegation *trustable* enough to walk away from.

Most handoff loops check *process* — PR format, test coverage, "the code looks right."
orchestrator-loop checks *reality*: it reproduces the exact number itself, reads the **deployed**
path (not `git grep`), gates **per partition** so a break in one cohort can't hide under a global
average, and treats every "done" as a claim to be re-established from scratch. The verifier runs
as a **fresh, context-isolated subagent** that sees only the diff + the acceptance criteria — never
the builder's "here's why it works" — so it can't inherit the builder's blind spots.

<br/>

## Proof: a catch-rate you can run

The behavioral test kit is the plugin's regression signal — 12 clean-room scenarios, each a
planted defect mapped to a guardrail and a real incident. One command scores it:

```bash
python3 test/harness/run.py          # prints per-scenario PASS/FAIL + a catch-rate, exits nonzero below threshold
```

What's actually verified (see [`test/harness/AT3-evidence.md`](test/harness/AT3-evidence.md) — we
publish only numbers that survive our own forensic check):

- **The judge is sound, deterministically.** `run.py --self-test` proves it distinguishes
  skeptical from credulous reasoning on **14/14** fixtures; a deliberately credulous transcript
  scores **0**. The harness is not a rubber stamp.
- **The guardrails *cause* the catch.** Same small model (Haiku), same scenarios: **5/5 with the
  guardrails, 0/5 without** ("Ship it — get it to 100% today" → "this is a data bug until proven").
  Break the rulebook and the number drops — the test measures something real.
- **Honest nuance (it's model-dependent).** A frontier model (Opus) is *already* skeptical, so it
  saturates these one-shot scenarios with or without the rules; a small model is where the
  guardrails visibly transform behavior — and is itself variable run-to-run. So the headline isn't
  a single shiny number — it's that **the loop makes a cheap, autonomous executor reason like a
  careful senior engineer, and you can re-run the proof yourself.**

> We caught our own README's first draft (auto-written by an unsupervised sub-agent) publishing a
> catch-rate it had never measured. The orchestrator re-scored from scratch, the number didn't
> reproduce, and the claim was rejected. That's the discipline, applied to itself.

<br/>

## What it refuses to ship

> **Too-good results.** Executor reports +23 pts 7-day retention from a one-week A/B. The loop
> refuses, reproduces the number, hunts the assignment leak. — scenario S1

> **Lying instruments.** A dashboard reports a model error below the random-chance floor. The
> reading is *structurally impossible*; the monitor reads a leaked, in-sample table. Quarantine
> it. — S2 · *Distrust the instrument*

> **Aggregate hiding local.** A corpus-wide canary at −3 looks healthy while one day's slice sits
> at +57. Gate per partition, not the average. — S3 · *Aggregate hides local*

> **Unverified migrations.** "0 references in source, dropped, done." The loop reads the *deployed*
> bundle — a column dropped while the old frontend is live turns every page-load into a 4xx. — S6/S9

<br/>

## The enforced loop

`rules → roadmap → PRD → handoff → verify`, driven from one goal by the `go` skill. What makes it
more than a checklist:

- **Fail-closed gate.** A Claude Code `Stop` hook refuses to end the turn while the PRD's
  scriptable checks are red (missing or erroring counts as failure). A turn can't end on a
  self-asserted "done."
- **Independent verifier.** `verify-handback` runs as a fresh subagent fed only the diff +
  acceptance criteria + app-profile facts; a guard rejects any bundle that leaks the build story.
- **Guarded tests.** Acceptance tests are committed *failing* first; the verifier rejects a
  handback that edited its own tests to go green.
- **Scoped findings.** The verifier blocks only on stated criteria / real regressions / sanity /
  freshness / security — style and non-goals are non-blocking notes, so it can't over-engineer.
- **Trivial fast path.** A one-line, reversible, single-file change skips the ceremony but still
  hits the gate; a migration never qualifies.
- **Decision ledger.** Every gate decision (pass/block + evidence) is appended to
  `.orchestrator/ledger.jsonl`; `stop_gate.py ledger` is the one-line summary surface.

<br/>

## The seven skills

| Skill (slash command) | What it does |
|---|---|
| **`/setup`** | One-time onboarding. Detects what's wired, auto-configures what it can, walks you through the gaps one step at a time, writes `CLAUDE.md`, confirms the guardrails load. |
| **`/go`** | The session driver. Orients, **refines your goal into testable requirements**, then loops `roadmap → draft-prd → architect-review → handoff → verify` across as many PRDs as the goal needs. |
| `/roadmap` | Broad goal → numbered PRDs, planned against the live system. |
| `/draft-prd` | One PRD to disk: proof (numbers, not adjectives), root cause, un-gameable acceptance tests. |
| `/architect-review` | Five structural questions answered *inside* the PRD. Layering/forking caught here, not in code review. |
| `/handoff-to-executor` | Self-contained brief; one PRD in flight; arms the fail-closed gate; explicit commit policy. |
| `/verify-handback` | Independent, context-isolated forensic re-test of the executor's claim. |

Each skill is a lean `SKILL.md` plus a deeper `references/methodology.md`. The full method, the
*why* behind every rule, and the war stories live in [`GUARDRAILS.md`](GUARDRAILS.md); a 50-line
always-on [`STARTUP.md`](STARTUP.md) primer is injected each session and the skills load the rest
on demand.

<br/>

## Execution modes — recommended: two brains

| Mode | Who plans/QAs | Who writes code | When |
|---|---|---|---|
| **Two-brain (recommended)** | Cowork orchestrator | **Claude Code CLI** executor | Serious, multi-PRD, autonomous runs |
| Cowork-solo | Cowork agent | itself (switches hats) | Quick start, non-technical, zero setup |
| Code-solo | Claude Code | itself (switches hats) | Terminal-native; strongest *enforcement* (hooks fire reliably) |

We recommend the **two-brain** setup — a Cowork orchestrator that plans and adversarially verifies,
with a separate Claude Code CLI doing the typing. Being honest about *why*, because we measured it:
on a frontier model the separate-verifier's one-shot catch-rate lift is roughly **neutral** (the
model is already skeptical). The real wins are **leverage** (a cheaper/parallel executor types
while the orchestrator stays in skeptic-mind), **enforcement** (the fail-closed gate and always-on
guardrails actually fire in Claude Code), and **tamper-resistance at scale** (an independent
verifier working from the PRD's *original* criteria resists softened or self-edited tests). Both
solo modes are fully supported; even solo, `verify-handback`'s isolated subagent recovers most of
the independence.

<br/>

## The app-profile

The framework knows method; your repo knows facts. They meet in one file — `CLAUDE.md`, scaffolded
from [`app-profile.template.md`](app-profile.template.md): connector mappings (each `~~category` →
a concrete tool, see [`CONNECTORS.md`](CONNECTORS.md)), infra + deploy mechanics, **domain rules
and sanity bounds** (the values that are structurally impossible, so the verifier can call them
out), and pointers to your roadmap + constitution. Where the two ever conflict, the app-profile
wins on *facts*, the framework wins on *method*.

<br/>

## Install

**Cowork.** Settings → Plugins → Add plugin → GitHub → `alopanik/orchestrator-loop`. Activates
next session. Run `/setup` once.

**Claude Code.**

```bash
claude plugin marketplace add alopanik/orchestrator-loop
claude plugin install orchestrator-loop
```

The repo *is* the marketplace (`.claude-plugin/marketplace.json` at root). Fork it for your own
variant. See [`PUBLISHING.md`](PUBLISHING.md).

<br/>

## Repo map

```
orchestrator-loop/
├── GUARDRAILS.md            # full method · 14 sections · 53 rules · 22 war stories (the SSoT)
├── STARTUP.md               # 50-line always-on primer injected at session start
├── ARCHITECTURE.md          # the constitution — every canonical component, one home each
├── CLAUDE.md                # this repo's own app-profile (the plugin dogfoods itself)
├── ROADMAP.md · CONNECTORS.md · PUBLISHING.md · app-profile.template.md
├── .claude-plugin/          # plugin.json + marketplace.json (version SSoT)
├── hooks/
│   ├── hooks.json           # SessionStart → STARTUP.md · Stop → fail-closed gate
│   └── stop_gate.py         # turn-end gate + decision ledger
├── prds/                    # PRD-NNN-*.md — the specs the loop produces
├── skills/                  # 7 skills, each SKILL.md + references/
└── test/
    ├── scenarios.json       # 12 scenarios — SSoT for the catch-rate
    ├── scenarios.md         # generated human view
    └── harness/             # run.py · judge.py · check_isolation/check_tests/classify_change
        ├── test_*.py        # unit tests for the gates
        ├── fixtures/        # good/bad transcripts (judge self-test)
        └── AT3-evidence.md  # the recorded catch-rate evidence
```

<br/>

---

<div align="center">

<sub><b>plan with rigor · build with leverage · verify like an adversary · ship the truth</b></sub>

<br/>

<sub>MIT · 7 skills · 53 rules · 22 war stories · 12 scenarios · fail-closed gate · run the catch-rate yourself</sub>

</div>
