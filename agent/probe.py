from pathlib import Path

from .config import FULL_CONTENT_BYTES, INVENTORY_LIMIT, SAMPLE_LINES, SAMPLE_WIDTH


def snapshot(workspace):
    ws = Path(workspace)
    return {p.relative_to(ws).as_posix() for p in ws.rglob("*") if p.is_file()}


def _text(path, limit):
    try:
        raw = Path(path).read_bytes()[:limit]
    except Exception:
        return None
    return None if b"\x00" in raw else raw.decode("utf-8", "replace")


def inventory(workspace):
    ws = Path(workspace)
    groups = {}
    for path in sorted(p for p in ws.rglob("*") if p.is_file()):
        head = _text(path, 8192) or ""
        groups.setdefault((path.suffix, head.splitlines()[0] if head else ""), []).append(path)
    out = []
    for members in groups.values():
        rep = members[0]
        rel, size = rep.relative_to(ws).as_posix(), rep.stat().st_size
        out.append(f"{len(members)} {rep.suffix or 'no-ext'} files share this shape; sample {rel} ({size}B):" if len(members) > 1 else f"{rel} ({size}B):")
        if size <= FULL_CONTENT_BYTES:
            out += [f"    {line}" for line in (_text(rep, FULL_CONTENT_BYTES) or "").splitlines()]
        else:
            out += [f"    | {line[:SAMPLE_WIDTH]}" for line in (_text(rep, 8192) or "").splitlines()[:SAMPLE_LINES]]
    return "\n".join(out)[:INVENTORY_LIMIT]
