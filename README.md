<div align="center">

<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/loop.svg" alt="orchestrator-loop: one goal in, verified result out. The diagram shows six skills running top to bottom, with two reject paths looping back from architect-review and verify to draft-prd." width="100%">

</div>

<br/>

# orchestrator-loop

A Claude plugin (Cowork & Code) that turns Claude into a disciplined engineering lead.
You state ONE session goal. The plugin orients on the repo, decomposes the goal into
numbered PRDs, drafts each in a house format, reviews it structurally **before any code
is written**, packages a self-contained brief for a coding executor, then **independently
re-verifies** the result against reality before accepting it — and loops to the next PRD
without prompting. App-agnostic by design: the framework knows *how to work*; you supply
*what your app is* through a one-time `CLAUDE.md` app-profile.

<br/>

## What it actually does

**Goal refinement.** `go` probes for fully-covered requirements before any work starts.
A one-line ask (*"add the dashboard"*) gets pulled apart into a testable definition of
done so the loop builds the right thing, not the first thing. Garbage in, garbage out — the
refine gate is where the cycle is saved.

**Decomposition.** `roadmap` translates a broad goal into a sequenced, numbered set of
PRD-sized units of work, planned against the *live* system (queries the database, reads
the repo, runs the thing) rather than from imagination. Lower numbers ship first.

**Architectural foresight, pre-code.** `architect-review` answers five structural
questions on the PRD *before* it's handed off: what's being **removed**, what the **single
source of truth** is, whether this is **layering or editing**, what **migration debt**
gets cleaned up *in* this PRD, and how it changes the **constitution**. A bad answer is
a redesign, not a warning. Catching layering on a PRD is an order of magnitude cheaper
than catching it on a diff.

**Context-isolated handoff.** `handoff-to-executor` packages the PRD into a brief the
executor can build from alone — a short prompt pointing at the PRD file path and the
branch name, or, if the executor can't read your docs, the full PRD body inlined. One
PRD in flight at a time. The executor never inherits whatever happened to be in the
orchestrator's context.

**Adversarial verification.** `verify-handback` treats the executor's "done" as a claim,
not a fact. It reproduces the exact numbers itself, reads the **deployed** path (not just
`git grep`), gates per partition (a global average hides a local break), and checks
freshness on every handback even when the ticket is unrelated. Three signals required for
any UI-affecting change: it renders, the network is green, the datastore reflects it.

**Autonomous multi-PRD loops.** You set ONE goal. The framework drives N PRDs through to
**verified** completion across the seam between them — re-orienting, re-planning, and
re-verifying without asking *"want me to continue?"* The three valid stop conditions:
goal met **and** independently verified; a genuine blocker (irreversible action, missing
credential, a real fork); or you stop it.

<br/>

## The seven skills

| Skill (slash command) | What it does |
|---|---|
| **`/orchestrator-loop:setup`** | One-time onboarding. Detects what's already wired in the repo, auto-configures what it can, walks the user one step at a time through the gaps, writes `CLAUDE.md` from the app-profile template, confirms the guardrails hook is loaded. |
| **`/orchestrator-loop:go`** | The session driver. Orients on app-profile + roadmap + live state, refines the user's goal, then loops `roadmap → draft-prd → architect-review → handoff → verify` across as many PRDs as the goal needs. |
| `/orchestrator-loop:roadmap` | Broad goal → numbered PRDs. Plans against the live system, not assumptions. |
| `/orchestrator-loop:draft-prd` | Writes one PRD to disk as `PRD-NNN-short-kebab.md`. House format: proof (numbers, not adjectives), root cause, un-gameable acceptance tests. |
| `/orchestrator-loop:architect-review` | Five structural questions answered inside the PRD. Layering and forking caught here, not in code review. |
| `/orchestrator-loop:handoff-to-executor` | Self-contained brief; one PRD in flight; explicit commit policy every time. |
| `/orchestrator-loop:verify-handback` | Independent forensic re-test of the executor's claim. 5 forensic checks + 3 signals + per-partition + freshness. |

Each skill has a lean `SKILL.md` plus a deeper `references/methodology.md` next to it.

<br/>

## Seven gates

<div align="center">

<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/gates.svg" alt="Seven gates per cycle: refinement, roadmap dependency, draft-PRD proof, architect-review, handoff scope, verify-handback, session completion. You set one goal; the loop enforces seven checkpoints before 'done.'" width="100%">

</div>

<br/>

### Engineered, not improvised

> **7** explicit gates per cycle
>
> **50** operating rules across 14 sections of `GUARDRAILS.md`
>
> **20** real-incident `Seen:` war stories the rules were paid for in
>
> **8** forensic checks before "done" is accepted

Auditable from the repo: `grep -c "^- \*\*" GUARDRAILS.md` ·
`grep -c "Seen:" GUARDRAILS.md` · `ls skills/`.

<br/>

