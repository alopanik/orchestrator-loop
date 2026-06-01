#!/usr/bin/env python3
"""Verifier-isolation guard (PRD-003).

An independent verifier may see ONLY a whitelisted bundle:
  1. the diff under review
  2. the acceptance criteria / un-gameable checks
  3. the app-profile facts + sanity bounds

It must NOT see the build story — the PRD's problem/root-cause narrative, planning/design
reasoning, the build log, or the executor's self-report. This module makes that boundary
mechanically checkable instead of a promise.

Strategy: the bundle is section-structured (`## ` headers). We (a) require the three allowed
sections, (b) reject any other top-level section (a leaked `## Root cause` etc.), and (c) scan
every NON-diff section for build-narrative phrases (so prose leakage without a header is still
caught). The diff section's body is exempt from the phrase scan — a code comment may legitimately
say "root cause".
"""
import re
import sys

ALLOWED = [
    ("diff", re.compile(r"diff", re.I)),
    ("acceptance criteria", re.compile(r"acceptance|criteria", re.I)),
    ("app-profile / sanity bounds", re.compile(r"app-?profile|sanity|facts", re.I)),
]

FORBIDDEN_PHRASES = [
    r"root cause", r"why (it|this) works", r"\bi implemented\b", r"\bwe implemented\b",
    r"the executor (reports|says|claims)", r"build log", r"\brationale\b",
    r"problem statement", r"planning (notes|reasoning)", r"design reasoning",
    r"as i (built|designed|planned)", r"my reasoning",
]
FORBIDDEN = [re.compile(p, re.I) for p in FORBIDDEN_PHRASES]

HEADER = re.compile(r"^##\s+(.*)$", re.M)


def _sections(text):
    """Return list of (header, body). Text before the first header is ignored."""
    out, last_h, last_i = [], None, None
    for m in HEADER.finditer(text):
        if last_h is not None:
            out.append((last_h, text[last_i:m.start()]))
        last_h, last_i = m.group(1).strip(), m.end()
    if last_h is not None:
        out.append((last_h, text[last_i:]))
    return out


def _is_allowed(header):
    return any(rx.search(header) for _, rx in ALLOWED)


def _is_diff(header):
    return bool(re.search(r"diff", header, re.I))


def check_bundle(text):
    problems = []
    secs = _sections(text)
    headers = [h for h, _ in secs]

    for name, rx in ALLOWED:
        if not any(rx.search(h) for h in headers):
            problems.append(f"missing required section: {name}")

    for h in headers:
        if not _is_allowed(h):
            problems.append(f"disallowed section leaks build context: '## {h}'")

    for h, body in secs:
        if _is_diff(h):
            continue  # diff body may legitimately contain these words in code/comments
        for rx in FORBIDDEN:
            m = rx.search(body)
            if m:
                problems.append(f"build-narrative phrase in '## {h}': {m.group(0)!r}")

    return (len(problems) == 0), problems


def main(argv):
    if not argv:
        print("usage: check_isolation.py BUNDLE.md", file=sys.stderr)
        return 2
    text = open(argv[0]).read()
    ok, problems = check_bundle(text)
    if ok:
        print(f"isolation OK: {argv[0]} contains only diff + criteria + app-profile facts ✓")
        return 0
    print(f"isolation FAILED: {argv[0]} leaks build context:", file=sys.stderr)
    for p in problems:
        print("   -", p, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
