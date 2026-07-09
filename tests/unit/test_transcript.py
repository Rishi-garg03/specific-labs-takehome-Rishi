from types import SimpleNamespace

from agent.transcript import Recorder


def test_active_recorder_captures_everything(tmp_path):
    path = tmp_path / "t.md"
    rec = Recorder(str(path))
    rec.add("Title", "the body")
    rec.turn(SimpleNamespace(content="thinking", tool_calls=[SimpleNamespace(function=SimpleNamespace(arguments='{"command": "ls -la"}'))]))
    rec.turn(SimpleNamespace(content="final answer", tool_calls=None))
    rec.tool("command output here")
    rec.flush("VERDICT LINE")
    text = path.read_text()
    for expected in ("VERDICT LINE", "Title", "the body", "ls -la", "command output here", "final answer"):
        assert expected in text


def test_inactive_recorder_is_noop(tmp_path):
    rec = Recorder(None)
    rec.add("t", "b")
    rec.turn(SimpleNamespace(content="x", tool_calls=None))
    rec.tool("out")
    rec.flush("v")
    assert rec.parts == [] and not (tmp_path / "t.md").exists()
