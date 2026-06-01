# PRD-002 — Stop loading the whole rulebook each session

**User-visible-surface impact:** Yes — what gets injected at SessionStart changes from the full
449-line rulebook to a short primer. Behavior must not regress (guarded by PRD-001's catch-rate).

## 1. Problem (with proof)

The SessionStart hook injects the entire rulebook every session:

```
$ cat hooks/hooks.json            # SessionStart -> cat "${CLAUDE_PLUGIN_ROOT}/GUARDRAILS.md"
$ wc -l GUARDRAILS.md             # 449 lines
$ wc -c GUARDRAILS.md             # 29081 chars  (~7-8k tokens, EVERY session)
```

Most of those 449 lines are *conditional* depth that isn't always-on guidance: ~20 verbose
`*Seen:*` war stories, `*Why:*` rationales, worked examples, and situational sections (design
guardrails, PRD discipline, migration mechanics, connectors, interaction discipline) that only
matter once a specific skill runs. Dumping all of it at every start **dilutes adherence** — the
always-true core (the skeptic's temperament + the loop + the autonomy contract) competes for
attention with rules that don't apply yet.

## 2. Root cause

There is exactly one injection and it points at the full canonical document. There is no
*primer* — no small always-on surface — so the only way to keep the rules "always in effect" has
been to inject everything. The conditional rules have no on-demand home distinct from the
always-on ones.

## 3. Scope

- **Add `STARTUP.md`** — the always-on primer: orchestrator identity, the three roles (one line
  each), the loop, the epistemic core as compressed imperatives (covering every behavior the
  PRD-001 scenarios test), the autonomy + session-completion contract in brief, and a clear
  pointer: *the full rules, the why behind each, and the war stories live in `GUARDRAILS.md`;
  each skill loads the sections it needs.* Budget: **≤ 60 lines / ≤ 4 KB** (vs 449 / 29 KB).
- **Point the SessionStart hook at `STARTUP.md`** instead of `GUARDRAILS.md` (`hooks/hooks.json`).
- **`GUARDRAILS.md` stays the SSoT** — unchanged as the full canonical method (war stories,
  Why, examples). The skills already carry their method inline (verify-handback's forensic
  method, draft-prd's PRD discipline, architect-review's five questions); add an explicit
  "load the relevant `GUARDRAILS.md` section on demand" pointer to each so the conditional depth
  has a clear load-on-demand path rather than riding every session start.
- **Add a guard** (`test/harness/check_startup.py`, wired into `run.py --check-startup`):
  STARTUP.md exists, is within budget, references `GUARDRAILS.md`, and GUARDRAILS.md still
  contains its canonical section anchors (so the primer can't silently replace the source).
- Update `ARCHITECTURE.md` (STARTUP.md = always-on primer; GUARDRAILS.md = full SSoT).

## 4. Non-goals

- Not rewriting the rules' content or deleting any rule from `GUARDRAILS.md`.
- Not changing the Cowork delivery path (app-profile first-line pointer) — that already loads
  GUARDRAILS.md on demand; this PRD is about the hook injection.
- Not auto-generating STARTUP.md from GUARDRAILS.md (a generator is more fragile than a curated
  primer; the guard enforces the relationship instead).

## 5. Acceptance tests (un-gameable)

- **AT-1 (size):** `wc -l STARTUP.md` ≤ 60 and `wc -c` ≤ 4096 — a fraction of today's 449/29081.
- **AT-2 (hook switched):** `hooks/hooks.json` SessionStart injects `STARTUP.md`, not
  `GUARDRAILS.md`; the guard `run.py --check-startup` exits 0.
- **AT-3 (no behavioral regression — load-bearing):** with **only `STARTUP.md`** injected
  (`run.py --method STARTUP.md`), the catch-rate on the core scenarios is **≥ the
  full-`GUARDRAILS.md` catch-rate** for the same model — i.e. the slim primer preserves the
  tested behavior. Measured on Haiku (the model where guardrails demonstrably matter: 5/5 vs 0/5
  in PRD-001). A drop means the primer dropped something load-bearing → put it back.
- **AT-4 (SSoT intact):** `GUARDRAILS.md` is unchanged in rule content; every canonical section
  anchor still present (guard checks this). No rule text is forked into STARTUP.md verbatim as a
  competing source — STARTUP.md is a primer that points to the canon.

## 6. Architect review

1. **Removal.** Removes the full-rulebook injection from session start (replaced by the primer).
   Nothing is deleted from the canon.
2. **SSoT.** `GUARDRAILS.md` remains the single source of rule truth; `STARTUP.md` is an
   always-on *primer/index* that points to it, and the skills load sections on demand. The guard
   prevents the primer from becoming a second, divergent source.
3. **Layering.** Editing the injection mechanism in place (one hook, one new primer file) — not a
   parallel rules system.
4. **Migration debt.** The hook switch + the guard ship in this PRD; no deferred cleanup.
5. **Constitution diff.** Extends the `ARCHITECTURE.md` "Method" rows (STARTUP.md row already
   declared as the startup stub). No fork.

## 7. Execution

Commit to `master` locally as `PRD-002` once AT-1, AT-2, AT-4 pass and AT-3 shows no drop on
Haiku. No push.
