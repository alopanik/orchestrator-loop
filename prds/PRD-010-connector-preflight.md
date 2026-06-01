# PRD-010 — Connector preflight gate

**User-visible-surface impact:** Yes — before the executor is dispatched, the loop verifies each
connector points at the project named in `CLAUDE.md`; a wrong Supabase/Vercel/etc. fails closed.

## 1. Problem (with proof)

The app-profile *names* the right project refs (`~~database = Supabase project abc`), but nothing
checks the executor is actually wired to them before it runs. The executor is a separate agent
with its own `.mcp.json`; it can be pointed at a different project and the loop only finds out
**reactively** at verify (if at all). For a destructive change that's a production incident, not
a review note. CONNECTORS.md binds categories by name; there is no *binding check*.

## 2. Root cause

Connector binding is declarative (names in the app-profile) with no preflight that compares the
*declared* ref to the *actual* ref the connected tool reports — so a mismatch is invisible until
something writes to the wrong place.

## 3. Scope

- **`.orchestrator/connectors.json`** — per connector: `{category, expected, probe}` where
  `expected` is the ref from `CLAUDE.md` and `probe` is a command that prints the *actual* ref of
  the currently-connected tool (e.g. a Supabase MCP call, `vercel project ls`, `gh repo view`).
- **`test/harness/preflight.py`** (stdlib): run each `probe`, compare to `expected`; **pass** only
  if every probe's output contains its expected ref. **Fail closed** on mismatch, missing probe,
  or a probe that errors. `preflight.py status` prints the table.
- **Compose with the gate + handoff:** `handoff-to-executor` runs preflight before dispatch and
  refuses to hand off on a mismatch; `preflight.py check` is addable to the Stop-gate manifest.
- **`test/harness/test_preflight.py`** — synthetic probes (matching ref → pass; wrong ref → fail;
  missing/erroring probe → fail-closed).
- Wire `handoff-to-executor` SKILL + `setup` (record probes) + `ARCHITECTURE.md`.

## 4. Non-goals

- Not hardcoding any provider's API — probes are declared per project (the framework stays
  app-agnostic; it provides the mechanism + the fail-closed comparison).

## 5. Acceptance tests (un-gameable)

- **AT-1 (match → pass):** every probe reports its expected ref → `preflight.py check` exits 0.
- **AT-2 (mismatch → block, the headline):** a probe reports a *different* ref than `CLAUDE.md`
  declares → exits nonzero, names the offending connector + both refs.
- **AT-3 (fail-closed):** a missing probe or a probe that errors → exits nonzero (never a silent
  pass).
- **AT-4 (gate-composed):** `preflight.py check` in the gate manifest makes a wrong-project
  handoff block the turn.

## 6. Architect review

1. **Removal.** Removes the blind "trust the executor is wired right"; adds a binding check.
2. **SSoT.** One preflight engine; expected refs trace to `CLAUDE.md`; `.orchestrator/connectors.json`
   is the probe manifest (one writer: setup/handoff).
3. **Layering.** Reuses the gate/check pattern (like check_tests); not a parallel system.
4. **Migration debt.** Engine + tests + wiring ship together.
5. **Constitution diff.** Extends Test-kit entries (preflight). No fork.

## 7. Execution

Commit to `master` as `PRD-010` once AT-1…AT-3 pass (AT-4 by composition). No push.
