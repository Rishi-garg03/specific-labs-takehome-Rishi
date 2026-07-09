import json
import os


def log_usage(usage):
    path = os.environ.get("GAUNTLET_USAGE_LOG")
    if not path:
        return
    cached = getattr(getattr(usage, "prompt_tokens_details", None), "cached_tokens", 0) or 0
    entry = {
        "input_tokens": usage.prompt_tokens - cached,
        "output_tokens": usage.completion_tokens,
        "cache_write_tokens": 0,
        "cache_read_tokens": cached,
    }
    with open(path, "a") as handle:
        handle.write(json.dumps(entry) + "\n")
