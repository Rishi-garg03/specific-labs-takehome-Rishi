#!/usr/bin/env python3
"""Verifier: every file must equal the pristine original with each manifest
value replaced by its token (LONGEST value first) — catches under- AND
over-redaction exactly. Longest-first means a short span ("Maya") can never
corrupt a longer span that contains it ("Maya Torres")."""

import json
import sys
from pathlib import Path


def fail(msg):
    print(msg)
    sys.exit(1)


def main():
    workspace = Path(sys.argv[1])
    task_dir = Path(__file__).parent
    pristine = task_dir / "workspace"
    entries = json.loads((task_dir / "manifest.json").read_text())["replacements"]

    by_file = {}
    for entry in entries:
        by_file.setdefault(entry["file"], []).append(entry)

    expected_files = sorted(str(p.relative_to(pristine))
                            for p in pristine.rglob("*") if p.is_file())
    actual_files = sorted(str(p.relative_to(workspace))
                          for p in workspace.rglob("*") if p.is_file())
    if actual_files != expected_files:
        fail(f"file set changed: expected {expected_files}, got {actual_files}")

    for rel in expected_files:
        expected = (pristine / rel).read_text()
        for entry in sorted(by_file.get(rel, []),
                            key=lambda e: len(e["value"]), reverse=True):
            expected = expected.replace(entry["value"], entry["token"])
        actual = (workspace / rel).read_text()
        if actual != expected:
            leftovers = [e["value"] for e in by_file.get(rel, [])
                         if e["value"] in actual]
            if leftovers:
                fail(f"{rel}: PII not redacted: {leftovers[0]}")
            fail(f"{rel}: content differs from expected redaction "
                 f"(over-redaction or altered text)")
    print("ok")


if __name__ == "__main__":
    main()
