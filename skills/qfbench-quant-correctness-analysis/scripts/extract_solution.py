"""Build a quant-correctness judging bundle: task context + agent solution + failing tests.

This extends `extract_trajectory.py` (from the trajectory skill) with three additional
fields specific to content-correctness judging:

  - `agent_code`: agent-emitted Python source (extracted from Write tool calls in
    multi-step trajectories, or the generated code section in finance-zero blobs)
  - `output_files`: contents of files the agent wrote to its output directory
    (results.json, summary.json, *.csv, etc.) — these are what the verifier reads
  - `failing_tests`: parsed from verifier/test-stdout.txt — list of
    {test_name, agent_value, expected_value, ratio, snippet}

The bundle layout written to `<trial>/agent/bundle.json`:

    {
      "trial_path": ..., "agent_harness": ..., "model": ...,
      "task_name": ..., "trajectory_kind": ...,
      "task_context": <task_context.build_context output>,
      "trajectory_text": "[step | source] message blocks (multi-step) or single blob",
      "agent_code": "<concatenated Python source as the agent wrote it>",
      "output_files": {"results.json": "<content>", ...},
      "failing_tests": [{"test_name": ..., "agent_value": ..., "expected_value": ...,
                         "ratio": ..., "snippet": "..."}],
      "n_steps": int,
      "summarized": bool,
      "bundle_hash": <sha256 over full bundle>,
      "size_chars": int, "size_tokens_est": int
    }

Backwards-compatible with `extract_trajectory.build_bundle` shape: any consumer that
only reads (trajectory_text, task_context, bundle_hash) will keep working.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from review_common import file_manifest, git_provenance, payload_hash, sha256, evidence_hash
import re
import sys
from pathlib import Path
from typing import Any, Optional

try:
    from task_context import build_context, resolve_tasks_root  # type: ignore
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from task_context import build_context, resolve_tasks_root  # type: ignore


# ----- shared helpers (mirrored from extract_trajectory) -------------------------

def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _truncate(text: str, max_chars: int, marker: str = "[...truncated...]") -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    keep = max_chars - len(marker) - 2
    if keep <= 0:
        return marker
    head = keep // 2
    tail = keep - head
    return text[:head] + "\n" + marker + "\n" + text[-tail:]


def _render_step(step: dict[str, Any], max_chars: int) -> str:
    sid = step.get("step_id", "?")
    src = step.get("source", "?")
    msg = step.get("message", "")
    if isinstance(msg, dict):
        msg = json.dumps(msg, ensure_ascii=False, default=str)
    elif not isinstance(msg, str):
        msg = str(msg)
    msg = _truncate(msg, max_chars)
    return f"[step={sid} source={src}]\n{msg}\n"


def _load_steps(traj_path: Path, kind: str) -> list[dict[str, Any]]:
    if kind == "finance-zero":
        text = traj_path.read_text(encoding="utf-8", errors="replace")
        return [{"step_id": 0, "source": "agent", "message": text}]
    with traj_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"trajectory must be an object: {traj_path}")
    steps = data.get("steps")
    if not isinstance(steps, list):
        raise ValueError(f"trajectory.json missing 'steps' list: {traj_path}")
    if any(not isinstance(step, dict) for step in steps):
        raise ValueError(f"trajectory steps must be objects: {traj_path}")
    return steps


def render_trajectory(
    steps: list[dict[str, Any]],
    *,
    max_step_chars: int,
    max_total_chars: int,
    head_keep: int = 6,
    tail_keep: int = 8,
) -> tuple[str, bool]:
    rendered = [_render_step(s, max_step_chars) for s in steps]
    total = sum(len(r) for r in rendered)
    if max_total_chars <= 0 or total <= max_total_chars:
        return "\n".join(rendered), any(max_step_chars > 0 and len(str(s.get("message", ""))) > max_step_chars for s in steps)
    if len(steps) <= head_keep + tail_keep + 1:
        per = max_total_chars // max(1, len(steps))
        rendered = [_render_step(s, max(200, per)) for s in steps]
        return _truncate("\n".join(rendered), max_total_chars), True
    head = rendered[:head_keep]
    tail = rendered[-tail_keep:]
    middle_count = len(steps) - head_keep - tail_keep
    placeholder = (
        f"\n[... {middle_count} middle steps elided to fit token budget; "
        f"head={head_keep}, tail={tail_keep} kept verbatim ...]\n"
    )
    out = "\n".join(head) + placeholder + "\n".join(tail)
    return _truncate(out, max_total_chars), True


# ----- agent-code extraction -----------------------------------------------------

_FINANCE_ZERO_CODE_RE = re.compile(
    r"=== Generated code ===\s*(.*?)(?:===|\Z)", re.DOTALL
)
_MARKDOWN_FENCE_RE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)


def _extract_finance_zero_code(blob: str) -> str:
    """Pull out the code body from a finance-zero text blob.

    Handles two flavors:
      1. Plain code between '=== Generated code ===' and the next '===' marker.
      2. Markdown-fenced code (```python ... ```) — strip the fences.
    Returns "" when no code is present.
    """
    m = _FINANCE_ZERO_CODE_RE.search(blob)
    if m is None:
        return ""
    body = m.group(1).strip()
    if not body:
        return ""
    # Strip outer markdown fences if present.
    fence_match = _MARKDOWN_FENCE_RE.search(body)
    if fence_match is not None:
        body = fence_match.group(1).strip()
    return body


def _extract_multi_step_code(steps: list[dict[str, Any]]) -> str:
    """Extract observed full Write contents. Partial edits are not final snapshots.

    The bundle explicitly warns that patch/shell writes may require direct source
    inspection; never represent this extraction as the executed final program.
    """
    last_writes: dict[str, str] = {}
    for step in steps:
        extra = step.get("extra") or {}
        if not isinstance(extra, dict):
            continue
        tool_name = extra.get("tool_use_name")
        if tool_name not in ("Write", "Edit"):
            continue
        raw_args = extra.get("raw_arguments") or {}
        if not isinstance(raw_args, dict):
            continue
        fp = raw_args.get("file_path")
        if not isinstance(fp, str) or not fp.endswith(".py"):
            continue
        content = raw_args.get("content")
        # For Edit, the result is a patch — fall back to the new_string if present.
        if tool_name == "Edit" and content is None:
            new_str = raw_args.get("new_string")
            if isinstance(new_str, str):
                # Edits are partial; we keep the last full Write as the canonical
                # snapshot. Skip recording Edit-only updates here.
                continue
        if isinstance(content, str):
            last_writes[fp] = content
    if not last_writes:
        return ""
    parts = []
    for fp in sorted(last_writes):
        parts.append(f"# === {fp} ===\n{last_writes[fp]}")
    return "\n\n".join(parts)


# ----- output-file extraction ----------------------------------------------------

_OUTPUT_DIRS_TO_TRY = ("output", "agent/output")


def _find_output_dir(trial: Path) -> Optional[Path]:
    """Locate the output directory the verifier reads. Common layouts:
      <trial>/output/
      <trial>/agent/output/
      <trial>/../output/
    """
    for sub in _OUTPUT_DIRS_TO_TRY:
        candidate = (trial / sub).resolve()
        if candidate.is_dir() and trial.resolve() in candidate.parents:
            return candidate
    return None


def _read_output_files(
    trial: Path,
    *,
    max_files: int = 20,
    max_chars_per_file: int = 8000,
    extensions: tuple[str, ...] = (".json", ".csv", ".txt"),
) -> dict[str, str]:
    out: dict[str, str] = {}
    out_dir = _find_output_dir(trial)
    if out_dir is None:
        return out
    files = sorted(p for p in out_dir.rglob("*") if p.is_file() and p.suffix.lower() in extensions)
    for p in (files[:max_files] if max_files > 0 else files):
        if out_dir.resolve() not in p.resolve().parents:
            continue  # output_manifest records external symlink targets as unread
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        out[p.relative_to(out_dir).as_posix()] = _truncate(text, max_chars_per_file)
    return out


# ----- failing-test extraction ---------------------------------------------------

_FAIL_HEADER_RE = re.compile(r"^_+\s*([\w\[\]\.\-]+(?:\.[\w\[\]\.\-]+)?)\s*_+\s*$")

# Numeric token: integers, decimals, signs, scientific notation. Anchored with
# (?<![\w\.]) / (?![\w\.]) to avoid matching pieces of identifiers.
_NUM = r"(?<![\w\.])([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?|[-+]?\.\d+(?:[eE][-+]?\d+)?)(?![\w\.])"

# Patterns ordered by precedence — first match wins. Each entry is
# (compiled_regex, role_of_group1, role_of_group2[, role_of_group3]) where
# role ∈ {"agent", "expected", "expected_lo", "expected_hi"}.
#
# The convention matches the rest of the skill: agent_value goes to the
# LHS of pytest's `assert X == Y` (X = actual, Y = reference).
_VALUE_PATTERNS = [
    # 1. pytest.approx form: "assert <agent> == <expected> ± <tol>"
    (re.compile(rf"assert\s+{_NUM}\s*==\s*{_NUM}\s*[±+/-]"), "agent", "expected"),
    # 2. np.isclose introspection — appears in pytest output as either
    #      "<function isclose at 0x...>(<agent>, <expected>, ...)"
    #    (the Python repr of the np.isclose function object) or
    #      "np.isclose at 0x...>(<agent>, <expected>, ...)"
    #    in older numpy releases. Match both — note "function" is followed by a
    #    space (function repr) but "np." is followed directly by isclose.
    (re.compile(rf"(?:function\s+|np\.)isclose\s+at\s+0x[0-9a-fA-F]+>?\s*\(\s*{_NUM}\s*,\s*{_NUM}"),
     "agent", "expected"),
    # 3. Direct np.isclose call (in source listing): "np.isclose(<agent>, <expected>, ...)"
    (re.compile(rf"np\.isclose\s*\(\s*{_NUM}\s*,\s*{_NUM}"), "agent", "expected"),
    # 4. abs-difference introspection from chained `assert abs(X - Y) < tol`:
    #      "where 0.787 = abs((-0.3937 - 0.3933))"
    #    Both X and Y are agent computations that disagreed; record X as "agent"
    #    and Y as "expected" so a ratio can be computed downstream. The judge sees
    #    the snippet and can disambiguate "both are agent values".
    (re.compile(rf"=\s*abs\(\(\s*{_NUM}\s*-\s*{_NUM}\s*\)\)"), "agent", "expected"),
    # 5. "expected X, got Y" — "got" follows "expected"
    (re.compile(rf"expected\s+{_NUM}[^\d\n]*?got\s+{_NUM}", re.IGNORECASE), "expected", "agent"),
    # 6. "got X, expected Y"
    (re.compile(rf"got\s+{_NUM}[^\d\n]*?expected\s+{_NUM}", re.IGNORECASE), "agent", "expected"),
    # 7. "VAR = VALUE, expected (in|~) RANGE_OR_VALUE"
    #    e.g., "european_put = 0.0000, expected in (10, 14)"
    #    e.g., "european_put_no_div = 0.0000, expected ~9.35"
    (re.compile(rf"=\s*{_NUM}[^\n]*?expected\s+in\s*\(\s*{_NUM}\s*,\s*{_NUM}\s*\)", re.IGNORECASE),
     "agent", "expected_lo", "expected_hi"),
    (re.compile(rf"=\s*{_NUM}[^\n]*?expected\s+~\s*{_NUM}", re.IGNORECASE), "agent", "expected"),
    # 8. "name = VALUE ... expected EXPECTED" (catch-all when ~ or "in" missing)
    (re.compile(rf"=\s*{_NUM}[^\n]*?expected\s+{_NUM}", re.IGNORECASE), "agent", "expected"),
    # 9. pytest plain "assert X == Y" (no approx)
    (re.compile(rf"^\s*assert\s+{_NUM}\s*==\s*{_NUM}", re.MULTILINE), "agent", "expected"),
    # 10. "X == Y ± Z" without "assert" prefix
    (re.compile(rf"^\s*{_NUM}\s*==\s*{_NUM}\s*[±+/-]", re.MULTILINE), "agent", "expected"),
    # 11. Single-sided threshold from pytest:
    #       "E       assert 0.384... < 0.001"   (agent value should be below tol)
    #       "E       assert -3.28e-34 > 0"      (agent value should be above 0)
    #       "E       assert 0 >= 2"             (count check)
    #     Pytest prefixes diagnostic lines with "E       ". Allow it. Record the
    #     agent-side value as ``agent`` and the threshold as ``expected_*`` so the
    #     judge knows it was a one-sided bound. ``<=`` / ``>=`` listed first so
    #     the single-char ``<`` / ``>`` patterns don't pre-empt them.
    (re.compile(rf"\bassert\s+{_NUM}\s*<=\s*{_NUM}\b"), "agent", "expected_hi"),
    (re.compile(rf"\bassert\s+{_NUM}\s*>=\s*{_NUM}\b"), "agent", "expected_lo"),
    (re.compile(rf"\bassert\s+{_NUM}\s*<\s*{_NUM}\b"), "agent", "expected_hi"),
    (re.compile(rf"\bassert\s+{_NUM}\s*>\s*{_NUM}\b"), "agent", "expected_lo"),
    # 12. np.<scalar-type>(NUM) wrapper around the LHS of a comparison:
    #       "assert np.float64(200.0) < 2.0"  / similar for np.int64, np.bool_
    (re.compile(rf"\bassert\s+np\.\w+\(\s*{_NUM}\s*\)\s*<\s*{_NUM}\b"), "agent", "expected_hi"),
    (re.compile(rf"\bassert\s+np\.\w+\(\s*{_NUM}\s*\)\s*>\s*{_NUM}\b"), "agent", "expected_lo"),
]


def _safe_float(s: str) -> Optional[float]:
    try:
        value = float(s)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None


def _midpoint(lo: Optional[float], hi: Optional[float]) -> Optional[float]:
    if lo is None or hi is None:
        return None
    return (lo + hi) / 2.0


def _extract_failing_tests(test_stdout: str, max_failures: int = 30) -> list[dict[str, Any]]:
    """Parse test_stdout.txt to extract failing tests with agent vs expected values.

    Pattern coverage (in priority order — first match wins per failure block):

      1.  pytest.approx: ``assert 0.000303 == 0.005763 ± 8.6e-04``
      2.  np.isclose introspection: ``+ where np.False_ = <function isclose at 0x..>(0.044649, 0.044707, ...)``
      3.  Direct np.isclose call: ``np.isclose(actual, expected, ...)``
      4.  abs-diff introspection from ``assert abs(fd - pw) < tol``:
          ``where 0.787 = abs((-0.3937 - 0.3933))`` — both args are agent computations
          that disagreed; first stored as ``agent``, second as ``expected``.
      5.  ``expected X, got Y`` / ``got X, expected Y``
      6.  Range bracket: ``var = VALUE, expected in (LO, HI)``  — expected_value set to (LO+HI)/2
      7.  Tilde target: ``var = VALUE, expected ~EXP``
      8.  Catch-all: ``var = VALUE ... expected EXP``
      9.  Plain ``assert X == Y`` (no approx)
     10.  Single-sided: ``assert LO < AGENT`` / ``assert AGENT > LO``

    Heuristics:
      - When an `expected_lo` and `expected_hi` are captured (case 5), the
        midpoint is recorded as expected_value, and lo/hi are kept in the
        per-failure dict as ``expected_lo`` / ``expected_hi``.
      - ratio = agent_value / expected_value when both are numeric and expected != 0.
    """
    lines = test_stdout.splitlines()
    failures: list[dict[str, Any]] = []
    section_starts: list[tuple[int, str]] = []
    for i, ln in enumerate(lines):
        m = _FAIL_HEADER_RE.match(ln.strip("=").strip())
        if m:
            section_starts.append((i, m.group(1)))
    for idx, (start, header_name) in enumerate(section_starts):
        end = section_starts[idx + 1][0] if idx + 1 < len(section_starts) else len(lines)
        block = "\n".join(lines[start:end])
        snippet = "\n".join(lines[start : min(end, start + 30)])

        agent_val: Optional[float] = None
        expected_val: Optional[float] = None
        expected_lo: Optional[float] = None
        expected_hi: Optional[float] = None
        match_pattern_idx: Optional[int] = None

        for i_pat, pat_tuple in enumerate(_VALUE_PATTERNS):
            pat = pat_tuple[0]
            roles = pat_tuple[1:]
            mm = pat.search(block)
            if not mm:
                continue
            captures = [_safe_float(mm.group(j + 1)) for j in range(len(roles))]
            if any(c is None for c in captures):
                continue
            for role, val in zip(roles, captures):
                if role == "agent":
                    agent_val = val
                elif role == "expected":
                    expected_val = val
                elif role == "expected_lo":
                    expected_lo = val
                elif role == "expected_hi":
                    expected_hi = val
            if expected_val is None and expected_lo is not None and expected_hi is not None:
                expected_val = _midpoint(expected_lo, expected_hi)
            if agent_val is not None and (
                expected_val is not None or expected_lo is not None or expected_hi is not None
            ):
                match_pattern_idx = i_pat
                break

        ratio: Optional[float] = None
        if agent_val is not None and expected_val not in (None, 0):
            try:
                ratio = float(agent_val) / float(expected_val)
                if not math.isfinite(ratio):
                    ratio = None
            except (TypeError, ZeroDivisionError):
                ratio = None

        entry: dict[str, Any] = {
            "test_name": header_name,
            "interpretation": "heuristic parser; expected_value is checker-asserted, not independently verified truth",
            "source": "verifier/test-stdout.txt",
            "agent_value": agent_val,
            "expected_value": expected_val,
            "ratio": ratio,
            "snippet": _truncate(snippet, 1200),
        }
        if expected_lo is not None or expected_hi is not None:
            entry["expected_lo"] = expected_lo
            entry["expected_hi"] = expected_hi
        if match_pattern_idx is not None:
            entry["_pattern_idx"] = match_pattern_idx
        failures.append(entry)
        if len(failures) >= max_failures:
            break
    return failures


# ----- bundle assembly -----------------------------------------------------------

def _bundle_hash(parts: list[str]) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def build_bundle(
    *,
    trial_path: Path,
    trajectory_path: Path,
    trajectory_kind: str,
    task_name: str,
    agent_harness: str,
    model: str,
    tasks_root: Optional[Path],
    max_total_chars: int,
    max_step_chars: int,
    max_instruction_chars: int,
    max_test_files: int,
    test_head_lines: int,
    include_oracle_headers: bool,
    max_output_files: int = 0,
    max_chars_per_output_file: int = 0,
    max_agent_code_chars: int = 0,
) -> dict[str, Any]:
    trial_path = trial_path.resolve()
    trajectory_path = trajectory_path.resolve()
    tasks_root = tasks_root.resolve() if tasks_root else None
    steps = _load_steps(trajectory_path, trajectory_kind)
    trajectory_text, summarized = render_trajectory(
        steps,
        max_step_chars=max_step_chars,
        max_total_chars=max_total_chars,
    )
    ctx = build_context(
        task_name,
        tasks_root,
        max_instruction_chars=max_instruction_chars,
        max_test_files=max_test_files,
        test_head_lines=test_head_lines,
        include_oracle_headers=include_oracle_headers,
    )
    # Agent code
    if trajectory_kind == "finance-zero":
        agent_code = _extract_finance_zero_code(steps[0].get("message", ""))
    else:
        agent_code = _extract_multi_step_code(steps)
    agent_code = _truncate(agent_code, max_agent_code_chars)

    # Output files
    output_files = _read_output_files(
        trial_path,
        max_files=max_output_files,
        max_chars_per_file=max_chars_per_output_file,
    )

    # Failing tests
    test_stdout_path = trial_path / "verifier" / "test-stdout.txt"
    failing_tests: list[dict[str, Any]] = []
    if test_stdout_path.is_file():
        try:
            failing_tests = _extract_failing_tests(test_stdout_path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass

    bundle: dict[str, Any] = {
        "trial_path": str(trial_path),
        "agent_harness": agent_harness,
        "model": model,
        "task_name": task_name,
        "trajectory_kind": trajectory_kind,
        "task_context": ctx,
        "trajectory_text": trajectory_text,
        "agent_code": agent_code,
        "output_files": output_files,
        "failing_tests": failing_tests,
        "n_steps": len(steps),
        "summarized": summarized,
        "size_chars": len(trajectory_text) + len(agent_code) + sum(len(v) for v in output_files.values()),
    }
    bundle["size_tokens_est"] = _approx_tokens(
        trajectory_text + agent_code + json.dumps(output_files) + json.dumps(failing_tests)
    )
    from list_failed_trials import result_status
    bundle["native_result"] = result_status(trial_path / "result.json")
    bundle["source_manifest"] = file_manifest(trial_path, exclude_names=("bundle.json", "labels.json", "labels.v4.json", "review_request.v4.json", "manual_responses.v4.json"))
    bundle["source_provenance"] = git_provenance(trial_path)
    bundle["trajectory_sha256"] = sha256(trajectory_path)
    bundle["extraction_limits"] = {"max_total_chars": max_total_chars, "max_step_chars": max_step_chars,
                                   "max_agent_code_chars": max_agent_code_chars, "max_output_files": max_output_files,
                                   "max_chars_per_output_file": max_chars_per_output_file}
    bundle["evidence_warnings"] = list(ctx.get("evidence_warnings", []))
    if summarized or any("[...truncated...]" in t for t in [agent_code, *output_files.values()]):
        bundle["evidence_warnings"].append("Evidence text truncated; inspect full hashed files before decisive conclusions.")
    if trajectory_kind != "finance-zero":
        bundle["evidence_warnings"].append("Agent code is observed full Write content, not a verified final executed snapshot; partial edits/shell writes may be missing.")
    bundle["verifier_stdout"] = test_stdout_path.read_text(encoding="utf-8", errors="replace") if test_stdout_path.is_file() else None
    out_dir = _find_output_dir(trial_path)
    bundle["output_manifest"] = file_manifest(out_dir) if out_dir else []
    rendered_outputs = set(output_files)
    bundle["omitted_output_files"] = [f["path"] for f in bundle["output_manifest"] if f["path"] not in rendered_outputs]
    if bundle["omitted_output_files"]:
        bundle["evidence_warnings"].append("Some output files are hashed but not rendered; inspect them separately.")
    bundle["bundle_hash"] = evidence_hash(bundle)
    return bundle


# ---------- CLI ------------------------------------------------------------------

def _autodetect(trial: Path) -> tuple[Optional[str], Optional[Path], str, str, Optional[str]]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from list_failed_trials import (  # type: ignore
        _detect_trajectory_kind,
        _task_name_from_result,
        _agent_model_from_dir,
    )
    agent_dir = trial / "agent"
    kind, traj = _detect_trajectory_kind(agent_dir)
    result_json = trial / "result.json"
    task_name = _task_name_from_result(result_json) if result_json.is_file() else None
    combo = trial.parent.parent.name if trial.parent.name in {"pass", "fail"} else trial.parent.name
    agent, model = _agent_model_from_dir(combo)
    return kind, traj, agent, model, task_name


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a quant-correctness judging bundle for a single trial.")
    p.add_argument("--trial", required=True)
    p.add_argument("--trajectory-kind", default=None)
    p.add_argument("--task-name", default=None)
    p.add_argument("--tasks-root", default=None)
    p.add_argument("--max-tokens", type=int, default=0)
    p.add_argument("--max-step-chars", type=int, default=0)
    p.add_argument("--max-instruction-chars", type=int, default=0)
    p.add_argument("--max-test-files", type=int, default=0)
    p.add_argument("--test-head-lines", type=int, default=0)
    p.add_argument("--max-output-files", type=int, default=0)
    p.add_argument("--max-chars-per-output-file", type=int, default=0)
    p.add_argument("--max-agent-code-chars", type=int, default=0)
    p.add_argument("--include-oracle-headers", action="store_true")
    p.add_argument("--out", default=None)
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    trial = Path(args.trial).expanduser().resolve()
    if not trial.is_dir():
        sys.stderr.write(f"[extract_solution] trial dir not found: {trial}\n")
        return 2
    kind, traj_path, agent_harness, model, task_name = _autodetect(trial)
    if args.trajectory_kind:
        kind = args.trajectory_kind
    if args.task_name:
        task_name = args.task_name
    if traj_path is None or kind is None:
        sys.stderr.write(f"[extract_solution] no trajectory file detected under {trial}/agent/\n")
        return 2
    if task_name is None:
        sys.stderr.write(f"[extract_solution] task_name unresolved for {trial}\n")
        return 2
    tasks_root = resolve_tasks_root(args.tasks_root, near=trial)
    bundle = build_bundle(
        trial_path=trial,
        trajectory_path=traj_path,
        trajectory_kind=kind,
        task_name=task_name,
        agent_harness=agent_harness,
        model=model,
        tasks_root=tasks_root,
        max_total_chars=args.max_tokens * 4,
        max_step_chars=args.max_step_chars,
        max_instruction_chars=args.max_instruction_chars,
        max_test_files=args.max_test_files,
        test_head_lines=args.test_head_lines,
        max_output_files=args.max_output_files,
        max_chars_per_output_file=args.max_chars_per_output_file,
        max_agent_code_chars=args.max_agent_code_chars,
        include_oracle_headers=args.include_oracle_headers,
    )
    out_path = Path(args.out) if args.out else (trial / "agent" / "bundle.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text(json.dumps(bundle, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    tmp.replace(out_path)
    sys.stderr.write(
        f"[extract_solution] {kind} task={task_name} steps={bundle['n_steps']} "
        f"code_chars={len(bundle['agent_code'])} output_files={len(bundle['output_files'])} "
        f"failing_tests={len(bundle['failing_tests'])} → {out_path}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
