# Redact PII in place

This directory holds customer-support material that contains personal data. Redact the personal data, editing the files in place.

## Files

- `notes/*.txt` — free-form plain-text notes.
- `records.jsonl` — one JSON object per line. Each object has a string field `body` that holds the free text (objects may also carry other fields such as `id`, `author`, `ip`, `date`, or `tag`).

## What to redact

1. **Email addresses** → replace each with the literal token `[EMAIL]`.

   An email address is: one or more of `A-Za-z0-9._%+-`, then `@`, then one or more of `A-Za-z0-9.-`, then a `.` followed by a TLD of two or more letters.

2. **US Social Security Numbers** → replace each with the literal token `[SSN]`.

   An SSN is a standalone number in the shape `ddd-dd-dddd` (three digits, a hyphen, two digits, a hyphen, four digits). *Standalone* means it is not bordered by another digit on either side — a `ddd-dd-dddd` that sits inside a longer run of digits is not an SSN.

   **Exception:** purchase-order references are not SSNs and must be left exactly as they are. When the `ddd-dd-dddd` is immediately preceded by `PO-` (e.g. `PO-123-45-6789`) or by `Order ` (the word `Order` and a single space, e.g. `Order 123-45-6789`), do not redact it.

Make no other changes. Anything that is not an email or an SSN under the rules above must stay byte-for-byte identical.

## Rules

- Edit every file **in place**. Do not create, rename, or delete any file — no backups, no new output files.
- In `records.jsonl`, change only the characters inside the JSON string values. Keys, field ordering, punctuation, spacing, and any non-ASCII characters must be preserved exactly. Do **not** re-serialize the JSON — operate on the file's text.

## Output

The same files (`notes/*.txt` and `records.jsonl`), edited in place.
