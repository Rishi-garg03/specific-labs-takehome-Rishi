from agent.run import _trim


def test_trim_shrinks_old_tool_outputs_and_commands():
    messages = [
        {"role": "system", "content": "s"},
        {"role": "assistant", "content": "a", "tool_calls": [{"function": {"arguments": "x" * 400}}]},
        {"role": "tool", "content": "y" * 400},
        {"role": "assistant", "content": "b"},
        {"role": "tool", "content": "recent-1"},
        {"role": "assistant", "content": "c"},
        {"role": "tool", "content": "recent-2"},
        {"role": "user", "content": "last"},
    ]
    _trim(messages)
    assert "[trimmed]" in messages[2]["content"]
    assert "earlier command omitted" in messages[1]["tool_calls"][0]["function"]["arguments"]
    assert messages[4]["content"] == "recent-1"
