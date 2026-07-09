# Merge quarterly sales files

The workspace contains three CSV files: `sales_q1.csv`, `sales_q2.csv`,
`sales_q3.csv`. They hold the same three columns — `order_id`, `date`,
`amount` — but the column ORDER differs between files.

Produce a single file `merged.csv` that:

1. Has the header exactly: `order_id,date,amount`
2. Contains every row from all three input files
3. Is sorted by `order_id` ascending (numeric)
4. Preserves every value exactly as it appears in the input (no reformatting
   of dates or amounts)

The grader compares your output mechanically — header, row order, and values
must match exactly.
