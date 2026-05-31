# orchestrator-loop

A reusable Cowork/Claude plugin that turns Claude into a **higher-level orchestrator** for
building software. It plans, writes PRDs, hands execution to a coding agent, and independently
QAs the result — enforcing a fixed set of engineering guardrails the whole way. It is
app-agnostic: you bring your own app-profile, roadmap, and connectors.

## What's frozen in the plugin
- **Guardrails** (always-on via a SessionStart hook — `GUARDRAILS.md`): build IN not ON TOP,
  single source of truth, code minimization, idempotent writes, PRD discipline, and
  never-trust-the-executor QA.
- **The loop**, as five skills:
  - `roadmap` — broad goal → sequenced, numbered PRD roadmap.
  - `draft-prd` — the house PRD format (proof, root cause, scope, un-gameable acceptance).
  - `architect-review` — the 5 questions that catch layering/forking before code is written.
  - `handoff-to-executor` — package a PRD into a self-contained brief for your coding agent.
  - `verify-handback` — independent QA: it renders + network green + datastore reflects it.

## What you supply (per app)
- An **app-profile** — copy `app-profile.template.md` into your repo as `CLAUDE.md` and fill in
  your stack, infra, domain rules, constitution, and roadmap pointer.
- **Connector mappings** — map the `~~category` placeholders (see `CONNECTORS.md`) to the
  concrete tools you use (database, hosting, VCS, browser-QA, coding executor).

## Install

**Cowork (desktop app):** Settings → Plugins → Add plugin → GitHub → enter `<owner>/orchestrator-loop`.
(Or upload the `.plugin` file directly.) Plugins activate on your **next session**, not mid-session.

**Claude Code (CLI):**
```
claude plugin marketplace add <owner>/orchestrator-loop
claude plugin install orchestrator-loop
```

Then copy `app-profile.template.md` into your repo as `CLAUDE.md` and fill it in.

> **Guardrails delivery.** The guardrails live in `GUARDRAILS.md`. In Claude Code they load
> automatically via the SessionStart hook. **Cowork does not reliably fire hooks**, so the
> guardrails are also carried by your app-profile: make its first line read *"Operating under
> orchestrator-loop — the plugin's GUARDRAILS.md is always in effect; read it first."* The
> five loop skills additionally enforce the relevant guardrails inline whenever they run.

## The loop, end to end
**rules → roadmap → PRD → handoff → verify.** You give a broad goal; the orchestrator
decomposes it into a numbered roadmap, drafts each PRD, architect-reviews it, hands it to your
coding agent, then independently verifies the result against your database and your live UI —
and only then accepts it. The executor writes the code; the orchestrator guarantees it's right.
