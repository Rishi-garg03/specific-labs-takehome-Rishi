from agent.probe import _text, inventory, snapshot


def test_snapshot_lists_all_files(tmp_path):
    (tmp_path / "a.txt").write_text("hi")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("yo")
    assert snapshot(tmp_path) == {"a.txt", "sub/b.txt"}


def test_inventory_groups_same_shaped_files(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    for i in range(6):
        (data / f"f{i}.csv").write_text(f"id,name\n{i},x\n")
    inv = inventory(tmp_path)
    assert "6" in inv and "id,name" in inv


def test_inventory_shows_small_file_in_full(tmp_path):
    (tmp_path / "small.txt").write_text("line-one\nline-two\n")
    inv = inventory(tmp_path)
    assert "line-one" in inv and "line-two" in inv


def test_inventory_samples_large_file(tmp_path):
    (tmp_path / "big.csv").write_text("h1,h2\n" + "1,2\n" * 5000)
    inv = inventory(tmp_path)
    assert "h1,h2" in inv and len(inv) < 8001


def test_text_returns_none_on_unreadable(tmp_path):
    assert _text(tmp_path, 100) is None


def test_inventory_skips_binary(tmp_path):
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01\x02data")
    assert "blob.bin" in inventory(tmp_path)
