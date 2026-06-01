---
name: setup
description: >
  One-time setup for orchestrator-loop in a project: pick your coding executor and connectors,
  write the app-profile (CLAUDE.md), and confirm the guardrails are in force. Use when the user
  says "set up orchestrator-loop", "configure the framework", "wire up my executor", "get me
  started", or is installing the plugin into a repo for the first time.
---

# Set up orchestrator-loop for this app

Goal: leave the project with a filled-in app-profile (`CLAUDE.md`) that names the executor and
connectors, so the loop + guardrails are ready to run. The framework is app-agnostic; this skill
is the bridge that wires it to the user's actual tools. Record the choices in the app-profile —
never hardcode an executor into the framework itself.

Run this one step at a time: if a step needs the user to click or install something, give ONE
step, wait for confirmation, then the next.

## Procedure

1. **Pick the executor.** Ask which coding executor drives the code. The recommended default is
   **Claude Code via Desktop Commander** — Cowork/this agent invokes the `claude` CLI through the
   Desktop Commander MCP. (Any coding agent with repo access also works.)

2. **Verify it's actually present — don't assume.** For the default:
   - Desktop Commander MCP installed? (it appears in the user's plugin/connector list).
   - `claude` CLI on PATH? (`which claude`).
   If either is missing, say so plainly and give the single install step for the missing piece —
   do not claim the executor is wired when it isn't. (A coding executor is not always an MCP you
   can auto-install from a plugin, which is why this skill verifies rather than assumes.)

3. **Map the other connectors** the app uses (skip the ones it doesn't): `~~vcs`, `~~ci`,
   `~~database`, `~~hosting`, `~~dns`, `~~browser-qa`, `~~project-tracker`. See `CONNECTORS.md`.

4. **Write the app-profile.** Copy `app-profile.template.md` into the repo as `CLAUDE.md` and
   fill in: the executor + connector mappings, infra, domain rules, **sanity bounds / impossible
   values**, and the constitution + roadmap pointers. Keep the very first line as the guardrails
   pointer (next step depends on it).

5. **Confirm guardrail delivery.** Cowork does not reliably fire SessionStart hooks, so the
   app-profile's first line must read: *"Operating under orchestrator-loop — the plugin's
   GUARDRAILS.md is always in effect; read it first."* Then tell the user to start a **new
   session** (guardrails load at session start) and verify by asking *"what do you do with a
   too-good-to-be-true result?"* — the answer must be, in substance, **distrust it, reproduce
   the number, find the data bug.** If it isn't, the pointer line is missing or the plugin
   didn't load.

## Output
A committed `CLAUDE.md` app-profile + a confirmed-loaded guardrail check. Then the user is ready
to run the loop: `roadmap` → `draft-prd` → `architect-review` → `handoff-to-executor` →
`verify-handback`.
