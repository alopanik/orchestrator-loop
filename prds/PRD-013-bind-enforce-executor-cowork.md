# PRD-013 — Bind & enforce the executor in Cowork (two-brain that actually binds)

**User-visible-surface impact:** Yes — selecting two-brain (power) mode now actually takes
effect: setup persists the choice and refuses to report "ready" until it's verified, the handoff
spells out the Cowork→desktop-commander dispatch path, and a fail-closed audit blocks a handback
whose code the orchestrator wrote itself instead of dispatching.

## 1. Problem (with proof)

Two-brain mode is *selected* but never *binds* in Cowork — the orchestrator just writes the code
itself. Three independent causes, all observed in this repo:

- **`.orchestrator/mode.json` does not exist** (only `gate.json` does). `enforce_executor.get_mode()`
  returns `"self"` when the file is absent, so the `PreToolUse` guard allows every `Edit`/`Write` —
  the enforcement is inert.
- **`CLAUDE.md` maps `~~executor = self`.** That prose is the SSoT the model reads, and GUARDRAILS'
  "when you are also the executor" section then *correctly* tells it to build the code itself.
- **Enforcement is a Claude Code `PreToolUse` hook**, but the orchestrator runs in **Cowork**, where
  (per this repo's own setup/CLAUDE.md notes) hook delivery is unreliable and a `PreToolUse` *deny*
  on Cowork's native `Edit`/`Write` is not guaranteed. Nothing records that an executor must do the
  writing, and nothing detects when it didn't — so the path of least resistance (native file tools)
  wins.

The user's report ("on tier 2, it still builds natively") reproduces from config + environment
alone — not a model lapse.

## 2. Root cause

The tier choice is never persisted (setup Step 0's `enforce_executor.py mode …` and Step 4's
`~~executor` line did not stick), and the only enforcement is **preventive + Claude-Code-only**.
Where the orchestrator actually runs (Cowork), there is no recorded dispatch path and no
fail-closed detection of "the orchestrator coded instead of dispatching."

## 3. Scope

- **`skills/setup/SKILL.md`** — Step 0 persists the tier to BOTH `.orchestrator/mode.json` (via
  `enforce_executor.py mode …`) AND the `~~executor` line in `CLAUDE.md`, and **mechanically
  verifies** `mode.json` matches the chosen tier before reporting tier-2 ready (fail closed, same
  discipline as Step 5's guardrail-pointer check).
- **`skills/handoff-to-executor/SKILL.md`** — make dispatch **environment-aware**: in Cowork
  two-brain, dispatch through the **desktop-commander** MCP on the real machine (where the coding
  CLI is installed + authed), NOT the workspace sandbox; `dispatch.py` is the in-CLI path. Spell
  out the one route.
- **`test/harness/audit_executor.py`** (new, stdlib) — a fail-closed **detective** control:
  `check` exits nonzero in `claude-code` mode when the working tree changed but no executor
  dispatch is recorded (`.orchestrator/executor.status` absent / not a completed run) — i.e. the
  orchestrator coded instead of dispatching. `self` mode always passes. Complements (does not
  replace) the preventive `PreToolUse` hook.
- **`test/harness/test_audit_executor.py`** (new) — temp-git matrix covering AT-3…AT-5.
- **`skills/verify-handback/SKILL.md`** — add "run `audit_executor.py check` (power mode)" to the
  real-pass checks; in Cowork this is where the boundary is actually enforced.
- **`.orchestrator/mode.json`** — write `{"executor":"self"}` for THIS repo (honest: the coding CLI
  isn't reachable this session); document the one-liner to switch to power mode.
- Wire **`ARCHITECTURE.md`** (one new Test-kit row: the audit).

## 4. Non-goals

- Not defeating *deliberate* circumvention (someone who hand-edits in power mode and fabricates an
  `executor.status` opts out knowingly). The audit catches the **accidental** orchestrator-coding
  that is the actual failure here.
- Not per-PRD cryptographic attribution of each diff line. The preventive guarantee remains the
  Claude Code `PreToolUse` hook (PRD-011); this adds the **Cowork-side fail-closed detection** that
  was missing.
- No change to self/solo behavior.

## 5. Acceptance tests (un-gameable)

- **AT-1 (mode persists):** after `enforce_executor.py mode claude-code`, `.orchestrator/mode.json`
  == `{"executor":"claude-code"}` and `status` reports it; existing `test_enforce_executor.py` stays
  green.
- **AT-2 (setup fail-closed):** setup's tier-2 path documents a mechanical verify that fails if
  `mode.json` is missing or ≠ the chosen tier (never report "ready" unverified).
- **AT-3 (audit blocks orchestrator-coding — headline):** mode `claude-code`, working tree changed,
  no `executor.status` → `audit_executor.py check` exits nonzero, message names power mode + dispatch.
- **AT-4 (audit allows the executor):** mode `claude-code`, working tree changed, `executor.status`
  = a completed run → exit 0.
- **AT-5 (self unaffected):** mode `self`, working tree changed → exit 0.
- **AT-6 (handoff documents the Cowork path):** `handoff-to-executor` names desktop-commander as the
  Cowork dispatch route.

## 6. Architect review

1. **Removal.** Removes the inert/honor-system gap in Cowork; adds a recorded dispatch path + a
   fail-closed audit. Nothing removed for self/solo.
2. **SSoT.** Mode stays one fact (`mode.json`), sourced from the app-profile `~~executor` mapping;
   setup is the one writer of both mode + the profile line. The audit reads the existing
   `.orchestrator/executor.status` (PRD-012) — no new state invented.
3. **Layering.** `audit_executor.py` sits beside `enforce_executor.py` as the *detective* complement
   to the *preventive* hook; reuses `.orchestrator/`; no parallel system.
4. **Migration debt.** Skill edits + audit + tests + ARCHITECTURE ship together.
5. **Constitution diff.** Adds one Test-kit row (audit_executor). Extends, doesn't fork.

## 7. Execution

Build in `self` mode (the executor here is the orchestrator switching hats — legitimate in self
mode). Commit to `master` as `PRD-013` once AT-1…AT-6 pass. **No push** (a release is the owner's
sign-off).
