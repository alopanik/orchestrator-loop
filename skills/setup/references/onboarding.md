# Guided onboarding — detection commands + per-service walkthroughs

The `SKILL.md` gives the flow. This is the concrete how-to for each piece: how to **detect** it,
what you can **auto-configure** through a shell MCP, and the **one-step walkthrough** for the
parts that need a human. Governing rule: **detect → auto → walk → skip** — never make the user do
something already done, never claim something is wired until detection confirms it, never dump a
multi-item checklist (one step, wait, confirm, next).

## What can be auto-done vs. what needs a human

A shell MCP (e.g. Desktop Commander) runs real commands on the user's machine — so once it is
connected, much is automatable. The honest boundary:

**Auto-doable through the shell MCP:**
- Detect a git repo/remote; read the repo + its MDs.
- Check VCS auth (`gh auth status`), clone, create branches.
- Detect the coding CLI (`which <cli>`); **install** it if missing; check its version.
- Run builds/tests/linters; write the `CLAUDE.md` app-profile.

**Needs a human (you launch/guide, they finish) — stays a one-step walkthrough:**
- **Installing the shell MCP itself** — chicken-and-egg: the agent can't install the tool it
  would use to install things. The user adds it in Cowork's plugin/connector settings first.
- **Cowork connectors** (database, hosting, project-tracker, browser-QA) — added in Settings or
  via OAuth; the agent opens/guides the screen, the user clicks Connect.
- **Interactive logins / OAuth** (e.g. `gh auth login`, a CLI account login) — the agent launches
  it; the human completes the browser step.

## Detection commands (run first; skip anything already present)

```bash
# VCS
git rev-parse --is-inside-work-tree 2>/dev/null   # in a repo?
git remote -v                                     # remote wired?
gh auth status 2>&1                               # GitHub auth (if gh present)

# Executor CLI (Tier 2) — substitute the chosen CLI's binary name
which <coding-cli>            # installed?
<coding-cli> --version        # runs?

# Repo docs to read before planning
ls README* CLAUDE.md docs/ARCHITECTURE.md docs/ROADMAP.md 2>/dev/null
```

For Cowork-side connectors (shell MCP, database, hosting, …) there is no shell probe — detect by
checking the in-session connector list (or ask) and by trying a trivial call; treat "not present"
as "walk the connect step."

## Per-service walkthroughs (one step each)

### Shell MCP (e.g. Desktop Commander) — Tier 2 prerequisite
Detect: is it in the user's connectors / can you run a shell command? If not:
> "Open Cowork Settings → Plugins/Connectors → add the Desktop Commander plugin, then tell me
> when it's connected." Wait. Re-detect. Only then proceed.

### Coding CLI (e.g. Claude Code) — Tier 2
Once the shell MCP works: `which <cli>` → if missing, install via that CLI's documented method
(e.g. an `npm i -g …` or the vendor installer) **through the shell MCP**, then `<cli> --version`
to confirm. If it needs login, launch the login command and ask the user to finish in the
browser; re-check before calling it ready.

### `~~vcs` (GitHub/GitLab/…)
Detect repo + remote + auth (above). Missing remote → walk one step to connect/select the repo.
Missing auth → launch `gh auth login` (or the host's flow) and wait. Then read the repo + MDs.

### `~~database`, `~~hosting`, `~~ci`, `~~dns`, `~~project-tracker`, `~~browser-qa`
Only for services this app uses. For each: detect (connector present? trivial call works?) → skip
if connected → else walk ONE connect step (open the Cowork connector / OAuth; user clicks
Connect) → confirm → record the concrete tool in the app-profile.

## Tiered executor — what to record in the app-profile

- **Tier 1 (Cowork direct):** `~~executor = this Cowork agent (writes code directly)`. No shell
  MCP or CLI required. Role separation is preserved *within one agent* — see the GUARDRAILS note
  on being your own executor (plan → build → verify as distinct phases; distrust your own "done"
  as hard as a separate agent's).
- **Tier 2 (Cowork brain + CLI):** `~~executor = <CLI> via <shell MCP>` (e.g. "Claude Code via
  Desktop Commander"). The brain plans/QAs; the CLI writes code; one PRD in flight at a time.

## Finish

Write/refresh `CLAUDE.md` from what was detected, keep the guardrails-pointer first line, then do
the Step 5 new-session guardrail check. End with a short summary: **auto-configured / you did /
skipped (already present)** — so the user sees exactly what happened and what, if anything, is
still pending.
