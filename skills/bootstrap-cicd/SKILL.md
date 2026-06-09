---
name: bootstrap-cicd
description: >
  Drop the existing orchestrator-loop gate into a repo as `~~ci` — one command scaffolds a CI
  workflow plus a pre-push fast gate that run the SAME checks (no re-listed set), with an
  idempotent managed block merged into `CLAUDE.md`. Use when the user says "set up CI", "add a
  CI gate", "bootstrap ci/cd", "make this repo CI-gated", "enforce the gate on the remote", or
  is onboarding a repo that has no CI yet.
---

# bootstrap-cicd

Arc 1 made the gate enforce locally; this relocates it. The Stop gate fires only at one
operator's turn-end on one machine — push directly and nothing runs, and a collaborator never
sees it. CI is not a new capability: it is **the same gate, relocated to a remote nobody can
bypass and everyone's commits pass through.** This skill scaffolds that, parameterized by
`~~ci` / `~~vcs`, so any repo the loop points at starts gated by default.

> **Provider bindings, the ratchet rationale, and worked output:** `references/methodology.md`.

## The one rule that keeps this on-thesis

The checks live **once**, as data, in `.orchestrator/ci-gate.json`. The workflow and the pre-push
hook both invoke the single engine `hooks/ci_gate.py`; they never re-list the checks. Re-listing
them in CI config forks the source of truth — the failure mode this framework punishes hardest.
CI is a new *runner* of the existing gate, not a new gate.

## Procedure

1. **Scaffold.** Run the generator, bound to the project's connectors:

   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/bootstrap-cicd/scaffold.py" install \
       --ci <your ~~ci provider> --vcs <your ~~vcs> --repo "$CLAUDE_PROJECT_DIR"
   ```

   It vendors the engine if absent, emits the workflow (or a portable runner for a provider
   without a first-class template), installs `.githooks/pre-push`, seeds `ci-gate.json` if
   missing, and merges an idempotent block into `CLAUDE.md`. Re-running is safe — the managed
   block is replaced in place, never duplicated, and nothing outside the sentinels is touched.

2. **Declare the standing checks.** Edit `.orchestrator/ci-gate.json` to the repo's real gate:
   each entry is `{"name", "cmd", "fast"}`. `fast: true` marks the cheap deterministic subset the
   pre-push hook runs; the full set runs in `~~ci`. Verify locally with
   `python3 hooks/ci_gate.py` (and `--fast`).

3. **Ratchet honestly — never on an unproven number.** If you gate on a metric, baseline it
   through the discrimination guard:

   ```
   python3 .../scaffold.py ratchet-baseline --signal "<real check>" --control "<ablated check>" \
       --name <metric> --repo "$CLAUDE_PROJECT_DIR"
   ```

   It **refuses** unless the ablated control actually moves the signal — you cannot ratchet a
   number the control can't reproduce as broken. A rising metric after the rules shrink is "too
   good" until proven; the guard is that proof.

4. **Activate deliberately.** Turn on the local fast gate with `git config core.hooksPath .githooks`
   (left to the user — never set silently). CI activates on the next push — **and a push is the
   owner's release call**, so stop there for sign-off; do not push to activate it yourself.

## Non-goals

This skill scaffolds and verifies locally; it does not push, enable remote settings, or manage
branch protection (that is the multi-hand release gate). It binds to `~~ci`/`~~vcs` by category
only — no provider is hardcoded in the framework.
