from agent.gate import gate


def test_missing_named_output_fails(tmp_path):
    ok, why = gate(tmp_path, "Produce a single file `out.csv`.", set())
    assert not ok and "out.csv" in why


def test_present_named_output_passes(tmp_path):
    (tmp_path / "out.csv").write_text("a,b\n1,2\n")
    ok, _ = gate(tmp_path, "Produce a single file `out.csv`.", set())
    assert ok


def test_unparseable_jsonl_fails(tmp_path):
    (tmp_path / "out.jsonl").write_text("{ not valid json\n")
    ok, _ = gate(tmp_path, "Write `out.jsonl`.", set())
    assert not ok


def test_inplace_stray_file_fails(tmp_path):
    (tmp_path / "notes.txt").write_text("original")
    snap = {"notes.txt"}
    (tmp_path / "stray.txt").write_text("added")
    ok, why = gate(tmp_path, "Redact `notes.txt` in place.", snap)
    assert not ok and "stray.txt" in why


def test_inplace_clean_passes(tmp_path):
    (tmp_path / "notes.txt").write_text("[EMAIL]")
    ok, _ = gate(tmp_path, "Redact `notes.txt` in place.", {"notes.txt"})
    assert ok


def test_repair_runs_pytest(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_ok():\n    assert 1 + 1 == 2\n")
    ok, _ = gate(tmp_path, "fix the module", set())
    assert ok


def test_repair_failing_pytest_blocks(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_bad():\n    assert False\n")
    ok, why = gate(tmp_path, "fix the module", set())
    assert not ok and "pytest" in why


def test_empty_output_fails(tmp_path):
    (tmp_path / "out.csv").write_text("")
    ok, why = gate(tmp_path, "Produce `out.csv`.", set())
    assert not ok and "empty" in why


def test_json_output_parses(tmp_path):
    (tmp_path / "out.json").write_text('{"ok": true}')
    ok, _ = gate(tmp_path, "Write `out.json`.", set())
    assert ok


def test_no_named_output_defers(tmp_path):
    (tmp_path / "whatever").write_text("x")
    ok, _ = gate(tmp_path, "Do something with no named file.", set())
    assert ok


def test_inplace_broken_existing_jsonl_fails(tmp_path):
    (tmp_path / "data.jsonl").write_text("{ broken\n")
    ok, why = gate(tmp_path, "Redact `data.jsonl` in place.", {"data.jsonl"})
    assert not ok and "parse" in why
