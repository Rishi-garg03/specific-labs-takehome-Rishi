# Fix the revenue summary script

The workspace contains a small ETL script `etl.py`, its input `input.csv`, and
a `tests/` directory. Running the test suite currently fails.

`etl.py` reads `input.csv` (columns `id,region,units,unit_price`) and must
write `summary.csv` with:

1. The header exactly: `region,total_revenue`
2. One row per region
3. `total_revenue` = the sum of `units * unit_price` over **every** row of that
   region, formatted with exactly 2 decimals
4. Rows sorted by `region` ascending

The script has bugs that make it produce the wrong output. **Fix `etl.py`** so
that `pytest -q` passes.

Do **not** modify anything under `tests/`, and do **not** modify `input.csv` —
the grader restores them before running, so changes there are discarded (and
count as a failure). Only the script should change.
