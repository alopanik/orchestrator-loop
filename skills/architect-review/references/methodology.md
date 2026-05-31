# Architect review — methodology + worked examples

The `SKILL.md` lists the five questions. This is how to answer them so they actually catch
things, plus the constitution + CI machinery that makes the answers stick, plus real catches.

The review exists because the cheapest place to remove a bad design is *before any code is
written*. A bad answer here is a redesign, not a warning — you send the PRD back to
`draft-prd`, you do not wave it through to `handoff-to-executor`.

## Why this review keeps a system lean

Systems don't rot in one big step; they rot one reasonable-looking addition at a time. Each
PR that "just adds" a table/view/flag alongside an existing concept forks the truth a little
more, until you have dozens of redundant stores nobody can reason about. The five questions
are a ratchet against that drift — every structural change has to *account for what it
removes and which single source it writes through* before it's allowed to land.

## The five questions, answered well

### 1. Removal — "what does this delete?"

A change that only *adds* while touching an existing concept is almost always layering.
Force the answer: what existing thing does this replace, and is that thing removed in this
same PRD? "Nothing, it's net-new" is only acceptable when the concept genuinely did not
exist before. If you're adding a second way to do an existing thing, the first way is the
removal — name it.

*Weak answer:* "N/A, this adds a new cache table."
*Strong answer:* "This replaces the per-request recompute; the old `recompute_on_read` path
is deleted in §3, not left as a fallback."

### 2. Single source of truth — "who owns this fact, and who writes it?"

Name the one store that owns the concept and the **one write-path** that writes it. SSoT is
about writes: two writers to one store is two truths waiting to diverge. If the PRD
introduces a second writer, that's a fork — redesign so there's one.

*Catch:* a PRD added an on-write trigger to keep a field "fresh" — but a batch job already
wrote that field. Two writers. The review forced a choice; the trigger was dropped and the
batch became the sole writer. (Two-writer fields are a recurring source of "the number
disagrees with itself" bugs.)

### 3. Layering — "are we editing the concept, or stacking on top of it?"

Default to editing the existing concept. A new layer is allowed only with a stated,
specific reason (a real boundary: a different lifecycle, a different owner, a different
consistency requirement). "It's easier" is not a reason — it's the failure mode.

*Catch:* a PRD proposed a downstream view that `COALESCE`s a corrected value over a known-bad
one. That's a band-aid layer hiding an upstream bug. The review rejected it and redirected to
fixing the upstream writer (build IN, not ON TOP).

### 4. Migration debt — "what gets cleaned up IN this PRD?"

Structural change ships its own cleanup. The change that adds the canonical thing also drops
what it supersedes. Any "tactical" patch (a temporary cast, a compatibility shim) is tagged
with the PRD number that will remove it, so it can't quietly become permanent. For anything
destructive (`DROP`/rename), confirm the migration is 2-stage soft-deprecate (add → backfill
→ swap reads → drop) or has a verified-deploy check on the readers.

*Catch:* a type-mismatch was bridged with a `::date` cast to unblock a pipeline. The review
required it be tagged `TODO(PRD-NNN)` and a follow-up PRD scheduled to unify the type at the
column level — so the cast is removed, not left as permanent debt.

### 5. Constitution diff — "does this EXTEND the canonical model, or FORK it?"

Check the change against the constitution doc (see below). If it extends the declared model,
cite the entry it touches. If it forks the model (a parallel table for an existing concept, a
second type for one logical column, a new store not in the doc), **stop and redesign.**

## The machinery that makes invariants stick

The review is only as strong as what enforces it between reviews. Two artifacts:

### The constitution (`ARCHITECTURE.md` or equivalent)

A single doc that, for **every** store, lists: its one purpose, its one write-path, and its
main readers — with the invariants at the top. The governing rule: **if a store isn't in the
constitution, it doesn't exist.** Every structural PRD updates this doc in the same change.
Typical invariants:

1. One concept → one store. No `_v2/_v3/_new/_old/_legacy/_copy/_tmp` siblings.
2. One logical column → one type, everywhere.
3. One write-path per store (named in the doc).
4. Views are read-only presentation — no cross-source `COALESCE`/fallback forks.
5. No store without both a writer and a reader; dead stores are dropped.
6. Trained-model internals are artifacts (files), not stores.
7. Structural change ships its own cleanup in the same PRD.

### The CI guardrail (`~~ci`)

A small lint, scoped to the **changed** files in the PR diff (so legacy debt doesn't trip
it), that **fails the build** on banned patterns: a `_v2`-style table name; a column added
with the wrong type for a unified logical field; a view whose body `COALESCE`s across two
different source stores (fork heuristic — flag for human review); a new store not listed in
the constitution. Ship it with one passing fixture and one failing fixture per rule.

*Why both:* the doc is the rule; CI is the rule-keeper that doesn't get tired. A rule no
machine enforces erodes the week everyone's busy — that's exactly how a schema sprawls back
toward dozens of redundant tables.

## How to run it

Answer all five in the PRD's review section. If a CI guardrail exists, confirm the change
would pass it. Any "stop and redesign" answer returns the PRD to `draft-prd`. Only a clean
sheet proceeds to `handoff-to-executor`.
