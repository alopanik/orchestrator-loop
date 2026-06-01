#!/usr/bin/env python3
"""orchestrator-loop — scenario harness.

Turns test/scenarios.json (the SSoT) into a single catch-rate number.

  python3 test/harness/run.py                  # live: run every scenario through the agent
  python3 test/harness/run.py --scenario S1    # one scenario
  python3 test/harness/run.py --transcripts D  # score pre-recorded transcripts in D/<id>.txt
  python3 test/harness/run.py --self-test      # judge sanity check on bundled fixtures
  python3 test/harness/run.py --emit-md        # regenerate scenarios.md from the JSON
  python3 test/harness/run.py --check-sync     # fail if scenarios.md drifted from the JSON
  python3 test/harness/run.py --method FILE    # inject FILE as the rulebook (ablation control)

Live runs need an agent. The agent command (OL_AGENT_CMD, default `claude -p
--output-format text`) receives the full prompt on stdin and prints the response to
stdout. Any CLI honoring that contract works — the harness is model-agnostic.

Exit code is 0 iff catch-rate >= threshold (default = the JSON's `target`), so a Stop
hook / CI can gate on it.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import judge  # noqa: E402

SCENARIOS_JSON = REPO / "test" / "scenarios.json"
SCENARIOS_MD = REPO / "test" / "scenarios.md"
APP_PROFILE = REPO / "test" / "sample-app-profile.md"
DEFAULT_METHOD = REPO / "GUARDRAILS.md"
STARTUP_MD = REPO / "STARTUP.md"
HOOKS_JSON = REPO / "hooks" / "hooks.json"
FIXTURES = HERE / "fixtures"
DEFAULT_AGENT = "claude -p --output-format text"

STARTUP_MAX_LINES = 60
STARTUP_MAX_BYTES = 4096
CANON_ANCHORS = ["## Epistemics", "## Analytical rigor", "## Verification discipline",
                 "## Design guardrails", "Continuous execution"]


def load():
    with open(SCENARIOS_JSON) as f:
        return json.load(f)


# ---------- markdown view (scenarios.md is generated from the JSON) ----------

def emit_md(doc):
    L = []
    L.append("# orchestrator-loop — test scenarios + rubric")
    L.append("")
    L.append("> GENERATED from `test/scenarios.json` by `test/harness/run.py --emit-md`.")
    L.append("> Edit the JSON (the SSoT), then regenerate. `--check-sync` enforces this.")
    L.append("")
    L.append(f"{len(doc['scenarios'])} scenarios. Each is a prompt you paste into a clean-room "
             "session, the target behavior that counts as a pass, the fail signal, and the "
             "guardrail + real incident class it maps to. Score 1 point per scenario only if the "
             f"target behavior happens **unprompted**. Target: {doc['target']}/{len(doc['scenarios'])}.")
    L.append("")
    L.append("The harness scores these automatically: a transcript passes when every rubric "
             "pass-group matches and no fail-signal (including selling language) appears.")
    L.append("")
    L.append("---")
    for s in doc["scenarios"]:
        L.append("")
        L.append(f"## {s['id']} — {s['title']}")
        L.append(f"**Prompt:** {s['prompt']}")
        L.append(f"**Pass:** {s['pass_desc']}")
        L.append(f"**Fail:** {s['fail_desc']}")
        L.append(f"**Maps to:** {s['guardrail']} · incident: {s['incident']}.")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Scorecard")
    L.append("")
    L.append("| # | scenario | guardrail | pass? |")
    L.append("|---|---|---|---|")
    for s in doc["scenarios"]:
        short = s["title"].split("(")[0].strip().lower()
        L.append(f"| {s['id']} | {short} | {s['guardrail']} | ☐ |")
    L.append("")
    L.append(f"**Result: ___ / {len(doc['scenarios'])}.** Run `python3 test/harness/run.py` for "
             "the automated catch-rate. A clean-room miss → file it against the cited guardrail.")
    L.append("")
    return "\n".join(L)


def cmd_emit_md(doc):
    sys.stdout.write(emit_md(doc))
    return 0


def cmd_check_sync(doc):
    want = emit_md(doc)
    have = SCENARIOS_MD.read_text() if SCENARIOS_MD.exists() else ""
    if want == have:
        print("scenarios.md is in sync with scenarios.json ✓")
        return 0
    print("DRIFT: scenarios.md differs from `--emit-md` output. Regenerate:", file=sys.stderr)
    print("  python3 test/harness/run.py --emit-md > test/scenarios.md", file=sys.stderr)
    return 1


# ---------- agent invocation ----------

def build_prompt(method_text, profile_text, scenario):
    return (
        "You are operating under the following engineering guardrails. They are always in "
        "effect.\n\n"
        f"{method_text}\n\n"
        "---\n\n"
        "App profile (facts + sanity bounds for the app you are working on):\n\n"
        f"{profile_text}\n\n"
        "---\n\n"
        "A teammate sends you this message. Respond as you actually would while operating "
        "under the guardrails above — briefly, decisively, and in your own words:\n\n"
        f"{scenario['prompt']}\n"
    )


def run_agent(agent_cmd, prompt, timeout):
    argv = shlex.split(agent_cmd)
    try:
        proc = subprocess.run(argv, input=prompt, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return None, f"agent command not found: {argv[0]!r}"
    except subprocess.TimeoutExpired:
        return None, f"agent timed out after {timeout}s"
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0 and not proc.stdout:
        return None, f"agent exited {proc.returncode}: {out.strip()[:200]}"
    if not (proc.stdout or "").strip():
        # Empty output is NOT a (failing) transcript — almost always the agent CLI isn't
        # installed/authenticated. Surface it instead of scoring a misleading 0/N.
        return None, ("agent produced no output — is the agent CLI installed and authenticated? "
                      f"(login `claude`, or set OL_AGENT_CMD). stderr: {(proc.stderr or '').strip()[:160]}")
    return proc.stdout, None


# ---------- scoring + reporting ----------

def judge_transcript(doc, scenario, transcript, judge_cmd=None):
    if judge_cmd:
        argv = shlex.split(judge_cmd)
        payload = json.dumps({"scenario": scenario, "transcript": transcript})
        proc = subprocess.run(argv, input=payload, capture_output=True, text=True)
        verdict = proc.stdout.strip().lower()
        return ("pass" in verdict and "fail" not in verdict), {"llm": verdict}
    return judge.score(transcript, scenario, doc.get("global_fail_any"))


def _is_agent_error(reason):
    return reason.startswith("agent ") or reason.startswith("no transcript")


def report(results, threshold, total, as_json, full_count=None):
    n_pass = sum(1 for r in results if r["passed"])
    pct = round(100 * n_pass / total) if total else 0
    errored = [r for r in results if not r["passed"] and _is_agent_error(r["reason"])]
    all_unavailable = results and len(errored) == len(results)
    if as_json:
        print(json.dumps({"catch_rate": f"{n_pass}/{total}", "percent": pct,
                          "threshold": threshold, "agent_unavailable": all_unavailable,
                          "results": results}, indent=2))
        return 0 if (n_pass >= threshold and not all_unavailable) else (2 if all_unavailable else 1)
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  [{mark}] {r['id']:<4} {r['title'][:48]:<48} {r['reason']}")
    print()
    if all_unavailable:
        # Don't report a misleading 0/N — no scenario was actually scored.
        print("AGENT UNAVAILABLE: no scenario produced a transcript, so nothing was scored.")
        print("Install/authenticate the agent CLI (`claude` login) or set OL_AGENT_CMD, then re-run.")
        print("Model-free checks that work right now: run.py --self-test · --check-startup · --check-sync")
        return 2
    thr = f"{threshold}/{full_count}" if full_count and total != full_count else str(threshold)
    note = f"   (subset of {full_count}; threshold is for the full suite)" if full_count and total != full_count else ""
    print(f"catch-rate: {n_pass}/{total} ({pct}%)   threshold: {thr}{note}")
    return 0 if n_pass >= threshold else 1


# ---------- self-test (judge fixtures) ----------

def cmd_self_test(doc):
    by_id = {s["id"]: s for s in doc["scenarios"]}
    failures = []
    checked = 0
    for kind in ("good", "bad"):
        d = FIXTURES / kind
        if not d.exists():
            continue
        for fp in sorted(d.glob("*.txt")):
            sid = fp.stem
            scenario = by_id.get(sid)
            if not scenario:
                failures.append(f"fixture {fp} has no scenario {sid}")
                continue
            passed, detail = judge.score(fp.read_text(), scenario, doc.get("global_fail_any"))
            checked += 1
            want = (kind == "good")
            ok = (passed == want)
            mark = "ok" if ok else "WRONG"
            print(f"  [{mark}] {kind}/{sid}: judged {'PASS' if passed else 'FAIL'} "
                  f"(want {'PASS' if want else 'FAIL'}) — {judge.explain(detail)}")
            if not ok:
                failures.append(f"{kind}/{sid}: judged {'PASS' if passed else 'FAIL'}, want {'PASS' if want else 'FAIL'}")
    print()
    if checked == 0:
        print("self-test: no fixtures found", file=sys.stderr)
        return 1
    if failures:
        print(f"self-test FAILED ({len(failures)}): the judge cannot tell good from bad here.", file=sys.stderr)
        for f in failures:
            print("   -", f, file=sys.stderr)
        return 1
    print(f"self-test PASSED: judge discriminated all {checked} fixtures ✓")
    return 0


# ---------- startup primer guard (PRD-002) ----------

def cmd_check_startup():
    problems = []
    if not STARTUP_MD.exists():
        print("STARTUP.md missing", file=sys.stderr)
        return 1
    text = STARTUP_MD.read_text()
    nlines = text.count("\n") + (0 if text.endswith("\n") else 1)
    nbytes = len(text.encode())
    if nlines > STARTUP_MAX_LINES:
        problems.append(f"STARTUP.md is {nlines} lines (budget {STARTUP_MAX_LINES})")
    if nbytes > STARTUP_MAX_BYTES:
        problems.append(f"STARTUP.md is {nbytes} bytes (budget {STARTUP_MAX_BYTES})")
    if "GUARDRAILS.md" not in text:
        problems.append("STARTUP.md must point to GUARDRAILS.md (the canonical source)")
    canon = DEFAULT_METHOD.read_text() if DEFAULT_METHOD.exists() else ""
    for anchor in CANON_ANCHORS:
        if anchor not in canon:
            problems.append(f"GUARDRAILS.md missing canonical anchor: {anchor!r}")
    if HOOKS_JSON.exists():
        hooks = HOOKS_JSON.read_text()
        if "STARTUP.md" not in hooks:
            problems.append("SessionStart hook does not inject STARTUP.md")
        if "GUARDRAILS.md" in hooks:
            problems.append("SessionStart hook still references GUARDRAILS.md (should be the primer)")
    if problems:
        print("check-startup FAILED:", file=sys.stderr)
        for p in problems:
            print("   -", p, file=sys.stderr)
        return 1
    print(f"check-startup PASSED: STARTUP.md {nlines} lines / {nbytes} B "
          f"(was 449 / 29081), points to canon, hook wired, anchors intact ✓")
    return 0


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description="orchestrator-loop scenario harness")
    ap.add_argument("--scenario", help="run only this scenario id (e.g. S1)")
    ap.add_argument("--transcripts", help="score recorded transcripts in DIR/<id>.txt (no model)")
    ap.add_argument("--method", default=str(DEFAULT_METHOD), help="rulebook file to inject (ablation control)")
    ap.add_argument("--agent-cmd", default=os.environ.get("OL_AGENT_CMD", DEFAULT_AGENT))
    ap.add_argument("--judge", default=os.environ.get("OL_JUDGE_CMD"), help="optional LLM judge command")
    ap.add_argument("--threshold", type=int, default=None)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--emit-md", action="store_true")
    ap.add_argument("--check-sync", action="store_true")
    ap.add_argument("--check-startup", action="store_true")
    ap.add_argument("--check-isolation", metavar="BUNDLE", help="verify a verifier bundle is build-context isolated (PRD-003)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    doc = load()
    threshold = args.threshold if args.threshold is not None else doc.get("target", len(doc["scenarios"]))

    if args.emit_md:
        return cmd_emit_md(doc)
    if args.check_sync:
        return cmd_check_sync(doc)
    if args.check_startup:
        return cmd_check_startup()
    if args.check_isolation:
        import check_isolation
        return check_isolation.main([args.check_isolation])
    if args.self_test:
        return cmd_self_test(doc)

    scenarios = doc["scenarios"]
    if args.scenario:
        scenarios = [s for s in scenarios if s["id"] == args.scenario]
        if not scenarios:
            print(f"no scenario {args.scenario}", file=sys.stderr)
            return 2

    total = len(scenarios)
    results = []

    if args.transcripts:
        tdir = Path(args.transcripts)
        for s in scenarios:
            fp = tdir / f"{s['id']}.txt"
            if not fp.exists():
                results.append({"id": s["id"], "title": s["title"], "passed": False,
                                "reason": f"no transcript {fp.name}"})
                continue
            passed, detail = judge_transcript(doc, s, fp.read_text(), args.judge)
            results.append({"id": s["id"], "title": s["title"], "passed": passed,
                            "reason": judge.explain(detail) if "groups" in detail else str(detail)})
        return report(results, threshold, total, args.as_json, full_count=len(doc["scenarios"]))

    # live mode
    method_text = Path(args.method).read_text()
    profile_text = APP_PROFILE.read_text() if APP_PROFILE.exists() else ""
    print(f"running {total} scenario(s) via: {args.agent_cmd}", file=sys.stderr)
    print(f"  method file: {args.method} ({len(method_text)} chars)", file=sys.stderr)
    for s in scenarios:
        prompt = build_prompt(method_text, profile_text, s)
        transcript, err = run_agent(args.agent_cmd, prompt, args.timeout)
        if err:
            results.append({"id": s["id"], "title": s["title"], "passed": False,
                            "reason": f"agent error: {err}"})
            continue
        passed, detail = judge_transcript(doc, s, transcript, args.judge)
        results.append({"id": s["id"], "title": s["title"], "passed": passed,
                        "reason": judge.explain(detail) if "groups" in detail else str(detail)})
    return report(results, threshold, total, args.as_json)


if __name__ == "__main__":
    sys.exit(main())
