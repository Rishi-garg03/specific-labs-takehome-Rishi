#!/usr/bin/env python3
"""Verifier: merged.csv must equal the recomputed merge of the pristine inputs."""

import csv
import sys
from pathlib import Path

INPUTS = ["sales_q1.csv", "sales_q2.csv", "sales_q3.csv"]
HEADER = ["order_id", "date", "amount"]


def fail(msg):
    print(msg)
    sys.exit(1)


def main():
    workspace = Path(sys.argv[1])
    pristine = Path(__file__).parent / "workspace"

    expected = []
    for name in INPUTS:
        with open(pristine / name) as fh:
            expected.extend((r["order_id"], r["date"], r["amount"])
                            for r in csv.DictReader(fh))
    expected.sort(key=lambda r: int(r[0]))

    out = workspace / "merged.csv"
    if not out.exists():
        fail("merged.csv not found")
    with open(out) as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header != HEADER:
            fail(f"wrong header: {header!r}, expected {HEADER!r}")
        got = [tuple(r) for r in reader]

    if len(got) != len(expected):
        fail(f"expected {len(expected)} rows, got {len(got)}")
    for i, (g, e) in enumerate(zip(got, expected)):
        if g != e:
            fail(f"row {i + 2} mismatch: got {g}, expected {e}")
    print("ok")


if __name__ == "__main__":
    main()
