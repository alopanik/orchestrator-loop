#!/usr/bin/env python3
"""Tests for classify_change.py (PRD-007). Run: python3 test/harness/test_classify_change.py"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CLS = os.path.join(HERE, "classify_change.py")
PY = sys.executable

TRIVIAL = """diff --git a/README.md b/README.md
index 1111111..2222222 100644
--- a/README.md
+++ b/README.md
@@ -1 +1 @@
-teh quick brown fox
+the quick brown fox
"""

MIGRATION_CONTENT = """diff --git a/app/db.py b/app/db.py
index 1..2 100644
--- a/app/db.py
+++ b/app/db.py
@@ -10 +10 @@
-    pass
+    db.execute("DROP TABLE sessions")
"""

MIGRATION_PATH = """diff --git a/migrations/003_add.sql b/migrations/003_add.sql
new file mode 100644
--- /dev/null
+++ b/migrations/003_add.sql
@@ -0 +1 @@
+SELECT 1;
"""

MULTI_FILE = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1 +1 @@
-x
+y
diff --git a/b.py b/b.py
--- a/b.py
+++ b/b.py
@@ -1 +1 @@
-p
+q
"""

LARGE = """diff --git a/util.py b/util.py
--- a/util.py
+++ b/util.py
@@ -1,2 +1,5 @@
-old
+l1
+l2
+l3
+l4
"""

DELETION = """diff --git a/old.py b/old.py
deleted file mode 100644
--- a/old.py
+++ /dev/null
@@ -1 +0,0 @@
-content
"""

CASES = [
    ("trivial 1-file 1-line edit -> exit 0 (trivial)", TRIVIAL, 0),
    ("DROP TABLE in content -> exit 1 (not trivial)", MIGRATION_CONTENT, 1),
    ("migrations/*.sql path -> exit 1 (not trivial)", MIGRATION_PATH, 1),
    ("two files -> exit 1 (not trivial)", MULTI_FILE, 1),
    (">3 changed lines -> exit 1 (not trivial)", LARGE, 1),
    ("file deletion -> exit 1 (not trivial)", DELETION, 1),
]


def run(diff_text):
    with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False) as f:
        f.write(diff_text)
        path = f.name
    try:
        p = subprocess.run([PY, CLS, "--file", path], capture_output=True, text=True)
        return p.returncode, (p.stdout + p.stderr)
    finally:
        os.unlink(path)


def main():
    passed = failed = 0
    for name, diff, want in CASES:
        rc, out = run(diff)
        ok = rc == want
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}  (exit {rc}, want {want})")
        passed += ok
        failed += not ok
    print()
    if failed:
        print(f"classify_change tests FAILED: {failed}/{len(CASES)}", file=sys.stderr)
        return 1
    print(f"classify_change tests PASSED: {passed}/{len(CASES)} ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
