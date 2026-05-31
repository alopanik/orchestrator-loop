# orchestrator-loop

A reusable Cowork/Claude plugin that turns Claude into a **higher-level orchestrator** for
building software. It plans, writes PRDs, hands execution to a coding agent, and independently
QAs the result — enforcing a fixed set of engineering guardrails the whole way. It is
app-agnostic: you bring your own app-profile, roadmap, and connectors.

## What's frozen in the plugin
- **Guardrails** (always-on via a SessionStart hook — `GUARDRAILS.md`). Not just structural
  rules (build IN not ON TOP, single source of truth + one write-path, idempotent/resumable
  writes, make-failure-loud, PRD discipline) but the **epistemics** — how to think:
  - *A surprising good result is a data bug until proven otherwise* — distrust it, reproduce
    it, find the contamination before you celebrate.
  - *Distrust the instrument, not just the result* — a monitor reading a leaked source lies
    confidently.
  - *Analytical rigor* — out-of-fold-only for ship decisions, multiple-comparisons/FDR
    correction, no-band-aids (fix the model, never blend the failure away), no leakage.
  - *Forensic verification* — reproduce the exact number, read the deployed path, gate per
    partition, trace performance to its mechanism. Never-trust-the-executor QA.
  - *Intellectual honesty* — surface the unwelcome truth, no selling, terminate in a
    recommendation + next action.
  - Each rule carries its **why** and a one-line **war story** — the reasoning is what tells
    you how to apply it to a case the rule didn't anticipate.
- **The loop**, as five skills (each with a `references/methodology.md` for the full method +
  worked examples — progressive disclosure: the `SKILL.md` is the lean spine):
  - `roadmap` — broad goal → sequenced, numbered PRD roadmap (integrity before consumption).
  - `draft-prd` — the house PRD format (proof in numbers, root cause, scope, un-gameable
    per-partition acceptance).
  - `architect-review` — the 5 questions + constitution + CI guardrail that catch
    layering/forking before code is written.
  - `handoff-to-executor` — package a PRD into a self-contained brief for your coding agent.
  - `verify-handback` — independent forensic QA: reproduce the number, three signals
    (renders + network green + datastore), per-partition, freshness.

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

## Test it before you trust it
Don't take the framing on faith — the plugin ships with a behavioral test kit in `test/`. It's
a clean-room sample app-profile plus ten scenarios drawn from real incidents (a too-good A/B
result, a dashboard reading a leaked source, a corpus average hiding a broken slice, a
DROP-before-deploy, …) and a pass/fail rubric.

The one rule that makes the test valid: **run it in a clean room** — a fresh session in a
folder with nothing but this plugin and the sample app-profile. If you run it inside a project
whose memory or `CLAUDE.md` already carries these rules, you can't tell whether the plugin or
the ambient context produced the good behavior (isolate the variable — that's one of the
plugin's own lessons). For a stronger signal, run each scenario once with the plugin and once
in a vanilla session without it; the plugin passes if the with-plugin answer hits the target
behavior and the without-plugin answer is visibly more credulous. See `test/README.md`.
