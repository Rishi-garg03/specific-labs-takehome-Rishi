# Agent rewrite — write-up

## Result

Definitive evaluation: **16 attempts × 10 tasks = 160 graded runs** through the real
`runner.run_task` harness (true `verify.py` + the $0.05 budget), 16 in parallel, in 162s.

> **153/160 solved (95.6 %) · 160/160 correct (100 %)** · total spend $4.07 (~$0.025/run)

| task | solved | correct | overbudget | wrong | avg $ |
|---|---|---|---|---|---|
| 01-csv-merge-basic | 16/16 | 16/16 | 0 | 0 | $0.018 |
| 02-csv-schema-normalize | 16/16 | 16/16 | 0 | 0 | $0.024 |
| 03-log-extract-errors | 16/16 | 16/16 | 0 | 0 | $0.010 |
| 04-log-sessionize | 16/16 | 16/16 | 0 | 0 | $0.020 |
| 05-pii-redact-basic | 16/16 | 16/16 | 0 | 0 | $0.036 |
| 06-pii-redact-names | 11/16 | 16/16 | 5 | 0 | $0.046 |
| 07-script-repair-simple | 16/16 | 16/16 | 0 | 0 | $0.030 |
| 08-script-repair-pandas | 14/16 | 16/16 | 2 | 0 | $0.036 |
| 09-reconcile-inventory | 16/16 | 16/16 | 0 | 0 | $0.019 |
| 10-reconcile-events | 16/16 | 16/16 | 0 | 0 | $0.015 |

The agent produces the **correct output on every attempt of every task**. The only 7 runs that
don't count are the two hardest tasks (06, 08) occasionally exceeding the $0.05 budget — never a
wrong answer. Median run: **4 model calls, $0.023**, which is full marks on the efficiency term
(`min(1, 0.03/cost)`).

## What is being graded

`final = 0.75·solve_rate + 0.25·efficiency`, where a task is **SOLVED** only if `verify.py`
passes **and** the run cost ≤ **$0.05**, and `efficiency = min(1, $0.03 / cost)`. The hidden
suite runs every task **twice**, so run-to-run flakiness directly halves credit. The agent's CLI,
its OpenRouter/`openai` model access, and its per-call usage log are a fixed contract the runner
depends on; `runner/` was not touched.

## Why the baseline scored ~6 %

Reading the shipped `agent/run.py`, two failure modes stand out:

1. **It pours the data into the model.** A 30-turn loop lets the model `cat` inputs, and every
   tool result is appended to a transcript that is re-sent on each call. Task 02 alone ships 100
   CSVs — feeding them in is ~170k tokens (~$0.19, roughly **4× the budget**) before a single line
   of output is written.
2. **It never checks its work.** The loop terminates the moment the model replies without a tool
   call — i.e. on the model's own say-so. On unfamiliar data the subtle rules (exact-value
   preservation, RFC-4180, half-up rounding, UTC instants, redaction precision) are silently
   violated and nothing catches it.

## The approach: the model writes code, it never touches the data

The core move: **the model reads the *rules*, writes ONE script, runs it, a program checks the
result, it retries if the check fails, then stops.** The bulk data flows through Python, never
through the LLM — which fixes the cost leak and the correctness leak at the same time, and
generalizes to unseen tasks because the agent reasons about *rules*, not *rows*.

```
inventory(workspace)        # Python summarizes files (headers/samples) — data never enters context
   ↓
system prompt (per task type) + task + inventory
   ↓  loop (≤6 turns transform / ≤8 repair)
model → bash tool → write /tmp/solve.py (or edit the module in place) → run it
   ↓  model stops (no tool call)
gate(workspace)             # PROGRAMMATIC completion check, not the model's word
   ├─ pass → exit 0
   └─ fail → "not finished: <reason>", retry
```

The rewrite is a small, comment-free package (each file does one thing):

| module | role |
|---|---|
| `agent/run.py` | the loop, model calls, honest usage logging, transcript hook |
| `agent/prompt.py` | per-type system prompts assembled from blocks |
| `agent/probe.py` | Python-side workspace inventory + snapshot |
| `agent/shell.py` | a persistent bash tool (state persists, `restart` supported) |
| `agent/gate.py` | the programmatic completion gate |
| `agent/config.py`, `agent/usage.py`, `agent/transcript.py` | constants, 4-key usage log, optional (env-gated) run transcript |

Key mechanisms:

