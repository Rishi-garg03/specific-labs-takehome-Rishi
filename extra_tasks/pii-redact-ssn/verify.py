#!/usr/bin/env python3
"""Deterministic verifier for the pii-redact-ssn task.

Usage: python verify.py <RUN_WORKSPACE>

Recomputes the expected redaction independently from this file's own pristine
inputs (./workspace) and compares, byte-for-byte, against the files produced
under <RUN_WORKSPACE>. Checks outputs only.
"""
import re
import sys
from pathlib import Path

# An email: local @ domain . tld(>=2 letters).
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# A standalone ddd-dd-dddd, NOT bordered by another digit, and NOT part of a
# purchase-order reference (immediately preceded by "PO-" or "Order ").
SSN_RE = re.compile(r"(?<!\d)(?<!PO-)(?<!Order )\d{3}-\d{2}-\d{4}(?!\d)")


def redact(text: str) -> str:
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = SSN_RE.sub("[SSN]", text)
    return text


def rel_files(root: Path):
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def fail(msg: str):
    print("FAIL: " + msg)
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        fail("usage: python verify.py <RUN_WORKSPACE>")
    run_root = Path(sys.argv[1])
    orig_root = Path(__file__).parent / "workspace"

    if not run_root.is_dir():
        fail(f"run workspace not found: {run_root}")

    expected_set = rel_files(orig_root)
    produced_set = rel_files(run_root)

    missing = expected_set - produced_set
    if missing:
        fail(f"missing expected file(s): {sorted(missing)}")
    stray = produced_set - expected_set
    if stray:
        fail(f"unexpected extra file(s): {sorted(stray)}")

    for rel in sorted(expected_set):
        orig_bytes = (orig_root / rel).read_bytes()
        expected_bytes = redact(orig_bytes.decode("utf-8")).encode("utf-8")
        produced_bytes = (run_root / rel).read_bytes()
        if produced_bytes != expected_bytes:
            # Report the first differing line for a useful message.
            exp_lines = expected_bytes.split(b"\n")
            got_lines = produced_bytes.split(b"\n")
            for i, (e, g) in enumerate(zip(exp_lines, got_lines), 1):
                if e != g:
                    fail(f"{rel}: line {i} mismatch\n  expected: {e!r}\n  got:      {g!r}")
            if len(exp_lines) != len(got_lines):
                fail(f"{rel}: line count differs "
                     f"(expected {len(exp_lines)}, got {len(got_lines)})")
            fail(f"{rel}: content mismatch")

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
