---
name: gated-migration
description: >
  Choreograph a `~~database` migration safely — draft → owner review → apply → verify → record,
  with a MANDATORY pause at the irreversible apply. Use whenever a change touches database schema
  or data: a migration, a `DROP`/`ALTER`/`TRUNCATE`, a backfill, or any destructive data change.
  Gives the "no bare destructive migration" rule mechanical teeth. Distinct from CI: CI gates
  code; this gates an irreversible data action.
---

# gated-migration

A migration is the framework's most dangerous, least-reversible operation. The rule has always
been "no bare destructive migration; pause before the irreversible step" — this makes it a gated,
recorded choreography instead of a hope. The framework does not run SQL (`~~database` does);
`migrate.py` gates and records the steps around the apply.

> Detailed rationale + the 2-stage soft-deprecate pattern: `references/methodology.md`.

## The choreography (do not skip a step, never skip the pause)

1. **Draft.** Write the migration and record it:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/test/harness/migrate.py" draft <name> --sql "<sql>|@path" [--staged]
   ```

   A destructive statement (`DROP`/`TRUNCATE`/`ALTER … DROP`/`RENAME`/`DELETE`) is flagged. If it
   is destructive, it must be a **2-stage soft-deprecate** — add → backfill → swap reads → drop —
   drafted with `--staged`; a bare destructive migration is blocked at apply.

2. **PAUSE for owner review.** This is the autonomy hard-exception: an irreversible action is
   ahead, so stop and get the owner's explicit go. The owner records it:

   ```
   python3 .../migrate.py approve <name> --by <owner>
   ```

   Never approve on the owner's behalf. Until this lands, apply is refused.

3. **Apply (gated).** Authorizes the apply — fails closed unless approved, and blocks a bare
   destructive change:

   ```
   python3 .../migrate.py apply <name>
   ```

   Then — and only then — the `~~database` connector runs the SQL, with the human's go. The
   framework never executes it for you.

4. **Verify against reality.** Confirm the schema/data reflects the change and the readers still
   work (the verification discipline — query the catalog, not just "it ran"). Record it:

   ```
   python3 .../migrate.py verify <name>
   ```

5. **Record.** Every transition is already appended to `.orchestrator/migrations/<name>.json` with
   who + when — the audit trail of draft → approve → apply → verify.

## The invariants this enforces

- The apply **pauses** for an owner review — it cannot run on a `drafted` migration.
- A **bare destructive** migration is **blocked** — destructive needs a `--staged` 2-stage plan
  (or a verified readers deploy).
- Who drafted, approved, applied, and verified is **recorded**, so the dangerous step is never
  anonymous or unreviewed.

This skill never executes SQL itself and never skips the pause or the staging requirement.
