#!/usr/bin/env python3
"""Deterministic verifier for the csv-encoding-merge task.

Usage: python verify.py <RUN_WORKSPACE>

The expected output is recomputed independently from this file's OWN pristine
inputs (Path(__file__).parent / "workspace"), never from hardcoded answers.
Only the produced output is checked, never how it was produced.
"""
import csv
import sys
from pathlib import Path

INPUT_FILES = ("orders_alpha.csv", "orders_beta.csv", "orders_gamma.csv")
KEEP = ["id", "name", "amount", "date"]
HEADER = ["id", "name", "amount", "date"]


def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)


def read_source(path):
    """Read one input CSV, tolerant of per-file encoding (utf-8 or latin-1).

    Try strict UTF-8 first; if the bytes aren't valid UTF-8, fall back to
    latin-1 (ISO-8859-1). Returns a list of dicts with the four kept fields,
    values preserved exactly as strings.
    """
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    reader = csv.DictReader(text.splitlines())
    fields = reader.fieldnames or []
    for col in KEEP:
        if col not in fields:
            fail(f"input {path.name} missing expected column {col!r}")
    rows = []
    for r in reader:
        rows.append({col: r[col] for col in KEEP})
    return rows


def expected_rows():
    ws = Path(__file__).resolve().parent / "workspace"
    all_rows = []
    for fn in INPUT_FILES:
        all_rows.extend(read_source(ws / fn))
    # Stable sort by NUMERICAL id. Input integer ids are unique, so the numeric
    # key fully determines the order.
    all_rows.sort(key=lambda r: int(r["id"]))
    return all_rows


def read_output(run_ws):
    out = Path(run_ws) / "merged.csv"
    if not out.exists():
        fail("merged.csv not found in run workspace")
    raw = out.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        fail(f"merged.csv is not valid UTF-8 ({e}); accented names must be UTF-8 encoded")
    reader = csv.reader(text.splitlines())
    try:
        header = next(reader)
    except StopIteration:
        fail("merged.csv is empty")
    rows = list(reader)
    return header, rows


def main():
    if len(sys.argv) != 2:
        fail("usage: python verify.py <RUN_WORKSPACE>")
    run_ws = sys.argv[1]

    exp = expected_rows()
    header, out_rows = read_output(run_ws)

    if header != HEADER:
        fail(f"header must be exactly {HEADER}, got {header}")

    if len(out_rows) != len(exp):
        fail(f"expected {len(exp)} data rows, got {len(out_rows)}")

    for i, (got, want) in enumerate(zip(out_rows, exp)):
        if len(got) != len(HEADER):
            fail(f"row {i} has {len(got)} columns, expected {len(HEADER)}: {got!r}")
        want_row = [want["id"], want["name"], want["amount"], want["date"]]
        if got != want_row:
            fail(f"row {i} mismatch:\n  expected {want_row!r}\n  got      {got!r}")

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
