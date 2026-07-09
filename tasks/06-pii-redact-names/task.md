# Redact customer names from chat transcripts

The workspace contains support-chat transcripts (`transcripts/chat_1.txt` ..
`transcripts/chat_5.txt`) with lines like `AGENT: ...` and `CUSTOMER: ...`,
plus a lookup table `roster.csv` with the header `customer_id,full_name`.

Every customer named in `roster.csv` may appear in the transcripts in **four
shapes**, and each one must be replaced with exactly `[NAME]`:

1. **Full name** — e.g. `Maya Torres`
2. **First name alone** — e.g. `Maya`
3. **Honorific + last name** — e.g. `Ms. Torres` or `Mr. Torres` (include the
   honorific in the replaced span, so `Ms. Torres` becomes `[NAME]`, not
   `Ms. [NAME]`)
4. **Possessive** — a name (shape 1 or 2) immediately followed by `'s`, e.g.
   `Maya's` or `Maya Torres's`. Redact only the name span and **keep the `'s`**,
   so `Maya's order` becomes `[NAME]'s order` (not `[NAME] order` and not
   `[NAME]s order`)

Edit the transcript files **in place**. Then:

1. Replace every occurrence of every roster-name shape above with `[NAME]`
2. **Do not modify `roster.csv`** — it is a reference table, not a target
3. **Not every capitalized, name-like token is a person.** Company names,
   products, and street names that merely look like names must survive
   untouched. For example `Morgan & Reed LLC`, `Ada Terminal`, and
   `Watson Ave` are NOT customers and must be left exactly as they are. Only
   names that resolve to a `roster.csv` entry get redacted.
4. Nothing else changes — the grader compares your files byte-for-byte, so
   **over-redaction fails just like under-redaction**
5. No files are added, deleted, or renamed
