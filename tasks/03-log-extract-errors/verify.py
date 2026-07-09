#!/usr/bin/env python3
"""Verifier for 03-log-extract-errors.

Recomputes the expected ERROR events from the pristine service.log with
independent parsing logic, then checks errors.jsonl matches exactly: same
records, same key order (ts, service, message), sorted by ts then service.
"""

import json
import re
import sys
from pathlib import Path

LEVELS = {"INFO", "WARN", "ERROR"}
TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
KEYS = ["ts", "service", "message"]


def fail(msg):
    print(msg)
    sys.exit(1)


def expected_events(log_text):
    events = []
    for line in log_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("{"):
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and obj.get("level") == "ERROR":
                events.append((obj["ts"], obj["svc"], obj["msg"]))
            continue
        tokens = line.split(None, 3)
        if len(tokens) >= 4 and TS_RE.match(tokens[0]) and tokens[2] in LEVELS:
            if tokens[2] == "ERROR":
                events.append((tokens[0], tokens[1], tokens[3]))
    events.sort(key=lambda e: (e[0], e[1]))
    return events


def main():
    workspace = Path(sys.argv[1])
    pristine = Path(__file__).parent / "workspace"

    expected = expected_events((pristine / "service.log").read_text())

    out = workspace / "errors.jsonl"
    if not out.exists():
        fail("errors.jsonl not found")

    got = []
    for i, line in enumerate(out.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            fail(f"line {i}: not valid JSON: {line!r}")
        if list(obj.keys()) != KEYS:
            fail(f"line {i}: keys must be {KEYS} in that order, got {list(obj.keys())}")
        got.append((obj["ts"], obj["service"], obj["message"]))

    if len(got) != len(expected):
        fail(f"expected {len(expected)} ERROR events, got {len(got)}")
    for i, (g, e) in enumerate(zip(got, expected), start=1):
        if g != e:
            fail(f"record {i} mismatch: got {g}, expected {e}")
    print("ok")


if __name__ == "__main__":
    main()
