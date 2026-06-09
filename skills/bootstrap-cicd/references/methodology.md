# bootstrap-cicd — method, provider bindings, and the ratchet rationale

## Why this exists (the thesis in one paragraph)

orchestrator-loop's Arc 1 built a real enforcement gate, but every piece of it runs on one
operator's machine and fires only at that operator's turn-end (`hooks/stop_gate.py` is a Claude
Code `Stop` hook). That makes the moat **bypassable** (push without running the agent) and
**unshared** (a collaborator's commits never hit it). CI fixes both by relocating the *same*
gate to a remote nobody controls. The engine and the checks do not change — only *where* they
run. This skill is the generator that performs the relocation.

## The single source of checks

The standing checks are data: `.orchestrator/ci-gate.json`, a list of `{name, cmd, fast}`. One
engine, `hooks/ci_gate.py`, reads and runs them (fail-closed, ledger-recorded). The CI workflow
and the pre-push hook are both thin callers of that engine. **Nothing re-lists the checks in CI
config.** If you ever find yourself pasting `pytest` or a check command into a workflow YAML,
stop — add it to `ci-gate.json` instead. The harness test `test_scaffold.py` (AT-1) fails the
build if a generated workflow contains an inline check.

## Provider bindings (`~~ci` / `~~vcs`)

`scaffold.py` knows exactly one provider-specific thing: how to emit the caller.

| `~~ci` value | emitted artifact | how it calls the engine |
|---|---|---|
| `github` | `.github/workflows/orchestrator-gate.yml` | `run: python3 hooks/ci_gate.py` |
| anything else (`generic`) | `orchestrator-gate.sh` (portable POSIX) | point your provider at `sh orchestrator-gate.sh` |

`~~vcs = git` installs `.githooks/pre-push`. Adding GitLab CI / CircleCI / Bitbucket later means
adding one more caller template here — never a second copy of the checks. The framework prose
(`SKILL.md`, `GUARDRAILS.md`) names no provider; only this generator binds them, by the `--ci`
flag.

## On a clean CI runner the plugin is not installed

A CI runner checks out the repo and nothing else — `${CLAUDE_PLUGIN_ROOT}` does not exist there.
So `scaffold.py` **vendors** `hooks/ci_gate.py` into the target repo (if absent) and the workflow
calls it by repo-relative path. The engine is deliberately standalone (no plugin imports) for
exactly this reason. In the plugin's own repo the file is already the canonical one, so vendoring
is a no-op.

## The ratchet, and why baseline-trust is mandatory

A ratchet is a floor a metric may not regress below. It is only as honest as the baseline. This
repo's own app-profile is one long warning that baselines get contaminated — "a *rising*
catch-rate after we shrink the rules is too good until proven"; "a perfect board is suspect." So
`scaffold.py ratchet-baseline` will not record a floor unless an **ablation control** demonstrates
the signal actually discriminates: it runs the real signal and the ablated control, and refuses
unless the signal passes while the control fails. You cannot ratchet a number you have not proven
is real. Once baselined, `ci_gate.py` folds the validated signal in as a standing check, so a
later regression in it fails CI like any other red check.

## Install is a merge, not a clobber

The `CLAUDE.md` block is delimited by `ORCHESTRATOR-LOOP:CI:BEGIN/END` sentinels and replaced in
place on re-run (idempotent), so the generator can be re-run as the repo evolves without
duplicating or disturbing hand-written content. Activation of the local hook
(`git config core.hooksPath .githooks`) is left to the user, and CI activates only on a push —
which is the owner's release call.
