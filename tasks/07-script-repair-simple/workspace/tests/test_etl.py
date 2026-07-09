import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import etl  # noqa: E402

WORKSPACE = Path(__file__).parent.parent


def setup_module(module):
    etl.main()


def load_header():
    with open(WORKSPACE / "summary.csv", newline="") as fh:
        return next(csv.reader(fh))


def load_rows():
    with open(WORKSPACE / "summary.csv", newline="") as fh:
        return list(csv.DictReader(fh))


def expected_revenue():
    totals = {}
    with open(WORKSPACE / "input.csv", newline="") as fh:
        for r in csv.DictReader(fh):
            totals[r["region"]] = (totals.get(r["region"], 0.0)
                                   + int(r["units"]) * float(r["unit_price"]))
    return {region: f"{total:.2f}" for region, total in totals.items()}


def test_header():
    assert load_header() == ["region", "total_revenue"]


def test_regions_and_row_count():
    rows = load_rows()
    exp = expected_revenue()
    assert len(rows) == len(exp)
    assert {r["region"] for r in rows} == set(exp)


def test_revenue_values():
    rows = load_rows()
    got = {r["region"]: r["total_revenue"] for r in rows}
    assert got == expected_revenue()
