# PRD-005 — Guard the tests (tests-first + tamper check)

**User-visible-surface impact:** Yes — the loop now requires acceptance tests committed *failing*
before implementation, and the verifier rejects a handback where the tests were edited to pass.

## 1. Problem (with proof)

The framework's whole premise is "un-gameable acceptance tests" — but the easiest way to game
them is untouched: **edit the test until it's green.** Nothing in the loop checks that the test
the executor passed is the same test that was specified. `draft-prd` says tests must be
"un-gameable," yet `verify-handback` re-runs them without ever asking *were these tests altered?*
A green run proves nothing if the executor rewrote the assertion. There is also no requirement
that a test was ever *red* — a test that passes vacuously (asserts nothing, or was written after
the code) looks identical to a real one at handback.

## 2. Root cause

Tests are treated as fixed truth, but they live in the same diff the executor controls. With no
*baseline* — no committed, failing version of the test from before implementation — there is
nothing to compare the handback against, so neither tampering nor "never actually failed" can be
detected.

## 3. Scope

Build on PRD-004's gate (the tamper check becomes one of its enforced checks):

- **`test/harness/check_tests.py`** (Python 3, stdlib + git):
  - `baseline --cmd "<test cmd>" --tests <glob>...` — assert the test command **fails now**
    (red); if it already passes, error ("tests must be committed failing first"). Record HEAD as
    the baseline ref + the test globs + cmd to `.orchestrator/tests.json`.
  - `verify` — read `.orchestrator/tests.json` and enforce BOTH: (a) **no tamper** —
    `git diff --name-only <baseline> HEAD -- <globs>` is empty (test files unchanged since the
    failing baseline); (b) **green now** — the test cmd passes at HEAD. Exit 0 only if untampered
    AND now-green; nonzero (with the offending files / the still-red result) otherwise.
- **Compose with the gate:** the gate manifest's checks include `check_tests.py verify`, so the
  Stop hook (PRD-004) refuses to end the turn if tests were altered or aren't truly green.
- **`test/harness/test_check_tests.py`** — spins up a throwaway git repo and exercises the happy
  path (red baseline → impl makes it green, test unchanged → verify passes) and the tamper path
  (test file edited after baseline → verify fails).
- Wire `draft-prd` (write tests first), `handoff-to-executor` (record the failing baseline before
  the executor implements), `verify-handback` (run `check_tests.py verify`). Update `ARCHITECTURE.md`.

## 4. Non-goals

- Not mandating a specific test framework — the test cmd + globs are declared per project.
- Not preventing *legitimate* test edits forever — only between the failing baseline and the
  handback for one PRD (a real test change is its own committed step with its own baseline).

## 5. Acceptance tests (un-gameable)

- **AT-1 (tamper rejected — the headline):** given a baseline ref where a test file was committed
  failing, a handback that **edits that test file** to pass is rejected by `check_tests.py verify`
  (nonzero, names the changed file). Proven in a throwaway git repo.
- **AT-2 (legit pass accepted):** baseline red → implementation makes it green **without** touching
  the test file → `verify` exits 0.
- **AT-3 (must be red first):** `check_tests.py baseline` errors if the test command already passes
  before implementation (a test that never failed isn't a guard).
- **AT-4 (green-now required):** if the test files are untouched but the suite is still red at
  HEAD, `verify` fails (an untampered but failing handback is not done).
- **AT-5 (gate-composed):** with `check_tests.py verify` in the gate manifest, a tampered handback
  makes the Stop hook block the turn (exit 2) — enforcement, not advice.

## 6. Architect review

1. **Removal.** Removes the blind spot "a green test is trusted regardless of whether it was
   edited"; replaces it with a baseline comparison.
2. **SSoT.** One tests manifest (`.orchestrator/tests.json`), one writer (`check_tests.py
   baseline`); the tamper/green logic lives in one place and is *consumed* by the PRD-004 gate
   rather than duplicated.
3. **Layering.** Extends the existing gate (PRD-004) with one more check — not a parallel
   enforcement path.
4. **Migration debt.** Engine + tests + skill wiring ship together.
5. **Constitution diff.** Extends `ARCHITECTURE.md` (tests manifest artifact; check engine). No fork.

## 7. Execution

Commit to `master` as `PRD-005` once AT-1…AT-5 pass (AT-1/AT-2/AT-3/AT-4 in the throwaway-repo
test; AT-5 via the gate). No push.
