#!/usr/bin/env python3
"""Standing check: `version` is identical across both plugin manifests (app-profile invariant).

plugin.json.version, marketplace.json metadata.version, and each marketplace plugins[].version
must all match. Exit 0 if they agree, 1 (with the mismatch named) otherwise. Wired into
.orchestrator/ci-gate.json so a version skew fails CI and the pre-push gate.

  python3 test/harness/check_version.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    plugin = os.path.join(ROOT, ".claude-plugin", "plugin.json")
    market = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
    try:
        pv = json.load(open(plugin)).get("version")
        m = json.load(open(market))
    except Exception as e:
        print(f"check-version: cannot read manifests: {e}", file=sys.stderr)
        return 1
    versions = {"plugin.json": pv,
                "marketplace.metadata": m.get("metadata", {}).get("version")}
    for i, p in enumerate(m.get("plugins", [])):
        versions[f"marketplace.plugins[{i}]"] = p.get("version")
    distinct = set(v for v in versions.values() if v is not None)
    if None in versions.values():
        missing = [k for k, v in versions.items() if v is None]
        print(f"check-version: missing version in {missing}", file=sys.stderr)
        return 1
    if len(distinct) != 1:
        print(f"check-version: versions disagree -> {versions}", file=sys.stderr)
        return 1
    print(f"check-version: all manifests at {distinct.pop()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
