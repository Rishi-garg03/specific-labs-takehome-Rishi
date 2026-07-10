# Extra test tasks

The take-home ships ten tasks. These are six more I wrote while building the
agent, to push on edges the visible set leaves thin: mixed file encodings,
malformed log lines, SSNs sitting next to look-alike order numbers, a pandas bug
that only bites one row, price reconciliation with a recency tiebreak, and one
task that chains extraction into reconciliation.

The layout matches the provided tasks — a `task.md`, a `workspace/` with the
inputs, and a `verify.py` that recomputes the expected output from its own
pristine copy of the inputs and diffs against what the agent produced. The
verifier checks the output file, never how it was made.

Run one:

    python -m runner.run_task extra_tasks/csv-encoding-merge

Run all six:

    python -m runner.run_task 'extra_tasks/*'

## The tasks

- **csv-encoding-merge** — three order exports whose columns are in different
  orders and whose text is in different encodings (one is latin-1). Merge them,
  drop the `email` column, sort by `id` numerically, and keep every kept value
  byte-exact (`19.90` stays `19.90`, `007` stays `007`).
- **log-extract-severity** — an app log mixing JSON lines, whitespace-delimited
  lines, and noise. Pull only the `WARN`/`ERROR` events into JSONL, in a fixed
  key order, without de-duplicating, sorted by timestamp then component.
- **pii-redact-ssn** — redact emails and standalone SSNs across `notes/*.txt`
  and a `records.jsonl`, in place, leaving `PO-` and `Order ` references
  untouched and never re-serializing the JSON.
- **repair-sales-pandas** — `report.py` has a row-dropping slice and a dtype bug
  (a zip read as a number, banker's rounding where half-up is required). Fix the
  script in place until `pytest -q` passes; the tests and data are off-limits.
- **reconcile-pricing** — reconcile a vendor feed against a store feed: case-fold
  the SKU, collapse duplicate rows within a file by the latest timestamp, and
  draw each output field from the named source with the specified fallback.
- **combined-extract-reconcile** — extract each SKU's latest price from a noisy
  `SET` log, then reconcile against an inventory CSV. A log line counts only on
  exact field count and a numeric price; everything else is noise.

I ran these against the agent while iterating — they're here as extra coverage,
not part of the official set.
