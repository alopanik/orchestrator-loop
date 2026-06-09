# PRD-019 — PRD claiming / ownership

**User-visible-surface impact:** Yes — `go` / `handoff-to-executor` can atomically *claim* a PRD
so two operators/agents never build the same one; a claim records who + which branch, and a stale
claim is reclaimable. Builds on 018's per-PRD state.

## 1. Problem (with proof)

018 gave each PRD its own state file, but nothing prevents two collaborators from both picking up
the same next PRD. `prd_state.py set` is last-writer-wins:

```
op-A: prd_state.py set PRD-020 building     # both read "planned",
op-B: prd_state.py set PRD-020 building     # both proceed — double build, wasted/conflicting work
```

There is no atomic "take this PRD if and only if nobody else has," no record of *who* holds it,
and no link between a claim and the branch the work lands on. With one operator this is invisible;
with two it causes duplicated builds and merge collisions.

## 2. Root cause

`set` is an unconditional write — there is no compare-and-acquire. Ownership was never modeled:
no claimant identity, no branch binding, no lease/TTL for recovering a claim whose holder vanished.

## 3. Scope

Add an atomic claim on top of the per-PRD state substrate (no new store).

- **Atomic claim via `O_EXCL`.** `prd_state.py claim <ID> --by <who> --branch <name>` creates
  `.orchestrator/prds/<ID>.claim` with `O_CREAT|O_EXCL` — the kernel guarantees exactly one
  creator wins; everyone else gets `EEXIST` → claim **denied** (exit nonzero). On success it also
  sets the PRD state to `claimed`. The claim file holds `{by, branch, ts}`.
- **Release.** `prd_state.py release <ID>` removes the claim (rename-aside — virtiofs-safe) so the
  next operator can take it.
- **Stale reclaim (lease).** A claim older than `--ttl` (default 24h) is *stale*; `claim … --force`
  may take over a stale claim (recording the new holder) but is **denied on a fresh** claim —
  force only overrides staleness, never a live owner.
- **List.** `prd_state.py claims` lists active claims (id · by · branch · age).
- **Branch binding.** The claim records the branch; `claim-check <ID> --branch <b>` verifies the
  working branch matches the claim (a handoff guard so work lands on the claimed branch).

## 4. Non-goals

- Not a distributed lock service — the atomicity is local-fs `O_EXCL` + a lease; good for a shared
  working tree / a serialized remote, not a multi-datacenter store.
- Not auto-releasing on process death (no daemon) — recovery is the TTL + explicit `--force`.
- Not changing how PRDs are built — only who may start one.

## 5. Acceptance tests (un-gameable)

- **AT-1 (exactly one winner).** 10 concurrent `claim PRD-X` → exactly 1 exit 0, 9 denied.
- **AT-2 (release frees it).** After `release`, a new `claim` succeeds.
- **AT-3 (identity + branch recorded).** `claim … --by alice --branch prd-x` → `claims` shows
  alice + the branch; the `.claim` file parses with those fields.
- **AT-4 (a live claim can't be stolen).** A second `claim` (even `--force`) on a FRESH claim is
  denied; the original holder is unchanged.
- **AT-5 (stale is reclaimable).** A claim with a `ts` older than the TTL is taken over by
  `claim … --force` and the new holder is recorded.
- **AT-6 (claim ⇒ state claimed).** A successful claim sets the PRD's `prd_state` to `claimed`.

All run locally; concurrency exercised with real parallel processes.

## 6. Architect review

1. **Removal.** Removes the unconditional "anyone may start any PRD"; replaces it with
   compare-and-acquire. Nothing else removed.
2. **Single source of truth.** The claim is one file per PRD (`<ID>.claim`) beside its state file;
   the `O_EXCL` create is the one atomic acquire — no second ownership record.
3. **Layering.** EXTENDS `prd_state.py` (same per-PRD substrate) with claim/release/reclaim — no
   parallel ownership store.
4. **Migration debt.** Additive — no existing data changes; absence of a `.claim` file = unclaimed.
5. **Constitution diff.** EXTENDS the "Shared state" section with the claim file + ops; cites the
   Per-PRD state entry from 018.

Passes — proceed to build.

## 7. Execution

Tests-first: `test/harness/test_claiming.py` committed failing, baselined, then the `prd_state.py`
claim ops to green. Commit locally as `PRD-019`. No DDL.
