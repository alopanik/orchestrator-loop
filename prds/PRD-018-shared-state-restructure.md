# PRD-018 — shared-state restructure (de-contend the loop)

**User-visible-surface impact:** Yes — per-PRD state moves into its own files; the ROADMAP status
section becomes a **generated view** (no longer hand-edited); the ledger's "one writer" invariant
is retired in favor of concurrency-safe atomic appends. Foundation of the collaborator thread.

## 1. Problem (with proof)

The loop's shared state is stored as single, hand-edited files with a single-writer assumption
that reality has already outgrown:

- **ROADMAP status is one hand-edited region.** Every PRD completion rewrites the same lines:
  ```
  - Arc 2: [x] 016 · [x] 017 · [ ] 018 · …
  ```
  Two operators each running `go` both edit `## Status` → a merge conflict or a lost update. The
  status of the work is contended state, written by hand.
- **The ledger's "one writer" invariant is already false.** `ARCHITECTURE.md` still said *"one
  writer: `hooks/stop_gate.py`"*, but PRD-016 gave the ledger a second entry point (`ci_gate.py`),
  and multiple operators/machines append concurrently. Two `open(path,"a").write(...)` calls from
  different processes can interleave into a torn line — there is no atomicity guarantee today.

With one operator this mostly hides; the moment a second collaborator or a CI runner writes
concurrently, it corrupts.

## 2. Root cause

Shared, mutable loop state (per-PRD status; the decision ledger) was modeled as single files
edited under a one-writer assumption. Concurrency was never designed in: status is hand-authored
in one contended document, and the ledger append is not atomic across writers.

## 3. Scope

Restructure so concurrent writers do not contend — per Andrew's chosen direction (claim files +
append-only ledger + ROADMAP-as-generated-view).

- **Per-PRD state files.** `test/harness/prd_state.py` manages `.orchestrator/prds/<PRD-ID>.json`
  = `{id, status, ts}` where `status ∈ {planned, claimed, building, verifying, shipped}`. One file
  per PRD ⇒ different PRDs never touch the same file; same-PRD writes are **atomic** (write temp +
  `os.replace`). `set <ID> <status>` / `get <ID>` / `list`.
- **ROADMAP status = a generated view.** `test/harness/roadmap_status.py render` derives the
  status block from the per-PRD state files and writes it into a **managed sentinel block** in
  `ROADMAP.md`; `--check` fails (nonzero) if the block is stale vs the generated content (a
  drift guard, like `--check-sync`). The roadmap *table* (the plan) stays hand-authored; only the
  *status* (what's done) is generated, so it is never hand-edited concurrently.
- **Concurrency-safe ledger.** Route every ledger append through an atomic helper
  (`os.write` to an `O_APPEND` fd, one line ≤ PIPE_BUF) in both `stop_gate.py` and `ci_gate.py`;
  add `test/harness/check_ledger.py` — a canary that fails on any torn/unparseable line. The "one
  writer" invariant is **retired**: many atomic appenders, ordered by `ts`.
- **Migration (ships in this PRD).** Seed a state file for every existing PRD (001–017 = shipped,
  018–023 = planned) and replace the hand-edited `## Status` checkboxes with the generated block.
  Hand-written shipped-note prose is left as history.
- **Constitution.** `ARCHITECTURE.md` catalogs `prd_state.py`, `roadmap_status.py`,
  `check_ledger.py`, `.orchestrator/prds/`; the ledger invariant is rewritten.

## 4. Non-goals

- **Not the claim protocol** (who may take a PRD, branch ↔ claim, stale reclaim) — that is 019;
  018 only provides the per-PRD state substrate it will use.
- Not provenance fields (who/what/which-commit) on the ledger — that is 020.
- Not a lock/lease (the chosen direction is to remove contention structurally, not lock it).
- Not regenerating Arc 1's frozen narrative notes.

## 5. Acceptance tests (un-gameable)

- **AT-1 (different PRDs don't contend).** 10 concurrent `prd_state set` across distinct PRD ids
  all land (10 distinct files, every value present) — no lost update.
- **AT-2 (same PRD is atomic).** N concurrent `set` on the SAME id leave a file that always parses
  to one of the written values (never a torn/partial file).
- **AT-3 (status is generated + drift-guarded).** `roadmap_status.py render` writes the managed
  block; `--check` exits 0 immediately after; hand-edit the block and `--check` exits nonzero.
- **AT-4 (ledger atomic under concurrency).** 20 concurrent appenders → `check_ledger.py` sees 20
  well-formed JSON lines, zero torn; a deliberately corrupted line makes `check_ledger.py` fail.
- **AT-5 (migration complete + faithful).** Every PRD 001–023 has a state file; the generated
  status marks exactly 001–017 shipped and 018–023 not — matching the pre-migration truth.
- **AT-6 (invariant retired in the constitution).** `ARCHITECTURE.md` no longer claims a single
  ledger writer; it states the atomic-appender model (grep-checkable).

## 6. Architect review

1. **Removal.** Removes hand-edited status contention and the false "one writer" claim. The status
   checkboxes are no longer authored by hand — they are generated.
2. **Single source of truth.** Per-PRD status SSoT = `.orchestrator/prds/<ID>.json` (one file =
   one PRD = one owner-at-a-time); ROADMAP status is a *view*, never a second source. The ledger
   stays one append-only log with a defined atomic-append contract.
3. **Layering.** EDITS the existing ROADMAP status into a generated view and the existing ledger
   append into an atomic one — no parallel status doc, no second ledger.
4. **Migration debt.** Seeds all state files and converts `## Status` in THIS PRD; the conversion
   is the cleanup, not a follow-up.
5. **Constitution diff.** EXTENDS: new state substrate + two generators + a canary; rewrites the
   ledger invariant to match reality (PRD-016 already broke the old wording). Cites "Decision
   ledger" + the Roadmap doc entry.

Passes — proceed to build.

## 7. Execution

Tests-first: `test/harness/test_shared_state.py` committed failing, baselined, then
`prd_state.py` + `roadmap_status.py` + `check_ledger.py` + the atomic-append edits to green.
Migration run in this PRD. Commit locally as `PRD-018`. No DDL; the file-format "migration" is
additive (state files seeded; ROADMAP status block swapped in with a verified generator).