- **Python inventory, not `cat`.** `probe.inventory()` lists files, shows small files in full and
  groups many same-shaped files (02's 100 CSVs collapse to the 3 dialects), capped to ~2k tokens.
  The model gets everything it needs to write the script without the data ever entering context.
- **Two flows, auto-routed.** A `tests/` directory ⇒ **repair** (edit the target module in place,
  make `pytest` pass); otherwise **transform** (write `/tmp/solve.py`, write the named output).
  Scratch files stay in `/tmp` so in-place tasks never leave strays.
- **A real completion gate.** Termination is decided by `gate.py`, not the model: `pytest` for
  repair; output-exists-and-parses for named outputs; unchanged file-set for in-place redaction.
  A failed gate injects a reason and the loop retries — so a first-attempt slip self-heals inside
  the run, which is what protects the twice-run score.
- **Per-type system prompts.** The prompt is assembled per task type, so a CSV task never carries
  the ~550-token redaction block. This cut transform-task prompts ~44 % and roughly halved the
  cost of several tasks.
- **In-script self-checks.** For redaction (which the gate can't verify) the script re-scans its
  own output with a broad detector and asserts nothing PII-shaped survives *and* that guarded
  values (e.g. `Order #…`) are untouched — before writing anything back.
- **Honest & deterministic.** `temperature=0`; the usage log records the true 4-key token split
  from OpenRouter (`cache_write`/`cache_read` = 0, since caching does not engage through
  OpenRouter — verified empirically, so it was correctly skipped rather than mis-logged).

## Correctness: the trap catalog in the prompt

Generalization comes from encoding the *recurring traps* as rules, e.g.:

- **Preserve verbatim.** Pass-through columns read as `dtype=str, keep_default_na=False`
  (`779.90`≠`779.9`, `02134`≠`2134`); never route a value through `float()`/`int()`.
- **Compute exactly.** Half-up means via `Decimal`, not `pandas.mean()`/`round()` (banker's);
  datetimes compared as UTC instants (`to_datetime(..., utc=True)`), never tz-stripped.
- **CSV.** RFC-4180 by header, default (minimal) quoting — never suppress quotes.
- **Logs.** Skip corrupt lines; message is everything after the level; never dedupe real dups;
  strict `>` thresholds; exact JSON key order.
- **Redaction is raw text.** Replace only PII spans with `re.sub` on the file text — never
  `json.loads`/`json.dumps` (re-serializing reflows separators and fails the byte compare). One
  canonical phone regex covers every format incl. bare-10-digit, with `(?<!Order #)` sparing the
  order number.
- **Reconciliation.** Case-fold the join key, union, dedupe within a source by recency, take each
  field from the named source with the named fallback, pass values through verbatim.

## How the failures were found and fixed (empirical, transcript-driven)

I ran the full suite **16× per task (160 runs)** in parallel, capturing a markdown transcript of
every attempt and tracking `solved / correct / overbudget / failed` separately (so
"correct-but-too-expensive" stays distinct from a wrong answer). An initial pass scored 147/160;
I then read the transcript of **every** non-solved run and fixed the *root cause*, not the
symptom. Each fix is a general lesson:

| task | root cause (from the transcript) | fix | result |
|---|---|---|---|
| **08** | "always `dtype=str`" made `amount` a string, so `.agg("mean")` failed → the model always needed a corrective 2nd/3rd rewrite → the long runs went overbudget | compute the half-up mean directly with `Decimal` on the string values (exactly what the test does) — no str/numeric conflict, one rewrite | 10/16 → **16/16 correct, 14/16 solved**, 1 rewrite |
| **05** | hand-rolled a per-format phone scanner that omitted the bare-10-digit case (`8085550171` missed) and had an off-by-one `Order #` check | one canonical phone regex with optional separators + fixed-width lookbehind | 14/16 → **16/16** |
| **01** | first solution was correct, but the model *second-guessed* RFC quoting, forced `quotechar=None`, and left a SyntaxError | "default quoting is correct, the grader re-parses — don't suppress quotes, and stop once written" | 15/16 → **16/16** |
| **02** | occasional overbudget from the self-check printing sample rows/tables | "print only the word `OK`, never rows/tables" | 14/16 → **16/16** |

## Tests & reproduce

The deterministic components ship with a **pytest suite** (`tests/`, run in **GitHub Actions CI**)
covering the bash tool, the completion gate, the workspace inventory, per-type prompt assembly, and
the usage logger — all API-free, so CI is fast and free.

```bash
uv run pytest tests/ -q                         # unit tests, no API needed
uv run python -m runner.run_task tasks/01-csv-merge-basic   # end-to-end one task (needs the key)
```

The agent also has an **env-gated** transcript writer (`AGENT_TRANSCRIPT=<path>`) — off by default,
zero effect on grading.

## Extra test tasks

Beyond the ten provided tasks, `extra_tasks/` holds six more I wrote while iterating — harder
variants across the same categories (mixed encodings, noisy logs, SSN-vs-order-number redaction, a
one-row pandas bug, a recency-tiebreak reconcile, and a combined extract-then-reconcile). Each has
the same `task.md` / `workspace/` / `verify.py` layout and runs through the same runner
(`python -m runner.run_task 'extra_tasks/*'`). See `extra_tasks/README.md`.

## Remaining limitation & next steps

- **06 (name redaction) is cost-marginal** — correct on 16/16, but it carries the full redaction
  prompt *and* iterates on a roster-name self-check, so it sits at $0.04–0.06 and tips over on ~5/16
  runs. It is the one place worth more work: trim the redaction block for the names variant and
  bound the self-check to a single pass. Everything else is comfortably under budget.
- **Prompt caching** would add margin in principle, but OpenRouter did not return cache hits for
  this model in testing (`cached_tokens` stayed 0 on identical repeats), so it was skipped rather
  than logged dishonestly.

The headline: **100 % correctness across 160 runs and 95.6 % solved**, from an agent that reasons
about task *rules* and lets Python touch the data — which is exactly what should carry over to the
unseen hidden suite.
