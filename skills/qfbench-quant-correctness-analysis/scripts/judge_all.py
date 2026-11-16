"""Prepare local review requests for all discovered native statuses by default.

Optional provider sweep is sequential, requires explicit API authorization and
pricing, and shares a conservative reservation budget across the entire sweep.
No automatic retry or implicit calibration claim is made. Manual responses are
imported with judge_trial.py after individual review.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from judge_trial import (ALL_MODES, add_common_args, applicable_modes, bundle_from_args,
                         cfg_from_args, config_hash, _can_skip, _trial_paths,
                         judge_trial, prompt_set_hash, write_labels_atomic)
from list_failed_trials import scan_root
from task_context import resolve_tasks_root


async def _run(args) -> int:
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"root not found: {root}")
    if args.responses_json:
        raise ValueError("use judge_trial.py --responses-json for evidence-bound individual manual imports")
    if args.watch and (args.watch_interval <= 0 or args.watch_interval > 60):
        raise ValueError("watch interval must be >0 and <=60 seconds")
    cfg = cfg_from_args(args)
    prepare = args.dry_run or not args.allow_api
    modes = applicable_modes("", args.modes.split(",") if args.modes else ALL_MODES)
    while True:
        entries = scan_root(root, tasks_root=resolve_tasks_root(args.tasks_root, near=root),
                            include_passing=not args.failures_only)
        summary = {"schema_version": "4.0", "discovered": len(entries), "prepared": 0,
                   "judged": 0, "skipped": 0, "errors": [], "unevaluable": [],
                   "native_status_counts": {s: sum(e["native_status"] == s for e in entries)
                                            for s in ("PASS", "FAIL", "PARTIAL", "ERROR", "UNKNOWN")}}
        for entry in entries:
            trial = Path(entry["trial_path"])
            if not entry["ready_for_judging"]:
                summary["unevaluable"].append({"trial": str(trial), "reason": "missing task identity or trajectory", "native_status": entry["native_status"]})
                continue
            try:
                bundle = bundle_from_args(trial, args, trajectory_kind=entry["trajectory_kind"], task_name=entry["task_name"])
                paths = _trial_paths(trial)
                if not prepare and not args.force and _can_skip(paths.labels, bundle_hash=bundle["bundle_hash"],
                    prompt_hash=prompt_set_hash(), judge_model=cfg.model, requested_modes=modes, judge_config_hash=config_hash(cfg)):
                    summary["skipped"] += 1
                    continue
                payload = await judge_trial(trial, cfg, requested_modes=modes, bundle=bundle, dry_run=prepare)
                target = trial / "agent" / "review_request.v4.json" if prepare else paths.labels
                write_labels_atomic(target, payload)
                summary["prepared" if prepare else "judged"] += 1
                if not prepare and not payload["ok"]:
                    summary["errors"].append({"trial": str(trial), "reason": "one or more mode assessments failed; see v4 labels"})
            except (OSError, ValueError, TypeError, PermissionError) as exc:
                summary["errors"].append({"trial": str(trial), "reason": str(exc)})
        summary.update(reserved_usd=cfg.reserved_usd, actual_cost_usd=cfg.actual_cost_usd,
                       finished_at=time.time(), provider_requests_authorized=bool(args.allow_api))
        write_labels_atomic(root / ".judge_state.v4.json", summary)
        print(json.dumps(summary), file=sys.stderr)
        if not args.watch or (cfg.budget_usd is not None and cfg.reserved_usd >= cfg.budget_usd):
            return 1 if summary["errors"] else 0
        await asyncio.sleep(args.watch_interval)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True)
    add_common_args(p)
    p.add_argument("--failures-only", action="store_true")
    p.add_argument("--watch", action="store_true")
    p.add_argument("--watch-interval", type=float, default=60.0)
    # Retained as accepted CLI options; sequential processing is deliberate.
    for option in ("concurrency", "concurrency-openai", "concurrency-anthropic", "concurrency-gemini", "judge-concurrency-per-trial", "backoff-max-attempts"):
        p.add_argument("--" + option, type=int, default=1, help="Legacy option; v4 uses sequential calls without automatic retry.")
    try:
        return asyncio.run(_run(p.parse_args()))
    except (OSError, ValueError, TypeError, PermissionError) as exc:
        print(f"[judge_all] {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
