---
name: setup
description: >
  Guided one-time onboarding for orchestrator-loop in a project: detect what's already wired,
  auto-configure everything possible, walk the user one step at a time through the gaps, then
  write the app-profile (CLAUDE.md) and confirm the guardrails are in force. Use when the user
  says "set up orchestrator-loop", "onboard", "configure the framework", "wire up my executor",
  "get me started", "connect my repo/services", or is installing the plugin into a repo for the
  first time. Run this BEFORE any roadmap/PRD work in a fresh project.
---

# Set up orchestrator-loop (guided onboarding)

Goal: leave the project ready to run the loop — executor chosen, repo + services connected,
app-profile (`CLAUDE.md`) written, guardrails confirmed loaded. The framework is app-agnostic;
this skill is the bridge that wires it to the user's actual tools and records the result in the
app-profile. **Never hardcode an executor into the framework** — record the choice here.

**Operating principle for every step: detect → auto → walk → skip.**
For each thing below: first **detect** whether it's already set up (and if so, say so and skip);
if not, **auto-configure** whatever can be done programmatically (via the shell/`~~executor`
tooling, e.g. Desktop Commander); and for anything that genuinely needs a human (installing an
MCP, clicking Connect, finishing an OAuth login), **walk the user through ONE step, wait for
confirmation, then continue.** Never dump a multi-item checklist. Full detection commands and
per-service walkthroughs: `references/onboarding.md`.

## Step 0 — Pick the executor tier

Ask which the user wants (default to the first that fits; detect tier 2's pieces before deciding):

- **Tier 1 — Cowork direct (zero setup).** The same Cowork agent plans, writes code with its own
  file tools, and QAs. No CLI, no shell MCP, nothing to install. Best for non-technical users or
  a quick start. The role-separation still holds *within one agent* (see GUARDRAILS "when you are
  also the executor").
- **Tier 2 — Cowork brain + coding CLI executor (power mode).** Cowork orchestrates/QAs; a
  separate coding CLI (e.g. Claude Code) writes the code, driven through a shell MCP (e.g.
  Desktop Commander). Best for large, multi-PRD, autonomous runs. Requires the pieces in Step 2.

If unsure, start Tier 1 — it always works — and offer to upgrade to Tier 2 later.

## Step 1 — Connect the repo and read it

Detect a git repo + remote; if present, **read the repo and its docs first** (README,
`CLAUDE.md`, `docs/ARCHITECTURE.md`, any roadmap) so the rest of setup is grounded in reality,
not assumptions. If there's no repo/remote yet, walk the user through connecting `~~vcs` (one
step). Confirm auth (`gh auth status` or equivalent) — if it's a browser/OAuth login, launch it
and wait for the user to finish.

## Step 2 — (Tier 2 only) Get the executor ready — auto where possible

Detect each piece and **skip anything already present**; otherwise auto-do it or walk the gap:

- **Shell MCP (e.g. Desktop Commander).** This is the chicken-and-egg piece: it must be added by
  the user in Cowork's plugin/connector settings (the agent can't install the very tool it would
  need to install things). If absent, walk them through adding it — one step — then continue.
- **Coding CLI (e.g. Claude Code).** Once the shell MCP is connected, **detect** it (`which`),
  and if missing **auto-install** it via the shell, then verify. Check its auth/login; if that's
  an interactive login, launch it and have the user finish the browser step.

State plainly what was auto-done vs. what still needs the user. Never report the executor "ready"
until detection actually confirms it.

## Step 3 — Connect the other services (only the ones this app uses)

For each of `~~database`, `~~hosting`, `~~ci`, `~~dns`, `~~browser-qa`, `~~project-tracker`
(see `CONNECTORS.md`): detect → skip if connected → otherwise walk one connect step. Cowork
connectors (database/hosting/etc.) are added in Settings or via OAuth — the agent can open/guide
them but the user clicks Connect. Record each concrete tool as it's confirmed.

## Step 4 — Write the app-profile

Copy `app-profile.template.md` into the repo as `CLAUDE.md` and fill in from what was detected:
the executor tier + connector mappings, infra, domain rules, **sanity bounds / impossible
values**, and the constitution + roadmap pointers. Keep the very first line as the guardrails
pointer (Step 5 depends on it).

## Step 5 — Confirm guardrail delivery

Cowork doesn't reliably fire SessionStart hooks, so the app-profile's first line must read:
*"Operating under orchestrator-loop — the plugin's GUARDRAILS.md is always in effect; read it
first."* Tell the user to start a **new session** (guardrails load at session start) and verify
by asking *"what do you do with a too-good-to-be-true result?"* — the answer must be, in
substance, **distrust it, reproduce the number, find the data bug.** If it isn't, the pointer
line is missing or the plugin didn't load.

## Output
A connected project + a committed `CLAUDE.md` app-profile + a confirmed-loaded guardrail check,
with a short summary of what was auto-configured, what the user did, and what was skipped as
already-present. Then the loop is ready: `roadmap` → `draft-prd` → `architect-review` →
`handoff-to-executor` → `verify-handback`.
