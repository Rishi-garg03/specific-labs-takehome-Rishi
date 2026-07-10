#!/usr/bin/env python3
"""Deterministic verifier for the reconcile-pricing task.

Usage: python verify.py <RUN_WORKSPACE>

Recomputes the expected catalog.csv independently from this file's own pristine
inputs (Path(__file__).parent / "workspace") and compares it against the file
produced under <RUN_WORKSPACE>/catalog.csv. Checks OUTPUTS ONLY.
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

HEADER = ["sku", "qty", "price", "status"]


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def parse_dt(s):
    return datetime.fromisoformat(s.strip())


def is_missing_price(p):
    return p.strip() == "" or p.strip().upper() == "N/A"


def load_latest(path, sku_col, date_col):
    """Return {UPPER_SKU: row_dict}, keeping the row with the latest date per sku
    (case-insensitive grouping)."""
    best = {}  # key -> (datetime, rowdict)
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row[sku_col].strip().upper()
            d = parse_dt(row[date_col])
            if key not in best or d > best[key][0]:
                best[key] = (d, row)
    return {k: v[1] for k, v in best.items()}


def compute_expected(workspace):
    vendor = load_latest(workspace / "vendor.csv", "sku", "updated")
    store = load_latest(workspace / "store.csv", "sku", "seen")

    keys = sorted(set(vendor) | set(store))  # UPPER, plain text ascending sort
    rows = []
    for key in keys:
        v = vendor.get(key)
        s = store.get(key)
        if v is not None and s is not None:
            status = "both"
        elif v is not None:
            status = "vendor_only"
        else:
            status = "store_only"

        qty = str(int(v["qty"])) if v is not None else "0"

        price = None
        if s is not None and not is_missing_price(s["price"]):
            price = s["price"]  # verbatim
        if price is None:
            price = v["cost"] if v is not None else ""  # verbatim fallback

        rows.append([key, qty, price, status])
    return rows


def read_actual(path):
    with open(path, newline="") as f:
        return list(csv.reader(f))


def main():
    if len(sys.argv) != 2:
        fail("usage: python verify.py <RUN_WORKSPACE>")
    run = Path(sys.argv[1])
    pristine = Path(__file__).parent / "workspace"

    out = run / "catalog.csv"
    if not out.exists():
        fail("catalog.csv not found in run workspace")

    expected = compute_expected(pristine)
    actual = read_actual(out)

    if not actual:
        fail("catalog.csv is empty")

    if actual[0] != HEADER:
        fail("header must be exactly %s, got %s" % (",".join(HEADER), ",".join(actual[0])))

    actual_data = actual[1:]

    if len(actual_data) != len(expected):
        fail("row count mismatch: expected %d data rows, got %d"
             % (len(expected), len(actual_data)))

    # detect malformed rows (wrong column count)
    for i, r in enumerate(actual_data):
        if len(r) != 4:
            fail("row %d has %d columns, expected 4: %r" % (i + 1, len(r), r))

    # ordering + duplicate diagnostics
    exp_skus = [r[0] for r in expected]
    act_skus = [r[0] for r in actual_data]
    if act_skus != exp_skus:
        if sorted(act_skus) == sorted(exp_skus):
            # same multiset, different order (or output not uppercased/sorted)
            fail("rows not in expected order (sku ascending, uppercased). "
                 "first divergence at index %d: expected %r got %r"
                 % (next(i for i in range(len(exp_skus)) if exp_skus[i] != act_skus[i]),
                    exp_skus[next(i for i in range(len(exp_skus)) if exp_skus[i] != act_skus[i])],
                    act_skus[next(i for i in range(len(act_skus)) if exp_skus[i] != act_skus[i])]))
        exp_set, act_set = set(exp_skus), set(act_skus)
        missing = sorted(exp_set - act_set)
        extra = sorted(act_set - exp_set)
        msg = "sku set mismatch."
        if missing:
            msg += " missing: %s" % missing[:10]
        if extra:
            msg += " unexpected: %s" % extra[:10]
        fail(msg)

    for i, (e, a) in enumerate(zip(expected, actual_data)):
        if e != a:
            fail("row %d mismatch for sku %s: expected %r got %r" % (i + 1, e[0], e, a))

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
