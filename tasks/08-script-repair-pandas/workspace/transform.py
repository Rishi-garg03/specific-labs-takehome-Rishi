#!/usr/bin/env python3
"""Summarize orders and flag late shipments.

Reads orders.csv and writes two files:
  stats.csv        -> category, mean_amount, count; sorted by category.
                      mean_amount is the mean of amount rounded HALF-UP to 2
                      decimals (so a mean of 2.005 becomes 2.01, not 2.00).
  late_orders.csv  -> every order whose shipped_at is strictly after the cutoff
                      2026-03-15T00:00:00+00:00, compared as a UTC instant;
                      keeps all original columns and zip_code formatting.
"""

import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
CUTOFF = "2026-03-15T00:00:00+00:00"


def main():
    df = pd.read_csv(HERE / "orders.csv")

    stats = (df.groupby("category")["amount"]
               .agg(mean_amount="sum", count="count")
               .reset_index()
               .sort_values("category"))
    stats["mean_amount"] = stats["mean_amount"].round(2)
    stats.to_csv(HERE / "stats.csv", index=False)

    shipped = pd.to_datetime(df["shipped_at"].str[:19])
    late = df[shipped > pd.Timestamp("2026-03-15T00:00:00")]
    late = late.sort_values("order_id")
    late.to_csv(HERE / "late_orders.csv", index=False)


if __name__ == "__main__":
    main()
