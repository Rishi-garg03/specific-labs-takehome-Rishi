#!/usr/bin/env python3
"""Verifier for 04-log-sessionize.

Recomputes the expected sessions from the pristine events.log with independent
logic: skip corrupt lines (tab-field count != 3), tolerate CRLF endings, keep
every event (duplicates included), sort each user's events by (ts, action),
split into sessions whenever the gap from the previous event exceeds 30 minutes
(strictly), then compare row-for-row against sessions.csv.
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

HEADER = ["user_id", "session_index", "start", "end", "events"]
GAP_SECONDS = 30 * 60


def fail(msg):
    print(msg)
    sys.exit(1)


def parse_ts(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")


def expected_rows(log_text):
    by_user = {}
    for line in log_text.splitlines():            # splitlines handles \r\n
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:                       # corrupt line: skip
            continue
        ts, user, action = parts
        by_user.setdefault(user, []).append((ts, action))

    rows = []
    for user in sorted(by_user):
        events = sorted(by_user[user], key=lambda ea: (parse_ts(ea[0]), ea[1]))
        stamps = [ts for ts, _ in events]
        idx = 0
        start = prev = stamps[0]
        count = 1
        for ts in stamps[1:]:
            if (parse_ts(ts) - parse_ts(prev)).total_seconds() > GAP_SECONDS:
                idx += 1
                rows.append((user, idx, start, prev, count))
                start = ts
                count = 1
            else:
                count += 1
            prev = ts
        idx += 1
        rows.append((user, idx, start, prev, count))

    rows.sort(key=lambda r: (r[0], r[1]))
    return [(u, str(i), s, e, str(c)) for (u, i, s, e, c) in rows]


def main():
    workspace = Path(sys.argv[1])
    pristine = Path(__file__).parent / "workspace"

    expected = expected_rows((pristine / "events.log").read_text())

    out = workspace / "sessions.csv"
    if not out.exists():
        fail("sessions.csv not found")

    with open(out, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header != HEADER:
            fail(f"wrong header: {header!r}, expected {HEADER!r}")
        got = [tuple(r) for r in reader]

    if len(got) != len(expected):
        fail(f"expected {len(expected)} rows, got {len(got)}")
    for i, (g, e) in enumerate(zip(got, expected), start=2):
        if g != e:
            fail(f"row {i} mismatch: got {g}, expected {e}")
    print("ok")


if __name__ == "__main__":
    main()
