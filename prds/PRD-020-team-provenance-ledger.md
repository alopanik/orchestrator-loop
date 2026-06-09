# PRD-020 — team provenance ledger

**User-visible-surface impact:** Yes — every ledger decision now records **who · which commit ·
which branch** alongside what/when, and the ledger surface shows it. Completes the spine
(shared-state → claims → provenance) and is the principal record 021 enforces on.

## 1. Problem (with proof)

The ledger records *what the gate decided* but not *who stood behind it*. A current entry:

```json
{"ts":"…","prd":"ci","decision":"pass","source":"ci-gate","checks":[…]}
```

With one operator that is fine — it was you. With a team, a collaborator reading the ledger cannot
tell **who** made the decision or **against which commit** it was made, so they cannot trust work
they did not personally watch. There is also no recorded principal for 021 (separation of duties)
to check planner ≠ verifier against.

## 2. Root cause

Provenance was never captured: the ledger writers (`stop_gate.py`, `ci_gate.py`) record the
decision and its checks but not the acting principal or the commit the decision applies to. The
log answers "what passed?" but not "whose word is this, on what code?"

## 3. Scope

Add provenance to every ledger entry, from both writers, and surface it.

- **Capture `{actor, commit, branch}`** on each entry. `actor` = `$OL_ACTOR` → `git config
  user.name` → `$USER` → `"unknown"`; `commit` = `git rev-parse --short HEAD`; `branch` =
  `git rev-parse --abbrev-ref HEAD`. Both `stop_gate.append_ledger` and `ci_gate.append_ledger`
  include it (inlined in each — `ci_gate` stays standalone/vendor-able).
- **Surface it.** `stop_gate.py ledger` prints `actor` + `commit` per decision, so the one-line
  ledger view answers "who decided this, on what commit."
- **Degrade gracefully.** Outside a git repo / with git absent, `commit`/`branch` = `"unknown"`
  and the gate still records and decides — provenance never crashes enforcement.
- **Constitution.** `ARCHITECTURE.md` ledger entry notes the provenance fields.

## 4. Non-goals

- Not *enforcing* planner ≠ verifier — that is 021 (this only records the principal it will read).
- Not identity/auth (no signing, no verified identity) — `actor` is a declared label, useful for
  audit and the 021 same-principal check, not a cryptographic guarantee.
- Not rewriting historical entries — provenance is additive, forward-only.

## 5. Acceptance tests (un-gameable)

- **AT-1 (fields present).** After a gate decision, the newest ledger line has non-empty `actor`,
  `commit`, and `branch`.
- **AT-2 (actor resolves + overrides).** With `OL_ACTOR=alice`, the entry's `actor == "alice"`;
  without it, a non-empty fallback is used.
- **AT-3 (commit is real).** In a git repo the entry's `commit` equals `git rev-parse --short HEAD`.
- **AT-4 (surface shows it).** `stop_gate.py ledger` output includes the actor and commit for a
  decision.
- **AT-5 (both writers).** A `ci_gate` decision AND a `stop_gate` decision each carry provenance.
- **AT-6 (graceful outside git).** In a non-git dir the gate still writes an entry with
  `commit == "unknown"` and exits normally (no crash).

## 6. Architect review

1. **Removal.** Removes the anonymous decision; nothing else removed.
2. **Single source of truth.** Provenance is captured at the one ledger-append path in each writer;
   no second provenance store. The ledger stays the one append-only log.
3. **Layering.** EXTENDS the existing entry shape with three fields + extends the existing ledger
   surface — no parallel audit log.
4. **Migration debt.** Additive; old entries simply lack the fields and the reader tolerates that.
5. **Constitution diff.** EXTENDS the "Decision ledger" entry; cites it. 021 will read `actor`.

Passes — proceed to build.

## 7. Execution

Tests-first: `test/harness/test_provenance.py` committed failing, baselined, then the provenance
capture + surface to green. Commit locally as `PRD-020`. No DDL.
