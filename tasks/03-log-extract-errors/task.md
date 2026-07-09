# Extract ERROR events from a service log

The workspace contains `service.log`, a single file that interleaves three kinds
of lines.

**(a) JSON lines** — one JSON object per line, with keys `ts`, `level`, `svc`,
`msg`:

    {"ts": "2026-03-14T09:21:07", "level": "INFO", "svc": "auth", "msg": "request completed"}

**(b) plain lines** — whitespace-separated fields
`<ts> <service> <level> <message...>` (four or more fields; the message is
everything after the level token and may contain spaces):

    2026-03-14T09:21:08 worker-3 ERROR failed to flush queue

**(c) noise lines** — anything that is neither of the above: stack-trace
fragments, separators like `---`, blank lines. Ignore them completely.

## Output

Write `errors.jsonl` (JSON Lines: one JSON object per line) containing exactly
one object for every line whose level is `ERROR`, drawn from shapes (a) and (b)
only. Each object has these three keys **in this exact order**:

- `ts` — the timestamp string, copied verbatim
- `service` — for a JSON line, the `svc` value; for a plain line, the second
  field
- `message` — for a JSON line, the `msg` value; for a plain line, everything
  after the level token

## Rules

1. Include only `ERROR` events. `INFO` and `WARN` lines are dropped.
2. Emit one JSON object per line, keys in the order `ts`, `service`, `message`.
3. Sort the output by `ts` ascending, then by `service` ascending. Both are
   compared as plain strings.

## Example

The plain line in shape (b) above produces exactly this output line:

    {"ts": "2026-03-14T09:21:08", "service": "worker-3", "message": "failed to flush queue"}

The grader parses each output line as JSON and compares the records (and their
order) exactly, so extra events, missing events, wrong key order, or wrong sort
order all fail.
