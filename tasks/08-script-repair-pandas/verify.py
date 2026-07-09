#!/usr/bin/env python3
"""Verifier for 08-script-repair-pandas.

Passes only if the tests/ directory and the input data are byte-for-byte
identical to the shipped originals AND `pytest -q` succeeds in the workspace.
"""

import subprocess
import sys
from pathlib import Path

PRISTINE = Path(__file__).parent / "workspace"
INPUTS = ["orders.csv"]


def fail(msg):
    print(msg)
    sys.exit(1)


def check_pristine(workspace, rel, label):
    pris = PRISTINE / rel
    run = workspace / rel
    if pris.is_dir():
        exp = {p.relative_to(PRISTINE) for p in pris.rglob("*")
               if p.is_file() and "__pycache__" not in p.parts}
        act = ({p.relative_to(workspace) for p in run.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts}
               if run.exists() else set())
        if exp != act:
            fail(f"{label} was modified: file set under {rel}/ changed")
        for r in sorted(exp):
            if (PRISTINE / r).read_bytes() != (workspace / r).read_bytes():
                fail(f"{label} was modified: {r}")
    else:
        if not run.exists():
            fail(f"{label} was modified: {rel} is missing")
        if pris.read_bytes() != run.read_bytes():
            fail(f"{label} was modified: {rel}")


def main():
    workspace = Path(sys.argv[1])
    check_pristine(workspace, "tests", "tests")
    for name in INPUTS:
        check_pristine(workspace, name, "input data")

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(workspace), capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-15:])
        fail(f"tests failing:\n{tail}")
    print("ok")


if __name__ == "__main__":
    main()
