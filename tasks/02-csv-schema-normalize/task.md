# Normalize customer CSVs to one schema

The `data/` directory holds 100 CSV files exported from three different systems.
Every file carries the same five fields — a customer id, a name, an email, a
date, and an amount — but each system uses its own **header labels** and its own
**date and amount encodings**. The three dialects are:

**Dialect A** — header `id,customer_name,email,date,amount`
- date: `MM/DD/YYYY` with zero-padded month and day, e.g. `01/05/2026`
- amount: a plain decimal number, trailing zeros trimmed, e.g. `1234`, `1234.5`,
  or `1234.55` (0, 1, or 2 decimal places)

**Dialect B** — header `ID,Name,Email,Date,Total`
- date: ISO `YYYY-MM-DD`, e.g. `2026-01-05`
- amount: US currency with a `$`, thousands separators, and exactly two
  decimals, e.g. `$1,234.50`. **Negative amounts are written in accounting
  style**, wrapped in parentheses with **no** dollar sign, e.g. `(1,234.50)`
  means `-1234.50`.

**Dialect C** — header `cust_id,client,contact,when,value`
- date: **one of two formats**, and both may appear even within the same file:
  - `Mon D, YYYY` — three-letter English month, day with **no** leading zero,
    e.g. `Jan 5, 2026`
  - `DD.MM.YYYY` — zero-padded **day first**, then month, dot-separated,
    e.g. `05.01.2026` (this is the 5th of January, not May 1st)
- amount: comma as the decimal separator, exactly two decimals, no thousands
  separator, no sign, e.g. `1234,50`

A file's dialect is identified by its header row. You may assume every file
matches one of the three headers above exactly.

## Data notes (read before parsing)

- **Names may contain commas.** Some names are written surname-first, e.g.
  `Torres, Maya`. In the source files these are quoted per RFC 4180
  (`"Torres, Maya"`). Splitting a line on commas will mis-parse these rows — use
  a real CSV parser.
- **Emails may be empty.** Some rows have an empty email cell; copy it through
  as an empty value (do not drop the row or invent a placeholder).
- **Ids are strings, and some carry leading zeros** (e.g. `0042317`). The
  padding is part of the id and must appear in the output **verbatim** —
  `0042317` and `42317` are different ids. Sorting is still numeric (rule 6),
  but the *value written out* is the original string. Round-tripping ids
  through integers will corrupt them.

## Output

Produce a single file `normalized.csv` in the workspace root with:

1. Header exactly: `id,name,email,date,amount`
2. One row for every input row across all 100 files
3. `id`, `name`, and `email` copied through unchanged (an empty email stays
   empty)
4. `date` converted to ISO `YYYY-MM-DD` (zero-padded month and day)
5. `amount` as a plain decimal string with exactly two decimal places, no
   currency symbol and no thousands separator. Negative amounts carry a leading
   minus sign, e.g. `-1234.50`
6. Rows sorted by `id` ascending, compared **numerically**
7. The output must be **valid RFC-4180 CSV**: any field containing a comma,
   quote, or newline must be quoted (a real CSV writer does this for you)

The grader compares your output mechanically — it re-parses your CSV, so a name
with a comma must be quoted correctly. Header, row order, and every value must
match exactly.
