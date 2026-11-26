# Local review scripts

These scripts implement the schema 4.0 **trial-diagnosis** route. General task correctness and quality review uses [the task-review protocol and report](../references/task-review.md), without requiring these scripts or a harness layout. Task-review reports are not accepted by the trial importer. These scripts organize evidence and ten quantitative error modes. They do not certify a task from native reward, reference agreement or reviewer confidence. Python 3.10+ and the standard library support the entire local workflow.

The active review campaign prohibits separate provider API calls. Its fresh blind solver must use only instructions and permitted inputs under the local blind protocol. **Bundles and review requests contain references and checkers and are for reviewers only.** Preparing a request is not a completed blind attempt, financial review or calibration.

## Local workflow

Discover every status, including native passes:

```sh
python scripts/list_failed_trials.py --root /path/to/workspace --tasks-root /path/to/tasks --out manifest.json
```

The historical script name is retained. Default discovery includes `PASS` (reward 1), `FAIL` (0), `PARTIAL` (between 0 and 1), `ERROR` (malformed/nonfinite/out-of-range reward or recorded execution failure), and `UNKNOWN` (missing reward or unfinished record). Directory splits are informational. Missing reward never implies a quantitative failure. Use `--failures-only` only when an explicitly restricted sample is intended. The manifest states the filter's effect.

Prepare reviewer evidence without a provider import or request:

```sh
python scripts/judge_trial.py --trial /path/to/workspace/harness_model/trial --tasks-root /path/to/tasks
python scripts/judge_all.py --root /path/to/workspace --tasks-root /path/to/tasks --prepare-only
```

Default behavior and `--dry-run` are equivalent to `--prepare-only`. Each eligible trial receives `agent/bundle.json` and `agent/review_request.v4.json`; preparation does not create labels. Requests include active taxonomy, industry standards, evidence-review rules and schema text for a fresh reviewer. All skill Markdown, including non-prompt policy files, participates in the request/resume hash. Unevaluable trials remain in the sweep state with reasons. Curated `pass/fail` and flat combo layouts are supported. A combo directory contains `_` to separate harness from model.

Use a fresh file **outside the trial tree** for manual responses, copying `schema_version`, `bundle_hash`, `prompt_hash` and `labels_template` from the request. Rename `labels_template` to `labels`, preserve every requested mode, and fill findings after independent review. A minimal label is:

```json
{
  "assessment_status": "insufficient_evidence",
  "match": null,
  "confidence": null,
  "root_cause_class": "unresolved",
  "root_cause_id": null,
  "evidence_step_ids": [],
  "evidence_refs": [],
  "quote": "",
  "notes": "The required output is unavailable; this mode cannot be assessed."
}
```

`assessed` requires a genuine boolean `match`, finite confidence in `[0,1]`, nonempty notes and references to specific evidence. `insufficient_evidence`, `not_assessed` and `error` require null `match` and confidence. No short-code threshold generates negatives. Confidence is recorded without an attribution gate. Every mode uses `agent`, `task_side`, `mixed`, `infrastructure` or `unresolved`; `root_cause_id` links a shared cause across modes without suppressing distinct errors. A valid negative can carry `task_side` attribution when a correct candidate is rejected by a defective grader.

Optional `review_decisions` keeps `candidate_correctness`, `task_validity` and `grader_adequacy` separate. Each present decision has `status` (`supported`, `defect`, `unresolved`, `not_assessed`), `evidence_refs` and `notes`. Decisive decisions require references. These are supplied judgments, never inferred from native PASS or all-negative labels.

```sh
python scripts/judge_trial.py --trial /path/to/workspace/harness_model/trial \
  --tasks-root /path/to/tasks --responses-json /path/to/review/responses.json \
  --reviewer reviewer-identifier
```

Import validates the complete response before writing `agent/labels.v4.json`. Prompt or source changes invalidate the request hashes and require review against refreshed evidence. Invalid imports fail without replacing existing labels. Previous v4 records are archived by hash in `agent/review_history/`; historical `labels.json` is preserved and is not implicitly migrated.

## Evidence and limits

