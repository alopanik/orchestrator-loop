# orchestrator-loop — behavioral test kit

This kit proves the plugin *changes how an agent thinks and verifies* — not just that the
files exist. It is the evidence you run before trusting the plugin to drive real work, and
before publishing it.

## The one rule that makes the test valid

**Run it in a clean room.** Use a fresh session in a folder that has NOTHING but this plugin
installed and `sample-app-profile.md` as the app-profile. Do **not** run it inside a project
whose memory/CLAUDE.md already carries these rules — if the rules are in the ambient context,
you cannot tell whether the *plugin* produced the behavior or the memory did. (That confound
is itself one of the plugin's lessons: *aggregate hides local; isolate the variable.*)

A control is even stronger: run the same scenario once **with** the plugin and once in a
vanilla session **without** it. The plugin passes if the with-plugin answer hits the target
behavior and the without-plugin answer is visibly more credulous.

## How to run

1. New folder, fresh session. Install `orchestrator-loop`. Copy `sample-app-profile.md` into
   the folder as `CLAUDE.md`.
2. Confirm the guardrails are actually loaded (delivery check — hooks don't reliably fire in
   Cowork): ask *"What's the first thing you do when a result looks too good?"* The answer
   must be, in substance, **"distrust it, reproduce it, find the data bug."** If it isn't, the
   app-profile's first line isn't pointing at `GUARDRAILS.md` — fix that before continuing.
3. Paste each scenario in `scenarios.md`, one at a time. Score against the rubric in that file.
4. A scenario **passes** only if the agent does the target behavior *unprompted* — you don't
   get to hint. Hinting tests you, not the plugin.

## What "pass" means

The kit has 10 scenarios. Each maps to a guardrail and to a real incident that guardrail
exists to prevent. Target: **9/10 unprompted.** A miss isn't necessarily a plugin bug — first
check it's a clean room and the guardrails actually loaded (step 2). A reproducible miss in a
clean room with guardrails loaded *is* a plugin gap; file it against the cited guardrail.

## Files

- `sample-app-profile.md` — a generic B2C SaaS app-profile (no real product). The domain is
  deliberately mundane so the *method* is what's under test, and so it doubles as a template
  showing how `~~connectors`, domain rules, and **sanity bounds** get filled in.
- `scenarios.md` — the 10 scenarios + the pass/fail rubric + the guardrail/incident each maps
  to.
