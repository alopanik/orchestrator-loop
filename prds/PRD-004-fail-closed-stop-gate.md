# PRD-004 — Make the hard gates fail closed (Stop hook)

**User-visible-surface impact:** Yes — a new `Stop` hook can block a turn from ending while a
declared gate's scriptable checks fail. No-op when no gate is active (normal turns never blocked).

## 1. Problem (with proof)

Every gate in the framework is **advisory markdown**. `verify-handback` says "re-run each
acceptance test… report ❌ for every miss," and `GUARDRAILS.md` says "make the invariants
enforceable, not aspirational" — but nothing *mechanically* stops a turn from ending on a
self-asserted "done." Quoting the guardrail that indicts the current state:

```
- **Make the invariants enforceable, not aspirational.** … back it with a CI check that fails
  the build on a banned pattern … *Why:* a rule no machine enforces erodes the week you're busy.
```

Today the only enforcement is the agent choosing to obey. A turn can end with checks unrun or
failing, and nothing catches it. The plugin preaches fail-closed gates and ships none.

## 2. Root cause

There is no machine in the loop with the authority to *refuse to end the turn*. Claude Code
provides exactly that authority — a `Stop` hook that can block by exiting 2 — and the plugin
doesn't use it. The scriptable acceptance checks exist only as prose in PRDs, never registered
anywhere a hook could run them.

## 3. Scope

- **`hooks/stop_gate.py`** — the gate engine + Stop-hook entrypoint (Python 3, stdlib):
  - **Hook mode** (no args, reads the Stop-event JSON on stdin): find the project dir, read the
    **gate manifest** `${CLAUDE_PROJECT_DIR}/.orchestrator/gate.json`. If no active gate → exit 0
    (never block a normal turn). If active → run each declared check command; **all must exit 0**.
    Any failing / missing / erroring check, or a corrupt manifest → **exit 2** with a stderr
    reason (blocks the stop; Claude sees the reason). Fail-closed: missing/error = failure.
  - **Management subcommands** for the loop: `set <PRD> <cmd>...`, `clear`, `status`, and `check`
    (run the gate's checks now and print pass/fail without stdin — for CI / testing).
  - **Loop safety:** respects `stop_hook_active` (adds context; the documented 8-block cap +
    `clear` are the escape hatches so a genuinely stuck gate can't trap the session forever).
- **`hooks/hooks.json`** — register the `Stop` hook → `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/stop_gate.py"`.
- **Gate manifest** `.orchestrator/gate.json` (gitignored): `{prd, active, checks:[{name,cmd}]}`.
  The loop writes it at handoff (the PRD's scriptable ATs) and clears it once verified. For this
  repo the checks are e.g. `run.py --self-test`, `--check-sync`, `--check-startup`.
- **`test/harness/test_stop_gate.py`** — unit tests feeding synthetic stdin + manifests and
  asserting exit codes (pass→0, fail→2, missing→2, none→0, corrupt→2, stop_hook_active path).
- Wire `verify-handback` / `handoff-to-executor` SKILLs to set/clear the gate; update `ARCHITECTURE.md`.

## 4. Non-goals

- Not the ledger (PRD-008 makes the gate append every decision; this PRD just exposes a clean
  decision point).
- Not the trivial-change fast path (PRD-007) — but the gate is the thing that fast path must
  still hit.
- Not Cowork enforcement — Cowork doesn't fire hooks reliably; this gate is real in Claude Code
  (which is exactly why two-brain/Code modes get the strongest enforcement).

## 5. Acceptance tests (un-gameable)

- **AT-1 (pass → allow):** active gate, check exits 0 → hook exits **0**.
- **AT-2 (fail → block):** active gate, a check exits nonzero → hook exits **2**, stderr names
  the failing check.
- **AT-3 (fail-closed):** a check whose command is missing or raises → hook exits **2** (counted
  as failure, never a silent pass).
- **AT-4 (no gate → no block):** no manifest / `active:false` → hook exits **0** (normal turns
  are never trapped).
- **AT-5 (corrupt → block):** manifest present but unparseable → hook exits **2**.
- **AT-6 (registered):** `hooks/hooks.json` contains a `Stop` hook invoking `stop_gate.py`.
- **AT-7 (escape exists):** `clear` deactivates the gate (→ AT-4), and `stop_hook_active` plus the
  documented block-cap mean a stuck gate can't infinitely trap the session. Documented + tested.

## 6. Architect review

1. **Removal.** Replaces "advisory-only" turn-ending with a real gate; removes the implicit
   "agent may end on self-asserted done."
2. **SSoT.** One gate engine (`stop_gate.py`), one manifest location (`.orchestrator/gate.json`),
   one writer (the loop via the management subcommands). The gate is the single enforcement point
   PRD-007 (fast path) and PRD-008 (ledger) extend — they don't fork it.
3. **Layering.** Edits `hooks/hooks.json` in place + adds one engine; not a parallel enforcer.
4. **Migration debt.** Hook + engine + tests + skill wiring ship together; `.orchestrator/`
   gitignored in this PRD.
5. **Constitution diff.** Extends `ARCHITECTURE.md` (Hooks row gains the Stop gate; new manifest
   artifact with one writer). No fork.

## 7. Execution

Commit to `master` as `PRD-004` once AT-1…AT-6 pass and AT-7 is demonstrated. No push.
