import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PRISTINE = Path(__file__).parent / "workspace"


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def _files(root):
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )


def main():
    if len(sys.argv) != 2:
        fail("usage: verify.py <RUN_WORKSPACE>")
    run = Path(sys.argv[1]).resolve()
    if not run.is_dir():
        fail("run workspace does not exist: %s" % run)

    pristine = PRISTINE.resolve()

    # The agent is only allowed to change report.py; it must still exist.
    run_report = run / "report.py"
    if not run_report.is_file():
        fail("report.py is missing from the run workspace")

    # sales.csv must be byte-identical to the pristine input.
    p_sales = pristine / "sales.csv"
    r_sales = run / "sales.csv"
    if not r_sales.is_file():
        fail("sales.csv is missing from the run workspace")
    if r_sales.read_bytes() != p_sales.read_bytes():
        fail("sales.csv was modified")

    # tests/ must be byte-identical to the pristine tests (same file set + bytes).
    p_tests = pristine / "tests"
    r_tests = run / "tests"
    if not r_tests.is_dir():
        fail("tests/ directory is missing from the run workspace")
    p_list = _files(p_tests)
    r_list = _files(r_tests)
    if p_list != r_list:
        fail("tests/ file set changed: got %r expected %r" % (r_list, p_list))
    for rel in p_list:
        if (r_tests / rel).read_bytes() != (p_tests / rel).read_bytes():
            fail("tests/%s was modified" % rel)

    # Independently recompute correctness: run the pristine tests against the
    # pristine sales.csv, importing the agent's report.py. Nothing but report.py
    # is taken from the run workspace, so the oracle cannot be tampered with.
    tmp = Path(tempfile.mkdtemp(prefix="verify_repair_sales_"))
    try:
        shutil.copy2(p_sales, tmp / "sales.csv")
        shutil.copytree(p_tests, tmp / "tests")
        shutil.copy2(run_report, tmp / "report.py")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            cwd=str(tmp),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.stdout.write(proc.stdout)
            sys.stdout.write(proc.stderr)
            fail("pytest did not pass (returncode %d)" % proc.returncode)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
