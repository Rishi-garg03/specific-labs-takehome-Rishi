import json
from types import SimpleNamespace

import pytest

import agent.run as run

SCRIPT = (
    "import csv\n"
    "rows = list(csv.reader(open('sales.csv', newline='')))\n"
    "with open('merged.csv', 'w', newline='') as f:\n"
    "    csv.writer(f).writerows(rows)\n"
    "print('OK')\n"
)
WRITE_CMD = f"cat > /tmp/solve.py <<'PY'\n{SCRIPT}PY\npython3 /tmp/solve.py"


class _ToolCall:
    def __init__(self, command=None, restart=False):
        self.id = "call_1"
        self.type = "function"
        args = {"restart": True} if restart else {"command": command}
        self.function = SimpleNamespace(name="bash", arguments=json.dumps(args))

    def model_dump(self):
        return {"id": self.id, "type": "function", "function": {"name": "bash", "arguments": self.function.arguments}}


def _client(turns):
    state = {"n": 0}

    def make(**_):
        def create(**__):
            turn = turns[min(state["n"], len(turns) - 1)]
            state["n"] += 1
            usage = SimpleNamespace(prompt_tokens=100, completion_tokens=20, prompt_tokens_details=SimpleNamespace(cached_tokens=0))
            if turn.get("stop"):
                msg = SimpleNamespace(content="done", tool_calls=None)
            elif turn.get("restart"):
                msg = SimpleNamespace(content="restart", tool_calls=[_ToolCall(restart=True)])
            else:
                msg = SimpleNamespace(content="cmd", tool_calls=[_ToolCall(command=turn["cmd"])])
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=usage)

        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    return make


def _setup(tmp_path, monkeypatch, turns, task="Produce a single file `merged.csv` with every row."):
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "sales.csv").write_text("order_id,amount\n1,10\n2,20\n")
    (tmp_path / "task.md").write_text(task)
    log = tmp_path / "usage.jsonl"
    monkeypatch.setattr(run, "OpenAI", _client(turns))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("GAUNTLET_USAGE_LOG", str(log))
    monkeypatch.setattr("sys.argv", ["agent.run", "--task-dir", str(tmp_path)])
    return ws, log


def test_happy_path_writes_output_and_logs_usage(tmp_path, monkeypatch):
    ws, log = _setup(tmp_path, monkeypatch, [{"cmd": WRITE_CMD}, {"stop": True}])
    run.main()
    assert (ws / "merged.csv").read_text().replace("\r\n", "\n") == "order_id,amount\n1,10\n2,20\n"
    entry = json.loads(log.read_text().splitlines()[0])
    assert set(entry) == {"input_tokens", "output_tokens", "cache_write_tokens", "cache_read_tokens"}
    assert entry["input_tokens"] == 100 and entry["output_tokens"] == 20


def test_retry_after_failed_self_gate(tmp_path, monkeypatch):
    ws, _ = _setup(tmp_path, monkeypatch, [{"stop": True}, {"cmd": WRITE_CMD}, {"stop": True}])
    run.main()
    assert (ws / "merged.csv").exists()


def test_restart_tool_call(tmp_path, monkeypatch):
    ws, _ = _setup(tmp_path, monkeypatch, [{"restart": True}, {"cmd": WRITE_CMD}, {"stop": True}])
    run.main()
    assert (ws / "merged.csv").exists()


def test_turn_exhaustion_exits_nonzero(tmp_path, monkeypatch):
    ws, _ = _setup(tmp_path, monkeypatch, [{"cmd": "echo noop"}])
    with pytest.raises(SystemExit) as exc:
        run.main()
    assert exc.value.code == 1 and not (ws / "merged.csv").exists()
