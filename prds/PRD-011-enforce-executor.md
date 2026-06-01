# PRD-011 — Enforce the executor (two-brain integrity)

**User-visible-surface impact:** Yes — in power mode the orchestrator's file-mutation tools are
blocked; only the Claude Code executor can write code. Separation becomes a guarantee, not a vibe.

## 1. Problem (with proof)

"Claude Code is the executor" is honor-system. `GUARDRAILS.md` says "You are not the coder…
the executor (`~~executor`) writes the code," but nothing *prevents* the orchestrator from
editing files itself in power mode. This session proved the risk twice: the zero-setup default
literally is the orchestrator coding, and a rogue sub-agent self-dispatched and committed work it
was never handed. If separation is the recommended mode's whole value (PRD-009), it has to be
enforced, not promised.

## 2. Root cause

Nothing distinguishes "orchestrator session" from "executor session" at the tool boundary, and
no hook denies file mutations to the orchestrator. Mode is declared in the app-profile but never
enforced.

## 3. Scope

- **`.orchestrator/mode.json`** — `{"executor": "self" | "claude-code"}` (set from the app-profile
  `~~executor` mapping at setup).
- **`hooks/enforce_executor.py`** — a Claude Code **`PreToolUse`** hook. On a file-mutation tool
  (`Edit|Write|MultiEdit|NotebookEdit`): allow if mode is `self`; if mode is `claude-code`, allow
  ONLY when the process is the executor (launched with env `OL_ROLE=executor`) — otherwise **deny**
  (exit 2) with "power mode: dispatch to the executor; the orchestrator plans + verifies, it does
  not edit files." Non-mutation tools always pass.
- **`hooks/hooks.json`** — register the `PreToolUse` hook (matcher on the write tools).
- **Convention:** the executor is launched with `OL_ROLE=executor` (the PRD-012 dispatch helper
  sets it); the orchestrator session never has it, so its writes are denied in power mode.
- **`test/harness/test_enforce_executor.py`** — synthetic `PreToolUse` stdin + env/mode matrix.
- Wire `setup` (write `mode.json`) + `ARCHITECTURE.md`.

## 4. Non-goals

- Not preventing deliberate circumvention (a user who exports `OL_ROLE=executor` in the
  orchestrator opts out knowingly) — this prevents *accidental* self-coding, which is the failure.
- Not changing zero-setup/solo behavior (`self` mode always allows — the role separation there is
  temporal, per GUARDRAILS).

## 5. Acceptance tests (un-gameable)

- **AT-1 (power mode blocks orchestrator writes — the headline):** mode `claude-code`, tool
  `Write`, no `OL_ROLE` → hook denies (exit 2, reason names power mode).
- **AT-2 (executor may write):** mode `claude-code`, tool `Write`, `OL_ROLE=executor` → allow
  (exit 0).
- **AT-3 (solo unaffected):** mode `self`, tool `Write` → allow (exit 0).
- **AT-4 (non-mutation tools pass):** mode `claude-code`, tool `Read`/`Bash`, no role → allow.
- **AT-5 (registered):** `hooks/hooks.json` has a `PreToolUse` hook invoking `enforce_executor.py`.

## 6. Architect review

1. **Removal.** Removes the honor-system "orchestrator promises not to code"; replaces with a
   tool-boundary denial.
2. **SSoT.** One mode manifest, one enforcement hook. The mode traces to the app-profile
   `~~executor` mapping.
3. **Layering.** Adds one PreToolUse hook beside the existing Stop hook; no parallel system.
4. **Migration debt.** Hook + mode manifest + tests + setup wiring ship together.
5. **Constitution diff.** Extends the Hooks row in `ARCHITECTURE.md` (PreToolUse enforcement). No
   fork.

## 7. Execution

Commit to `master` as `PRD-011` once AT-1…AT-5 pass. No push.
