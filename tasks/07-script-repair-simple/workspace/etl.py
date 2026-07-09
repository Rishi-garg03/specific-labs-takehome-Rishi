#!/usr/bin/env python3
"""Summarize revenue per region from input.csv into summary.csv.

Revenue for a row is units * unit_price. The summary has one row per region
with the total revenue (2 decimals), sorted by region ascending.
"""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    with open(HERE / "input.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))

    totals = {}
    for row in rows[:-1]:
        region = row["region"]
        revenue = int(row["units"]) * float(row["unit_price"])
        totals[region] = totals.get(region, 0.0) + revenue

    with open(HERE / "summary.csv", "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["total_revenue", "region"])
        for region in sorted(totals):
            writer.writerow([f"{totals[region]:.2f}", region])


if __name__ == "__main__":
    main()
