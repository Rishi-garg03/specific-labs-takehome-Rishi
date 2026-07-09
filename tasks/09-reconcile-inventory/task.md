# Reconcile warehouse and storefront inventory

The workspace has two CSV files that describe the same catalog of products from
two systems (each has a few thousand rows):

- `warehouse.csv` — header `sku,qty,price,updated`
- `storefront.csv` — header `sku,stock,price_usd,last_seen`

Some skus appear in both files, some in only one. Produce a single reconciled
file `inventory.csv` with the header exactly:

```
sku,qty,price,status
```

Output **one row per sku in the union** of the two files.

## Matching skus (case-insensitive)

The two systems do not agree on the letter case of a sku: the same product may
be written `SKU-0042` in one file and `sku-0042` in the other. **Match skus
case-insensitively** — treat a sku as its uppercase form when deciding whether
two rows refer to the same product, and **write every output `sku` uppercased**.

## Duplicate rows within a file

A sku may appear on **more than one row within the same file** (a later re-count
or re-scrape). When a file has two rows for the same sku, keep the one with the
**later** `updated` (warehouse) / `last_seen` (storefront) value — both are ISO
dates (`YYYY-MM-DD`), so a later date is the more recent row. Use that row's
values and ignore the older one.

## Field rules

Apply these to every output row:

1. **qty** — the `qty` from `warehouse.csv`, written as a plain integer. A
   warehouse `qty` can be **negative** (a returns adjustment, e.g. `-14`); pass
   it through unchanged. If the sku is **not** in `warehouse.csv`, `qty` is `0`.
2. **price** — the `price_usd` from `storefront.csv`, copied through **exactly
   as written in the source file** (the verbatim source string). **But** if that
   storefront cell is `N/A` or empty, *or* the sku is not in `storefront.csv` at
   all, use the `price` from `warehouse.csv` instead (again verbatim). (Every
   sku that has an `N/A`/empty storefront price also has a warehouse row, so a
   fallback price always exists.)

   Prices in both files carry **irregular precision** — you will see zero, one,
   two, and three decimal places (`99`, `15.6`, `8.00`, `12.375`). Do **not**
   reformat or renormalize the winning value: copy its characters straight
   through. `15.6` must stay `15.6` (not `15.60`), `99` must stay `99` (not
   `99.00`), and `12.375` must stay `12.375` (not rounded to `12.38`). In
   particular, do not route the price through a float or a `"%.2f"` formatter —
   that rewrites the string.
3. **status** — one of:
   - `both` — the sku is in both files
   - `warehouse_only` — the sku is only in `warehouse.csv`
   - `storefront_only` — the sku is only in `storefront.csv`

Sort the output rows by `sku` ascending, compared as text (lexicographic); since
every output sku is uppercase and fixed-width, that is also numeric order.

Notes / worked example:

- Take **qty from the warehouse** and **price from the storefront** — do not
  swap in the storefront `stock` or the warehouse `price` for a sku that is in
  both files. The two systems disagree on those numbers on purpose.
- Example: `warehouse.csv` has `sku-0042,120,88.4,2026-03-01` and
  `storefront.csv` has `SKU-0042,95,91.5,2026-04-02`. The output row is
  `SKU-0042,120,91.5,both` — uppercased sku, warehouse qty `120`, storefront
  price copied verbatim as `91.5` (not `91.50`). If the storefront price cell
  had been `N/A`, the row would be `SKU-0042,120,88.4,both` (warehouse price
  `88.4`, again verbatim).

The grader compares your output mechanically — header, row order, and every
value must match exactly.
