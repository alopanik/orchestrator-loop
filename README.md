<div align="center">

<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/loop.svg" alt="orchestrator-loop: one goal in, verified result out. The diagram shows six skills running top to bottom, with two reject paths looping back from architect-review and verify to draft-prd." width="100%">

</div>

<br/>

# orchestrator-loop

A coding agent that reports **"done"** on broken work is the most expensive failure mode
in autonomous engineering — the failure is *invisible* until the next user hits it.
`orchestrator-loop` is a Claude plugin (Cowork & Code) that **refuses to accept the
executor's own "done."** Every change runs through seven explicit gates and is verified
against reality before the result is allowed to ship.

<br/>

## The loop

Read top to bottom. ONE goal enters. Six skills run in sequence — `go`, `roadmap`,
`draft-prd`, `architect-review`, `handoff`, `verify`. Two checkpoints can reject and
loop back to `draft-prd`: the architect review (before a line of code is written) and
the forensic verification (after). Nothing exits as **verified done** until both gates
go green.

<br/>

## What it refuses to ship

> **Skepticism.** The executor reports +23 pts 7-day retention from a one-week A/B test.
> The loop refuses, reproduces the number, and finds the assignment leak.
> — `test/scenarios.md` S1

> **Lying instrument.** A dashboard reports a model-vs-benchmark error score below the
> random-chance floor. The reading is structurally impossible; the monitor is reading a
> leaked, in-sample table. Quarantine it.
> — `GUARDRAILS.md` → *Distrust the instrument*

> **Aggregate hides local.** A corpus-wide canary at −5 (healthy) sailed through a gate
> while one day's slice sat at +57. The average diluted a real re-contamination into
> invisibility. Gate per partition.
> — `GUARDRAILS.md` → *Aggregate hides local*

> **Verified deploy.** "0 references in source, dropped, done." The loop reads the
> deployed bundle, not just `git grep`. A column dropped while the old frontend was still
> deployed turns every page-load into a 4xx.
> — `GUARDRAILS.md` → *No destructive migration without a verified-deploy check*

> **Same bug, different door.** A pricing bug fixed in the forward pipeline came back
> days later from the backfill pipeline, which read the wrong source and slipped past a
> gate that only checked the aggregate.
> — `GUARDRAILS.md` → *The same bug returns through a different door*

> **Silent rot.** A job failed for a week and logged only `[object Object]`; its watchdog
> died on the identical bug it was meant to catch. Make failure loud.
> — `GUARDRAILS.md` → *Silent failure is the enemy*

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

The numbers are auditable from the repo: `grep -c "^- \*\*" GUARDRAILS.md` ·
`grep -c "Seen:" GUARDRAILS.md` · `ls skills/`.

<br/>

## You vs. the loop

| You do (once per session) | The loop does (autonomously) |
|---|---|
| State **one** goal | Orient against live state |
| Answer a short refinement batch | Decompose to numbered PRDs |
| Approve only at irreversible boundaries | Draft → review → handoff → verify, PRD after PRD |
| | Re-orient between PRDs |
| | Stop only on the 3 valid boundaries |

The three valid stop conditions: the goal is met **and** independently verified; a
genuine blocker (irreversible action, missing credential, a real fork); or you stop it.
Finishing a PRD, hitting a passing test, "want me to continue?" — none of those are
stop conditions. The framework names this and forbids it.

<br/>

## Install

**Cowork.** Settings → Plugins → Add plugin → GitHub → `alopanik/orchestrator-loop`.
Run `setup` once; every session after that is `go`.

**Claude Code.**

```bash
claude plugin marketplace add alopanik/orchestrator-loop
claude plugin install orchestrator-loop
```

The repo is the marketplace. See [`PUBLISHING.md`](PUBLISHING.md).

<br/>

---

<div align="center">

<sub><b>plan with rigor · build with leverage · verify like an adversary · ship the truth</b></sub>

<br/>

<sub>MIT · 7 skills · 50 rules · 20 war stories · 7 gates</sub>

</div>
