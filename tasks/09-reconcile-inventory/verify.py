#!/usr/bin/env python3
"""Verifier for 09-reconcile-inventory: recompute the reconciliation from the
pristine warehouse.csv + storefront.csv and compare inventory.csv exactly.

Matching is case-insensitive (skus keyed by their uppercase form); within a file
the row with the later updated/last_seen wins; a storefront price of "N/A" or
empty falls back to the warehouse price; the winning price string is carried
through VERBATIM (no reformatting of its precision); negative warehouse
quantities pass through unchanged."""

import csv
import sys
from pathlib import Path

HEADER = ["sku", "qty", "price", "status"]


def fail(msg):
    print(msg)
    sys.exit(1)


def load(path, date_col):
    kept = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            key = r["sku"].upper()
            if key not in kept or r[date_col] > kept[key][date_col]:
                kept[key] = r
    return kept


def reconcile(warehouse, storefront):
    expected = []
    for sku in sorted(set(warehouse) | set(storefront)):
        in_w = sku in warehouse
        in_s = sku in storefront
        qty = str(int(warehouse[sku]["qty"])) if in_w else "0"
        if in_s and storefront[sku]["price_usd"] not in ("", "N/A"):
            price = storefront[sku]["price_usd"]  # verbatim source string
        else:
            price = warehouse[sku]["price"]  # verbatim source string
        status = ("both" if in_w and in_s
                  else "warehouse_only" if in_w else "storefront_only")
        expected.append((sku, qty, price, status))
    return expected


def main():
    workspace = Path(sys.argv[1])
    pristine = Path(__file__).parent / "workspace"

    warehouse = load(pristine / "warehouse.csv", "updated")
    storefront = load(pristine / "storefront.csv", "last_seen")
    expected = reconcile(warehouse, storefront)

    out = workspace / "inventory.csv"
    if not out.exists():
        fail("inventory.csv not found")
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
