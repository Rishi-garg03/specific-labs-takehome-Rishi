# Split events into sessions

The workspace contains `events.log`. It is large (tens of thousands of lines);
inspect it with a program, not by eyeballing a `cat`.

Each **valid** line is three TAB-separated fields:

    <ts>\t<user_id>\t<action>

for example (the separator is a literal tab character):

    2026-05-01T09:00:00	u0001	login

The file is written in roughly chronological order, but individual lines are
slightly out of order, so you must sort before analyzing.

## Parsing rules

1. A **valid** line has exactly **three** tab-separated fields. Any line that
   does not (wrong field count, junk markers, blank lines) is **corrupt** and
   must be **skipped**, not parsed.
2. Some lines use Windows **CRLF** (`\r\n`) endings. Treat `\r\n` exactly like
   `\n`; a trailing `\r` is not part of the `action`.
3. **Duplicate events are real.** Two events for the same user may share a
   timestamp, and may even be byte-for-byte identical (same `ts` and `action`).
   Count every event; never deduplicate.
4. When you sort a user's events, order them by `ts` ascending and break ties
   by `action` ascending. (Equal timestamps never change a session boundary,
   but this keeps the ordering well-defined.)

## Sessionizing rule

Process each user independently:

1. Sort that user's events by `ts` ascending (ties by `action`, per rule 4).
2. Walk the sorted events. A **new session** begins whenever the gap from the
   previous event is **strictly greater than 30 minutes** (more than 1800
   seconds). A gap of **exactly** 30 minutes (1800 seconds) stays in the **same**
   session; a gap of 1801 seconds starts a new one.

## Output

Write `sessions.csv` with this exact header:

    user_id,session_index,start,end,events

One row per session:

- `user_id` — the user
- `session_index` — 1-based index of the session for that user, in chronological
  order (the user's earliest session is 1)
- `start` — the `ts` of the session's first event (verbatim)
- `end` — the `ts` of the session's last event (verbatim)
- `events` — the number of events in the session (duplicates included)

Sort the rows by `user_id` ascending (as a string), then by `session_index`
ascending (as a number).

## Worked example

Three events for one user:

    2026-05-01T09:00:00	u01	login
    2026-05-01T09:15:00	u01	view
    2026-05-01T09:46:00	u01	logout

Gaps: 09:00 → 09:15 is 15 minutes (same session); 09:15 → 09:46 is 31 minutes
(> 30, so a new session starts at 09:46). This yields two sessions:

    user_id,session_index,start,end,events
    u01,1,2026-05-01T09:00:00,2026-05-01T09:15:00,2
    u01,2,2026-05-01T09:46:00,2026-05-01T09:46:00,1
