---
name: handoff-to-executor
description: >
  Package a reviewed PRD into a self-contained brief for the coding executor and dispatch it.
  Use after architect-review passes, when the user says "hand this to the executor / Claude
  Code", "dispatch the PRD", or is ready to build. You plan + verify; the executor writes code.
---

# Handoff to executor

The executor (`~~executor`) writes the code; you do not. The handoff is a self-contained brief.

## Rules

- **Self-contained.** The executor must build from the brief alone. If `~~executor` can read
  the repo (e.g. a coding agent with filesystem access), the brief is a short prompt that
  points to the PRD file path + the branch name. If it cannot read your docs, inline the full
  PRD body in the message.
- **One PRD per handoff**, in numbered order (lowest first). Do not stack the next brief while
  one is in flight — wait for the handback first.
- **Commit policy is explicit, every time.** State whether the executor may commit + push or
  must stop for review. Default for a completed PRD with green acceptance: commit + push.
  Speculative/ad-hoc work waits for sign-off. **The executor commits and pushes — never tell
  the owner to push the branch.**
- **Forbid out-of-scope commits.** Say it explicitly in every brief: do not commit anything
  outside this PRD's scope. A global no-commit rule does not auto-propagate to a sub-agent.
- **Branch + acceptance.** Name the branch. Restate the acceptance tests. Require the executor
  to run them and report before/after numbers.

## After dispatch

Wait for the handback. Do not start the next PRD. When the executor reports done, do NOT
accept it — run `verify-handback`. The executor's "done" is a claim to be tested, not trusted.
