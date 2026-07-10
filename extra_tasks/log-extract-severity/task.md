# Extract incidents from an application log

`workspace/app.log` is a raw application log. Its lines come in three shapes,
interleaved in arbitrary order:

1. **JSON lines** — a single JSON object with the keys `ts`, `level`,
   `component`, `detail`. Example:
   `{"ts": "2024-03-10T08:00:27", "level": "WARN", "component": "db", "detail": "token refresh succeeded"}`

2. **Plain lines** — whitespace-separated fields in the form
   `<ts> <component> <LEVEL> <message>`, where `<ts>` and `<component>` are
   single tokens (no spaces), `<LEVEL>` is one of the uppercase level names,
   and `<message>` is the rest of the line and may contain spaces. Example:
   `2024-03-10T08:01:46 db ERROR token refresh succeeded`

3. **Noise** — anything else: blank lines, separators, stack-trace fragments,
   comments, unparseable text, etc.

The recognized level names are `INFO`, `DEBUG`, `TRACE`, `WARN`, `ERROR`.

## Task

Write `workspace/incidents.jsonl` containing one JSON object per line for
**every** log line whose level is `WARN` or `ERROR`. Lines at any other level
(`INFO`, `DEBUG`, `TRACE`) are excluded, and noise lines are ignored.

Each output object must have exactly these four keys, **in this order**:

- `ts` — the timestamp
- `component` — the component
- `severity` — the level string (`WARN` or `ERROR`)
- `message` — for a JSON line, its `detail`; for a plain line, the message
  portion (everything after the level token)

Rules:

- Do **not** de-duplicate: if the same event appears more than once, emit it
  every time.
- Sort the output by `ts` ascending, then by `component` ascending, using
  ordinary string comparison.

Write only `workspace/incidents.jsonl`. One JSON object per line.
