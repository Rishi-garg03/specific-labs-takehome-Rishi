# Redact contact PII

The workspace contains free-text notes (`notes/*.txt`) and a support ticket
export (`tickets.jsonl`). Scattered through them are email addresses and US
phone numbers (several formats: parenthesized area codes, dots, dashes,
spaces, a leading +1, and bare 10-digit strings).

Edit the files **in place** so that:

1. Every email address is replaced with exactly `[EMAIL]`
2. Every phone number is replaced with exactly `[PHONE]`
3. Order references like `Order #4159940188` are **not** PII — the 10 digits
   after `Order #` are an order number, not a phone, and must stay untouched
4. Nothing else changes — the grader compares your files to the expected
   result byte-for-byte, so over-redaction fails just like under-redaction
5. No files are added, deleted, or renamed

`tickets.jsonl` must remain valid JSONL after redaction (replacing PII inside
string values keeps it valid — just don't break the structure).
