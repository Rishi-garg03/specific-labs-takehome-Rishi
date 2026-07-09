from agent.prompt import system_prompt


def test_repair_prompt_routes_to_repair():
    p = system_prompt(True, False)
    assert "pytest" in p and "REWRITE" in p and "Redaction is a RAW-TEXT" not in p


def test_transform_prompt_routes_to_transform():
    p = system_prompt(False, False)
    assert "/tmp/solve.py" in p and "Redaction is a RAW-TEXT" not in p


def test_redaction_prompt_carries_redaction_block():
    p = system_prompt(False, True)
    assert "Redaction is a RAW-TEXT" in p and "(?<!Order #)" in p


def test_transform_prompt_is_leaner_than_redaction():
    assert len(system_prompt(False, False)) < len(system_prompt(False, True))


def test_all_variants_carry_core_correctness_rules():
    for repair, redact in [(True, False), (False, False), (False, True)]:
        assert "BYTE FOR BYTE" in system_prompt(repair, redact)
