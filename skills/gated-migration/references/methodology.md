# gated-migration — method + the 2-stage soft-deprecate

## Why a migration is special

Code is revertible — redeploy the old bundle. A migration that drops or rewrites data is not: once
`DROP TABLE users` runs, the data is gone. So a migration gets the framework's strongest gate: it
cannot apply without an owner's review, a bare destructive change is refused, and every step is
recorded. The behavioral rules said this; `migrate.py` makes it mechanical.

## The 2-stage soft-deprecate (why `--staged` exists)

Never drop or rename a column/table the running readers still use — the deploy and the schema
change race, and a reader hitting the missing column 500s/400s. Stage it instead:

1. **Add** the new shape (new column/table) — non-destructive, deploy-safe.
2. **Backfill** the new shape from the old.
3. **Swap reads** — deploy the readers to use the new shape; verify nothing reads the old.
4. **Drop** the old shape — only now, and only after step 3 is verified in production.

Each stage is its own migration. The destructive final drop is drafted `--staged` to assert this
plan exists; `migrate.py apply` blocks a destructive statement that is not staged. (The
alternative the rule allows — a verified deploy of the readers first — is the same idea: never drop
what something still reads.)

## Verify against reality, not "it ran"

After the connector applies the SQL, `verify` should mean you queried the catalog: the column/table
is actually in the expected state, row counts are sane, and the readers return success — the same
three-signals / freshness discipline the verifier uses everywhere. "The migration command exited 0"
is not verification.

## What this skill does NOT do

It does not execute SQL (the `~~database` connector does, with the human's go), does not approve on
the owner's behalf, and does not let the apply skip the pause or the staging requirement. It is the
gate and the audit trail around the irreversible act — not the act itself.
