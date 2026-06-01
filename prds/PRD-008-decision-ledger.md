# PRD-008 — Record what the loop catches (ledger)

**User-visible-surface impact:** Yes — every gate decision is appended to an append-only ledger
with a one-line summary surface. No change to whether a turn blocks (PRD-004 decides that).

## 1. Problem (with proof)

The gate (PRD-004) makes a real accept/block decision every turn — and then **forgets it.**
`stop_gate.py` writes the block reason to stderr for the current turn and exits; nothing is
recorded. So there's no answer to "what has the loop actually caught?" — no audit trail, no way
to show a skeptic the gate fired on real failures, no history to learn from. The plugin's whole
pitch is forensic, evidence-first verification, yet it keeps no evidence of its own decisions.

## 2. Root cause

The gate's decision is transient (stderr + exit code) with no persistence. There is no ledger
and no writer for one.

## 3. Scope

Compose onto the existing gate — the gate is the single decision point, so it is the single
writer:

- **`.orchestrator/ledger.jsonl`** — append-only, one JSON object per gate decision:
  `{ts, prd, decision: "pass"|"block", checks: [{name, ok, detail}], source: "stop-gate"}`.
  The `detail` on a failed check is the evidence (exit code + captured stderr/stdout snippet).
- **`hooks/stop_gate.py`** — when the gate evaluates an active gate (hook mode), append one entry
  recording the decision and every check's result (pass *and* block). One writer; no other
  component writes the ledger.
- **`stop_gate.py ledger [--tail N]`** — the one-line summary surface: `<ts> <prd> <PASS|BLOCK>
  <n_ok>/<n_total>  <failing check names>` per entry, newest last; a final count line.
- **`test/harness/test_stop_gate.py`** — extend with ledger assertions (a block writes a block
  entry carrying the failing check's evidence; a pass writes a pass entry; the summary renders).
- Update `ARCHITECTURE.md` (ledger home = `.orchestrator/ledger.jsonl`, one writer = the gate).

## 4. Non-goals

- Not a metrics dashboard or retention policy — just an append-only record + a text surface.
- Not logging non-gate guard runs invoked standalone — they're captured as the gate's check
  `detail` when run *through* the gate (one writer principle).

## 5. Acceptance tests (un-gameable)

- **AT-1 (every block is recorded with evidence — the headline):** a gate evaluation that blocks
  on a failing check appends an entry with `decision:"block"` and that check's name + detail
  (evidence) in `.orchestrator/ledger.jsonl`.
- **AT-2 (passes recorded too):** a passing gate evaluation appends a `decision:"pass"` entry.
- **AT-3 (summary surface):** `stop_gate.py ledger` prints one line per decision (ts, prd,
  PASS/BLOCK, ratio, failing names) — readable at a glance.
- **AT-4 (one writer / append-only):** only `stop_gate.py` writes the ledger; entries are appended
  (never rewritten); `.orchestrator/` is gitignored.
- **AT-5 (composes with #1's blocks):** when a PRD-001/005 check (e.g. tamper) fails through the
  gate, that block is in the ledger with the check's evidence — demonstrated end-to-end.

## 6. Architect review

1. **Removal.** Removes the "decision is forgotten" gap; the gate now persists what it decided.
2. **SSoT.** One ledger file, one writer (the gate). Other guards don't write it; their results
   ride in the gate entry's `checks[].detail`.
3. **Layering.** Extends `stop_gate.py` (the existing decision point) — no parallel logger.
4. **Migration debt.** Ledger write + summary + tests ship together; `.orchestrator/` already
   gitignored.
5. **Constitution diff.** Updates the `ARCHITECTURE.md` ledger row (home `.orchestrator/ledger.jsonl`).
   No fork.

## 7. Execution

Commit to `master` as `PRD-008` once AT-1…AT-5 pass. No push.
