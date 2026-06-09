#!/usr/bin/env python3
"""Dispatch + watch the executor (PRD-012).

Launches the coding executor as a subprocess, streams its output live to the console AND to a
tailable log, and marks the process as the executor (OL_ROLE=executor) so PRD-011's enforcement
lets it write while the orchestrator can't. Anthropic's guidance is to treat Claude Code like a
junior engineer you can watch, redirect, or step away from — this is the "watch" part.

  dispatch.py run --brief "<brief>" [--cmd "<executor cmd>"]   # default cmd: claude -p
  dispatch.py watch                                            # print the executor log (tail -f for live)

The log + status live at .orchestrator/executor.{log,status} — a stable path you can also
`tail -f` or watch in a tmux pane.
"""
import argparse
import datetime
import json
import os
import signal
import subprocess
import sys
import threading
import time

LOG_REL = os.path.join(".orchestrator", "executor.log")
STATUS_REL = os.path.join(".orchestrator", "executor.status")
OUTCOME_REL = os.path.join(".orchestrator", "executor.outcome.json")  # structured outcome (PRD-017)
DEFAULT_CMD = "claude -p"


def pdir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _ts():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _write_outcome(d, **fields):
    """Merge fields into .orchestrator/executor.outcome.json (PRD-017). dispatch is the only writer."""
    path = os.path.join(d, OUTCOME_REL)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cur = {}
    if os.path.exists(path):
        try:
            cur = json.load(open(path))
        except Exception:
            cur = {}
    cur.update(fields)
    with open(path, "w") as f:
        json.dump(cur, f, indent=2)
        f.write("\n")


def cmd_run(args):
    d = pdir()
    os.makedirs(os.path.join(d, ".orchestrator"), exist_ok=True)
    logpath, statuspath = os.path.join(d, LOG_REL), os.path.join(d, STATUS_REL)
    env = dict(os.environ, OL_ROLE="executor")
    started = _ts()
    with open(statuspath, "w") as s:
        s.write(f"running {started}\n")  # legacy status line (PRD-012/013 readers + tests)
    log = open(logpath, "a")
    log.write(f"\n=== dispatch {started} :: {args.cmd} ===\n")
    log.flush()

    # Launch in its own session so a timeout can kill the whole process group (PRD-017).
    try:
        proc = subprocess.Popen(args.cmd, shell=True, cwd=d, env=env, text=True, bufsize=1,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, start_new_session=True)
    except Exception as e:  # the shell itself could not be launched — never leave 'running'
        _write_outcome(d, state="launch-error", code=None, pid=None,
                       started=started, ended=_ts(), error=str(e)[:200])
        with open(statuspath, "w") as s:
            s.write(f"exited launch-error {_ts()}\n")
        log.write(f"=== launch-error: {e} ===\n")
        log.close()
        print(f"\n[dispatch] launch error: {e}", file=sys.stderr)
        return 127

    _write_outcome(d, state="running", code=None, pid=proc.pid,
                   started=started, ended=None, heartbeat=started)
    if args.brief:
        try:
            proc.stdin.write(args.brief)
            proc.stdin.close()
        except (BrokenPipeError, ValueError):
            pass

    def _stream():
        try:
            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                log.write(f"{_ts()} {line}")
                log.flush()
                _write_outcome(d, heartbeat=_ts())  # liveness for crash/stall detection
        except Exception:
            pass
    t = threading.Thread(target=_stream, daemon=True)
    t.start()

    timeout = args.timeout if (args.timeout and args.timeout > 0) else None
    deadline = (time.time() + timeout) if timeout else None
    state, code = None, None
    while True:
        rc = proc.poll()
        if rc is not None:
            code = rc
            state = "ok" if rc == 0 else "failed"
            break
        if deadline and time.time() > deadline:
            for sig in (signal.SIGTERM, signal.SIGKILL):  # bound the hang
                try:
                    os.killpg(os.getpgid(proc.pid), sig)
                except Exception:
                    pass
                try:
                    proc.wait(timeout=2)
                    break
                except Exception:
                    continue
            code = proc.poll()
            state = "timeout"
            break
        time.sleep(0.1)

    t.join(timeout=2)
    ended = _ts()
    _write_outcome(d, state=state, code=code, pid=proc.pid, started=started, ended=ended)
    with open(statuspath, "w") as s:
        s.write(f"exited {code} {ended}\n")  # legacy line preserved (audit_executor reads 'exited')
    log.write(f"=== {state} (exit {code}) {ended} ===\n")
    log.close()
    print(f"\n[dispatch] executor {state} (exit {code}) — log: {LOG_REL}", file=sys.stderr)
    # Preserve PRD-012 contract: a normal run returns the executor's real exit code; only the
    # failure-to-finish cases normalize to a nonzero code.
    if state == "ok":
        return 0
    if state == "failed":
        return code if isinstance(code, int) and code != 0 else 1
    if state == "timeout":
        return 124
    return 1


def cmd_watch(_args):
    p = os.path.join(pdir(), LOG_REL)
    if not os.path.exists(p):
        print("no executor log yet")
        return 0
    sys.stdout.write(open(p).read())
    print("\n[dispatch] (for live follow: tail -f .orchestrator/executor.log)", file=sys.stderr)
    return 0


def cmd_clear_outcome(_args):
    """Consume the outcome on accept (verify-handback), so it can't stale-block the next cycle."""
    p = os.path.join(pdir(), OUTCOME_REL)
    if os.path.exists(p):
        try:
            os.replace(p, p + ".cleared")  # rename, not unlink (virtiofs-safe)
        except Exception:
            open(p, "w").write("{}\n")
    print("executor outcome cleared")
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="sub", required=True)
    r = sub.add_parser("run")
    r.add_argument("--cmd", default=DEFAULT_CMD)
    r.add_argument("--brief", default="")
    r.add_argument("--timeout", type=int, default=0,
                   help="max executor runtime in seconds (0 = no limit); kills the group on exceed")
    sub.add_parser("watch")
    sub.add_parser("clear-outcome")
    args = ap.parse_args(argv)
    if args.sub == "run":
        return cmd_run(args)
    if args.sub == "watch":
        return cmd_watch(args)
    if args.sub == "clear-outcome":
        return cmd_clear_outcome(args)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
