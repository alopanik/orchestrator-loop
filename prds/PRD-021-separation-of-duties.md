# PRD-021 — separation of duties (planner ≠ verifier, enforced)

**User-visible-surface impact:** Yes — when a team opts in, `verify-handback` fails closed if the
same principal who built a PRD also blessed it. Builds on 020's recorded principal. Realizes the
parked "Agent Teams mode" first step.

## 1. Problem (with proof)

The whole moat is that the verifier is an adversary, not a co-author — but nothing *stops* the
author from being the verifier. 020 records who made each decision; 021 uses it. Today, with a
team, one agent can plan, build, AND bless its own PRD, defeating the independence the framework
sells. There is no check that the principal who moved a PRD to `building` differs from the one who
moved it to `shipped`.

## 2. Root cause

Role separation was a convention (the verifier *should* be independent), never an enforced
invariant. The per-PRD state recorded only the latest status — not *who* effected each transition —
so even with provenance on the ledger, nothing compared builder-principal to verifier-principal.

## 3. Scope

Record the acting principal on every status transition, and enforce non-identity when a team opts
in. Opt-in because solo/self mode legitimately has one principal (dormant by default — like
`audit_executor`).

- **`prd_state.py` records the principal + history.** Each `set` stamps `by` (the same resolution
  as 020: `$OL_ACTOR` → git user → `$USER` → `unknown`) and appends `{status, by, ts}` to a
  `history` array in the PRD's state file (atomic write preserved).
- **Policy (opt-in).** Separation is required iff `OL_REQUIRE_SEPARATION=1` **or**
  `.orchestrator/policy.json` has `{"require_separation": true}`. Otherwise dormant.
- **`test/harness/check_separation.py <ID>`** — when required, fail closed if any principal who
  set a *builder* status (`claimed`/`building`) also set a *verifier* status
  (`verifying`/`shipped`); if history is missing/insufficient to prove separation, fail closed.
  When not required → dormant pass.
- **`skills/verify-handback/SKILL.md`** — run `check_separation.py <ID>` as part of a real accept.
- **Constitution.** `ARCHITECTURE.md` catalogs `check_separation.py` + the policy file + the
  state `history`/`by` fields.

## 4. Non-goals

- Not identity/auth — `by` is a declared label (as in 020); this raises the bar against accidental
  self-blessing and honest single-actor teams, not a determined impersonator.
- Not on by default — solo/self mode stays dormant (one principal is legitimate there).
- Not changing the claim or state model — only adds `by`/`history` and one check.

## 5. Acceptance tests (un-gameable)

- **AT-1 (dormant by default).** No policy set: same principal builds and ships → `check_separation`
  passes (solo is legitimate).
- **AT-2 (same principal blocked when required).** `OL_REQUIRE_SEPARATION=1`: alice sets `building`
  and alice sets `shipped` → fails closed, names the collision.
- **AT-3 (distinct principals pass when required).** alice `building`, bob `shipped`, required →
  passes.
- **AT-4 (history recorded).** After transitions, the state file's `history` lists each
  `{status, by}`; the latest `by` matches the last setter.
- **AT-5 (policy via file too).** With no env but `.orchestrator/policy.json`
  `{"require_separation":true}`, the same-principal case fails closed.
- **AT-6 (insufficient history fails closed when required).** Required, but only a builder
  transition recorded (no independent verifier) → fails closed (cannot prove separation).

## 6. Architect review

1. **Removal.** Removes the unenforced "verifier should be independent" convention; replaces it
   with an opt-in enforced check. Nothing else removed.
2. **Single source of truth.** The principal-per-transition lives once, in the PRD's state
   `history`; the policy lives once (env or `policy.json`). No second role store.
3. **Layering.** EXTENDS `prd_state.py` (adds `by`/`history`) and adds a sibling check; it does not
   fork the state model or the ledger.
4. **Migration debt.** Additive — pre-existing state files simply lack `history`; the check treats
   absent history as insufficient (fails closed only when separation is *required*).
5. **Constitution diff.** EXTENDS the "Shared state" section; cites Per-PRD state (018) + the
   provenance principal (020) it builds on.

Passes — proceed to build.

## 7. Execution

Tests-first: `test/harness/test_separation.py` committed failing, baselined, then `prd_state.py`
`by`/`history` + `check_separation.py` to green. Commit locally as `PRD-021`. No DDL.