Instructions, test text, supplementary text files and verifier stdout are complete by default. Numeric limits default to zero (unlimited); explicit positive limits produce warnings. Full source manifests include hashes for every regular task/trial/output file, Git commit and dirty-path metadata when available, and hashes for unrendered binary outputs. Content manifests and commit identity bind evidence; incidental Git dirty-path display is retained for audit but excluded from the binding hash so generated review files do not invalidate unchanged inputs. Paths are canonicalized before hashing. A hash proves identity, not correctness or blind isolation. Inspect unrendered evidence before a decisive finding.

Agent-code extraction finds observed full Write content; partial edits and shell-written files may be absent. It is not a verified final executed snapshot. Output discovery is confined to the trial's `output` or `agent/output` folder; it does not borrow a sibling trial's outputs. Parsed test values are heuristic checker assertions, not independently verified expected truth. Full stdout and source files remain available for adjudication.

`scan_citations_v2.py --tasks-root /path/to/tasks --out /path/to/scan` produces a lexical navigation inventory. Formula, citation and schema matches establish neither correctness nor sufficient specification, and no matched cue does not establish ambiguity. It makes no network request.

## Aggregation and human calibration

```sh
python scripts/aggregate_labels.py --root /path/to/workspace
python scripts/seed_calibration.py --root /path/to/workspace --tasks-root /path/to/tasks --n 20 --out /path/to/fresh-calibration
python scripts/aggregate_labels.py --root /path/to/workspace --human-labels /path/to/fresh-calibration/human_labels.csv
```

Reports default to `reports-v4`, preserving historical reports. They include all discovered trials, ten expected mode rows per trial, missing/invalid/insufficient counts, assessed denominators, native-status strata and attribution for positive, negative and unassessed records. `trial_decisions.csv` preserves candidate correctness, task validity and grader adequacy separately, with absent decisions marked `not_assessed`. Native strata use the stored assessment-time result; current status/reward and known result-file drift are separate columns. Historical aggregation does not rebuild all source contexts: `source_freshness` explicitly states this, and policy drift is flagged. A class negative requires every constituent mode to be assessed negative; an observed positive establishes a class positive. Zero assessed denominator is blank, not a zero error rate. Duplicate causes may appear under multiple modes; sums across modes are not unique-failure counts.

Calibration sampling stratifies by harness, model and native status. It creates blank labels and a manifest marked `template_unreviewed`; no measured agreement is claimed. Its preview contains frozen copies of reviewer inputs and a SHA-256 receipt, never model predictions or mutable symlinks. This is label-blind human calibration, not the separate blind solver environment. Existing human-label files are never overwritten. Humans mark `human_assessment_status=assessed` and `human_match=0/1` only when evaluable; otherwise leave the match empty. Human CSVs bind `schema_version`, `bundle_hash` and `prompt_hash`. Aggregation requires an exact trial/mode/evidence-version match, excludes missing or stale human labels and unassessed model records, reports the exclusions, and rejects duplicate/invalid human values. Unversioned historical CSVs require explicit independent re-review; they are not migrated automatically. Summaries and agreement are stratified by prompt/policy hash instead of silently pooling changed rubrics. Cohen's kappa is undefined for all-negative or all-positive identical labels; observed agreement is reported separately. No arbitrary confidence threshold silently changes labels.

## Optional provider adapter

This path is **not permitted by the current campaign**. For separately authorized future work, it requires all of `--allow-api`, a positive `--budget-usd`, an exact `--judge-model`, and `--pricing-json`. No model prices are assumed or silently set to zero. Pricing format:

```json
{"provider/model-id": {"input_per_million": 1.0, "output_per_million": 2.0}}
```

The values above illustrate the format only; they are not a price quote. Install `litellm` separately only if authorized API use requires it. Calls are sequential without automatic retries. Each request reserves a conservative byte-based prompt allowance plus maximum output charge before importing/calling the provider; failed calls retain their reservation and unknown cost stays null. This is a local reservation guard, not a provider-enforced billing cap. Actual usage is recorded when available. Legacy concurrency/retry flags remain accepted by the sweep but do not enable parallel calls or retries.

Resume requires fully valid, assessed v4 records with matching source bundle, prompt/schema/script hash, model and generation settings. Invalid, insufficient or missing labels are never reused as completed assessments. Manual imports always validate anew.
