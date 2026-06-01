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
import os
import subprocess
import sys

LOG_REL = os.path.join(".orchestrator", "executor.log")
STATUS_REL = os.path.join(".orchestrator", "executor.status")
DEFAULT_CMD = "claude -p"


def pdir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _ts():
    return datetime.datetime.now().isoformat(timespec="seconds")


def cmd_run(args):
    d = pdir()
    os.makedirs(os.path.join(d, ".orchestrator"), exist_ok=True)
    logpath, statuspath = os.path.join(d, LOG_REL), os.path.join(d, STATUS_REL)
    env = dict(os.environ, OL_ROLE="executor")
    with open(statuspath, "w") as s:
        s.write(f"running {_ts()}\n")
    with open(logpath, "a") as log:
        log.write(f"\n=== dispatch {_ts()} :: {args.cmd} ===\n")
        log.flush()
        proc = subprocess.Popen(args.cmd, shell=True, cwd=d, env=env, text=True, bufsize=1,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        if args.brief:
            try:
                proc.stdin.write(args.brief)
                proc.stdin.close()
            except BrokenPipeError:
                pass
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            log.write(f"{_ts()} {line}")
            log.flush()
        code = proc.wait()
    with open(statuspath, "w") as s:
        s.write(f"exited {code} {_ts()}\n")
    print(f"\n[dispatch] executor exited {code} — log: {LOG_REL}", file=sys.stderr)
    return code


def cmd_watch(_args):
    p = os.path.join(pdir(), LOG_REL)
    if not os.path.exists(p):
        print("no executor log yet")
        return 0
    sys.stdout.write(open(p).read())
    print("\n[dispatch] (for live follow: tail -f .orchestrator/executor.log)", file=sys.stderr)
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="sub", required=True)
    r = sub.add_parser("run")
    r.add_argument("--cmd", default=DEFAULT_CMD)
    r.add_argument("--brief", default="")
    sub.add_parser("watch")
    args = ap.parse_args(argv)
    return cmd_run(args) if args.sub == "run" else cmd_watch(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
