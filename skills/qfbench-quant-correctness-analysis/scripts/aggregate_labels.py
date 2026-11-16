"""Aggregate v4 assessments with explicit missingness and native-result strata.

Legacy labels are counted as unavailable for v4 analysis, never silently upgraded.
A mode's denominator contains only valid assessed labels. A class is negative
only when every mode in that class is assessed negative; any observed positive
establishes a class positive. Undefined kappa remains blank, including all-negative
agreement. Trial acceptance is not inferred from mode labels or native reward.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from judge_trial import ALL_MODES, SCHEMA_VERSION, ROOT_CAUSES, validate_label, validate_review_decisions, prompt_set_hash
from list_failed_trials import scan_root
from review_common import strict_loads

CLASS_OF = {m: c for c, modes in {
    "Model_Formula": ALL_MODES[:3], "Convention_Units": ALL_MODES[3:6],
    "Data_Numerics": ALL_MODES[6:9], "Output_Compliance": ALL_MODES[9:]
}.items() for m in modes}
CLASSES = list(dict.fromkeys(CLASS_OF.values()))


def _walk_labels(root: Path) -> list[dict[str, Any]]:
    rows = []
    current_policy_hash = prompt_set_hash()
    for entry in scan_root(root, tasks_root=None):
        trial = Path(entry["trial_path"])
        path = trial / "agent" / "labels.v4.json"
        payload, error = {}, None
        try:
            payload = strict_loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
                raise ValueError("invalid v4 payload schema_version")
            if not isinstance(payload.get("labels"), dict):
                raise ValueError("labels must be an object")
        except (OSError, ValueError) as exc:
            payload = {}
            error = str(exc)
        stored_native = payload.get("native_result") if isinstance(payload.get("native_result"), dict) else {}
        native_drift = bool(stored_native and any(stored_native.get(k) != entry.get(k) for k in ("native_status", "reward", "result_sha256")))
        policy_drift = bool(payload.get("prompt_hash") and payload["prompt_hash"] != current_policy_hash)
        decisions = payload.get("review_decisions", {})
        decisions_error = None
        try:
            validate_review_decisions(decisions)
        except (ValueError, TypeError) as exc:
            decisions, decisions_error = {}, str(exc)
        for mode in ALL_MODES:
            info = payload.get("labels", {}).get(mode) if isinstance(payload.get("labels"), dict) else None
            reason = error
            valid = False
            if not reason and info is not None:
                try:
                    validate_label(info)
                    if info.get("ok") is not True:
                        raise ValueError(info.get("error", "label not marked ok"))
                    valid = True
                except (ValueError, TypeError) as exc:
                    reason = str(exc)
            elif not reason:
                reason = "mode label missing"
            status = info["assessment_status"] if valid else "missing" if info is None and not path.exists() else "invalid"
            eligible = valid and status == "assessed"
            rows.append({"trial_path": str(trial), "trial_name": trial.name,
                "agent_harness": entry["agent_harness"], "model": entry["model"],
                "task_name": entry["task_name"], "trajectory_kind": entry["trajectory_kind"],
                "native_status": stored_native.get("native_status", "UNKNOWN"), "reward": stored_native.get("reward"),
                "current_native_status": entry["native_status"], "current_reward": entry["reward"],
                "native_result_drift": native_drift,
                "native_provenance_status": "stored_at_assessment" if stored_native else "missing_stored_native_result",
                "source_freshness": "known_native_result_drift" if native_drift else "not_verified",
                "policy_drift": policy_drift,
                "bundle_hash": payload.get("bundle_hash"), "prompt_hash": payload.get("prompt_hash"),
                "review_decisions_json": json.dumps(decisions), "review_decisions_error": decisions_error,
                "mode": mode, "mode_class": CLASS_OF[mode], "assessment_status": status,
                "match": info["match"] if eligible else None,
                "confidence": info["confidence"] if eligible else None,
                "root_cause_class": info["root_cause_class"] if valid else "unresolved",
                "root_cause_id": info["root_cause_id"] if valid else None,
                "ok": valid, "eligible": eligible,
                "judge_model": payload.get("judge_model"), "reviewer": payload.get("reviewer"),
                "evidence_step_ids": json.dumps(info["evidence_step_ids"] if valid else []),
                "evidence_refs": json.dumps(info["evidence_refs"] if valid else []),
                "quote": info["quote"] if valid else "", "notes": info["notes"] if valid else reason,
                "legacy_labels_present": (trial / "agent" / "labels.json").is_file()})
    return rows


def _trial_decision_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trials = {row["trial_path"]: row for row in rows}
    result = []
    provenance_keys = ("trial_path", "task_name", "agent_harness", "model", "reviewer", "judge_model",
                       "bundle_hash", "prompt_hash", "native_status", "reward", "current_native_status",
                       "current_reward", "native_result_drift", "native_provenance_status", "source_freshness", "policy_drift")
    for row in trials.values():
        decisions = strict_loads(row["review_decisions_json"])
        for kind in ("candidate_correctness", "task_validity", "grader_adequacy"):
            decision = decisions.get(kind, {"status": "not_assessed", "evidence_refs": [],
                                             "notes": row["review_decisions_error"] or "No explicit decision supplied."})
            result.append({**{k: row[k] for k in provenance_keys}, "decision": kind,
                           "status": decision["status"], "evidence_refs": json.dumps(decision["evidence_refs"]),
                           "notes": decision["notes"]})
    return result


def _summarize(rows: list[dict[str, Any]], group_keys: list[str]) -> list[dict[str, Any]]:
    groups = {}
    for row in rows:
        groups.setdefault(tuple(row.get(k) for k in group_keys), []).append(row)
    result = []
    for key, items in sorted(groups.items(), key=lambda x: str(x[0])):
        row = dict(zip(group_keys, key))
        trials = sorted({r["trial_path"] for r in items})
        row["n_trials"] = len(trials)
        row["n_assessed"] = sum(r["eligible"] for r in items)
        row["n_unassessed"] = len(items) - row["n_assessed"]
        for mode in ALL_MODES:
            eligible = [r for r in items if r["mode"] == mode and r["eligible"]]
            n, pos = len(eligible), sum(r["match"] is True for r in eligible)
            row.update({f"{mode}_n_judged": n, f"{mode}_n_match": pos,
                        f"{mode}_pct": pos / n * 100 if n else None})
        for cls in CLASSES:
            expected = {m for m in ALL_MODES if CLASS_OF[m] == cls}
            n = pos = 0
            for trial in trials:
                observed = [r for r in items if r["trial_path"] == trial and r["mode_class"] == cls and r["eligible"]]
                positive = any(r["match"] is True for r in observed)
                if positive or {r["mode"] for r in observed} == expected:
                    n += 1
                    pos += positive
            row.update({f"{cls}_n_judged": n, f"{cls}_n_match": pos,
                        f"{cls}_pct": pos / n * 100 if n else None})
        result.append(row)
    return result


def cohens_kappa(a: list[int], b: list[int]) -> float:
    if not a or len(a) != len(b) or any(x not in (0, 1) for x in a+b):
        return math.nan
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    expected = pa * pb + (1-pa) * (1-pb)
    return (observed - expected) / (1 - expected) if expected < 1 else math.nan


def _load_human_labels(path: Path) -> dict[tuple[str, str, str, str], int]:
    result = {}
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if not {"trial_path", "mode", "human_match", "schema_version", "bundle_hash", "prompt_hash"} <= set(reader.fieldnames or []):
            raise ValueError("human CSV must bind schema_version, bundle_hash and prompt_hash; unversioned historical CSV is not implicitly migrated")
        for row in reader:
            value = (row.get("human_match") or "").strip()
            human_status = (row.get("human_assessment_status") or "").strip()
            if human_status and human_status != "assessed":
                if value:
                    raise ValueError("unassessed human labels must leave human_match empty")
                continue
            if not value:
                continue
            if value not in {"0", "1"} or row["mode"] not in ALL_MODES:
                raise ValueError("human labels must be explicit 0/1 for a recognized mode")
            if row["schema_version"] != SCHEMA_VERSION or any(len(row[k]) != 64 or any(c not in "0123456789abcdef" for c in row[k]) for k in ("bundle_hash", "prompt_hash")):
                raise ValueError("filled human labels require schema 4.0 and exact SHA-256 bundle/prompt hashes")
            key = (row["trial_path"], row["mode"], row["bundle_hash"], row["prompt_hash"])
            if key in result:
                raise ValueError(f"duplicate human label: {key}")
            result[key] = int(value)
    return result


def _agreement_table(rows, human):
    result = []
    versions = sorted({r.get("prompt_hash") for r in rows}, key=str)
    human_path_modes = {(key[0], key[1]) for key in human}
    for version in versions:
        version_rows = [r for r in rows if r.get("prompt_hash") == version]
        for mode in [*ALL_MODES, "OVERALL"]:
            selected = [r for r in version_rows if mode == "OVERALL" or r["mode"] == mode]
            pairs = []
            missing = stale = unassessed = 0
            for row in selected:
                key = (row["trial_path"], row["mode"], row.get("bundle_hash"), row.get("prompt_hash"))
                if not row["eligible"]:
                    unassessed += 1
                elif key in human:
                    pairs.append((human[key], int(row["match"])))
                elif key[:2] in human_path_modes:
                    stale += 1
                else:
                    missing += 1
            a, b = [p[0] for p in pairs], [p[1] for p in pairs]
            kappa = cohens_kappa(a, b)
            result.append({"prompt_hash": version, "mode": mode, "n": len(pairs), "kappa": None if math.isnan(kappa) else kappa,
                           "kappa_status": "defined" if not math.isnan(kappa) else "undefined_no_pairs" if not pairs else "undefined_zero_marginal_variance",
                           "observed_agreement": sum(x == y for x, y in pairs) / len(pairs) if pairs else None,
                           "n_human_match": sum(a), "n_judge_match": sum(b),
                           "n_excluded_missing_human_or_unassessed": len(selected) - len(pairs),
                           "n_excluded_human_version_mismatch": stale, "n_excluded_missing_human": missing,
                           "n_excluded_unassessed": unassessed})
    return result


def _write_csv(path, rows, columns=None):
    columns = columns or (list(rows[0]) if rows else [])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in columns})


def _md_table(rows, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        values = []
        for key in columns:
            value = row.get(key)
            values.append("—" if value is None else f"{value:.3f}" if isinstance(value, float) else str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--out")
    parser.add_argument("--human-labels")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    out = Path(args.out).expanduser().resolve() if args.out else root / "reports-v4"
    try:
        rows = _walk_labels(root)
        if not rows:
            raise ValueError("no discoverable trials")
        out.mkdir(parents=True, exist_ok=True)
        _write_csv(out / "labels.csv", rows)
        _write_csv(out / "trial_decisions.csv", _trial_decision_rows(rows))
        for filename, keys in (("summary_by_model.csv", ["agent_harness", "model", "prompt_hash"]),
                               ("summary_by_task.csv", ["task_name", "prompt_hash"]),
                               ("summary_by_native_status.csv", ["native_status", "prompt_hash"])):
            _write_csv(out / filename, _summarize(rows, keys))
        coverage = [{"mode": mode, **{status: sum(r["mode"] == mode and r["assessment_status"] == status for r in rows)
                    for status in ("assessed", "not_assessed", "insufficient_evidence", "error", "missing", "invalid")}} for mode in ALL_MODES]
        _write_csv(out / "coverage.csv", coverage)
        _write_csv(out / "review_needed.csv", [r for r in rows if not r["eligible"]])
        # Attribution includes assessed negatives (e.g. correct candidate rejected
        # by defective grader) and unresolved/unassessed rows, never just matches.
        counts = Counter((r["mode"], r["root_cause_class"], r["assessment_status"], r["match"]) for r in rows)
        attribution = [{"mode": k[0], "root_cause_class": k[1], "assessment_status": k[2], "match": k[3], "n": v}
                       for k, v in sorted(counts.items(), key=lambda x: str(x[0]))]
        _write_csv(out / "attribution.csv", attribution)
        text = ["# Quantitative correctness review — v4\n\n",
                f"Discovered trials: {len({r['trial_path'] for r in rows})}. Expected mode records: {len(rows)}.\n\n",
                "Native scoring outcomes, candidate correctness, task validity and grader adequacy remain separate. "
                "Rates use only assessed labels; missing/invalid/insufficient records are excluded and counted. "
                "A negative mode label is not certification. Classes require complete negatives or an observed positive. "
                "Legacy labels remain historical and are not implicitly migrated. "
                "Native strata use stored assessment-time results; current observations and drift are separate columns. "
                "Full source freshness is not verified by historical aggregation. Policy drift and known native-result drift are flagged. "
                "Separate candidate/task/grader decisions are preserved in trial_decisions.csv; absence means not_assessed. "
                "Summaries and agreement are stratified by policy/prompt hash; human matches require identical schema, bundle and prompt versions.\n\n",
                _md_table(coverage, list(coverage[0]))]
        if args.human_labels:
            human = _load_human_labels(Path(args.human_labels))
            agreement = _agreement_table(rows, human)
            eligible_keys = {(r["trial_path"], r["mode"], r.get("bundle_hash"), r.get("prompt_hash")) for r in rows if r["eligible"]}
            alignment = {"n_filled_human_labels": len(human), "n_matched_versioned_labels": sum(k in eligible_keys for k in human),
                         "unmatched_human_labels": [{"trial_path": k[0], "mode": k[1], "bundle_hash": k[2], "prompt_hash": k[3]} for k in human if k not in eligible_keys]}
            (out / "human_label_alignment.json").write_text(json.dumps(alignment, indent=2), encoding="utf-8")
            _write_csv(out / "agreement.csv", agreement)
            text.extend(["\n## Human agreement\n\n", _md_table(agreement, list(agreement[0])),
                         "\nUndefined kappa is not perfect reliability. Agreement uses only independently supplied binary human labels and assessed v4 records; pooled modes are descriptive, not independent observations.\n"])
        else:
            text.append("\nNo human calibration supplied; no calibration result is claimed.\n")
        (out / "report.md").write_text("".join(text), encoding="utf-8")
        print(f"Wrote v4 reports to {out}", file=sys.stderr)
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"[aggregate_labels] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
