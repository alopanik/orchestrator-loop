# PRD-012 — Watch-the-executor visibility

**User-visible-surface impact:** Yes — dispatching the Claude Code executor now streams its live
output into the session and a tailable log, so it isn't a black box; it also stamps the executor
process so PRD-011's enforcement works.

## 1. Problem (with proof)

In power mode the executor (`claude -p`) runs as an opaque subprocess: you get a result, not a
view of the work. The user explicitly asked to "see it" / remote-control it. `handoff-to-executor`
describes the brief but provides no dispatch mechanism that streams the executor's output or lets
you attach — so there's no way to watch, redirect, or step in mid-run. (Anthropic's own guidance:
treat Claude Code like a junior engineer you "watch, redirect, or step away from" — we provide no
way to watch.)

## 2. Root cause

There is no dispatch helper — handoff is described in prose, and whatever launches the executor
does so without teeing output to a live stream + a persistent log, and without marking the process
as the executor.

## 3. Scope

- **`test/harness/dispatch.py`** (stdlib): `run` launches the executor command (default
  `claude -p`, brief on stdin) with **`OL_ROLE=executor`** set (so PRD-011 allows its writes),
  streams stdout **live** to the console AND appends timestamped lines to
  `.orchestrator/executor.log`, and writes `.orchestrator/executor.status`
  (`running` → `exited <code>`). Returns the executor's exit code.
- **`dispatch.py watch`** tails `.orchestrator/executor.log` (live follow); the log path is
  stable so the user can also `tail -f` it or watch it in a tmux pane (documented).
- **`test/harness/test_dispatch.py`** — a fake executor command; assert the log captured its
  output, `OL_ROLE=executor` reached it, status recorded the exit code, and streaming returned
  the lines.
- Wire `handoff-to-executor` SKILL (dispatch via this helper; how to watch) + `ARCHITECTURE.md`.

## 4. Non-goals

- Not building a GUI or a hosted viewer — live stream + tailable log + tmux-friendly path is the
  scope.
- Not changing the brief format (PRD-009/handoff) — only how it's launched + surfaced.

## 5. Acceptance tests (un-gameable)

- **AT-1 (live + logged):** `dispatch.py run --cmd <fake>` streams the executor's lines to stdout
  AND `.orchestrator/executor.log` contains them.
- **AT-2 (role stamped):** the executor process sees `OL_ROLE=executor` (the fake cmd echoes it;
  it appears in the log) — so PRD-011 lets the executor write while the orchestrator can't.
- **AT-3 (status):** `.orchestrator/executor.status` records `exited <code>` with the real exit
  code; `dispatch.py run` returns that code.
- **AT-4 (watchable):** `dispatch.py watch` reads the log; the path is stable/documented for
  `tail -f` / tmux.

## 6. Architect review

1. **Removal.** Removes the opaque-subprocess handoff; adds a streaming, logged, markable dispatch.
2. **SSoT.** One dispatch helper; one executor log + status under `.orchestrator/`. It is also the
   one place that sets `OL_ROLE=executor` (the marker PRD-011 keys on).
3. **Layering.** A helper around the existing handoff; reuses `.orchestrator/`; no parallel path.
4. **Migration debt.** Helper + tests + skill wiring ship together.
5. **Constitution diff.** Extends Test-kit entries (dispatch). No fork; integrates with PRD-011's
   mode + PRD-010 preflight (preflight → dispatch).

## 7. Execution

Commit to `master` as `PRD-012` once AT-1…AT-4 pass. No push.
