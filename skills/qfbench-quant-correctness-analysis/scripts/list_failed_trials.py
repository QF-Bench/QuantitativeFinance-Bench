"""Discover all trials and preserve native scoring status separately from diagnosis.

The historical filename is retained for compatibility. Default discovery includes
PASS, FAIL, PARTIAL, ERROR and UNKNOWN; --failures-only is an explicit filter.
Directory names never determine status. Reward uses the documented [0, 1] scale.
Missing reward is UNKNOWN, malformed/nonfinite reward or execution error is ERROR.
Neither native status nor reward establishes financial correctness.
"""

from __future__ import annotations

import argparse
import json
import math
from review_common import strict_loads, sha256
import os
import sys
from pathlib import Path
from typing import Any, Optional

try:
    from task_context import resolve_tasks_root  # type: ignore
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from task_context import resolve_tasks_root  # type: ignore


# The authoritative task_name lives in result.json. As a fallback when the file
# is missing, we suffix-match the trial dir name against the set of task names
# under tasks_root, picking the longest match.


def _detect_trajectory_kind(agent_dir: Path) -> tuple[Optional[str], Optional[Path]]:
    if not agent_dir.is_dir():
        return None, None
    files = {f.name: f for f in agent_dir.iterdir() if f.is_file()}
    if "claude-code.txt" in files and "trajectory.json" in files:
        return "claude-code", files["trajectory.json"]
    if "codex.txt" in files and "trajectory.json" in files:
        return "codex", files["trajectory.json"]
    if "gemini-cli.txt" in files and "trajectory.json" in files:
        # standard schema preferred when both .trajectory.json and trajectory.json are present
        return "gemini-cli", files["trajectory.json"]
    if "gemini-cli.trajectory.json" in files:
        return "gemini-cli-alt", files["gemini-cli.trajectory.json"]
    if "finance-zero.txt" in files:
        return "finance-zero", files["finance-zero.txt"]
    if "trajectory.json" in files:
        return "trajectory-json", files["trajectory.json"]
    return None, None


