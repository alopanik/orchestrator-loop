<div align="center">

<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/hero.svg" alt="orchestrator-loop — set one goal; Claude plans, hands off the code, and verifies against reality" width="100%">

<br/><br/>

![version](https://img.shields.io/badge/version-0.5.0-1f6feb?style=flat-square&labelColor=0d1117)
&nbsp;![license](https://img.shields.io/badge/license-MIT-3fb950?style=flat-square&labelColor=0d1117)
&nbsp;![app-agnostic](https://img.shields.io/badge/app-agnostic-8b949e?style=flat-square&labelColor=0d1117)
&nbsp;![skills](https://img.shields.io/badge/skills-7-d29922?style=flat-square&labelColor=0d1117)

</div>

> An agent that writes code fast is easy. An agent you can *trust to run unattended* is the hard
> part — because the failure mode isn't bad code, it's an agent **believing its own output** and
> shipping a false win. `orchestrator-loop` is a plugin for Claude (Cowork & Code) that makes the
> agent plan, build, and then **verify against reality like an adversary** — so you can hand it a
> goal and walk away.

<br/>

## The move that matters

Anyone can wire an agent to write a feature. The question a scientist asks is: *what does it do
when handed a result that's too good to be true?* This:

<div align="center">
<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/verify.svg" alt="A worked verification trace: a +47% lift claim is reproduced, found to have a 61/39 sample-ratio mismatch and a post-exposure label leak, gated per segment to a bot-heavy slice, and rejected — instead of shipped." width="86%">
</div>

> Same model, same diff. A naive agent ships the **+47%** and reports a win. This one treats the
> number as a *bug to disprove* — reproduces it, catches the sample-ratio mismatch, traces the
> leaked label, slices it per segment, and **rejects it with a next action.** That gap — between
> *plausible* and *true* — is the entire product.

<br/>

## One goal in, a verified result out

You don't juggle skills. You type one word and state a goal:

```text
go → "ship the analytics dashboard, end to end"
```

<div align="center">
<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/loop.svg" alt="The go-driven loop, top to bottom" width="62%">
</div>

`go` runs five moves, then loops:

1. **Orient** — read the project (code, schema, roadmap, live state) before planning a thing.
2. **Set the goal** — restate it as a *testable* definition of done.
3. **Refine** — a short round of probing questions that decomposes the goal into fully-covered
   requirements, high and low level. *Garbage in, garbage out* — the cheapest verification there
   is. (Skippable, explicitly, when the goal's already crisp.)
4. **Drive** — `roadmap → draft-prd → architect-review → handoff → verify`, PRD after PRD,
   re-orienting at each seam. No per-step check-ins, no *"want me to continue?"*.
5. **Stop** — only when the goal is **met and independently verified**, you halt it, or it hits
   the one safety rail: an **approval gate before anything irreversible** (a deploy, a migration,
   real money). Everything else runs unattended.

<br/>

## Why you can trust it unattended

Most "autonomous coding" fails by believing its own output. The guardrails are a temperament
against exactly that — each carries its *why* and a one-line war story, so the reasoning travels
to cases the rule never anticipated.

| | Principle | In practice |
|--|--|--|
| 🔬 | **Surprising-good = data bug** | reproduce the number; find the contamination before you celebrate |
| 🩻 | **Distrust the instrument** | a monitor on a leaked source lies confidently; impossible reading ⇒ the *metric* is wrong |
| 📐 | **Analytical rigor** | out-of-fold ship decisions · FDR for multiple comparisons · no leakage · no band-aids |
| 🧩 | **Aggregate hides local** | a clean average can mask one broken slice — gate per partition |
| 🧯 | **Root cause, not symptom** | name the mechanism; a bigger timeout isn't a fix |
| 🛡️ | **Never trust "done"** | reproduce it, read the *deployed* path, 3 signals: renders · 200 · datastore |
| 🎯 | **Intellectual honesty** | surface the unwelcome truth, no selling, end in a recommendation |

<br/>

## What's frozen vs. what you bring

App-agnostic by design: the plugin knows *how to work*, not *what your app is*.

| 🔒 Frozen in the plugin | 🧩 You supply, once |
|--|--|
| the loop + guardrails + epistemics | `CLAUDE.md` app-profile — stack, domain rules, **sanity bounds** |
| 7 skills (`go` + 6 stages) | connectors — `~~database`, `~~hosting`, `~~vcs`, … mapped to your tools |

<details>
<summary><b>The seven skills</b> — you normally touch only <code>go</code></summary>

<br/>

| Skill | Role |
|--|--|
| **`go`** | entry point — orient · set goal · refine · drive to done |
| `roadmap` | broad goal → sequenced, numbered PRDs |
| `draft-prd` | proof in numbers · root cause · scope · un-gameable per-partition acceptance |
| `architect-review` | 5 questions that catch layering/forking *before* code is written |
| `handoff-to-executor` | package one PRD into a self-contained brief; explicit commit policy |
| `verify-handback` | the forensic QA above — reproduce · deployed path · 3 signals |
| `setup` | one-time onboarding — pick executor, wire connectors, write the profile |

Each skill keeps a lean `SKILL.md` with a deep `references/methodology.md` one click away.

</details>

<br/>

## Install

**Cowork** — Settings → Plugins → Add plugin → GitHub → `alopanik/orchestrator-loop` *(or upload
the `.plugin` file)*. Activates next session. Then run **`setup`** once; after that, every session
is just **`go`**.

**Claude Code**
```bash
claude plugin marketplace add alopanik/orchestrator-loop
claude plugin install orchestrator-loop
```

> 💡 If a marketplace install shows a stale version, the **`.plugin` upload** is the reliable path
> (some catalogs cache server-side). The repo is always the source of truth.

<details>
<summary><b>Executor tiers</b> — friend-proof to power-user</summary>

<br/>

Nothing is hardcoded; `setup` verifies what's present and guides any gap.

| Tier | Executor | Best for |
|--|--|--|
| **1 · zero-setup** | the Cowork agent writes code directly | non-technical users, a fast start |
| **2 · power** | a coding CLI (e.g. Claude Code) via a shell MCP | large, multi-PRD autonomous runs |

Even when one agent is *both* planner and coder, the phases stay separate — you distrust your
*own* "done" as hard as a stranger's.

</details>

<details>
<summary><b>Test it before you trust it</b></summary>

<br/>

Ships a **behavioral test kit** (`test/`): a clean-room app-profile + scenarios from real
incidents (a too-good A/B, a leaked-source dashboard, a corpus average hiding a broken slice, a
DROP-before-deploy) + a pass/fail rubric.

**Run it in a clean room** — a fresh session with *nothing* but this plugin and the sample
profile. Run it inside a project whose memory already carries these rules and you can't tell
whether the plugin or the ambient context produced the behavior (*isolate the variable* — one of
the plugin's own lessons). See `test/README.md`.

</details>

<br/>

<div align="center">

**plan with rigor · build with leverage · verify like an adversary · ship the truth**

<sub>MIT · app-agnostic · bring your own stack</sub>

</div>
