# PRD-022 — multi-hand release gate (owner sign-off, enforced)

**User-visible-surface impact:** Yes — a release (a version bump that ships) now requires a
recorded **owner** sign-off, enforced by `release.py check`; `bootstrap-cicd` emits a release
workflow that runs it. Extends 016 (CI) + builds on the provenance/owner ideas from 020.

## 1. Problem (with proof)

The app-profile says a push is a release and "user sign-off required, never autonomous" — but that
is a *convention*, enforced only by an agent choosing to obey it. `CLAUDE.md`:

> "A push to the remote is a RELEASE — user sign-off required, never autonomous."

With one trusted operator that holds. With multiple committers, **anyone can bump the version in
both manifests and push** — nothing mechanically requires the *owner's* sign-off on the release.
The "release = owner sign-off" rule has no teeth.

## 2. Root cause

Releasing is just "bump version + push," and nothing ties a version bump to an authorized owner's
approval. There is no recorded sign-off and no check that a shipped version carries one.

## 3. Scope

Make owner sign-off a recorded, checked precondition of a release. (Branch protection itself is a
remote setting — documented; the mechanical enforcement is the check, runnable in CI / pre-push.)

- **`test/harness/release.py`** — `signoff --by <owner> [--version V]` records
  `.orchestrator/release-signoff.json` = `{version, by, ts, commit}`, but **refuses a non-owner**.
  `check` fails closed unless the current manifest version is signed off **by an authorized owner**
  for that exact version. `status` prints version · signed-off · owners.
- **Authorized owners (SSoT, no new hardcoded identity).** From
  `.orchestrator/release-policy.json` `{"owners":[…]}` if present, else the **marketplace
  manifest** `owner.name`. So "owner" derives from what the repo already declares.
- **`bootstrap-cicd` scaffold emits a release gate.** `scaffold.py install` also writes a release
  workflow (`~~ci=github` → `.github/workflows/orchestrator-release.yml`) that runs
  `release.py check`; `references/methodology.md` documents the branch-protection setup (require
  the gate, restrict who pushes the release branch).
- **Release-time, not a standing dev check.** `release.py check` gates a *release* (a version
  bump), so it is NOT added to the standing `ci-gate.json` — a pending, un-signed bump is the
  *correct* state between "built" and "released," and must not block ordinary dev commits.
- **Constitution.** `ARCHITECTURE.md` (Distribution) catalogs `release.py` + the signoff/policy
  files and states the new release invariant.

## 4. Non-goals

- Not cryptographic identity — `by` is a declared owner label (as with 020's provenance); this
  stops an *accidental* or *non-owner* release, not a determined impersonator.
- Not configuring the remote (GitHub branch protection is a UI/API action) — the skill documents
  it; the check is what's mechanical.
- Not auto-signing or auto-pushing — sign-off is the owner's deliberate act.

## 5. Acceptance tests (un-gameable)

- **AT-1 (unsigned bump blocked).** Manifest at a new version with no matching signoff →
  `release.py check` fails closed and names the pending version.
- **AT-2 (owner signoff passes).** `signoff --by <owner>` for the current version → `check` passes.
- **AT-3 (non-owner rejected).** `signoff --by <stranger>` is refused (no record written); and a
  fabricated signoff whose `by` is not an owner is rejected by `check`.
- **AT-4 (no pending release passes).** When the signed-off version equals the manifest version,
  `check` passes (nothing to release).
- **AT-5 (scaffold emits the release gate).** `scaffold.py install --ci github` writes a release
  workflow that invokes `release.py check` (and contains no inline approval logic).
- **AT-6 (owners resolve from policy then marketplace).** With a `release-policy.json` its owners
  win; without it, the marketplace `owner.name` is the authorized owner.

## 6. Architect review

1. **Removal.** Removes the unenforced "release = owner sign-off" convention; replaces it with a
   recorded, checked precondition. Nothing else removed.
2. **Single source of truth.** Owners derive from one place (policy file → else marketplace owner);
   the signoff is one record; the version SSoT stays the manifest pair. No second owner list.
3. **Layering.** EXTENDS `bootstrap-cicd` (a second emitted workflow + one check); does not fork the
   gate or the manifests.
4. **Migration debt.** Additive — no signoff yet means `check` reports "pending" (correct). The repo
   self-installs the release gate in release prep.
5. **Constitution diff.** EXTENDS the Distribution section; cites the version-pair invariant and the
   `~~ci` scaffolder (016).

Passes — proceed to build.

## 7. Execution

Tests-first: `test/harness/test_release_gate.py` committed failing, baselined, then `release.py`
+ the scaffold release-workflow emission to green. Commit locally as `PRD-022`. No DDL. The actual
release (bump + sign-off + push) stays the owner's action.
