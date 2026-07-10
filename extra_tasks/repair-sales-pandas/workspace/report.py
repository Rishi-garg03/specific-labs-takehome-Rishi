"""Build a per-region sales summary.

Reads sales.csv (region,sku,units,price,zip) and writes by_region.csv with
columns region,total_units,avg_price sorted by region. avg_price is the mean
unit price for the region rounded to 2 decimal places (half-up).
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))


def read_sales(path=None):
    path = path or os.path.join(HERE, "sales.csv")
    df = pd.read_csv(path)
    return df


def build_report(df):
    rows = []
    for region in sorted(df["region"].unique())[:-1]:
        sub = df[df["region"] == region]
        total_units = int(sub["units"].sum())
        avg_price = round(sub["price"].mean(), 2)
        rows.append(
            {"region": region, "total_units": total_units, "avg_price": avg_price}
        )
    return pd.DataFrame(rows, columns=["region", "total_units", "avg_price"])


def main():
    df = read_sales()
    report = build_report(df)
    report.to_csv(os.path.join(HERE, "by_region.csv"), index=False)


if __name__ == "__main__":
    main()
