#!/usr/bin/env python3
"""Verifier for 10-reconcile-events: recompute the merged timeline from the
pristine streams and compare timeline.jsonl line by line.

Rules recomputed: dedupe within each stream keeping the first occurrence; A wins
on ids shared across streams; every B timestamp is corrected by -2000 ms while
preserving the source string's precision (a source with a fractional part keeps
three fractional digits, including ".000"; a bare-seconds source stays
seconds-precision); sort by (ts, event_id) after correction. Each output line is
parsed as JSON, and its key order and values are checked."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

KEYS = ["event_id", "ts", "type", "payload"]


def fail(msg):
    print(msg)
    sys.exit(1)


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def correct(ts):
    """Subtract 2000 ms, preserving the SOURCE string's precision: if the source
    had a fractional part keep three fractional digits (including ".000"); if it
    had none stay seconds-precision."""
    dt = datetime.fromisoformat(ts) - timedelta(seconds=2)
    base = dt.strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{dt.microsecond // 1000:03d}" if "." in ts else base


def dedupe(records):
    seen, out = set(), []
    for r in records:
        if r["event_id"] in seen:
            continue
        seen.add(r["event_id"])
        out.append(r)
    return out


def build(a_records, b_records):
    a_records = dedupe(a_records)
    b_records = dedupe(b_records)
    a_ids = {r["event_id"] for r in a_records}
    merged = [{"event_id": r["event_id"], "ts": r["ts"],
               "type": r["type"], "payload": r["payload"]} for r in a_records]
    for r in b_records:
        if r["event_id"] in a_ids:
            continue
        merged.append({"event_id": r["event_id"], "ts": correct(r["ts"]),
                       "type": r["type"], "payload": r["payload"]})
    merged.sort(key=lambda r: (r["ts"], r["event_id"]))
    return merged


def main():
    workspace = Path(sys.argv[1])
    pristine = Path(__file__).parent / "workspace"

    merged = build(read_jsonl(pristine / "stream_a.jsonl"),
                   read_jsonl(pristine / "stream_b.jsonl"))

    out = workspace / "timeline.jsonl"
    if not out.exists():
        fail("timeline.jsonl not found")
    got = read_jsonl(out)

    if len(got) != len(merged):
        fail(f"expected {len(merged)} events, got {len(got)}")
    for i, (g, e) in enumerate(zip(got, merged)):
        if list(g.keys()) != KEYS:
            fail(f"line {i + 1}: keys {list(g.keys())}, expected {KEYS}")
        if [g[k] for k in KEYS] != [e[k] for k in KEYS]:
            fail(f"line {i + 1} mismatch: got {[g.get(k) for k in KEYS]}, "
                 f"expected {[e[k] for k in KEYS]}")
    print("ok")


if __name__ == "__main__":
    main()
