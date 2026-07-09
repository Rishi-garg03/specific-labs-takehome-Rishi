#!/usr/bin/env python3
"""Verifier: normalized.csv must equal the recomputed normalization of the
pristine dialect files under data/. Independent reference logic below."""

import csv
import sys
from pathlib import Path

HEADER = ["id", "name", "email", "date", "amount"]

# header tuple -> dialect letter
DIALECTS = {
    ("id", "customer_name", "email", "date", "amount"): "A",
    ("ID", "Name", "Email", "Date", "Total"): "B",
    ("cust_id", "client", "contact", "when", "value"): "C",
}

MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
          "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}


def fail(msg):
    print(msg)
    sys.exit(1)


def norm_date(dialect, s):
    if dialect == "A":  # MM/DD/YYYY
        mm, dd, yyyy = s.split("/")
        return f"{yyyy}-{mm}-{dd}"
    if dialect == "B":  # already ISO YYYY-MM-DD
        return s
    # dialect C: "Mon D, YYYY" or DD.MM.YYYY
    if "." in s:
        dd, mm, yyyy = s.split(".")
        return f"{yyyy}-{mm}-{dd}"
    parts = s.replace(",", "").split()  # "Jan 5 2026"
    return f"{int(parts[2])}-{MONTHS[parts[0]]:02d}-{int(parts[1]):02d}"


def norm_amount(dialect, s):
    if dialect == "A":
        value = float(s)
    elif dialect == "B":
        negative = s.startswith("(")
        core = s.strip("()").replace("$", "").replace(",", "")
        value = float(core)
        if negative:
            value = -value
    else:  # C: comma is the decimal separator
        value = float(s.replace(",", "."))
    return f"{value:.2f}"


def main():
    workspace = Path(sys.argv[1])
    pristine = Path(__file__).parent / "workspace"

    expected = []
    for path in sorted((pristine / "data").glob("*.csv")):
        with open(path, newline="") as fh:
            reader = csv.reader(fh)
            header = tuple(next(reader))
            dialect = DIALECTS.get(header)
            if dialect is None:
                fail(f"unrecognized dialect header in {path.name}: {header}")
            for row in reader:
                rid, name, email, date_s, amount_s = row
                expected.append((rid, name, email,
                                 norm_date(dialect, date_s),
                                 norm_amount(dialect, amount_s)))
    expected.sort(key=lambda r: int(r[0]))

    out = workspace / "normalized.csv"
    if not out.exists():
        fail("normalized.csv not found")
    with open(out, newline="") as fh:
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
