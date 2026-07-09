# Fix the orders transform script

The workspace contains `transform.py` (a small pandas script), its input
`orders.csv`, and a `tests/` directory. The test suite currently fails.

`orders.csv` has columns `order_id, zip_code, category, amount, shipped_at`
(where `shipped_at` is an ISO-8601 timestamp with a timezone offset, and
`zip_code` may have leading zeros such as `02134`).

`transform.py` must write two files:

1. `stats.csv` — one row per category with columns `category,mean_amount,count`:
   `mean_amount` is the **mean** of `amount` for that category rounded **half-up**
   to 2 decimals (so a mean of `2.005` becomes `2.01`, not `2.00` — note that
   pandas' `.round(2)` rounds half-to-even on a float and will not do this),
   `count` is the number of orders. Sorted by `category` ascending.
2. `late_orders.csv` — every order whose `shipped_at` is strictly **after**
   the cutoff `2026-03-15T00:00:00+00:00`, compared as a **UTC instant**
   (offsets matter). Keep the original columns, and preserve `zip_code`
   exactly as written in the input, including leading zeros.

The script has bugs. **Fix `transform.py`** so that `pytest -q` passes.

Do **not** modify anything under `tests/`, and do **not** modify `orders.csv` —
the grader restores them before running, so any change there is discarded and
counts as a failure. Only the script should change.