def result_status(result_json: Path) -> dict[str, Any]:
    out = {"native_status": "UNKNOWN", "reward": None, "reward_raw": None,
           "status_reason": "missing result.json", "finished": False}
    if not result_json.is_file():
        return out
    out["result_sha256"] = sha256(result_json)
    try:
        data = strict_loads(result_json.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("result.json must be an object")
    except (OSError, ValueError) as exc:
        out.update(native_status="ERROR", status_reason=f"invalid result.json: {exc}")
        return out
    out["finished"] = bool(data.get("finished_at"))
    vr = data.get("verifier_result")
    rewards = vr.get("rewards") if isinstance(vr, dict) else None
    raw = rewards.get("reward") if isinstance(rewards, dict) else None
    out["reward_raw"] = raw
    if raw is not None:
        try:
            if isinstance(raw, bool):
                raise ValueError("boolean reward")
            value = float(raw)
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("reward outside finite [0, 1]")
            out["reward"] = value
        except (TypeError, ValueError):
            out.update(native_status="ERROR", status_reason="invalid reward")
            return out
    execution = str(data.get("status") or data.get("termination_status") or "").upper()
    if data.get("exception_info") or data.get("error") or (isinstance(vr, dict) and (vr.get("error") or vr.get("exception_info"))) or execution in {"ERROR", "TIMEOUT", "TIMED_OUT"}:
        out.update(native_status="ERROR", status_reason="execution/infrastructure error; reward retained",
                   execution_status=execution or "ERROR")
    elif not out["finished"]:
        out["status_reason"] = "unfinished or completion metadata missing"
    elif raw is None:
        out["status_reason"] = "reward missing; quantitative outcome unevaluated"
    else:
        out.update(native_status="PASS" if out["reward"] == 1 else "FAIL" if out["reward"] == 0 else "PARTIAL",
                   status_reason="native reward on [0, 1] scale; not an independent correctness verdict")
    return out


def _extract_reward(result_json: Path) -> Optional[float]:
    return result_status(result_json)["reward"]


def _result_finished(result_json: Path) -> bool:
    return result_status(result_json)["finished"]


def _task_name_from_result(result_json: Path) -> Optional[str]:
    try:
        with result_json.open("r", encoding="utf-8") as fh:
            data = strict_loads(fh.read())
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    name = data.get("task_name")
    if isinstance(name, str) and name:
        return name.rsplit("/", 1)[-1]  # strip any path prefix like "qfbench/power-options"
    tid = data.get("task_id")
    if isinstance(tid, dict):
        path = tid.get("path")
        if isinstance(path, str) and path:
            return path.rsplit("/", 1)[-1]
    return None


def _task_name_from_dir(trial_name: str, known_tasks: list[str]) -> Optional[str]:
    """Recover task_name by finding the longest known task that is a suffix
    of trial_name (after stripping the `fb-` prefix). Returns None if no
    known tasks match."""
    candidate = trial_name[3:] if trial_name.startswith("fb-") else trial_name
    matches = [t for t in known_tasks if candidate.endswith(t)]
    if not matches:
        return None
    matches.sort(key=len, reverse=True)
    return matches[0]


def _list_known_tasks(tasks_root: Optional[Path]) -> list[str]:
    if tasks_root is None or not tasks_root.is_dir():
        return []
    return [p.name for p in tasks_root.iterdir() if p.is_dir() and not p.name.startswith(".")]


def _agent_model_from_dir(name: str) -> tuple[str, str]:
    if "_" in name:
        agent, model = name.split("_", 1)
        return agent, model
    return name, ""


# Names we never treat as trial directories at any level.
_RESERVED_DIRS = frozenset({".git", "reports", "calibration", ".judge_state",
                            "figures", "_cache"})


def _looks_like_trial(p: Path) -> bool:
    """A directory is a trial iff it has either result.json or an agent/ subdir."""
    if not p.is_dir() or p.name.startswith("."):
        return False
    if p.name in _RESERVED_DIRS:
        return False
    return (p / "result.json").is_file() or (p / "agent").is_dir()


def walk_trial_dirs(combo: Path) -> list[tuple[Path, str]]:
    """Yield (trial_path, source_split) for every trial under a combo dir.

    Supports both the curated `<combo>/{pass,fail}/<trial>/` layout and the
    flat `<combo>/<trial>/` layout. If both shapes are present in the same
    combo (e.g. a few uncategorized trials at the top level alongside curated
    pass/fail), all of them are picked up.

    `source_split` is informational ("pass" / "fail" / "flat"); the caller
    derives the real pass/fail status from `result.json`.
    """
    out: list[tuple[Path, str]] = []
    if not combo.is_dir():
        return out
    for child in sorted(combo.iterdir(), key=lambda p: p.name):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if child.name in ("pass", "fail") and not _looks_like_trial(child):
            for trial in sorted(child.iterdir(), key=lambda p: p.name):
                if _looks_like_trial(trial):
                    out.append((trial, child.name))
            continue
        if child.name in _RESERVED_DIRS:
            continue
        if _looks_like_trial(child):
            out.append((child, "flat"))
    return out


def scan_root(
    root: Path,
    *,
    tasks_root: Optional[Path],
    include_passing: bool = True,
) -> list[dict[str, Any]]:
    root = root.resolve()
    tasks_root = tasks_root.resolve() if tasks_root else None
    entries: list[dict[str, Any]] = []
    known_tasks = _list_known_tasks(tasks_root)
    for combo in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
        if combo.name in _RESERVED_DIRS:
            continue
        if "_" not in combo.name:
            continue
        agent, model = _agent_model_from_dir(combo.name)
        for trial, source_split in walk_trial_dirs(combo):
            result_json = trial / "result.json"
            reward: Optional[float] = None
            ready = False
            task_name: Optional[str] = None
            if result_json.is_file():
                reward = _extract_reward(result_json)
                ready = _result_finished(result_json)
                task_name = _task_name_from_result(result_json)
            if task_name is None:
                task_name = _task_name_from_dir(trial.name, known_tasks)
            status = result_status(result_json)
            is_failure = status["native_status"] == "FAIL"
            if not is_failure and not include_passing:
                continue
            kind, traj_path = _detect_trajectory_kind(trial / "agent")
            resolved = None
            if tasks_root is not None and task_name:
                cand = tasks_root / task_name
                if cand.is_dir():
                    resolved = str(cand)
            entries.append(
                {
                    "trial_path": str(trial),
                    "agent_harness": agent,
                    "model": model,
                    "task_name": task_name,
                    "trial_dir_name": trial.name,
                    "trajectory_kind": kind,
                    "trajectory_path": str(traj_path) if traj_path else None,
                    "reward": reward,
                    "is_failure": is_failure,
                    "source_split": source_split,
                    "ready_for_judging": bool(kind is not None and task_name),
                    **status,
                    "tasks_root_path": resolved,
                }
            )
    return entries


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Discover all QF-Bench trial statuses and emit a manifest.")
    p.add_argument("--root", default=".",
                   help="Root containing <agent>_<model>/<trial>/ or "
                        "<agent>_<model>/{pass,fail}/<trial>/ (both layouts auto-detected).")
    p.add_argument("--tasks-root", default=None,
                   help="QF-Bench tasks root; falls back to QFBENCH_TASKS_ROOT.")
    p.add_argument("--include-passing", action="store_true", help="Compatibility flag; all statuses are included by default.")
    p.add_argument("--failures-only", action="store_true", help="Explicitly restrict discovery to native FAIL trials.")
    p.add_argument("--out", default=None, help="Output JSON path; default stdout.")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        sys.stderr.write(f"[list_failed_trials] root not found: {root}\n")
        return 2
    tasks_root = resolve_tasks_root(args.tasks_root, near=root)
    entries = scan_root(root, tasks_root=tasks_root, include_passing=not args.failures_only)
    n_failed = sum(1 for e in entries if e["is_failure"])
    manifest = {
        "root": str(root),
        "tasks_root": str(tasks_root) if tasks_root else None,
        "n_failed": n_failed,
        "discovery_filter": "native_FAIL_only" if args.failures_only else "all_statuses",
        "n_total_listed": len(entries),
        "status_counts": {s: sum(e["native_status"] == s for e in entries) for s in ("PASS", "FAIL", "PARTIAL", "ERROR", "UNKNOWN")},
        "entries": entries,
    }
    serialized = json.dumps(manifest, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(serialized, encoding="utf-8")
        sys.stderr.write(
            f"[list_failed_trials] wrote {n_failed} failed "
            f"({len(entries)} listed) → {args.out}\n"
        )
    else:
        sys.stdout.write(serialized + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
