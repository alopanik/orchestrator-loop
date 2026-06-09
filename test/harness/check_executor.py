#!/usr/bin/env python3
"""Executor-outcome gate (PRD-017) — a fail-closed check that a dispatched executor finished
CLEANLY before a handback is accepted.

`audit_executor.py` answers "did the orchestrator dispatch instead of coding itself?" (the
boundary). This answers a different, complementary question: "if a dispatch happened, did it
*finish clean*?" The day-one bug was that a crashed / killed / partial / timed-out executor was
indistinguishable from a clean one — every termination read as "done." Here, only `state == ok`
passes; anything else fails closed, and a stale `running` whose pid is dead is reported as a
crash (resumable — the loop may re-dispatch).

  check_executor.py check     # 0 = clean or dormant (no dispatch); nonzero = unclean/crash/in-flight
  check_executor.py status    # print what the gate currently sees
"""
import json
import os
import sys

OUTCOME_REL = os.path.join(".orchestrator", "executor.outcome.json")
CLEAN = "ok"


def pdir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _load(d):
    p = os.path.join(d, OUTCOME_REL)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except Exception:
        return {"state": "corrupt"}


def _pid_alive(pid):
    if not isinstance(pid, int):
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by another user
    except Exception:
        return False


def check():
    d = pdir()
    o = _load(d)
    if o is None:
        # No dispatch this cycle. audit_executor owns the "tree changed with no dispatch" case;
        # here, nothing to attribute — don't block a legitimate self-mode handback.
        print("check_executor: no executor dispatch recorded — dormant ✓")
        return 0
    state = o.get("state")
    if state == CLEAN:
        print(f"check_executor: executor finished clean (exit {o.get('code')}) ✓")
        return 0
    if state == "running":
        if _pid_alive(o.get("pid")):
            sys.stderr.write(
                f"check_executor: an executor dispatch is still IN FLIGHT (pid {o.get('pid')}). "
                "A handback cannot be verified mid-run. FAIL CLOSED. [check_executor]\n")
            return 2
        sys.stderr.write(
            f"check_executor: executor CRASHED mid-run — outcome is 'running' but pid "
            f"{o.get('pid')} is dead (started {o.get('started')}). This run did not finish; it is "
            "not 'done'. Re-dispatch (resumable). FAIL CLOSED. [check_executor]\n")
        return 2
    # failed / timeout / killed / launch-error / corrupt
    sys.stderr.write(
        f"check_executor: executor did NOT finish cleanly (state={state!r}, exit={o.get('code')}). "
        f"A {state} run is a claim, not a result — fix or re-dispatch before accepting. "
        "FAIL CLOSED. [check_executor]\n")
    return 2


def status():
    d = pdir()
    o = _load(d)
    if o is None:
        print("check_executor: no outcome recorded (dormant)")
        return 0
    alive = _pid_alive(o.get("pid")) if o.get("state") == "running" else False
    print(f"check_executor: state={o.get('state')!r} code={o.get('code')} pid={o.get('pid')} "
          f"alive={alive} started={o.get('started')} ended={o.get('ended')}")
    return 0


def main(argv):
    cmd = argv[0] if argv else "check"
    if cmd == "check":
        return check()
    if cmd == "status":
        return status()
    print(f"usage: check_executor.py [check|status] (got {cmd!r})", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
