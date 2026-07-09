from agent.shell import TOOL, Shell, clip


def test_echo_and_exit_code(tmp_path):
    sh = Shell(tmp_path)
    assert "hello" in sh.run("echo hello") and "[exit 0]" in sh.run("echo hi")


def test_nonzero_exit(tmp_path):
    assert "[exit 1]" in Shell(tmp_path).run("ls /nonexistent_dir_xyz")


def test_state_persists_across_calls(tmp_path):
    sh = Shell(tmp_path)
    sh.run("MYVAR=persisted")
    assert "persisted" in sh.run("echo $MYVAR")


def test_heredoc_then_run(tmp_path):
    out = Shell(tmp_path).run("cat > f.py <<'PY'\nprint(6 * 7)\nPY\npython3 f.py")
    assert "42" in out


def test_starts_in_workspace(tmp_path):
    (tmp_path / "marker.txt").write_text("x")
    assert "marker.txt" in Shell(tmp_path).run("ls")


def test_restart(tmp_path):
    sh = Shell(tmp_path)
    sh.restart()
    assert "[exit 0]" in sh.run("true")


def test_clip_truncates_long_output():
    clipped = clip("x" * 40000)
    assert "truncated" in clipped and len(clipped) < 40000


def test_tool_schema():
    assert TOOL["type"] == "function" and TOOL["function"]["name"] == "bash"
    assert "command" in TOOL["function"]["parameters"]["properties"]


def test_timeout_restarts_session(tmp_path):
    assert "timed out" in Shell(tmp_path).run("sleep 5", timeout=0.2)


def test_respawns_dead_process(tmp_path):
    sh = Shell(tmp_path)
    sh.proc.kill()
    sh.proc.wait()
    assert "hi" in sh.run("echo hi")


def test_exit_command_hits_eof(tmp_path):
    assert "[exit ?]" in Shell(tmp_path).run("exit 0")
