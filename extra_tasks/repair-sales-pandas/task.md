# Fix `report.py`

`report.py` turns `sales.csv` into a per-region summary, but the test suite in
`tests/` is failing. Make the tests pass.

## The data

`sales.csv` has columns `region,sku,units,price,zip`.

## What `report.py` must produce

`report.main()` writes `by_region.csv` next to `report.py` with exactly this
header and one row per region, sorted ascending by region name:

```
region,total_units,avg_price
```

- `total_units` — sum of `units` for the region.
- `avg_price` — the mean of `price` over the region's rows, rounded to 2
  decimal places using half-up rounding, and always written with exactly two
  decimals.

`report.py` also exposes `read_sales()`, which returns the sales data as a
DataFrame. `zip` is a postal code, not a number.

## Rules

- Fix `report.py` only. Do not edit anything under `tests/` and do not edit
  `sales.csv`.
- Run the suite with `pytest -q`. All tests must pass.
