# PRD-017 — executor reliability (a crashed run is never "done")

**User-visible-surface impact:** Yes — `handoff-to-executor` + `verify-handback` gain an
executor-outcome gate; `dispatch.py` gains a timeout and a structured outcome. Sequenced before
the collaborator thread: this bit on day one of single-operator (two-brain) use.

## 1. Problem (with proof)

The executor lifecycle has no concept of a *clean* finish. `dispatch.py` records every
termination identically:

```
.orchestrator/executor.status :  "running <ts>"  ->  "exited <code> <ts>"
```

and `audit_executor.py` treats **any** `"exited"` as a satisfied dispatch:

```python
# audit_executor.py:_dispatch_recorded
return ("exited" in txt), (txt or "<empty>")
```

So an executor that **crashed (exit 1), was killed, or returned a partial diff** is
indistinguishable from one that succeeded — the audit passes and the handback can be accepted as
"done." Two more day-one gaps in the same file: there is **no timeout** (`for line in proc.stdout`
+ `proc.wait()` hang forever on a stuck executor), and a process killed mid-dispatch leaves
`status` stuck at `"running"` with **no way to tell in-flight from crashed** — so the loop can
neither resume nor reclaim it.

## 2. Root cause

`dispatch.py` records *that* the process ended, not *how*. Outcome (exit code, timeout, kill,
launch failure) is collapsed into one string, and the only reader keys on the substring
`"exited"`. Liveness (pid/heartbeat) is never recorded, so a stale `"running"` is ambiguous.
Reliability was never modeled — only "a process was launched and the tree changed."

## 3. Scope

The smallest change that makes a non-clean executor run fail the handback closed, bounds a hang,
and makes an interrupted run distinguishable.

- **`test/harness/dispatch.py`** — `cmd_run` wraps execution in try/finally; adds `--timeout`
  (terminate → SIGKILL on exceed); records a **structured** outcome to a new
  `.orchestrator/executor.outcome.json`: `{state, code, pid, started, ended, heartbeat}` where
  `state ∈ {running, ok, failed, timeout, killed, launch-error}` (`ok` ⟺ exit 0). The legacy
  `executor.status` line is kept verbatim (PRD-012/013 back-compat). A `clear-outcome`
  subcommand removes it on accept.
- **`test/harness/check_executor.py`** (new) — `check`: dormant-pass when no outcome exists (a
  self-mode cycle with no dispatch — `audit_executor` covers the "tree changed, no dispatch"
  case). When an outcome exists it **fails closed unless `state == ok`**; a `running` outcome
  whose `pid` is **not alive** is reported as a crash (resumable: the loop may re-dispatch); a
  `running` outcome whose pid IS alive blocks (a verify must not run mid-dispatch).
- **`skills/verify-handback/SKILL.md`** — run `check_executor.py check` as part of a real pass
  (beside `audit_executor`); clear the outcome only on accept.
- **`skills/handoff-to-executor/SKILL.md`** — note the `--timeout` and that a non-clean outcome
  blocks the handback.
- **Constitution.** `ARCHITECTURE.md` catalogs `check_executor.py` + `executor.outcome.json` under
  the executor components.

## 4. Non-goals

- Not auto-retrying or auto-resuming a crashed executor — this PRD *detects* and *classifies*;
  re-dispatch stays the orchestrator's call.
- Not a daemon/heartbeat service — heartbeat is a timestamp written during streaming, not a
  separate process.
- Not changing `audit_executor`'s boundary semantics (planner-didn't-code) — outcome is a new,
  separate concept with its own home.

## 5. Acceptance tests (un-gameable)

- **AT-1 (clean passes).** Dispatch `sh -c 'exit 0'` → `outcome.state == ok` →
  `check_executor.py check` exits 0.
- **AT-2 (failure fails closed).** Dispatch `sh -c 'exit 3'` → `state == failed`, `code == 3` →
  `check_executor.py` exits nonzero and names the failure.
- **AT-3 (a hang is bounded).** Dispatch `sh -c 'sleep 30'` with `--timeout 1` returns in
  ≲ a few seconds (NOT 30) with `state == timeout`; the gate then fails closed.
- **AT-4 (crash ≠ in-flight, ≠ done).** A fabricated `running` outcome with a dead pid →
  `check_executor.py` fails closed and reports a crash (resumable), not a pass.
- **AT-5 (no dispatch ⇒ dormant).** With no `executor.outcome.json`, `check_executor.py` exits 0
  (it must not block a legitimate self-mode handback; `audit_executor` owns the no-dispatch case).
- **AT-6 (launch error is not "running").** Dispatch a non-existent command → `state` is
  `launch-error`/`failed` (never left `running`) → gate fails closed.

All six run locally with toy executors; no real model invoked.

## 6. Architect review

1. **Removal.** Removes the false-equivalence "any exit == done"; replaces the substring check
   with an outcome state. Nothing user-facing removed.
2. **Single source of truth.** Outcome lives once, in `executor.outcome.json`, written only by
   `dispatch.py` (the executor's lifecycle owner) and read by `check_executor.py`. The mode is
   still read through `enforce_executor.get_mode` — no second source.
3. **Layering.** EXTENDS `dispatch.py` (adds outcome + timeout) and adds a sibling check beside
   `audit_executor`; it does NOT overload the boundary audit with outcome logic (distinct concept,
   distinct home).
4. **Migration debt.** `executor.status` legacy line kept for PRD-012/013 readers + their tests;
   the new outcome file is additive. `ARCHITECTURE.md` updated in this PRD.
5. **Constitution diff.** EXTENDS the executor components (dispatch/audit) with one new check +
   one new state file; cites the "Executor dispatch" and "Executor audit" entries.

Passes — proceed to build.

## 7. Execution

Tests-first: `test/harness/test_executor_reliability.py` committed failing, baselined, then
`dispatch.py` + `check_executor.py` to green. Commit locally as `PRD-017`. No push; no
migration/DDL.
