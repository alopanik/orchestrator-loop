# PRD-023 — gated-migration choreography

**User-visible-surface impact:** Yes — a new `gated-migration` skill choreographs
draft → owner review → apply → verify → record, with a mandatory pause at the irreversible apply.
Distinct from CI (016): CI gates *code*; this gates an *irreversible data action* on `~~database`.

## 1. Problem (with proof)

The framework's most dangerous operation has the least mechanical protection. The rules forbid a
bare destructive migration — `GUARDRAILS.md` / the startup primer:

> "No destructive migration (DROP/rename) without a verified deploy of the readers, or a 2-stage
> soft-deprecate." … "pause before anything irreversible … a DB migration."

But these are *behavioral rules* an agent chooses to follow. Nothing **stops** an agent from
running `DROP TABLE` with no review, no staging, and no record. A migration is irreversible; "the
agent should pause" is not the same as "the apply is gated until an owner has reviewed it."

## 2. Root cause

Migration safety lived only as prose guidance. There is no choreography that (a) forces an owner
review *before* the irreversible apply, (b) blocks a *bare* destructive change (no 2-stage plan),
and (c) records who approved/applied it. The discipline was advisory, not enforced.

## 3. Scope

A distinct skill + a small state machine that gives the existing rule teeth. (The framework does
not execute SQL — `~~database` does; `migrate.py` *gates and records* the choreography around it.)

- **`test/harness/migrate.py`** — the gate + record state machine over
  `.orchestrator/migrations/<name>.json`:
  - `draft <name> --sql <text|@file> [--staged]` → record `{name, sql, destructive, staged,
    state: drafted, history}`; flag destructive (`DROP/ALTER/TRUNCATE/RENAME/DELETE`).
  - `approve <name> --by <reviewer>` → state `approved` (the owner-review gate; recorded).
  - `apply <name>` → **fails closed** unless `approved`; **blocks a bare destructive** migration
    (destructive and not `--staged`); on pass → state `applied` (authorizes the connector to run
    the SQL — the irreversible step, done with the human's go).
  - `verify <name>` → state `verified`; `status` → list.
  - Every transition appends to `history` (who · ts) — the audit trail.
- **`skills/gated-migration/SKILL.md`** (+ `references/`) — the choreography:
  draft → **PAUSE for owner review** (`approve`) → `apply` (gate) → connector runs SQL →
  `verify` → recorded. Names the irreversible pause explicitly (the autonomy hard-exception).
- **Constitution.** `ARCHITECTURE.md` catalogs `migrate.py` + the `gated-migration` skill +
  `.orchestrator/migrations/`.

## 4. Non-goals

- Not a SQL executor / migration engine — `~~database`'s tool applies the SQL; this gates + records.
- Not auto-approving or auto-applying — approval is a human act; the pause is mandatory.
- Not identity/auth — `by` is a declared reviewer label (as with 020/022).

## 5. Acceptance tests (un-gameable)

- **AT-1 (draft records).** `draft m1 --sql "CREATE TABLE t(id int)"` → state `drafted`; `status`
  lists it; non-destructive.
- **AT-2 (apply gated on review — the mandatory pause).** `apply m1` with no approval → **fails
  closed**, naming the missing owner review.
- **AT-3 (approve unlocks apply).** `approve m1 --by alice` → `apply m1` succeeds → state `applied`.
- **AT-4 (bare destructive blocked).** A migration whose SQL contains `DROP TABLE`, approved but
  **not** `--staged`, → `apply` **fails closed** ("bare destructive; needs 2-stage soft-deprecate");
  the same SQL drafted `--staged` → `apply` (after approval) is allowed.
- **AT-5 (audit trail recorded).** After the lifecycle, the migration record's `history` names who
  drafted, approved, and applied (distinct transitions with `by`/`ts`).
- **AT-6 (full lifecycle).** `draft → approve → apply → verify` advances
  `drafted→approved→applied→verified`; `status` reflects the final state.

## 6. Architect review

1. **Removal.** Removes the purely-advisory "don't do a bare destructive migration"; replaces it
   with a gated, recorded choreography. Nothing else removed.
2. **Single source of truth.** Each migration is one record (`<name>.json`) with its state +
   history; no second migration log. Distinct from CI's `ci-gate.json` (code) — this is data-action.
3. **Layering.** New skill + one state-machine tool; does not fork the gate or the ledger. It is
   deliberately a *separate* skill from `bootstrap-cicd` (Andrew: CI gates code, this gates data).
4. **Migration debt.** Additive; `.orchestrator/migrations/` is new runtime state.
5. **Constitution diff.** EXTENDS the stage-skills + a new tool; cites the "no destructive
   migration" rule in `GUARDRAILS.md` it enforces.

Passes — proceed to build.

## 7. Execution

Tests-first: `test/harness/test_migration_gate.py` committed failing, baselined, then `migrate.py`
+ the skill to green. Commit locally as `PRD-023`. The skill never executes SQL or skips the pause.
