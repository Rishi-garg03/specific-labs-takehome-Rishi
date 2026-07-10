# Reconcile pricing across two systems

Two systems export the same product catalog. You have both exports in this
directory:

- `vendor.csv` with columns `sku,qty,cost,updated`
- `store.csv` with columns `sku,stock,price,seen`

`updated` and `seen` are ISO-8601 timestamps. `cost` and `price` are decimal
strings. `qty` is an integer (it may be negative). `stock` is an integer.

The two systems don't agree on capitalization: the same product may be written
`ab-100` in one file and `AB-100` in the other. Treat SKUs
**case-insensitively** — they refer to the same product.

Within a single file, the same SKU can appear on more than one row (the system
re-exported it over time). When that happens, the row with the **latest**
`updated` (for `vendor.csv`) or `seen` (for `store.csv`) timestamp is the
current one; ignore the older rows for that SKU.

## Output

Write `catalog.csv` in this directory with this exact header:

```
sku,qty,price,status
```

Emit **one row per SKU** across the union of both files, where:

- `sku` — the SKU in **UPPERCASE**.
- `qty` — the vendor's `qty` as a plain integer. If the SKU appears only in
  `store.csv`, use `0`.
- `price` — the store's `price`, copied exactly as written. If the store price
  is empty or `N/A`, or the SKU appears only in `vendor.csv`, use the vendor's
  `cost` instead (again copied exactly as written).
- `status` — `both` if the SKU is in both files, `vendor_only` if only in
  `vendor.csv`, `store_only` if only in `store.csv`.

Sort the rows by `sku` in ascending (text) order.
