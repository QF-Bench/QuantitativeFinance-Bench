# Structured trial judgments — schema 4.0

This schema remains for candidate/trial diagnosis. General task correctness and quality use the separate [task-review report, version 1.0](task-review.md#report-contract), which does not require a candidate or reward. The trial scripts do not validate or import that report. Do not create candidate-mode labels to represent a task-only audit.

The ten mode keys are stable:

| ID | Key |
|---|---|
| A1 | `wrong_model_measure` |
| A2 | `missing_extra_formula_term` |
| A3 | `wrong_parameterization` |
| B1 | `unit_scale_error` |
| B2 | `sign_convention_error` |
| B3 | `time_calendar_convention` |
| C1 | `data_fabrication_wrong_source` |
| C2 | `numerical_optimization_failure` |
| C3 | `statistical_variant_mismatch` |
| D1 | `spec_output_compliance` |

## Mode label

| Field | Type and meaning |
|---|---|
| `assessment_status` | `assessed`, `insufficient_evidence`, `not_assessed` or `error` |
| `match` | Boolean for assessed labels; otherwise null |
| `confidence` | Finite number in [0,1] for assessed labels; otherwise null. Subjective, not calibrated probability. |
| `root_cause_class` | `agent`, `task_side`, `mixed`, `infrastructure` or `unresolved` |
| `root_cause_id` | String identifying a causal defect within the trial, or null |
| `evidence_step_ids` | Array of actual integer trajectory step IDs or code line numbers; may be empty |
| `evidence_refs` | Array of artifact references. Nonempty for an assessed label; use real paths/locations and explain their role. |
| `quote` | Short exact excerpt, or empty string if not needed |
| `notes` | Requirement, independent basis, observation, causal interpretation and material limits; nonblank for assessed labels |

Do not encode booleans as strings, use NaN/Infinity, or replace unknown with false. A mode match records a candidate error mechanism, not automatic agent responsibility. Task-side findings remain reportable when candidate mode matches are false. Group overlapping mode observations with root_cause_id; distinguish unique causes from mode counts.

## Offline import

First prepare a review request using judge_trial.py. Complete a separate response document with:

- `schema_version`: `"4.0"`.
- `bundle_hash` and `prompt_hash`: copied from the exact prepared request, binding the judgment to those sources/prompts.
- `labels`: an object containing exactly the requested mode keys and their mode-label objects.
- Optional `review_decisions`: separate candidate_correctness, task_validity and grader_adequacy decisions.

Each review decision has `status`, `evidence_refs` and `notes`. Status is `supported`, `defect`, `unresolved` or `not_assessed`. “Supported” means the corresponding proposition—candidate correct, task valid or grader adequate—is supported only within the documented inspection scope. A native PASS never fills these decisions automatically. A narrow diagnostic can leave whole-task validity or whole-grader adequacy unassessed.

Import with --responses-json and a reviewer identifier. The script validates the schema and binding, then writes labels.v4.json. It preserves historical labels.json. The exact envelope/provenance fields produced by the script are documented by the prepared request and scripts/README.md; do not fabricate model or tool telemetry.

## Reporting and migration

The optional `review_decisions` have distinct scopes:

- `candidate_correctness`: financial, mathematical and numerical validity of the actual candidate evidence. Output-contract compliance is reported in D1. An empty submission can have D1=true while quantitative correctness remains unresolved.
- `task_validity`: coherence, correctness and sufficient specification of the delivered instructions and permitted inputs. Assess the delivered version; state any narrower inspected scope.
- `grader_adequacy`: whether the actual evaluation, including its task-version pairing and reward aggregation, supports its claims for the inspected output families. Attribute a demonstrated packaging/version mismatch to infrastructure where appropriate.

Each decision's notes must state its inspected scope. A grader gap discovered through an extra control need not explain the original candidate's outcome: report actual-outcome responsibility and additional audit findings separately. Neither a correctly rejected bad calibration nor a valid passing approximation becomes a different candidate result because another checker gap is found.

For a standalone candidate-trial artifact packet outside the supported harness layout, preserve a complete, versioned packet manifest and document the adapter that builds its reviewer bundle. Validate the same mode/decision schema and binding hashes. Label custom adapter results as such; do not imply that the normal harness importer, a fresh solver or Docker was used.

Keep native result, assessment status, mode match, attribution and review decisions distinct. Show denominators and unassessed/error counts. Report task-side findings attached to negative mode labels rather than dropping them from summaries. Multi-label percentages can exceed 100%; they are not necessarily a partition of trials.

Legacy labels have different semantics. Preserve them with their original schema, prompts, source and cohort. Do not turn legacy gate-skipped negatives into assessed negatives or map agent_conceptual/agent_coding automatically to current labels without reinspection. Re-prepare and explicitly review a trial to create a new v4 result.
