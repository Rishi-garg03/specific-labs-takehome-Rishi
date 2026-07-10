# Price reconciliation

Your workspace contains two files:

- `price_updates.log` — an append-only price feed. Each *valid* entry is a single line of the form:

  ```
  <iso_timestamp> SET <SKU> <price>
  ```

  where `<iso_timestamp>` is an ISO-8601 timestamp like `2026-03-02T19:54:00`, the literal
  keyword is `SET`, `<SKU>` is the product code, and `<price>` is a decimal or integer number
  (e.g. `19.90`, `100.00`, `7`). Fields are separated by single spaces. The feed also contains
  blank lines, comments, connection noise, and other lines that do not match this exact shape.

- `inventory.csv` — columns `sku,qty`, one row per stocked SKU.

Produce **`priced_inventory.csv`** in the workspace.

## What to compute

1. **Latest price per SKU.** From the log, determine each SKU's most recent price — the price
   from the entry with the newest timestamp for that SKU (this is not necessarily the last such
   line in the file). Any line that does not match the valid entry shape above is not a price
   update and plays no part in this. SKUs are case-insensitive.

2. **Reconcile against inventory.** Write one row for every SKU that appears in `inventory.csv`,
   in the log, or both, with these columns:

   - `sku` — the SKU, uppercased.
   - `qty` — the quantity from `inventory.csv`; use `0` for a SKU that appears only in the log.
   - `price` — that SKU's latest price from the log, written exactly as it appeared in the log.
     Leave this field empty for a SKU that never appears in the log.
   - `status` — `priced` if the SKU had a price in the log, otherwise `unpriced`.

## Output format

`priced_inventory.csv` with this exact header line:

```
sku,qty,price,status
```

followed by the data rows sorted by `sku` ascending.
