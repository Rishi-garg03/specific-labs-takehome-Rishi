import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

import transform  # noqa: E402

WORKSPACE = Path(__file__).parent.parent
CUTOFF = pd.Timestamp("2026-03-15T00:00:00", tz="UTC")


def setup_module(module):
    transform.main()


def read_orders():
    return pd.read_csv(WORKSPACE / "orders.csv",
                       dtype={"zip_code": str, "order_id": str, "amount": str})


def half_up_mean(amounts):
    total = sum(Decimal(a) for a in amounts)
    return (total / Decimal(len(amounts))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP)


def test_stats_categories_and_count():
    orders = read_orders()
    stats = pd.read_csv(WORKSPACE / "stats.csv")
    assert list(stats.columns) == ["category", "mean_amount", "count"]
    exp = orders.groupby("category")["amount"].count().sort_index()
    got = stats.set_index("category")["count"].sort_index()
    assert list(got.index) == list(exp.index)
    assert got.to_dict() == exp.to_dict()


def test_stats_mean_amount():
    orders = read_orders()
    stats = pd.read_csv(WORKSPACE / "stats.csv",
                        dtype={"category": str, "mean_amount": str})
    got = dict(zip(stats["category"], stats["mean_amount"]))
    for category, group in orders.groupby("category"):
        expected = half_up_mean(list(group["amount"]))
        assert Decimal(got[category]) == expected, (
            f"{category}: got {got[category]!r}, want {expected}")


def test_late_orders_set():
    orders = read_orders()
    shipped = pd.to_datetime(orders["shipped_at"], utc=True)
    expected_ids = set(orders.loc[shipped > CUTOFF, "order_id"])
    late = pd.read_csv(WORKSPACE / "late_orders.csv", dtype={"order_id": str})
    assert set(late["order_id"].astype(str)) == expected_ids


def test_late_orders_zip_preserved():
    orders = read_orders().set_index("order_id")
    late = pd.read_csv(WORKSPACE / "late_orders.csv", dtype=str)
    assert len(late) > 0
    for _, row in late.iterrows():
        assert row["zip_code"] == orders.loc[str(row["order_id"]), "zip_code"]
