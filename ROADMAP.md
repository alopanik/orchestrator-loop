# Roadmap — harden the verifier moat

Source: `REQUIREMENTS.md`. The planning loop is commodity; the moat is **forensic verification
against deployed reality.** This roadmap hardens that moat, makes it measurable, and stops
competing on the commodity half. Lowest number ships first; the number IS the execution order.

| # | scope (one line) | depends-on | user-visible? | risk |
|---|---|---|---|---|
| 001 | Make the loop measurable — scenario harness prints a catch-rate; breaking the verifier drops it | — | dev-facing (new `test/harness`) | med |
| 002 | Stop loading the whole rulebook each session — small startup stub, rest on demand | 001 | yes (startup behavior) | med |
| 003 | Make the verifier independent — fresh subagent sees only diff + criteria | 001 | yes (verify-handback) | med |
| 004 | Make the hard gates fail closed — Stop hook blocks turn-end until checks pass | 001 | yes (new Stop hook) | high |
| 005 | Guard the tests — tests committed failing first; verifier rejects tampered tests | 001, 004 | yes (verify + handoff) | med |
| 006 | Don't let the verifier over-report — findings scoped to correctness + criteria | 001, 003 | yes (verify-handback) | med |
| 007 | Escape hatch for trivial changes — fast path, gate still enforced | 004 | yes (go / draft-prd) | med |
| 008 | Record what the loop catches — append-only ledger + one-line surface | 004 | yes (new ledger) | low |
| 009 | README rewrite — lead with delegation value prop + published catch-rate; refresh visuals | 001–008 | yes (README) | low |
| 013 | Bind & enforce the executor in Cowork — persist the tier + fail-closed write-audit | 011, 012 | yes (setup/handoff/verify) | high |
| 014 | Anti-cheat catch-rate — scenarios for a lying executor + subset score | 001, 005 | yes (test kit) | med |
| 015 | Reposition on the moat — README + verifier framing (spec-compliance/drift) | 013, 014 | yes (README) | low |

## Arc 2 — operate the loop across people, machines & time (016–024)

Arc 1 won the *local, single-operator* enforcement battle: the gate, the executor lock, the
tamper-check, the ledger — all live on one machine and fire only when that operator's agent ends
a turn. This arc makes the same moat hold when the loop is no longer one person babysitting one
agent: enforced on a remote nobody can bypass (CI), and safe when multiple collaborators/agents
share the repo. Both faces of one question — *does the loop still hold across people, machines,
and time?* Lowest number ships first.

