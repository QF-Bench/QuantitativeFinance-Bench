"""Prepare or manually assess ten quantitative modes; providers require explicit opt-in.

Default: write a complete local review_request.v4.json, with no provider import,
credential access or model request. Import reviewer JSON using --responses-json.
V4 labels are separate from historical labels.json. A provider path exists only
for separately authorized work and requires --allow-api, --budget-usd and an
explicit exact-model pricing file. The current local blind campaign forbids it.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from extract_solution import build_bundle
from list_failed_trials import _detect_trajectory_kind, _task_name_from_result, _agent_model_from_dir
from review_common import payload_hash, sha256, strict_loads
from task_context import resolve_tasks_root

SKILL_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = SKILL_ROOT / "prompts"
SCHEMA_VERSION = "4.0"
ALL_MODES = ["wrong_model_measure", "missing_extra_formula_term", "wrong_parameterization",
             "unit_scale_error", "sign_convention_error", "time_calendar_convention",
             "data_fabrication_wrong_source", "numerical_optimization_failure",
             "statistical_variant_mismatch", "spec_output_compliance"]
ROOT_CAUSES = {"agent", "task_side", "mixed", "infrastructure", "unresolved"}
ASSESSMENT_STATUSES = {"assessed", "insufficient_evidence", "not_assessed", "error"}
LABEL_FIELDS = {"assessment_status", "match", "confidence", "root_cause_class", "root_cause_id",
                "evidence_step_ids", "evidence_refs", "quote", "notes"}


def load_prompt(mode: str) -> str:
    if mode not in ALL_MODES:
        raise ValueError(f"unknown mode: {mode}")
    return (PROMPTS_DIR / f"{mode}.md").read_text(encoding="utf-8")


def load_system_prompt() -> str:
    return (PROMPTS_DIR / "system_judge.md").read_text(encoding="utf-8")


def fill_placeholders(prompt: str, bundle: dict[str, Any]) -> str:
    ctx = bundle.get("task_context") or {}
    agent_evidence = {k: v for k, v in bundle.items() if k != "task_context"}
    replacements = {
        "TRAJECTORY_KIND": bundle.get("trajectory_kind", "unknown"),
        "TASK_INSTRUCTION_MD": ctx.get("instruction_md") or "[instruction unavailable]",
        "TASK_TESTS_DIGEST": json.dumps(ctx, ensure_ascii=False),
        "AGENT_SOLUTION": json.dumps(agent_evidence, ensure_ascii=False),
        "TRAJECTORY": bundle.get("trajectory_text") or "[trajectory unavailable]",
    }
    for key, value in replacements.items():
        prompt = prompt.replace("{{" + key + "}}", value)
    return "Active review policy (historical anecdotes are not evidence):\n" + json.dumps(policy_context(), ensure_ascii=False) + "\n\nMode and trial evidence:\n" + prompt


def policy_context() -> dict[str, str]:
    """Current review rules included for a fresh reviewer, separate from evidence."""
    names = ["SKILL.md", "TAXONOMY.md", "INDUSTRY_STANDARDS.md",
             "references/output-schema.md", "references/review-evidence.md",
             "references/spec_citation_patterns.md", "references/spread_option_approximations.md"]
    return {name: (SKILL_ROOT / name).read_text(encoding="utf-8") for name in names if (SKILL_ROOT / name).is_file()}


def prompt_set_hash() -> str:
    # Every Markdown policy/reference file participates, even historical files
    # excluded from active prompt context. No silent reuse after policy changes.
    paths = list(SKILL_ROOT.rglob("*.md")) + list((SKILL_ROOT / "scripts").glob("*.py"))
    paths += list(SKILL_ROOT.rglob("*.schema.json"))
    paths += [p for p in (SKILL_ROOT / "schemas").glob("*.json") if p not in paths]
    return payload_hash({str(p.relative_to(SKILL_ROOT)): sha256(p) for p in sorted(paths)})


def validate_label(data: Any) -> dict[str, Any]:
    """Validate without coercing missing, uncertain or malformed fields to false."""
    if not isinstance(data, dict):
        raise ValueError("label must be an object")
    missing = LABEL_FIELDS - data.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    status = data["assessment_status"]
    if status not in ASSESSMENT_STATUSES:
        raise ValueError("invalid assessment_status")
    confidence = data["confidence"]
    if status == "assessed":
        if type(data["match"]) is not bool:
            raise ValueError("assessed match must be boolean")
        if type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("assessed confidence must be finite [0, 1]")
    elif data["match"] is not None or confidence is not None:
        raise ValueError("unassessed match and confidence must be null")
    if data["root_cause_class"] not in ROOT_CAUSES:
        raise ValueError("invalid root_cause_class")
    if data["root_cause_id"] is not None and (not isinstance(data["root_cause_id"], str) or not data["root_cause_id"].strip()):
        raise ValueError("root_cause_id must be a nonempty string or null")
    ids = data["evidence_step_ids"]
    if not isinstance(ids, list) or any(type(x) is not int or x < 0 for x in ids):
        raise ValueError("evidence_step_ids must be nonnegative integer list")
    refs = data["evidence_refs"]
    if not isinstance(refs, list) or any(not isinstance(x, str) or not x.strip() for x in refs):
        raise ValueError("evidence_refs must be nonempty string references")
    if any(not isinstance(data[k], str) for k in ("quote", "notes")):
        raise ValueError("quote and notes must be strings")
    if not data["notes"].strip() or (status == "assessed" and not refs):
        raise ValueError("notes required; assessed labels also require evidence_refs")
    return {k: data[k] for k in LABEL_FIELDS}


def parse_judge_response(raw: str) -> dict[str, Any]:
    try:
        return {"ok": True, **validate_label(strict_loads(raw))}
    except (ValueError, TypeError) as exc:
        return {"ok": False, "error": str(exc), "raw": raw}


def unassessed(reason: str, status: str = "not_assessed") -> dict[str, Any]:
    return {"assessment_status": status, "match": None, "confidence": None,
            "root_cause_class": "unresolved", "root_cause_id": None,
            "evidence_step_ids": [], "evidence_refs": [], "quote": "", "notes": reason}


def validate_review_decisions(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("review_decisions must be an object")
    allowed = {"candidate_correctness", "task_validity", "grader_adequacy"}
    if set(value) - allowed:
        raise ValueError("unknown review_decisions key")
    for key, item in value.items():
        if not isinstance(item, dict) or item.get("status") not in {"supported", "defect", "unresolved", "not_assessed"}:
            raise ValueError(f"invalid review decision: {key}")
        refs = item.get("evidence_refs")
        if not isinstance(refs, list) or any(not isinstance(r, str) or not r.strip() for r in refs):
            raise ValueError(f"invalid evidence_refs: {key}")
        if not isinstance(item.get("notes"), str) or not item["notes"].strip():
            raise ValueError(f"decision requires notes: {key}")
        if item["status"] in {"supported", "defect"} and not refs:
            raise ValueError(f"decisive review decision requires evidence: {key}")
    return value


@dataclass
class JudgeCfg:
    model: str = "manual"
    reasoning_effort: str = "high"
    temperature: float = 0.0
    max_tokens: int = 2048
    timeout: float = 180.0
    pricing: dict[str, dict[str, float]] = field(default_factory=dict)
    allow_api: bool = False
    budget_usd: Optional[float] = None
    reserved_usd: float = 0.0
    actual_cost_usd: float = 0.0


def validate_api_config(cfg: JudgeCfg) -> None:
    # This runs before even importing a provider library or inspecting credentials.
    if not cfg.allow_api:
        raise PermissionError("provider disabled: --allow-api required (forbidden in current local campaign)")
    if cfg.budget_usd is None or not math.isfinite(cfg.budget_usd) or cfg.budget_usd <= 0:
        raise ValueError("provider requires a positive finite --budget-usd")
    price = cfg.pricing.get(cfg.model)
    if not isinstance(price, dict) or any(type(price.get(k)) not in (int, float) or not math.isfinite(price[k]) or price[k] <= 0 for k in ("input_per_million", "output_per_million")):
        raise ValueError("explicit exact-model --pricing-json with positive input_per_million/output_per_million is required")
    if cfg.max_tokens <= 0 or not math.isfinite(cfg.timeout) or cfg.timeout <= 0:
        raise ValueError("max_tokens and timeout must be positive")


async def acomplete_judge(cfg: JudgeCfg, system_prompt: str, user_prompt: str) -> dict[str, Any]:
    validate_api_config(cfg)
    price = cfg.pricing[cfg.model]
    # Byte-based allowance is intentionally conservative, but prices/usage remain
    # provider-dependent. Retain each reservation even after a failed request.
    input_allowance = len((system_prompt + user_prompt).encode("utf-8")) + 4096
    reserved = (input_allowance * price["input_per_million"] + cfg.max_tokens * price["output_per_million"]) / 1_000_000
    if cfg.reserved_usd + reserved > cfg.budget_usd:
        return {"ok": False, "error": "budget reservation would exceed cap", "cost_usd": 0.0}
    cfg.reserved_usd += reserved  # no await before shared reservation is committed
    try:
        import litellm
        kwargs = {"model": cfg.model, "messages": [{"role": "system", "content": system_prompt},
                   {"role": "user", "content": user_prompt}], "max_tokens": cfg.max_tokens,
                  "timeout": cfg.timeout, "num_retries": 0}
        if cfg.reasoning_effort:
            kwargs["reasoning_effort"] = cfg.reasoning_effort
        response = await litellm.acompletion(**kwargs)
        content = response.choices[0].message.content
        usage = response.usage
        def token_value(key):
            value = usage.get(key) if isinstance(usage, dict) else getattr(usage, key, None)
            if type(value) is not int or value < 0:
                raise ValueError("provider did not return valid token usage")
            return value
        prompt_tokens, completion_tokens = token_value("prompt_tokens"), token_value("completion_tokens")
        cost = (prompt_tokens * price["input_per_million"] + completion_tokens * price["output_per_million"]) / 1_000_000
        cfg.actual_cost_usd += cost
        if cost > reserved:
            cfg.reserved_usd += cost - reserved
        return {"ok": True, "content": content, "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
                "cost_usd": cost, "reserved_usd": reserved}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "cost_usd": None, "reserved_usd": reserved}


@dataclass
class TrialPaths:
    trial: Path
    bundle: Path
    labels: Path


def _trial_paths(trial: Path) -> TrialPaths:
    return TrialPaths(trial, trial / "agent" / "bundle.json", trial / "agent" / "labels.v4.json")


def _load_or_build_bundle(trial: Path, *, trajectory_kind=None, task_name=None, tasks_root=None,
                          max_total_chars=0, max_step_chars=0, max_instruction_chars=0,
                          max_test_files=0, test_head_lines=0, include_oracle_headers=False,
                          refresh=False) -> dict[str, Any]:
    # Always re-read source; a cached truncated bundle cannot detect changed tails.
    trial = trial.resolve()
    tasks_root = tasks_root.resolve() if tasks_root else None
    kind, path = _detect_trajectory_kind(trial / "agent")
    kind = trajectory_kind or kind
    name = task_name or _task_name_from_result(trial / "result.json")
    if not kind or not path or not name:
        raise ValueError(f"missing task identity or trajectory: {trial}")
    combo = trial.parent.parent.name if trial.parent.name in {"pass", "fail"} else trial.parent.name
    agent, model = _agent_model_from_dir(combo)
    bundle = build_bundle(trial_path=trial, trajectory_path=path, trajectory_kind=kind,
                          task_name=name, agent_harness=agent, model=model, tasks_root=tasks_root,
                          max_total_chars=max_total_chars, max_step_chars=max_step_chars,
                          max_instruction_chars=max_instruction_chars, max_test_files=max_test_files,
                          test_head_lines=test_head_lines, include_oracle_headers=include_oracle_headers)
    write_labels_atomic(_trial_paths(trial).bundle, bundle)
    return bundle


def applicable_modes(trajectory_kind: str, requested: list[str]) -> list[str]:
    modes = requested or ALL_MODES
    if len(set(modes)) != len(modes) or set(modes) - set(ALL_MODES):
        raise ValueError("requested modes must be unique members of the ten-mode taxonomy")
    return list(modes)


def config_hash(cfg: JudgeCfg) -> str:
    return payload_hash({k: getattr(cfg, k) for k in ("model", "reasoning_effort", "temperature", "max_tokens", "timeout")})


def _can_skip(labels_path: Path, *, bundle_hash: str, prompt_hash: str, judge_model: str,
              requested_modes: list[str], judge_config_hash: Optional[str] = None) -> bool:
    try:
        cached = strict_loads(labels_path.read_text(encoding="utf-8"))
        if not isinstance(cached, dict) or cached.get("schema_version") != SCHEMA_VERSION or not cached.get("ok"):
            return False
        if any(cached.get(k) != v for k, v in {"bundle_hash": bundle_hash, "prompt_hash": prompt_hash,
               "judge_model": judge_model, "judge_config_hash": judge_config_hash}.items()):
            return False
        for mode in requested_modes:
            info = cached["labels"][mode]
            validate_label(info)
            if not info.get("ok") or info["assessment_status"] != "assessed":
                return False
        return True
    except (OSError, ValueError, TypeError, KeyError):
        return False


def _check_insufficient_solution(bundle: dict[str, Any]) -> tuple[bool, str]:
    # No length heuristic: concise formulas and shell-authored code can be valid.
    empty = not any(bundle.get(k) for k in ("agent_code", "output_files", "trajectory_text"))
    return empty, "No candidate code, output or trajectory evidence is available."


def _build_insufficient_labels(modes: list[str], reason: str) -> dict[str, Any]:
    return {mode: {"ok": True, **unassessed(reason, "insufficient_evidence")} for mode in modes}


def prepare_request(bundle: dict[str, Any], modes: list[str]) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "bundle_hash": bundle["bundle_hash"],
            "prompt_hash": prompt_set_hash(), "system_prompt": load_system_prompt(),
            "review_policy": policy_context(),
            "prompts": {m: fill_placeholders(load_prompt(m), bundle) for m in modes},
            "labels_template": {m: unassessed("Pending independent evidence review.") for m in modes},
            "evidence_warnings": bundle.get("evidence_warnings", []),
            "notice": "Reviewer context includes references/checkers. Never supply this request to a blind solver."}


async def judge_trial(trial: Path, cfg: JudgeCfg, *, requested_modes: list[str], bundle: dict[str, Any],
                      concurrency: int = 1, dry_run: bool = False, responses: Optional[dict[str, Any]] = None,
                      reviewer: Optional[str] = None) -> dict[str, Any]:
    modes = applicable_modes(bundle["trajectory_kind"], requested_modes)
    if dry_run:
        return prepare_request(bundle, modes)
    if responses is None:
        validate_api_config(cfg)
    else:
        if not reviewer or not reviewer.strip():
            raise ValueError("manual import requires --reviewer identity")
        if not isinstance(responses, dict) or responses.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("manual response requires schema_version 4.0; legacy labels are not migrated implicitly")
        for key, expected in (("bundle_hash", bundle["bundle_hash"]), ("prompt_hash", prompt_set_hash())):
            if responses.get(key) != expected:
                raise ValueError(f"manual response {key} must match prepared current evidence")
        if not isinstance(responses.get("labels"), dict) or set(responses["labels"]) != set(modes):
            raise ValueError("manual labels must contain exactly the requested modes")
        for label in responses["labels"].values():
            validate_label(label)
    started_cost, started_reservation = cfg.actual_cost_usd, cfg.reserved_usd
    results = {}
    system = load_system_prompt()
    for mode in modes:
        if responses is not None:
            results[mode] = {"ok": True, **validate_label(responses["labels"][mode])}
            continue
        insufficient, reason = _check_insufficient_solution(bundle)
        if insufficient:
            results[mode] = _build_insufficient_labels([mode], reason)[mode]
            continue
        response = await acomplete_judge(cfg, system, fill_placeholders(load_prompt(mode), bundle))
        if response.get("ok"):
            parsed = parse_judge_response(response.get("content") or "")
        else:
            parsed = {"ok": False, "error": response.get("error")}
        results[mode] = parsed if parsed["ok"] else {"ok": False, **unassessed(parsed["error"], "error"), "error": parsed["error"]}
        results[mode].update(usage=response.get("usage"), cost_usd=response.get("cost_usd"), judge_raw=response.get("content"))
    decisions = validate_review_decisions(responses.get("review_decisions", {})) if responses is not None else {}
    return {"schema_version": SCHEMA_VERSION, "ok": all(x["ok"] for x in results.values()), "labels": results,
            "bundle_hash": bundle["bundle_hash"], "prompt_hash": prompt_set_hash(),
            "judge_config_hash": config_hash(cfg), "judge_model": cfg.model,
            "reviewer": reviewer, "review_decisions": decisions,
            "task_context_hash": bundle["task_context"]["content_hash"],
            **{k: bundle[k] for k in ("trial_path", "trajectory_kind", "task_name", "agent_harness", "model", "native_result")},
            "judged_at": time.time(),
            "total_cost_usd": None if responses is None and any(r.get("cost_usd") is None and r["assessment_status"] == "error" for r in results.values()) else cfg.actual_cost_usd - started_cost,
            "known_cost_usd": cfg.actual_cost_usd - started_cost,
            "reserved_usd": cfg.reserved_usd - started_reservation, "evidence_warnings": bundle.get("evidence_warnings", [])}


def write_labels_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False)
    if path.name == "labels.v4.json" and path.exists() and path.read_text(encoding="utf-8") != data:
        archive = path.parent / "review_history"
        archive.mkdir(exist_ok=True)
        backup = archive / (sha256(path) + ".json")
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(path)


def add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--tasks-root")
    p.add_argument("--judge-model", default="manual")
    p.add_argument("--reasoning-effort", default="high")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-tokens", type=int, default=2048)
    p.add_argument("--timeout", type=float, default=180.0)
    p.add_argument("--modes")
    p.add_argument("--allow-api", action="store_true")
    p.add_argument("--budget-usd", type=float)
    p.add_argument("--pricing-json")
    p.add_argument("--prepare-only", "--dry-run", dest="dry_run", action="store_true")
    p.add_argument("--responses-json")
    p.add_argument("--reviewer")
    p.add_argument("--force", action="store_true")
    p.add_argument("--refresh-bundle", action="store_true", help="Compatibility flag; source is always refreshed.")
    p.add_argument("--include-oracle-headers", action="store_true", help="Also add a reference signature digest; references remain unverified evidence.")
    for name in ("bundle-max-tokens", "bundle-max-step-chars", "bundle-max-instruction-chars", "bundle-max-test-files", "bundle-test-head-lines"):
        p.add_argument("--" + name, type=int, default=0, help="0 means complete context; any positive limit is reported.")


def cfg_from_args(args) -> JudgeCfg:
    pricing = strict_loads(Path(args.pricing_json).read_text()) if args.pricing_json else {}
    cfg = JudgeCfg(model=args.judge_model, reasoning_effort=args.reasoning_effort,
                   temperature=args.temperature, max_tokens=args.max_tokens, timeout=args.timeout,
                   pricing=pricing, allow_api=args.allow_api, budget_usd=args.budget_usd)
    if args.allow_api:
        validate_api_config(cfg)
    return cfg


def bundle_from_args(trial: Path, args, **kw) -> dict[str, Any]:
    return _load_or_build_bundle(trial, tasks_root=resolve_tasks_root(args.tasks_root, near=trial),
             max_total_chars=args.bundle_max_tokens * 4, max_step_chars=args.bundle_max_step_chars,
             max_instruction_chars=args.bundle_max_instruction_chars, max_test_files=args.bundle_max_test_files,
             test_head_lines=args.bundle_test_head_lines, include_oracle_headers=args.include_oracle_headers, **kw)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--trial", required=True)
    p.add_argument("--concurrency", type=int, default=1, help="Compatibility option; calls are sequential for budget accounting.")
    add_common_args(p)
    args = p.parse_args()
    try:
        if args.responses_json and args.allow_api:
            raise ValueError("manual responses and provider mode are mutually exclusive")
        cfg = cfg_from_args(args)
        trial = Path(args.trial).expanduser().resolve()
        bundle = bundle_from_args(trial, args)
        modes = applicable_modes(bundle["trajectory_kind"], args.modes.split(",") if args.modes else ALL_MODES)
        prepare = args.dry_run or not (args.allow_api or args.responses_json)
        responses = strict_loads(Path(args.responses_json).read_text()) if args.responses_json else None
        paths = _trial_paths(trial)
        if args.allow_api and not args.force and _can_skip(paths.labels, bundle_hash=bundle["bundle_hash"],
                prompt_hash=prompt_set_hash(), judge_model=cfg.model, requested_modes=modes, judge_config_hash=config_hash(cfg)):
            print("Current fully assessed v4 labels retained.", file=sys.stderr)
            return 0
        payload = asyncio.run(judge_trial(trial, cfg, requested_modes=modes, bundle=bundle,
                     dry_run=prepare, responses=responses, reviewer=args.reviewer))
        dest = trial / "agent" / "review_request.v4.json" if prepare else paths.labels
        write_labels_atomic(dest, payload)
        print(f"Wrote {dest}", file=sys.stderr)
        return 0 if prepare or payload["ok"] else 1
    except (OSError, ValueError, TypeError, PermissionError) as exc:
        print(f"[judge_trial] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
