# PRD-007 — Escape hatch for trivial changes

**User-visible-surface impact:** Yes — a one-line, reversible, single-file change may skip the
full PRD ceremony, but it still hits the verify gate. A migration/schema change can never qualify.

## 1. Problem (with proof)

The loop applies the *same* ceremony to every change: `GUARDRAILS.md` says "Every non-trivial
change rides it: codify the rules, place the work in the numbered roadmap, write a PRD, hand it
to `~~executor`, then independently verify." But it never defines **trivial**, so in practice a
typo fix in a README or a one-line copy change drags the full roadmap→PRD→architect-review→handoff
weight — or, worse, people skip the loop entirely for "small stuff" and that becomes the hole the
gate doesn't cover. Either way the framework loses: ceremony theater, or an ungated side door.

## 2. Root cause

"Non-trivial" is asserted but never operationalized — there's no test for what counts as trivial,
and no fast path that drops the *planning* ceremony while keeping the *verification* gate. So the
choice is all-or-nothing, and the easy escape (skip everything) also skips the gate.

## 3. Scope

- **`test/harness/classify_change.py`** (Python 3, stdlib): given a diff (`--file <diff>` or
  `--git [ref]`), decide fast-path eligibility. **Trivial** = exactly one file changed, ≤ 3
  changed lines, not a file deletion, and **no** migration/schema/DDL/destructive markers
  (`DROP|ALTER … TABLE/COLUMN`, `CREATE TABLE`, `TRUNCATE`, `RENAME COLUMN`, a `migrations/`
  path, a `.sql` file, "schema"). Prints a verdict + reasons; exit 0 if trivial, 1 if full
  ceremony required. **Migrations never qualify, regardless of line count.**
- **The gate stays intact.** The fast path skips roadmap + full PRD + architect-review — NOT the
  PRD-004 verify gate. Document that a trivial change still arms/clears the gate (even if the only
  check is "the one assertion this change implies").
- **`GUARDRAILS.md` (PRD discipline):** define the trivial fast path + its hard exclusion
  (migrations/structural never trivial), and that the gate is never skipped.
- **`skills/go` + `skills/draft-prd`:** when a change is classified trivial, take the fast path
  (make the change, run the gate, done) instead of drafting a full PRD.
- **`test/harness/test_classify_change.py`** — synthetic diffs for each case.
- Update `ARCHITECTURE.md`.

## 4. Non-goals

- Not auto-applying changes — only classifying whether the *ceremony* can be skipped.
- Not loosening the gate — verification is mandatory on both paths.

## 5. Acceptance tests (un-gameable)

- **AT-1 (trivial → fast path):** a 1-file, 1-line, non-migration diff classifies trivial
  (exit 0).
- **AT-2 (migration can't, the headline):** a one-line diff that drops/alters a column, or touches
  a `migrations/`/`.sql` file, classifies **NOT trivial** (exit 1, reason names the migration
  marker) — even though it's one line.
- **AT-3 (multi-file / large / delete → not trivial):** >1 file, or >3 changed lines, or a file
  deletion → not trivial.
- **AT-4 (gate intact on fast path):** documented + true that the fast path still runs the verify
  gate (PRD-004); the escape hatch drops planning ceremony, never the gate. (A change can be
  trivial *and* still be gated — the two are independent.)

## 6. Architect review

1. **Removal.** Removes the all-or-nothing ceremony default; replaces with a classified fast path.
2. **SSoT.** One classifier (`classify_change.py`); the "what is trivial" definition lives there
   and is cited by the skills, not duplicated as prose rules that could drift.
3. **Layering.** Adds a classifier + a documented path through the *existing* loop; the gate is
   reused, not forked.
4. **Migration debt.** Classifier + tests + skill/guardrail wiring ship together.
5. **Constitution diff.** Extends the Test-kit entries (classifier). No fork; the gate is shared.

## 7. Execution

Commit to `master` as `PRD-007` once AT-1…AT-4 pass. No push.