| # | scope (one line) | depends-on | user-visible? | risk |
|---|---|---|---|---|
| 016 | bootstrap-cicd — one command drops the EXISTING gate into any repo as `~~ci` (workflow + pre-push hook) running the same checks (no forked list), parameterized by `~~ci`/`~~vcs`; a ratchet that ships with baseline-trust discipline; install merges into `CLAUDE.md` via a managed sentinel block | — | yes (new skill) | high |
| 017 | executor reliability — make the executor lifecycle fail-safe: reliable exit-status capture, crash / timeout / heartbeat detection, a non-clean exit fails the handback **closed** (a killed or partial run is never "done"), and an interrupted PRD is resumable, not lost. Bit on day one of single-operator use — foundational, before the collaborator thread | 012, 013 | yes (dispatch / verify) | high |
| 018 | shared-state restructure — de-contend the loop for concurrent operators: per-PRD claim files + concurrency-safe append-only ledger (retire the "one writer" invariant); ROADMAP status becomes a generated view over the PRD/claim files | — | yes (`.orchestrator` + ROADMAP) | high |
| 019 | PRD claiming / ownership — atomic claim so two agents don't grab the same PRD; branch ↔ claim; stale-claim reclaim | 018 | yes (go / handoff) | med |
| 020 | team provenance ledger — extend the decision record to who · what · which-check · which-commit, so a collaborator can trust work they didn't watch | 018, 008 | yes (ledger surface) | med |
| 021 | separation of duties — planner ≠ verifier made enforceable: fail closed if the same recorded principal planned and blessed a PRD (builds on 020's principal record; realizes the parked "Agent Teams mode" in part) | 020 | yes (verify-handback) | med |
| 022 | multi-hand release gate — extend the CI scaffold so "push = release, owner sign-off" holds with multiple committers: required CI check + protected branch + a signoff record | 016, 019 | yes (PUBLISHING) | med |
| 023 | gated-migration choreography — a **distinct** skill (not CI): draft SQL → owner review → apply → verify → record, with a mandatory pause at the irreversible apply; gives the existing "no bare destructive migration" rule mechanical teeth on `~~database` | 008 | yes (new skill) | med |
| 024 | README refresh — center the value prop, fold in Arc 2 (unbypassable remote + team-safe), refresh every count to a runnable figure; release-readiness for 0.8.0 | 016–023 | yes (README) | low |

**Spine** (per Andrew): shared-state (018) → claims (019) → provenance (020); separation-of-duties
(021) builds on the principal record from 020. **Executor-reliability (017)** is sequenced before
the collaborator thread because it bit on day one of single-operator use — foundational, not a
multi-collaborator nicety. **023** is independent of the collaborator sub-thread: a smaller
capstone that pairs with the ledger (008) for its record step.

## Later / bigger (NOT in this session — do not pull forward)
Forking risk if the verifier internals (003, 004) aren't hardened first.

- Self-improving rules: verifier catches a failure with no matching rule → auto-draft a candidate
  `Seen:` war story for human approval (never auto-commit).
- Agent Teams mode: verifier as a standing team member auditing every handback; subagent fallback.
  *(Partially pulled into Arc 2 — 019 makes planner ≠ verifier enforceable as the first step.)*
- Standalone verifier: package `verify-handback` so an external planner can call it with just a
  diff + criteria + app-profile (the adoption play).

## Status
<!-- ORCHESTRATOR-LOOP:STATUS:BEGIN (generated by roadmap_status.py — do not hand-edit) -->
- Shipped (24): 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015 016 017 018 019 020 021 022 023 024
- Open (0): —
<!-- ORCHESTRATOR-LOOP:STATUS:END -->

### Arc 2 — shipped notes
016 shipped (0c90d70): bootstrap-cicd — one command relocates the existing gate to `~~ci`
(workflow + pre-push fast gate, both calling the single engine `hooks/ci_gate.py`; no forked
check list). Idempotent `CLAUDE.md` merge; `ratchet-baseline` REFUSES a non-discriminating signal
(baseline-trust). 24/24 acceptance; repo passes its own new gate (dogfood green). NOT pushed.
017 shipped: executor reliability — `dispatch.py` gains `--timeout` (kills the process group on a
hang) + a structured `executor.outcome.json`; new `check_executor.py` fails the handback closed
unless the last run finished `ok` (crash/kill/timeout/partial ≠ done), and a stale `running` with a
dead pid is reported as a resumable crash. 14/14 acceptance; PRD-012 dispatch still 6/6 (no
regression). Bit on day one of two-brain use; sequenced before the collaborator thread.
018 shipped: shared-state restructure — per-PRD state files (`.orchestrator/prds/<ID>.json`, atomic
temp+rename) so concurrent operators don't contend; ROADMAP status is now a generated view
(`roadmap_status.py`, drift-guarded as a standing CI check); the ledger's "one writer" invariant
retired for many atomic `O_APPEND` appenders + a `check_ledger.py` torn-line canary. 13/13
acceptance; migration seeded 23 state files; tests-first chain re-established cleanly; gate green.
019 shipped: PRD claiming — atomic `O_EXCL` claim (`prd_state.py claim`) so exactly one of N
concurrent operators wins a PRD; records who + branch; lease-based stale reclaim (`--force` only
overrides a stale claim, never a live owner); claim binds the branch. Claims are runtime fs
coordination (gitignored); state JSON stays committed. 9/9 acceptance; gate green.
020 shipped: team provenance ledger — every gate decision now records who · commit · branch
(`OL_ACTOR` → git user → `$USER`; short HEAD sha), from BOTH writers (`stop_gate` + `ci_gate`),
surfaced in `stop_gate.py ledger`; degrades to `unknown` outside git (never crashes the gate). The
recorded principal is what 021 enforces planner≠verifier on. 10/10 acceptance; completes the spine.
021 shipped: separation of duties — `prd_state` stamps every transition with its principal (`by`) +
keeps a `history`; new `check_separation.py` fails the handback closed (when a team opts in via
`OL_REQUIRE_SEPARATION` or `policy.json`) if the same principal built and blessed a PRD. Dormant in
solo/self mode. 8/8 acceptance; realizes the first step of the parked "Agent Teams mode"; completes
the collaborator-safety mechanism (claims → provenance → separation).
022 shipped: multi-hand release gate — a release (a version bump that ships) now requires a recorded
OWNER sign-off. `release.py signoff --by <owner>` refuses a non-owner; `release.py check` fails
closed unless the current manifest version is signed off by an authorized owner (owners from
`release-policy.json` else the marketplace `owner.name`). `bootstrap-cicd` emits a release workflow
that runs it; branch protection documented. Release-time check, not a standing dev check. 11/11
acceptance; the actual release stays the owner's act.
023 shipped: gated-migration choreography — a distinct skill (`skills/gated-migration/`) + state
machine (`migrate.py`): draft → owner review → apply → verify → record on `~~database`. The apply
fails closed unless an owner approved it (the mandatory pause at the irreversible step), and a bare
destructive migration (`DROP`/`TRUNCATE`/…) is blocked unless drafted `--staged` (2-stage
soft-deprecate). Every transition recorded with who+when. CI gates code; this gates a data action.
14/14 acceptance. CI gates code; this gates a data action.
024 shipped: README refresh — centered on the value prop, folded in Arc 2 (unbypassable remote +
team-safe), every count refreshed to a runnable figure (9 skills · 149 tests · 22 self-test
fixtures · 16 scenarios), links verified. Version bumped to **0.8.0** in both manifests; `claude
plugin validate` ✔. **Arc 2 complete — 016–024 shipped + independently verified; 0.8.0
release-ready, pending the owner's push.**

### This session — make the moat bind + prove it (013–015)
Goal: two-brain actually binds in Cowork (013), the kit proves we catch a *lying* executor (014),
and the README leads with that wedge (015). Lowest ships first; 013 is the load-bearing fix.

001 shipped (80e60c9): one-command catch-rate; AT-3 proven (Haiku 5/5 guarded → 0/5 credulous;
Opus saturated). Evidence: test/harness/AT3-evidence.md.
002 shipped (ef3d47e): startup injection 449→48 lines (29KB→3.3KB); Haiku primer-only 5/5
(== full); guard run.py --check-startup keeps GUARDRAILS.md the SSoT.
003 shipped (7103e3b): verify-handback = fresh subagent fed only diff+criteria+facts;
run.py --check-isolation guard; isolated verifier caught a planted defect from the bundle alone.
004 shipped: fail-closed Stop hook (hooks/stop_gate.py) — blocks turn-end while a gate's
scriptable checks are red; 10/10 unit tests; real demo blocks a planted failing check.
005 shipped: check_tests.py (tests-first baseline + tamper/green); composed into the Stop gate — a handback that edits its own tests to pass is blocked (4/4 unit + AT-5 gate demo).
006 shipped: verifier scoped to correctness vs stated criteria (style/non-goals = non-blocking notes); S12 added (12 scenarios, target 11). Honest finding: over-reporting rare on both models; guarantee rests on deterministic self-test (bad/S12 FAILs).
007 shipped: classify_change.py — trivial (1-file/1-line/no-migration) fast path skips ceremony but not the gate; migrations never qualify (6/6 tests).
008 shipped: .orchestrator/ledger.jsonl — the gate appends every decision (pass/block + per-check evidence); `stop_gate.py ledger` summary; one writer. A real tamper block is recorded with its evidence.
009 shipped: README rewritten — value prop + moat + HONEST catch-rate (self-test 14/14, ablation 5/5->0/5, model-dependence nuance; no fabricated number); two-brain recommended + both solos. Rejected a rogue sub-agent's unauthorized README (fabricated 11/12). Judge FN bugs fixed; war story added.
010 shipped: preflight.py — verify executor is wired to the project CLAUDE.md names; fail closed on wrong Supabase/Vercel/repo (5/5 tests).
011 shipped: enforce_executor.py PreToolUse hook — in power mode the orchestrator can't Write/Edit (only the OL_ROLE=executor process can); self/solo unaffected (6/6 tests).
012 shipped: dispatch.py — launch executor live-streamed + logged (.orchestrator/executor.log), stamps OL_ROLE=executor (enables PRD-011); watchable / tmux-friendly (6/6 tests).
013 shipped: executor binding + Cowork enforcement — setup persists the tier to mode.json AND the ~~executor line (verifies before "ready"); handoff routes Cowork dispatch via the shell MCP (e.g. Desktop Commander), not the sandbox; audit_executor.py fail-closes a handback whose tree changed with no recorded dispatch (7/7 tests; AT-3 repro blocked→allowed). Root cause: mode.json missing (defaulted self) + CLAUDE.md ~~executor=self.
014 shipped: anti-cheat catch-rate — S13–S16 (tampered tests, fabricated number, done-without-running, reward-hacked check); --category filter + core/anti-cheat breakdown; self-test discriminates all 22 fixtures (8 new good/bad).
015 shipped: repositioned on the moat — README leads with "assume the executor cheats, we catch it" + competitive contrast + spec-compliance/drift framing; version 0.7.0 (both manifests); claude plugin validate ✔. NOT pushed (release = owner sign-off).
