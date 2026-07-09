import csv
import json
import re
import subprocess
import sys
from pathlib import Path

_OUTPUT = re.compile(r"`([^`\n]+?\.(?:csv|jsonl|json|txt))`")


def _parses(path):
    p = Path(path)
    try:
        if p.stat().st_size == 0:
            return f"{p.name} is empty"
        if p.suffix == ".jsonl":
            for line in p.read_text().splitlines():
                if line.strip():
                    json.loads(line)
        elif p.suffix == ".json":
            json.loads(p.read_text())
        elif p.suffix == ".csv":
            with p.open(newline="") as handle:
                list(csv.reader(handle))
    except Exception as error:
        return f"{p.name} does not parse: {error}"
    return None


def gate(workspace, task, snapshot):
    ws = Path(workspace)
    if (ws / "tests").is_dir():
        done = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ws, capture_output=True, text=True)
        return (done.returncode == 0, "" if done.returncode == 0 else "pytest is still failing")
    now = {p.relative_to(ws).as_posix() for p in ws.rglob("*") if p.is_file()}
    mentioned = [n for n in dict.fromkeys(_OUTPUT.findall(task)) if "*" not in n]
    expected = [n for n in mentioned if n not in snapshot]
    if expected:
        missing = [n for n in expected if n not in now]
        if missing:
            return (False, f"expected output not created: {missing}")
        for n in expected:
            bad = _parses(ws / n)
            if bad:
                return (False, bad)
        return (True, "")
    if mentioned:
        strays = sorted(now - snapshot)
        if strays:
            return (False, f"you created files that must not exist ({strays}); this task edits in place, so remove them")
        for n in mentioned:
            bad = _parses(ws / n)
            if bad:
                return (False, bad)
    return (True, "")
