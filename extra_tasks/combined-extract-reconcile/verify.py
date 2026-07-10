import sys, csv, re
from pathlib import Path
from datetime import datetime

# Usage: python verify.py <RUN_WORKSPACE>
# Recomputes the expected priced_inventory.csv independently from this file's
# own pristine workspace, then compares against the produced output.

PRICE_RE = re.compile(r"\d+(\.\d+)?")


def compute_expected(ws: Path):
    # Step 1: extract latest price per SKU (case-insensitive key, uppercased).
    latest = {}  # SKU_UPPER -> (datetime, price_str_verbatim)
    with open(ws / "price_updates.log") as f:
        for line in f:
            toks = line.rstrip("\n").split()
            if len(toks) != 4:
                continue
            ts_s, kw, sku, pr = toks
            if kw != "SET":
                continue
            try:
                t = datetime.fromisoformat(ts_s)
            except ValueError:
                continue
            try:
                float(pr)
            except ValueError:
                continue
            su = sku.upper()
            if su not in latest or t > latest[su][0]:
                latest[su] = (t, pr)
    log_price = {k: v[1] for k, v in latest.items()}

    # Step 2: reconcile with inventory (union of inventory + log skus).
    inv_qty = {}
    with open(ws / "inventory.csv", newline="") as f:
        for row in csv.DictReader(f):
            inv_qty[row["sku"].upper()] = row["qty"]

    rows = [["sku", "qty", "price", "status"]]
    for s in sorted(set(inv_qty) | set(log_price)):
        qty = inv_qty.get(s, "0")
        if s in log_price:
            rows.append([s, qty, log_price[s], "priced"])
        else:
            rows.append([s, qty, "", "unpriced"])
    return rows


def read_rows(path: Path):
    with open(path, newline="") as f:
        return [row for row in csv.reader(f)]


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        fail("usage: python verify.py <RUN_WORKSPACE>")
    run_ws = Path(sys.argv[1])
    pristine_ws = Path(__file__).parent / "workspace"

    out = run_ws / "priced_inventory.csv"
    if not out.exists():
        fail("priced_inventory.csv not found in run workspace")

    expected = compute_expected(pristine_ws)

    try:
        actual = read_rows(out)
    except Exception as e:
        fail(f"could not parse priced_inventory.csv: {e}")

    if not actual:
        fail("priced_inventory.csv is empty")

    if actual[0] != ["sku", "qty", "price", "status"]:
        fail(f"header mismatch: expected ['sku','qty','price','status'], got {actual[0]!r}")

    if len(actual) != len(expected):
        fail(f"row count mismatch: expected {len(expected)-1} data rows, got {len(actual)-1}")

    for i, (e, a) in enumerate(zip(expected, actual)):
        if len(a) != 4:
            fail(f"row {i} does not have exactly 4 fields: {a!r}")
        if e != a:
            fail(f"row {i} mismatch: expected {e!r}, got {a!r}")

    print("ok")


if __name__ == "__main__":
    main()
