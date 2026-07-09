import json
from types import SimpleNamespace

from agent.usage import log_usage


def test_logs_four_honest_keys(tmp_path, monkeypatch):
    log = tmp_path / "usage.log"
    monkeypatch.setenv("GAUNTLET_USAGE_LOG", str(log))
    usage = SimpleNamespace(prompt_tokens=100, completion_tokens=20,
                            prompt_tokens_details=SimpleNamespace(cached_tokens=30))
    log_usage(usage)
    entry = json.loads(log.read_text().strip())
    assert entry == {"input_tokens": 70, "output_tokens": 20,
                     "cache_write_tokens": 0, "cache_read_tokens": 30}


def test_handles_missing_cache_details(tmp_path, monkeypatch):
    log = tmp_path / "usage.log"
    monkeypatch.setenv("GAUNTLET_USAGE_LOG", str(log))
    log_usage(SimpleNamespace(prompt_tokens=5, completion_tokens=2, prompt_tokens_details=None))
    assert json.loads(log.read_text().strip())["input_tokens"] == 5


def test_noop_without_env(monkeypatch):
    monkeypatch.delenv("GAUNTLET_USAGE_LOG", raising=False)
    log_usage(SimpleNamespace(prompt_tokens=1, completion_tokens=1, prompt_tokens_details=None))
