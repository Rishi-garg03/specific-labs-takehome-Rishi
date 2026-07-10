# Merge customer order CSVs

This directory contains three CSV exports of customer orders, each pulled from a
different internal system:

- `orders_alpha.csv`
- `orders_beta.csv`
- `orders_gamma.csv`

Every file carries the same five fields — `id`, `name`, `email`, `amount`, `date` —
but the **column order is not the same** from file to file.

Produce a single file named `merged.csv` in this same directory that:

- Has the header exactly: `id,name,amount,date` (the `email` column is dropped).
- Contains exactly one row for every row across all three input files.
- Is sorted by `id` in ascending **numerical** order.
- Preserves every kept value **exactly** as it appears in the input. Do not
  reformat amounts, dates, or ids — an amount written `19.90` must stay `19.90`
  (not `19.9`), and an id written `007` must stay `007` (not `7`).
- Is written in UTF-8.

Write only `merged.csv`. Do not modify the input files.
