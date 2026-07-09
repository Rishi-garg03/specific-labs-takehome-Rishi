# Merge two event streams into one timeline

The workspace has two JSON Lines files, `stream_a.jsonl` and `stream_b.jsonl`
(a few thousand lines each). Every line is one JSON object with exactly these
keys:

```json
{"event_id": "ev-48213", "ts": "2026-05-01T02:14:07.250", "type": "click", "payload": "p48213"}
```

- `event_id` is a string.
- `ts` is an ISO-8601 timestamp with **no** timezone. Its precision varies per
  line: some are **seconds** precision (`YYYY-MM-DDTHH:MM:SS`) and some are
  **milliseconds** precision (`YYYY-MM-DDTHH:MM:SS.mmm`, always exactly three
  fractional digits — and `.mmm` can be `.000`). When you need to compare two
  timestamps, treat one with no fractional part as `.000`; but this is only for
  reasoning about order — it does **not** change how a value is written out
  (see rule 1).
- `payload` is an arbitrary string. Some payloads contain double quotes,
  backslashes, and non-ASCII characters (accents, currency symbols, emoji).

Produce `timeline.jsonl` by merging the two streams with these rules.

## 1. Correct stream B's clock

**Known fact:** stream B's clock runs exactly **2000 milliseconds (2 seconds)
fast**. Subtract 2000 ms from the `ts` of every record that comes from stream B.
Stream A's timestamps are already correct — do not change them.

**Preserve each source timestamp's precision.** Because the correction is a
whole number of seconds, it never touches the fractional digits — so a corrected
value is written with **exactly the same number of fractional digits as its
source string**:

- `2026-05-04T10:22:01.250` → `2026-05-04T10:21:59.250` (millisecond source →
  keep three digits);
- `2026-05-04T10:22:01.000` → `2026-05-04T10:21:59.000` (a `.000` source keeps
  its three digits — do **not** collapse it to seconds);
- `2026-05-04T10:22:01` → `2026-05-04T10:21:59` — a bare-seconds source stays
  seconds-precision; **do not** write `2026-05-04T10:21:59.000`.

Do not derive the precision from the parsed value (its microseconds); derive it
from the source string. The subtraction may roll the minute, hour, or day
backward (`2026-05-01T00:00:01` → `2026-04-30T23:59:59`).

## 2. Dedupe

Deduplication happens at two levels:

- **Within a stream.** An `event_id` may appear on more than one line of the
  *same* file. Keep the **first** occurrence (in file order) and drop the later
  ones — do this to each stream independently before merging.
- **Across streams.** After the within-stream dedupe, some `event_id`s appear in
  both streams. Keep **stream A's** record (its `ts`, `type`, and `payload`
  unchanged) and drop B's copy. A record whose `event_id` is only in B is kept
  with the corrected `ts` from rule 1.

## 3. Output format

Each output line is a JSON object with keys in exactly this order: `event_id`,
`ts`, `type`, `payload`. **Serialize each line with a real JSON encoder** (e.g.
Python's `json.dumps`) so that quotes, backslashes, and non-ASCII payloads are
escaped correctly — do not build the JSON by hand with string formatting.

## 4. Sort

Sort the output lines by `ts` ascending, then by `event_id` ascending (both as
strings). The timestamp format above sorts chronologically as text, so a
string comparison is correct — but you must sort **after** correcting B's
timestamps, so the corrected value determines a record's position.

The grader parses each output line as JSON and checks the key order, the values,
and the line order — all must match exactly.
