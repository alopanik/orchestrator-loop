# Roadmap — methodology + worked example

The `SKILL.md` gives the spine. This is the full method and a worked example. Roadmapping is
role 3 (run the roadmap): a broad goal arrives, and you convert it into a *sequence the
executor can chew through* without you re-planning at every step.

## The principle that governs everything here

**Plan against reality, not against assumptions.** The single most common roadmap failure is
decomposing the goal from imagination instead of from the live system. Before you write a
single roadmap entry, you go look: query the `~~database`, read the repo through `~~vcs`,
check what's actually deployed on `~~hosting`, run the thing and watch it behave. The gap
between *what is* and *what should be* is the roadmap. You cannot see that gap from the goal
alone.

## Method

### 1. Anchor on the mission, in one sentence

Restate the goal and its success condition so concretely that you could later test "did we
get there?" "Make the product better" is not anchorable. "A user can do X and the system
proves it by Y" is. If the goal is genuinely ambiguous in a way that *changes the
decomposition*, ask 1–3 focused questions. Otherwise proceed on the best reading and state
it explicitly so the owner can correct you cheaply.

### 2. Discover the current state — forensically

This is discovery, not a glance. Establish, with evidence:

- **What exists.** The real schema, the real modules, the real jobs — from the live system,
  not the docs (docs drift). Note where one logical concept already lives in two places; that
  is debt the roadmap must retire, not route around.
- **What's broken or load-bearing.** Run a freshness/health check even if it's "out of
  scope" — a silently-frozen pipeline or a contaminated data store changes the whole plan.
- **What's actually true vs. what a dashboard claims.** Apply the epistemics: if a monitor
  shows an implausibly good number, distrust the instrument before you build a roadmap on top
  of its story.

Write the gap down. The gap is the input to decomposition.

### 3. Decompose top-down, then bottom-up

Break the goal into subsystems (top-down), then into the smallest units that each leave the
system **working** (bottom-up). A unit is PRD-sized when it has:

- exactly one clear outcome,
- an acceptance test you can verify against reality, and
- a bounded blast radius (you can name every store/module it touches).

If a unit has two outcomes, split it. If you can't write its acceptance test, you haven't
discovered enough yet — go back to step 2.

### 4. Order by dependency and risk

Lower number ships first — **the number is the execution order.** Within that:

- Foundational/plumbing work that everything else depends on goes first.
- **Data-integrity and measurement work goes before anything that consumes the numbers.** You
  cannot decide what to build next on top of numbers you haven't proven are real. A roadmap
  that sequences "use the metric" before "prove the metric is trustworthy" is inverted.
- Reversible/low-risk before irreversible/high-risk.
- Flag every unit gated on another (a data migration, a deploy, an external job, a long
  backfill). A gate is a dependency edge; draw it.

### 5. Write the roadmap as a living table

One row per PRD: `# | scope (one line, outcome not implementation) | depends-on |
user-visible? | risk`. Save it to the app's docs location and update it as PRDs land — it is
a living document, not a one-time artifact.

### 6. Reconcile, don't accumulate

If the new work overlaps existing stores/functions/UI, the roadmap must say what gets
**removed or merged**, not only what's added. Layering is the failure mode; building IN is
the goal. A roadmap that only ever adds rows is quietly growing the thing you'll have to
untangle later.

## Worked example (app-agnostic)

**Broad goal:** "Our analytics product shows users a 'quality score' for each item, but
users say the scores feel random. Make the scores trustworthy and useful."

**Bad roadmap (planned from imagination):**
1. Add a nicer score visualization.
2. Add score filtering.
3. Improve the scoring model.
4. Add score explanations.

This is inverted and assumption-driven: it dresses up and consumes a number nobody has shown
is real.

**Discovery (step 2) finds:**
- The score is written by *two* different jobs (a nightly batch and an on-write trigger) that
  disagree — two write-paths, two truths. (Violates one-write-path.)
- A "score accuracy" dashboard claims 95% accuracy — but it's computed on the same rows the
  model trained on (in-sample; leaked). The instrument is lying.
- For 12% of items the score is computed from a field that's null at write time and
  backfilled later, so the stored score is stale.

**Good roadmap (planned from reality):**

| # | scope (outcome) | depends-on | user-visible? | risk |
|---|---|---|---|---|
| 1 | Collapse scoring to one write-path; the other job is removed | — | no (plumbing) | med |
| 2 | Replace the in-sample accuracy dashboard with an out-of-fold metric; quarantine the old one | 1 | no | low |
| 3 | Fix the stale-field race so the stored score reflects final inputs | 1 | no | med |
| 4 | Establish the honest accuracy baseline (OOF, per-segment, FDR-gated) — is the score even good? | 2,3 | no | low |
| 5 | *Only if 4 shows real signal:* score explanations + filtering UI | 4 | yes | low |

Note what the discovery bought: items 1–4 are all "prove the number is real / make it real"
and must precede the UI work. Item 5 is explicitly *gated on the evidence from item 4* — if
the score has no real signal, the roadmap changes (fix the model first, per the no-band-aids
rule) rather than shipping explanations for noise.

## Output

A numbered roadmap (lowest = next), each entry ready to feed `draft-prd`. Hand the owner the
table and name the single next PRD to write. Do **not** start coding from the roadmap — each
unit still goes through `draft-prd` → `architect-review` → `handoff-to-executor` →
`verify-handback`.
