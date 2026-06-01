# PRD-003 — Make the verifier independent (fresh subagent)

**User-visible-surface impact:** Yes — `verify-handback` changes from "the orchestrator checks
in its own context" to "a fresh subagent verifies from a whitelisted bundle." No change to the
catch-rate behavior (guarded by PRD-001).

## 1. Problem (with proof)

The verifier shares the planner/builder's context. `skills/verify-handback/SKILL.md` says
"re-establish every claim yourself" but nothing makes the verifier *blind to the build story*.
Today the same agent that wrote the PRD (problem, root cause, "here's why it works") and/or
built the diff also verifies it — in the same context window. Quoting the current skill:

```
This is role 2 (QA). The executor's "done" is a claim. Re-establish every claim yourself,
against reality — as an adversary trying to break the claim, not a co-author hoping it worked.
```

That's the right intent, but it's unenforced: a verifier that can see the builder's rationale
inherits its framing and its blind spots. Confirmation bias is strongest exactly when the same
mind both built and checks — "of course it works, here's the reasoning" is the failure mode.
There is currently **no mechanism** that restricts what the verifier sees.

## 2. Root cause

Verification is specified as a *mindset* ("be an adversary") rather than an *isolation boundary*.
Nothing constructs a verifier context from a restricted input set, so the build reasoning is
always in scope. Independence has to be structural, not aspirational.

## 3. Scope

- **Rewrite `verify-handback` to run as a fresh subagent** spawned with a **whitelisted bundle**
  and nothing else. The bundle contains ONLY: (a) the **diff** under review, (b) the **acceptance
  tests / criteria** (the un-gameable checks), (c) the **app-profile facts + sanity bounds**
  (`~~database`, impossible values, etc.). It explicitly EXCLUDES: the PRD's problem/root-cause
  narrative, any planning/design reasoning, the build log, and the executor's self-report.
- **`skills/verify-handback/SKILL.md`** gains a "Run as an isolated subagent" section: how to
  assemble the bundle, the forbidden list, and the rule that the verifier reports only from the
  bundle + reality (the connectors), never from build context.
- **`references/methodology.md`** documents the bundle spec + why each exclusion exists.
- **`test/harness/check_isolation.py`** (+ `run.py --check-isolation FILE`): given a verifier
  bundle, assert it contains the three allowed parts and NONE of the forbidden markers (e.g.
  `## Root cause`, `## Problem`, "why it works", "I implemented", "the executor reports",
  "build log", "rationale"). Ships with `fixtures/bundle_clean.md` (passes) and
  `fixtures/bundle_leaky.md` (fails) for a self-test.
- Update `ARCHITECTURE.md` (verify-handback = isolated subagent; the bundle is the boundary).

## 4. Non-goals

- Not changing the forensic checks themselves (three signals, per-partition, freshness) — only
  *what context the verifier is allowed to see* while it runs them.
- Not requiring Agent Teams (a later item); a one-shot fresh subagent is the mechanism, with the
  orchestrator-as-its-own-verifier still bound by the same bundle discipline in zero-setup.

## 5. Acceptance tests (un-gameable)

- **AT-1 (isolation is provable):** `run.py --check-isolation fixtures/bundle_clean.md` exits 0;
  `--check-isolation fixtures/bundle_leaky.md` (same bundle + PRD rationale/build log appended)
  exits nonzero, naming the leaked markers. The boundary is mechanically checkable, not a promise.
- **AT-2 (fresh-subagent mandated):** `verify-handback/SKILL.md` specifies spawning a fresh
  subagent from the whitelisted bundle and the forbidden-context list; a grep confirms the
  section exists and names the three allowed inputs + the exclusions.
- **AT-3 (no regression):** the PRD-001 self-test still passes and the core-scenario catch-rate
  is unchanged (independence must not make the verifier worse). Demonstrated: a fresh subagent
  given only a diff-with-planted-defect + criteria still catches it.
- **AT-4 (SSoT):** one bundle assembler, one isolation guard; `ARCHITECTURE.md` updated; no
  forked verifier path.

## 6. Architect review

1. **Removal.** Removes the implicit "verifier sees everything" default; replaces in-context
   self-verification with a bounded bundle.
2. **SSoT.** One verifier bundle spec, one isolation guard. The bundle is the single definition
   of "what the verifier may see."
3. **Layering.** Edits `verify-handback` in place + adds the guard; not a parallel verifier.
4. **Migration debt.** The guard + fixtures + skill rewrite ship together; nothing deferred.
5. **Constitution diff.** Extends `ARCHITECTURE.md` (verify-handback isolation boundary). No fork.

## 7. Execution

Commit to `master` as `PRD-003` once AT-1, AT-2, AT-4 pass and AT-3 shows no regression. No push.
