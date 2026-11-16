"""Resolve a QF-Bench task_name to its task folder and emit a compact context bundle.

A QF-Bench task folder is expected at <tasks_root>/<task_name>/ and typically
contains:

    instruction.md            (canonical agent instruction; required if present)
    tests/                    (unit tests run by the verifier)
    solution/  or oracle/     (reference solution; optional)
    task.yaml                 (optional metadata)
    data/                     (optional)

Resolution order for tasks_root:
    1. --tasks-root flag
    2. QFBENCH_TASKS_ROOT environment variable
    3. sibling ../QuantitativeFinance-Bench/tasks of the trial workspace
    4. sibling ../qf-bench/tasks of the trial workspace

Outputs a JSON object with keys:
    task_name, tasks_root, resolved_path, found,
    instruction_md, instruction_md_path, instruction_md_truncated,
    tests_digest [{path, head, lines, truncated}], tests_root,
    oracle_summary (only if --include-oracle-headers),
    content_hash (sha256 over the canonical content)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional
from review_common import file_manifest, git_provenance, payload_hash, sha256, evidence_hash


# ---------- candidate resolution -------------------------------------------------

def _candidate_roots(explicit: Optional[str], near: Optional[Path]) -> list[Path]:
    cands: list[Path] = []
    if explicit:
        return [Path(explicit).expanduser().resolve()]
    env = os.environ.get("QFBENCH_TASKS_ROOT")
    if env:
        return [Path(env).expanduser().resolve()]
    if near is not None:
        near = near.resolve()
        for parent in [near, *near.parents]:
            cands.append(parent / "QuantitativeFinance-Bench" / "tasks")
            cands.append(parent / "qf-bench" / "tasks")
            if parent.parent == parent:
                break
    seen: set[Path] = set()
    out: list[Path] = []
    for c in cands:
        c = c.expanduser()
        try:
            c = c.resolve()
        except OSError:
            pass
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def resolve_tasks_root(
    explicit: Optional[str], near: Optional[Path] = None
) -> Optional[Path]:
    for c in _candidate_roots(explicit, near):
        if c.is_dir():
            return c
    return None


# ---------- task folder content loading ------------------------------------------

_TEST_FILE_GLOBS = ["**/*.py", "**/*.sh", "**/*.json", "**/*.yaml", "**/*.yml", "**/*.txt"]


def _load_instruction_md(task_dir: Path, max_chars: int) -> tuple[Optional[str], Optional[str], bool]:
    """Return (text, path, truncated)."""
    candidate_names = ["instruction.md", "instructions.md", "INSTRUCTION.md", "task.md", "README.md"]
    for name in candidate_names:
        p = task_dir / name
        if p.is_file() and task_dir.resolve() in p.resolve().parents:
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            truncated = False
            if max_chars > 0 and len(text) > max_chars:
                text = text[:max_chars] + "\n\n[... truncated by task_context.py ...]"
                truncated = True
            return text, str(p), truncated
    return None, None, False


def _enumerate_tests(task_dir: Path, max_files: int, head_lines: int) -> tuple[list[dict[str, Any]], Optional[str]]:
    tests_dir = None
    for cand in ("tests", "test", "verification", "verifier"):
        p = task_dir / cand
        if p.is_dir():
            tests_dir = p
            break
    if tests_dir is None:
        return [], None
    files: list[Path] = []
    for pattern in _TEST_FILE_GLOBS:
        files.extend(tests_dir.glob(pattern))
    files = sorted({f for f in files if f.is_file()})
    digest: list[dict[str, Any]] = []
    for f in (files[:max_files] if max_files > 0 else files):
        if task_dir.resolve() not in f.resolve().parents:
            continue  # source_manifest records external targets as unread evidence
        try:
            with f.open("r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        truncated = head_lines > 0 and len(lines) > head_lines
        head = "".join(lines[:head_lines] if head_lines > 0 else lines)
        digest.append(
            {
                "path": str(f.relative_to(task_dir)),
                "lines": len(lines),
                "sha256": sha256(f),
                "truncated": truncated,
                "head": head,
            }
        )
    return digest, str(tests_dir.relative_to(task_dir))


_DEF_PATTERN = re.compile(r"^\s*(def|class)\s+\w+.*:\s*$", re.MULTILINE)


def _oracle_summary(task_dir: Path, max_chars: int) -> Optional[str]:
    for cand in ("solution", "oracle", "sample_solution", "reference"):
        d = task_dir / cand
        if d.is_dir():
            sigs: list[str] = []
            for f in sorted(d.rglob("*.py")):
                if task_dir.resolve() not in f.resolve().parents:
                    continue
                try:
                    text = f.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                rel = f.relative_to(task_dir)
                hits = _DEF_PATTERN.findall(text)
                lines = [m.group(0) for m in _DEF_PATTERN.finditer(text)]
                if not lines:
                    continue
                sigs.append(f"# {rel}")
                sigs.extend(lines)
                if sum(len(s) for s in sigs) > max_chars:
                    break
            if sigs:
                joined = "\n".join(sigs)
                if len(joined) > max_chars:
                    joined = joined[:max_chars] + "\n# [... truncated ...]"
                return joined
    return None


# ---------- public API -----------------------------------------------------------

def build_context(
    task_name: str,
    tasks_root: Optional[Path],
    *,
    max_instruction_chars: int = 0,
    max_test_files: int = 0,
    test_head_lines: int = 0,
    include_oracle_headers: bool = False,
    max_oracle_chars: int = 4000,
) -> dict[str, Any]:
    tasks_root = tasks_root.resolve() if tasks_root else None
    out: dict[str, Any] = {
        "task_name": task_name,
        "tasks_root": str(tasks_root) if tasks_root else None,
        "resolved_path": None,
        "found": False,
        "instruction_md": None,
        "instruction_md_path": None,
        "instruction_md_truncated": False,
        "tests_root": None,
        "tests_digest": [],
        "oracle_summary": None,
    }
    if tasks_root is None:
        out["content_hash"] = _hash_payload(out)
        return out
    task_dir = (tasks_root / task_name).resolve()
    if tasks_root.resolve() not in task_dir.parents:
        raise ValueError("task_name must resolve inside tasks_root")
    if not task_dir.is_dir():
        out["content_hash"] = _hash_payload(out)
        return out
    out["resolved_path"] = str(task_dir)
    out["found"] = True
    instr, instr_path, truncated = _load_instruction_md(task_dir, max_instruction_chars)
    out["instruction_md"] = instr
    out["instruction_md_path"] = instr_path
    out["instruction_md_truncated"] = truncated
    digest, tests_root = _enumerate_tests(task_dir, max_test_files, test_head_lines)
    out["tests_digest"] = digest
    out["tests_root"] = tests_root
    if include_oracle_headers:
        out["oracle_summary"] = _oracle_summary(task_dir, max_oracle_chars)
    out["source_manifest"] = file_manifest(task_dir)
    out["source_provenance"] = git_provenance(task_dir)
    # Read complete text context by default; limits are explicit and reported.
    rendered = {d["path"] for d in digest}
    attachments = []
    for item in out["source_manifest"]:
        rel = item["path"]
        if rel in rendered or (instr_path and rel == Path(instr_path).name):
            continue
        path = task_dir / rel
        if item.get("error"):
            continue
        if path.suffix.lower() in {".md", ".py", ".sh", ".json", ".csv", ".txt", ".yaml", ".yml", ".toml"}:
            try:
                attachments.append({"path": rel, "sha256": item["sha256"], "text": path.read_text(encoding="utf-8"), "truncated": False})
            except (OSError, UnicodeError):
                pass
    out["context_files"] = attachments
    test_files = [d for d in out["source_manifest"] if tests_root and d["path"].startswith(tests_root + "/")]
    out["omitted_test_files"] = [d["path"] for d in test_files if d["path"] not in rendered and not any(a["path"] == d["path"] for a in attachments)]
    rendered_paths = rendered | {a["path"] for a in attachments}
    if instr_path:
        rendered_paths.add(str(Path(instr_path).relative_to(task_dir)))
    out["unrendered_context_files"] = [d["path"] for d in out["source_manifest"] if d["path"] not in rendered_paths]
    out["evidence_warnings"] = []
    if tests_root and task_dir.resolve() not in (task_dir / tests_root).resolve().parents:
        out["evidence_warnings"].append("External tests-directory target was not read.")
    if out["unrendered_context_files"]:
        out["evidence_warnings"].append("Task files are hashed but not rendered; inspect the unrendered_context_files before conclusions depending on them.")
    if truncated or any(d["truncated"] for d in digest) or out["omitted_test_files"]:
        out["evidence_warnings"].append("Context truncated or omitted; inspect source files before a decisive assessment.")
    if not instr:
        out["evidence_warnings"].append("Task instructions missing; task validity cannot be certified.")
    out["reference_status"] = "unverified evidence; reference/checker agreement is not proof of correctness"
    out["content_hash"] = _hash_payload(out)
    return out


def _hash_payload(ctx: dict[str, Any]) -> str:
    return evidence_hash({k: v for k, v in ctx.items() if k != "content_hash"})


# ---------- CLI ------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Resolve a QF-Bench task and emit context JSON.")
    p.add_argument("--task-name", required=True)
    p.add_argument("--tasks-root", default=None, help="Path to <repo>/tasks; falls back to QFBENCH_TASKS_ROOT.")
    p.add_argument("--near", default=None, help="A path near the trial; used to look for sibling tasks roots.")
    p.add_argument("--max-instruction-chars", type=int, default=0)
    p.add_argument("--max-test-files", type=int, default=0)
    p.add_argument("--test-head-lines", type=int, default=0)
    p.add_argument("--include-oracle-headers", action="store_true")
    p.add_argument("--max-oracle-chars", type=int, default=4000)
    p.add_argument("--out", default=None, help="Output JSON path; default stdout.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    near = Path(args.near).expanduser() if args.near else None
    root = resolve_tasks_root(args.tasks_root, near)
    if root is None and (args.tasks_root or os.environ.get("QFBENCH_TASKS_ROOT")):
        sys.stderr.write(
            "[task_context] WARNING: tasks-root could not be resolved; emitting degraded context.\n"
        )
    ctx = build_context(
        args.task_name,
        root,
        max_instruction_chars=args.max_instruction_chars,
        max_test_files=args.max_test_files,
        test_head_lines=args.test_head_lines,
        include_oracle_headers=args.include_oracle_headers,
        max_oracle_chars=args.max_oracle_chars,
    )
    serialized = json.dumps(ctx, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(serialized, encoding="utf-8")
    else:
        sys.stdout.write(serialized + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
