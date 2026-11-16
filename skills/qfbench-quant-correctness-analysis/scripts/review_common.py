"""Local provenance and strict JSON helpers; no provider dependencies or calls."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON number: {value}")


def strict_loads(text: str) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(text, parse_constant=reject_constant, object_pairs_hook=pairs)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def payload_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def evidence_hash(value: Any) -> str:
    """Bind content/commit identity while recording incidental Git status separately.

    Full source manifests cover dirty file contents. Git's porcelain display also
    includes newly generated review artifacts, so it is audit metadata rather
    than evidence identity and must not invalidate an unchanged prepared request.
    """
    def stable(item):
        if isinstance(item, list):
            return [stable(v) for v in item]
        if isinstance(item, dict):
            return {k: stable({pk: pv for pk, pv in v.items() if pk != "dirty_paths"})
                    if k == "source_provenance" and isinstance(v, dict) else stable(v)
                    for k, v in item.items()}
        return item
    return payload_hash(stable(value))


def file_manifest(root: Path, *, exclude_names=()) -> list[dict[str, Any]]:
    """Hash every regular file, recording unreadable files and external symlinks."""
    rows = []
    root = root.resolve()
    for path in sorted(root.rglob("*")):
        if any(p in {".git", "__pycache__", "review_history"} for p in path.relative_to(root).parts):
            continue
        if path.name in exclude_names or not path.is_file():
            continue
        row = {"path": str(path.relative_to(root)), "size_bytes": path.stat().st_size}
        if path.is_symlink():
            row["symlink_target"] = str(path.resolve())
            if root not in path.resolve().parents:
                row["error"] = "external symlink not read"
                rows.append(row)
                continue
        try:
            row["sha256"] = sha256(path)
        except OSError as exc:
            row["error"] = str(exc)
        rows.append(row)
    return rows


def git_provenance(path: Path) -> dict[str, Any]:
    """Read local Git metadata without fetching or changing repository state."""
    def run(*args):
        p = subprocess.run(["git", "-C", str(path), *args], capture_output=True,
                           text=True, timeout=10)
        return p.stdout.strip() if p.returncode == 0 else None
    try:
        return {"commit": run("rev-parse", "HEAD"),
                "repository_root": run("rev-parse", "--show-toplevel"),
                "dirty_paths": run("status", "--porcelain", "--", str(path))}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"commit": None, "error": str(exc)}
