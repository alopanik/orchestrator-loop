<div align="center">

<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/hero.svg" alt="orchestrator-loop — turn Claude into a disciplined engineering lead" width="100%">

<br/><br/>

![version](https://img.shields.io/badge/version-0.4.1-6366f1?style=flat-square)
&nbsp;![license](https://img.shields.io/badge/MIT-16a34a?style=flat-square)
&nbsp;![app-agnostic](https://img.shields.io/badge/app--agnostic-7c3aed?style=flat-square)
&nbsp;![skills](https://img.shields.io/badge/7_skills-0891b2?style=flat-square)
&nbsp;![Cowork + Code](https://img.shields.io/badge/Claude_Cowork_+_Code-0e1116?style=flat-square)

</div>

> **You set one goal. It runs the whole loop to completion** — plans the work, writes the spec,
> hands the coding to an executor, then independently QAs the result against reality. Skeptical,
> forensic, honest. High leverage, low overhead, unusual velocity — *without* the usual cost of
> unverified autonomy.

<br/>

<div align="center">
<img src="https://raw.githubusercontent.com/alopanik/orchestrator-loop/master/assets/loop.svg" alt="the go-driven loop" width="100%">
</div>

<br/>

## Start a session

You don't juggle six skills. Type one word and state a goal:

```
go    →    "ship the analytics dashboard, end to end"
```

`go` **orients** (reads your project), **sets the goal** as a testable definition of done, then
**drives the loop** — re-orienting at each seam, never stopping at a per-PRD checkpoint, never
asking *"want me to continue?"*. It stops only when the goal is **met and independently
verified**, a decision is genuinely yours, or you halt it — and **pauses automatically before
anything irreversible** (a deploy, a migration, a trade).

<br/>

## How it thinks

Most "autonomous coding" fails not by doing the wrong thing, but by **believing its own output.**
The guardrails encode a temperament against exactly that — each rule carries its *why* and a
one-line war story, because the reasoning is what travels to a case the rule never anticipated.

|  | Principle |
|--|--|
| 🔬 | **A surprising-good result is a data bug until proven** — reproduce the exact number and find the contamination *before* you celebrate. |
| 🩻 | **Distrust the instrument** — a monitor reading a leaked source lies confidently; an impossible reading means the *instrument* is wrong. |
| 🧯 | **Root cause, not symptom** — name the mechanism; raising a timeout to "fix" a slow query is patching a symptom. |
| 🚪 | **The same bug returns through a different door** — fix every sibling path in the same change. |
| 📐 | **Analytical rigor** — out-of-fold-only ship decisions, FDR-correct multiple comparisons, no leakage, **no band-aids**. |
| 🧩 | **Aggregate hides local** — a clean average can mask one broken partition; gate per partition. |
| 🛡️ | **Never trust the executor's "done"** — reproduce it, read the *deployed* path, check three signals (renders · network 200 · datastore). |
| 🎯 | **Intellectual honesty** — surface the unwelcome truth, no selling, end in a recommendation + next action. |
| 🏗️ | **Build IN, not ON TOP** — fix the existing path; one concept, one home; structural change ships its own cleanup. |

<br/>

## Two layers

The framework is **frozen and app-agnostic** — it knows *how to work*, not *what your app is*.
You supply the specifics once.

| 🔒 Frozen in the plugin | 🛠️ You supply, once |
|--|--|
| `GUARDRAILS.md` — method + epistemics | `CLAUDE.md` app-profile — stack, domain rules, sanity bounds |
| 7 skills (`go` + 6 stages) | connector mappings — `~~database`, `~~hosting`, `~~vcs`, … |
| *the constant* | *everything specific to your app* |

<br/>

## The seven skills

You normally touch only the first — **`go`** orchestrates the rest. Each keeps a lean `SKILL.md`
with a deep `references/methodology.md` one click away (progressive disclosure).

| Skill | Role |
|--|--|
| 🟣 **`go`** | **Entry point.** Orient → set one goal → drive the loop to completion. |
| 🧭 `roadmap` | Broad goal → a sequenced, numbered PRD roadmap. |
| 📝 `draft-prd` | Proof in numbers, root cause, scope, **un-gameable per-partition acceptance**. |
| 🏛️ `architect-review` | The 5 questions that catch layering/forking *before* code is written. |
| 📦 `handoff-to-executor` | Package a PRD into a self-contained brief; one in flight; explicit commit policy. |
| 🔬 `verify-handback` | Forensic QA — reproduce the number, read the deployed path, three signals. |
| 🧰 `setup` | One-time onboarding — pick your executor, wire connectors, write the app-profile. |

<br/>

## Install

**Cowork** — Settings → Plugins → Add plugin → GitHub → `alopanik/orchestrator-loop`
*(or upload the `.plugin` file).* Activates on your **next** session.

**Claude Code**
```bash
claude plugin marketplace add alopanik/orchestrator-loop
claude plugin install orchestrator-loop
```

Then run **`setup`** once — it picks your executor, wires connectors, writes `CLAUDE.md`, and
confirms the guardrails loaded. After that, every session is just **`go`**.

> 💡 If a marketplace install shows a stale version, the **`.plugin` file upload** is the reliable
> path — some catalogs cache server-side. The GitHub repo is always the source of truth.

<br/>

## Executor tiers

Nothing is hardcoded and nothing auto-installs — `setup` verifies what's present and guides any gap.

| Tier | Executor | Best for |
|--|--|--|
| **1 · zero-setup** | the Cowork agent writes code directly | non-technical users, a fast start |
| **2 · power** | a coding CLI (e.g. Claude Code) via a shell MCP | large, multi-PRD, autonomous runs |

Even when one agent is *both* planner and coder, the separation of concerns holds — you distrust
your *own* "done" as hard as a stranger's.

<br/>

## Test it before you trust it

The plugin ships a **behavioral test kit** (`test/`) — a clean-room app-profile + scenarios drawn
from real incidents (a too-good A/B, a leaked-source dashboard, a corpus average hiding a broken
slice, a DROP-before-deploy) and a pass/fail rubric.

> 🧪 **Run it in a clean room** — a fresh session with *nothing* but this plugin and the sample
> profile. Inside a project whose memory already carries these rules, you can't tell whether the
> plugin or the ambient context produced the behavior (*isolate the variable* — one of the
> plugin's own lessons). See `test/README.md`.

<br/>

<div align="center">

**Plan with rigor · build with leverage · verify like an adversary · ship the truth.**

`MIT` · app-agnostic · bring your own stack

</div>
