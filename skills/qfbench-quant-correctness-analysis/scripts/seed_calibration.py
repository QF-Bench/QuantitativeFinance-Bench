"""Stratified-sample N trials across native statuses for human spot-checking.

Produces an unfilled human review template; this is not completed calibration. Output:

    <out>/manifest.json         the chosen trials (subset of list_failed_trials)
    <out>/human_labels.csv      one row per (trial × mode); fill `human_match`
                                with 0/1 then feed back to aggregate_labels.py
                                via --human-labels.
    <out>/preview/<trial-name>/ immutable reviewer-input copies with no model labels
                                for each chosen trial, for easy reading.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Optional
from review_common import strict_loads, sha256

try:
    from list_failed_trials import scan_root  # type: ignore
    from judge_trial import ALL_MODES, applicable_modes, _load_or_build_bundle, prepare_request, write_labels_atomic  # type: ignore
    from task_context import resolve_tasks_root  # type: ignore
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from list_failed_trials import scan_root  # type: ignore
    from judge_trial import ALL_MODES, applicable_modes, _load_or_build_bundle, prepare_request, write_labels_atomic  # type: ignore
    from task_context import resolve_tasks_root  # type: ignore


def _stratify(entries: list[dict[str, Any]], n: int, *, seed: int) -> list[dict[str, Any]]:
    """Round-robin pick from buckets keyed by (agent_harness, model) until we
    have n entries. Within a bucket, items are randomly shuffled."""
    if n <= 0 or not entries:
        return []
    rng = random.Random(seed)
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for e in entries:
        key = (e.get("agent_harness") or "", e.get("model") or "", e.get("native_status") or "UNKNOWN")
        buckets.setdefault(key, []).append(e)
    for v in buckets.values():
        rng.shuffle(v)
    chosen: list[dict[str, Any]] = []
    keys = list(buckets.keys())
    rng.shuffle(keys)
    cursor = 0
    while len(chosen) < n and any(buckets[k] for k in keys):
        k = keys[cursor % len(keys)]
        cursor += 1
        if buckets[k]:
            chosen.append(buckets[k].pop())
    return chosen[:n]


def _build_csv_rows(chosen: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for e in chosen:
        kind = e.get("trajectory_kind") or ""
        modes = applicable_modes(kind, list(ALL_MODES))
        for m in modes:
            rows.append({
                "trial_path": e["trial_path"],
                "trial_name": e["trial_dir_name"],
                "agent_harness": e["agent_harness"],
                "model": e["model"],
                "task_name": e["task_name"],
                "trajectory_kind": kind,
                "mode": m,
                "schema_version": "4.0",
                "bundle_hash": e["bundle_hash"],
                "prompt_hash": e["prompt_hash"],
                "native_status": e.get("native_status"),
                "human_assessment_status": "",
                "human_match": "",
                "human_notes": "",
            })
    return rows


def _link_preview(trial: Path, dest: Path) -> list[dict[str, str]]:
    """Freeze reviewer inputs without model predictions or mutable symlinks."""
    dest.mkdir(parents=True, exist_ok=True)
    receipt = []
    for name in ("bundle.json", "review_request.v4.json"):
        src = trial / "agent" / name
        if not src.is_file():
            raise ValueError(f"calibration input missing: {src}")
        payload = strict_loads(src.read_text(encoding="utf-8"))
        if name == "review_request.v4.json":
            payload.pop("labels_template", None)
        dst = dest / name
        if dst.exists() or dst.is_symlink():
            raise ValueError(f"refusing to overwrite frozen calibration evidence: {dst}")
        dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        receipt.append({"path": name, "sha256": sha256(dst)})
    return receipt


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sample failed trials for human calibration.")
    p.add_argument("--root", required=True)
    p.add_argument("--tasks-root", default=None)
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default=None)
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        sys.stderr.write(f"[seed_calibration] root not found: {root}\n")
        return 2
    out = Path(args.out).expanduser().resolve() if args.out else (root / "calibration-v4")
    if (out / "human_labels.csv").exists():
        sys.stderr.write("[seed_calibration] refusing to overwrite existing human labels; choose a fresh --out\n")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    tasks_root = resolve_tasks_root(args.tasks_root, near=root)
    entries = scan_root(root, tasks_root=tasks_root)
    eligible = [e for e in entries if e.get("ready_for_judging") and e.get("trajectory_kind")]
    if not eligible:
        sys.stderr.write(f"[seed_calibration] no eligible trials under {root}\n")
        return 1
    chosen = _stratify(eligible, args.n, seed=args.seed)
    # Refresh source identity before sampling evidence. This is local reviewer
    # preparation only; it neither calls providers nor changes historical labels.
    for e in chosen:
        trial = Path(e["trial_path"])
        bundle = _load_or_build_bundle(trial, tasks_root=tasks_root,
                    trajectory_kind=e["trajectory_kind"], task_name=e["task_name"])
        request = prepare_request(bundle, list(ALL_MODES))
        write_labels_atomic(trial / "agent" / "review_request.v4.json", request)
        e.update(schema_version="4.0", bundle_hash=bundle["bundle_hash"], prompt_hash=request["prompt_hash"])
    (out / "manifest.json").write_text(
        json.dumps({"schema_version": "4.0", "calibration_status": "template_unreviewed", "seed": args.seed, "n": len(chosen), "entries": chosen}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    rows = _build_csv_rows(chosen)
    cols = [
        "trial_path", "trial_name", "agent_harness", "model", "task_name",
        "trajectory_kind", "mode", "schema_version", "bundle_hash", "prompt_hash", "native_status", "human_assessment_status", "human_match", "human_notes",
    ]
    with (out / "human_labels.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    preview_root = out / "preview"
    for e in chosen:
        dest = preview_root / (e["agent_harness"] + "_" + e["model"]) / e["trial_dir_name"]
        receipt = _link_preview(Path(e["trial_path"]), dest)
        (dest / "frozen_manifest.json").write_text(json.dumps({"schema_version": "4.0",
            "bundle_hash": e["bundle_hash"], "prompt_hash": e["prompt_hash"], "files": receipt,
            "notice": "Frozen reviewer input only; no model predictions included. Hashes identify this evidence version."}, indent=2), encoding="utf-8")
    sys.stderr.write(
        f"[seed_calibration] sampled {len(chosen)}/{len(eligible)} trials → {out}\n"
        f"[seed_calibration] fill human_match column in {out / 'human_labels.csv'}, "
        f"then re-run aggregate_labels.py --human-labels {out / 'human_labels.csv'}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
