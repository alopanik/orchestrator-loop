# PRD-024 — README refresh: center the value prop, fold in Arc 2

**User-visible-surface impact:** Yes — the public README. Keeps the anti-cheat/verifier-moat lead;
sharpens the contrast vs other orchestrator loops now that Arc 2 makes the moat *unbypassable on
the remote* and *safe across a team*; refreshes every stale count to a true, runnable figure.

## 1. Problem (with proof)

The README predates Arc 2 and now mis-states the project. Verified in-repo:

```
README badge: tests 47/47       actual: 149 passing assertions across 15 test files
README: "7 skills"              actual: 9 (added bootstrap-cicd, gated-migration)
README architecture tree        omits every Arc 2 component (ci_gate, prd_state, roadmap_status,
                                check_ledger, check_executor, check_separation, release, migrate)
README version 0.7.0            release is 0.8.0
```

It also *under-sells the differentiation*: it argues "we verify, they plan," but the strongest
contrast is now that orchestrator-loop's enforcement **holds where it matters** — on a remote
nobody can bypass (CI), and when multiple collaborators/agents share the repo — which no
planning-first loop addresses at all.

## 2. Root cause

The README was last rewritten at 0.7.0 (PRD-015) before the Arc-2 work existed; counts and the
component inventory drifted, and the positioning never absorbed the "across people, machines, and
time" expansion.

## 3. Scope

- **`README.md`** — (a) refresh badges/hero to 0.8.0 and the **true** test count; (b) keep the
  anti-cheat lead, add one line that the gate now runs unbypassably on the remote and the loop is
  team-safe; (c) sharpen the "How it's different" contrast with the Arc-2 wedge; (d) add a compact
  "Holds across people, machines & time" section (CI relocation, claims, provenance, separation,
  executor reliability, gated migration) — each tied to a file/command; (e) refresh the
  architecture tree + footer counts to current reality (9 skills, the new harness tools).
- **Numbers are real or they don't go in.** Every count traces to a command (the framework's own
  rule); the deterministic self-test (22 fixtures) stays the stable headline proof.

## 4. Non-goals

- Not rewriting the voice or the proof methodology — only the lead's breadth, the contrast, the
  inventory, and the counts.
- Not the version bump itself (that's release prep) — but the README names the release version.
- No new fabricated metric; no claim without a runnable command behind it.

## 5. Acceptance tests (un-gameable)

- **AT-1:** every numeric claim in the README is reproducible — `9` skills (`ls skills`), `149`
  test assertions / `15` files (run the kit), `22` self-test fixtures (`run.py --self-test`), `16`
  scenarios. No number without a source.
- **AT-2:** the first screen still names the anti-cheat thesis AND now names the unbypassable-remote
  / team-safe expansion.
- **AT-3:** the "how it's different" contrast names the planning-loop category and the Arc-2 wedge
  (enforcement on the remote + across a team), not just "we verify."
- **AT-4:** the architecture tree lists the Arc-2 components and 9 skills; no relative link or asset
  ref is broken (every `](path)` and `src=` resolves in the tree).
- **AT-5:** version references read `0.8.0` (hero cache-bust `?v=0.8.0`, badge, footer).

## 6. Architect review

1. **Removal.** Removes the stale counts + the under-sell; replaces with current, sourced figures.
2. **SSoT.** Counts come from the kit / `ls`, not hand-invented; version is the manifest pair.
3. **Layering.** Edits the existing README; no second doc.
4. **Migration debt.** README + the inventory ship together; no dangling references.
5. **Constitution diff.** None (README already catalogued in `ARCHITECTURE.md` Docs).

Passes — proceed.

## 7. Execution

Edit `README.md`; verify AT-1…AT-5 (counts reproduced, links resolve). Commit locally as
`PRD-024`. Version references anticipate the `0.8.0` bump done in release prep.
