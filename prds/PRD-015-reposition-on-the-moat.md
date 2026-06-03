# PRD-015 — Reposition on the moat (assume the agent cheats)

**User-visible-surface impact:** Yes — README leads with the anti-cheat thesis + the new
self-test-backed number, and verify-handback is framed as **spec-compliance / drift detection**
(the gap the market names).

## 1. Problem (with proof)

The field competes on the *planning* half — BMAD-METHOD's role-agents, Task Master's task
decomposition, spec-kit, the 270-tool packs, Claude Code Agent Teams — on the premise that the
agent is honest. Their own reviewers name the gap nobody fills: *"automatic spec-to-implementation
verification,"* and no native *drift detection* or *guaranteed spec compliance*. Our README states
"the verifier is the moat" but buries it under loop mechanics and doesn't claim the one thing no
competitor can: **we assume the executor cheats, and we catch it — with a reproducible number.**
We're under-selling the only defensible wedge.

## 2. Root cause

Positioning leads with *process* (the loop, the five roles) rather than the differentiated
*outcome* (a lying executor gets caught). The verifier is described in generic QA terms, not in the
market's terms (spec-compliance / drift).

## 3. Scope

- **`README.md`** — lead the value prop with "assume the agent might fake done — prove it's
  caught"; surface the **anti-cheat catch-rate** (PRD-014, self-test-backed) beside the existing
  core proof; add a compact competitive contrast (planning tools vs. this, with the named gap);
  reframe the verifier section as **spec-compliance / drift detection**. Keep the honest framing
  (self-test + ablation; no fabricated absolute number).
- **`skills/verify-handback/SKILL.md`** — one-line framing that the job is spec-compliance: "did the
  diff satisfy the PRD's acceptance against reality, or did it drift?" (no behavior change; naming
  the gap).
- **`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`** — refresh the description to
  lead with the verification/anti-cheat wedge; bump `version` to `0.7.0` in BOTH (the SSoT pair).
  **No push** — the version bump only ships when the owner pushes.

## 4. Non-goals

- No fabricated metrics; every number traces to a runnable command.
- Not rewriting the loop docs — only the lead/positioning + the verifier framing.

## 5. Acceptance tests

- **AT-1:** README's first screen names the anti-cheat thesis + a runnable proof command; no claim
  lacks a command behind it.
- **AT-2:** the competitive contrast names the planning-tool category and the verification gap.
- **AT-3:** verify-handback names spec-compliance/drift.
- **AT-4:** `version` identical in both manifests (grep both); structure stays valid.
- **AT-5:** no broken internal links / asset refs introduced (every relative ref in README resolves
  in the tree).

## 6. Architect review

1. **Removal.** Replaces the process-led lead with an outcome-led one; removes the under-sell.
2. **SSoT.** Numbers come from the harness (PRD-014), not hand-typed; version stays the one pair.
3. **Layering.** Edits existing docs; no new doc.
4. **Migration debt.** README + skill + manifests ship together.
5. **Constitution diff.** None (docs already catalogued).

## 7. Execution

Commit as `PRD-015` once AT-1…AT-5 pass. Version bumped locally; **the push is the owner's release
call.**
