#!/usr/bin/env python3
"""Classify whether a change may take the trivial fast path (PRD-007).

Trivial (fast path: skip roadmap/full-PRD/architect-review, but NOT the verify gate) =
  * exactly one file changed
  * <= 3 changed lines
  * not a file deletion
  * no migration / schema / DDL / destructive markers (in content OR path)
Migrations and structural changes NEVER qualify, regardless of line count.

  classify_change.py --file <unified.diff>     # classify a diff file
  classify_change.py --git [<git diff args>]   # classify `git diff <args>` (default: working tree)
  classify_change.py --staged                  # classify `git diff --cached`

exit 0 = trivial (fast-path eligible); exit 1 = full ceremony required.
"""
import argparse
import os
import re
import subprocess
import sys

MAX_TRIVIAL_LINES = 3

DDL_MARKERS = [
    r"\bDROP\s+(TABLE|COLUMN|INDEX|VIEW)\b",
    r"\bALTER\s+TABLE\b",
    r"\bCREATE\s+TABLE\b",
    r"\bTRUNCATE\b",
    r"\bRENAME\s+(TABLE|COLUMN)\b",
    r"\bADD\s+COLUMN\b",
    r"\bCREATE\s+(UNIQUE\s+)?INDEX\b",
]
PATH_MARKERS = [r"migrations?/", r"\.sql\b", r"schema"]


def get_diff(args):
    if args.file:
        return open(args.file).read()
    pdir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    cmd = ["git", "-C", pdir, "diff"]
    if args.staged:
        cmd.append("--cached")
    elif args.git:
        cmd += args.git
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def classify(diff):
    files = re.findall(r"^diff --git a/(\S+) b/(\S+)", diff, re.M)
    paths = sorted({b for _, b in files})
    n_files = len(paths) if paths else (1 if diff.strip() else 0)
    added = len([l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")])
    removed = len([l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")])
    deletion = "deleted file mode" in diff
    changed = added + removed

    reasons = []
    # migration / DDL — content
    for pat in DDL_MARKERS:
        m = re.search(pat, diff, re.I)
        if m:
            reasons.append(f"migration/DDL marker: {m.group(0).strip()!r}")
    # migration / schema — path
    for p in paths:
        for pm in PATH_MARKERS:
            if re.search(pm, p, re.I):
                reasons.append(f"migration/schema path: {p!r}")
                break

    if n_files != 1:
        reasons.append(f"{n_files} files changed (trivial requires exactly 1)")
    if changed > MAX_TRIVIAL_LINES:
        reasons.append(f"{changed} changed lines (> {MAX_TRIVIAL_LINES})")
    if deletion:
        reasons.append("a file deletion (not a reversible trivial edit)")

    trivial = len(reasons) == 0
    return trivial, {"files": paths, "n_files": n_files, "added": added,
                     "removed": removed, "deletion": deletion, "reasons": reasons}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--git", nargs="*")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    diff = get_diff(args)
    if not diff.strip():
        print("no change detected", file=sys.stderr)
        return 1
    trivial, info = classify(diff)
    if args.json:
        import json
        print(json.dumps({"trivial": trivial, **info}, indent=2))
    elif trivial:
        print(f"TRIVIAL — fast-path eligible (1 file, {info['added']}+/{info['removed']}- lines, "
              "no migration markers). The verify gate still applies.")
    else:
        print("NOT trivial — full ceremony (roadmap/PRD/architect-review) required:", file=sys.stderr)
        for r in info["reasons"]:
            print("   -", r, file=sys.stderr)
    return 0 if trivial else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