## What it refuses to ship

> **Skepticism.** Executor reports +23 pts 7-day retention from a one-week A/B. Loop
> refuses, reproduces the number, finds the assignment leak. — `test/scenarios.md` S1

> **Lying instrument.** Dashboard reports a model-vs-benchmark error below the
> random-chance floor. The reading is structurally impossible; the monitor reads a
> leaked, in-sample table. Quarantine it. — `GUARDRAILS.md` → *Distrust the instrument*

> **Aggregate hides local.** Corpus-wide canary at −5 (healthy) passed while a single
> day's slice sat at +57. Gate per partition. — `GUARDRAILS.md` → *Aggregate hides local*

> **Verified deploy.** "0 references in source, dropped, done." Loop reads the deployed
> bundle. A column dropped while the old frontend was still deployed turns every
> page-load into a 4xx. — `GUARDRAILS.md` → *No destructive migration without a
> verified-deploy check*

<br/>

## The app-profile

The framework knows method; your repo knows facts. The two meet in a single file —
`CLAUDE.md`, scaffolded from [`app-profile.template.md`](app-profile.template.md). It
declares:

- **Connector mappings.** Each `~~category` placeholder used by the skills (`~~executor`,
  `~~vcs`, `~~ci`, `~~database`, `~~hosting`, `~~dns`, `~~browser-qa`,
  `~~project-tracker`) gets bound once to a concrete tool. See
  [`CONNECTORS.md`](CONNECTORS.md).
- **Infrastructure and deploy mechanics** — what a push triggers, where secrets live.
- **Domain rules and sanity bounds** — the things an agent must not get wrong, and the
  values that are structurally impossible (so the verifier can call them out).
- **Roadmap pointer + constitution** — where the PRD files live, where the SSoT
  declaration lives.

Where the app-profile and `GUARDRAILS.md` ever seem to conflict, the app-profile wins
on *facts*; the framework wins on *method*.

### Executor mapping

The framework supports two execution modes, selected by the `~~executor` mapping:

- **Zero-setup** — the orchestrator agent (Cowork) writes the code itself, switching
  hats between planning and building.
- **Power** — a separate coding agent (typically Claude Code via Desktop Commander)
  receives the handoff and writes the code; the orchestrator never edits files itself.

The discipline is identical either way. When the orchestrator is also the executor,
*"never trust the executor's done"* becomes *"never trust your own done"* — the
verifier role still runs adversarially against the planner role's claim.

<br/>

## How you use it

**First time in a repo.** Run `/orchestrator-loop:setup`. It detects existing
structure, fills what it can, asks you one question at a time for the gaps, and writes
`CLAUDE.md`. After this, the SessionStart hook cats `GUARDRAILS.md` into context every
session — the rules are *always* in effect, not opt-in.

**Day to day.** Every session is `/orchestrator-loop:go` with a one-line goal. The
framework probes, plans, drafts, reviews, dispatches, verifies, and re-enters the loop
for the next PRD. You answer clarifying questions during refinement; otherwise it
drives itself until the goal is verifiably met.

**Direct invocations** when you don't want the full loop:

- `/orchestrator-loop:draft-prd` — write a single PRD against an existing roadmap entry.
- `/orchestrator-loop:architect-review` — review an already-drafted PRD before handoff.
- `/orchestrator-loop:verify-handback` — re-verify an already-shipped change against
  reality (useful when a result feels too clean).

<br/>

## Install

**Cowork.** Settings → Plugins → Add plugin → GitHub → `alopanik/orchestrator-loop`.
Activates next session. Run `/orchestrator-loop:setup` once.

**Claude Code.**

```bash
claude plugin marketplace add alopanik/orchestrator-loop
claude plugin install orchestrator-loop
```

The repo *is* the marketplace (`.claude-plugin/marketplace.json` at the root). If you
want your own variant — different guardrails, additional skills, a stack-specific
profile — fork the repo and install from your fork. See [`PUBLISHING.md`](PUBLISHING.md).

<br/>

## Repo map

```
orchestrator-loop/
├── GUARDRAILS.md           # 449 lines · 14 sections · 50 rules · 20 war stories
├── CONNECTORS.md           # 8 categories · ~~category placeholders
├── PUBLISHING.md           # repo IS the marketplace
├── app-profile.template.md # the CLAUDE.md you fill in once
├── .claude-plugin/         # plugin.json + marketplace.json
├── hooks/                  # 1 SessionStart hook → cats GUARDRAILS.md
├── skills/                 # 7 skills, each with SKILL.md + references/
└── test/                   # 11-scenario clean-room behavioral kit
```

<br/>

---

<div align="center">

<sub><b>plan with rigor · build with leverage · verify like an adversary · ship the truth</b></sub>

<br/>

<sub>MIT · 7 skills · 50 rules · 20 war stories · 7 gates · 8 connector categories</sub>

</div>
