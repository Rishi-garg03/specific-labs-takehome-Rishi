#!/usr/bin/env python3
"""Deterministic verifier for the log-extract-severity task.

Usage: python verify.py <RUN_WORKSPACE>

Recomputes the expected incidents.jsonl independently from this file's own
pristine workspace/app.log, then compares (semantically, key-order-aware)
against the produced <RUN_WORKSPACE>/incidents.jsonl.
"""
import json
import re
import sys
from pathlib import Path

LEVELS = ("INFO", "DEBUG", "TRACE", "WARN", "ERROR")
KEEP = ("WARN", "ERROR")
PLAIN_RE = re.compile(r"^(\S+)\s+(\S+)\s+(INFO|DEBUG|TRACE|WARN|ERROR)\s+(.*)$")


def parse_log(text):
    """Return list of ordered [(k,v),...] records (file order), pre-sort."""
    records = []
    for raw in text.split("\n"):
        line = raw.strip()
        if line == "":
            continue
        if line.startswith("{"):
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if not isinstance(obj, dict):
                continue
            level = obj.get("level")
            if level in KEEP:
                records.append([
                    ("ts", obj.get("ts")),
                    ("component", obj.get("component")),
                    ("severity", level),
                    ("message", obj.get("detail")),
                ])
            continue
        m = PLAIN_RE.match(line)
        if not m:
            continue
        ts, comp, level, msg = m.group(1), m.group(2), m.group(3), m.group(4)
        if level in KEEP:
            records.append([
                ("ts", ts),
                ("component", comp),
                ("severity", level),
                ("message", msg),
            ])
    # stable sort by (ts, component) ascending, string compare
    records.sort(key=lambda r: (r[0][1], r[1][1]))
    return records


def load_produced(path):
    text = path.read_text()
    out = []
    for i, raw in enumerate(text.split("\n")):
        if raw.strip() == "":
            continue
        try:
            pairs = json.loads(raw, object_pairs_hook=lambda kv: list(kv))
        except Exception as e:
            return None, f"line {i+1} is not valid JSON: {e}"
        if not isinstance(pairs, list):
            return None, f"line {i+1} is not a JSON object"
        out.append(pairs)
    return out, None


def fail(msg):
    print("MISMATCH: " + msg)
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("usage: python verify.py <RUN_WORKSPACE>")
        sys.exit(2)
    run_ws = Path(sys.argv[1])
    produced_path = run_ws / "incidents.jsonl"
    if not produced_path.exists():
        fail(f"expected output file not found: {produced_path}")

    pristine = Path(__file__).parent / "workspace" / "app.log"
    expected = parse_log(pristine.read_text())

    produced, err = load_produced(produced_path)
    if err is not None:
        fail(err)

    if len(produced) != len(expected):
        fail(f"expected {len(expected)} incidents, got {len(produced)}")

    for idx, (exp, got) in enumerate(zip(expected, produced)):
        exp_keys = [k for k, _ in exp]
        got_keys = [k for k, _ in got]
        if got_keys != ["ts", "component", "severity", "message"]:
            fail(f"line {idx+1}: keys/order must be "
                 f"['ts','component','severity','message'], got {got_keys}")
        if got_keys != exp_keys:
            fail(f"line {idx+1}: key order mismatch: {got_keys} vs {exp_keys}")
        for (ek, ev), (gk, gv) in zip(exp, got):
            if ev != gv:
                fail(f"line {idx+1}: field '{ek}' expected {ev!r} got {gv!r}")

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
