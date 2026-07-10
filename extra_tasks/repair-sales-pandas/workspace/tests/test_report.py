import os
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import report  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALES = os.path.join(ROOT, "sales.csv")
OUT = os.path.join(ROOT, "by_region.csv")


def _read_sales_rows():
    with open(SALES) as f:
        header = f.readline().rstrip("\n").split(",")
        idx = {c: i for i, c in enumerate(header)}
        rows = []
        for line in f:
            if not line.strip():
                continue
            rows.append(line.rstrip("\n").split(","))
    return idx, rows


def _expected():
    idx, rows = _read_sales_rows()
    units = defaultdict(int)
    psum = defaultdict(lambda: Decimal("0"))
    pcnt = defaultdict(int)
    for p in rows:
        r = p[idx["region"]]
        units[r] += int(p[idx["units"]])
        psum[r] += Decimal(p[idx["price"]])
        pcnt[r] += 1
    out = []
    for r in sorted(units):
        avg = (psum[r] / pcnt[r]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        out.append((r, units[r], str(avg)))
    return out


def _read_output():
    with open(OUT) as f:
        header = f.readline().rstrip("\n").split(",")
        assert header == ["region", "total_units", "avg_price"], header
        rows = []
        for line in f:
            if not line.strip():
                continue
            parts = line.rstrip("\n").split(",")
            assert len(parts) == 3, parts
            rows.append((parts[0], int(parts[1]), parts[2]))
    return rows


def test_zip_preserved_as_string():
    df = report.read_sales()
    zips = df["zip"].tolist()
    assert all(isinstance(z, str) for z in zips)
    assert all(len(z) == 5 for z in zips)
    # leading zeros must survive, not be truncated to 4 digits
    assert any(z.startswith("0") for z in zips)


def test_by_region_output():
    report.main()
    got = _read_output()
    exp = _expected()
    assert got == exp
