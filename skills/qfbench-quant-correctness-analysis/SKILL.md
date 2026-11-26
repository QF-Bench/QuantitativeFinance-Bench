---
name: qfbench-quant-correctness-analysis
description: Review the correctness and quality of quantitative and financial tasks, and diagnose errors in submitted solutions. Use for audits of task instructions, assumptions, inputs, financial models, mathematics, reference solutions, graders and required outputs; also use for suspicious passes, failed trials and batch error analysis. Supports new tasks without a candidate, benchmark harness or prior run.
---

# Quantitative Task Quality and Error Review

Assess whether a task is sound, clear, meaningful for its stated purpose, practically solvable and fairly evaluated. When a submitted solution exists, explain its errors separately from defects in the task or evaluation.

A reference answer, native PASS, model consensus or familiar convention is not ground truth. A correct candidate can fail a defective grader; an incorrect candidate can pass a weak one. The task's quality requires its own assessment.

## Choose the review route

- **Task review:** inspect a new or existing quantitative/financial task, its quality, or any of its materials. No existing candidate, reward, trial ID or particular directory layout is required. Use [the task-review protocol and report](references/task-review.md). Review references, graders and outputs when present or required by the scope; distinguish optional absent components from missing necessary evidence.
- **Trial diagnosis:** explain a submitted attempt, suspicious pass or defined cohort. Use the workflow below and [schema 4.0](references/output-schema.md). The bundled scripts implement this route. Candidate-mode labels retain their existing meaning.
- **Both:** produce task findings and candidate assessment separately, linked to the same source version. Do not invent candidate labels for a task-only audit.

Match depth to the request. A focused formula check need not launch a benchmark. Full task acceptance uses the agreed three-round method below with documented coverage. QF-Bench examples are optional illustrations; this skill also applies to unseen tasks outside that benchmark.

## Principles

- Financial models, quantitative mathematics and material numerical results must be correct within the stated scope. Assumptions may be simplified or suboptimal if internally consistent, sufficiently specified or reasonably inferable, and defensible to a competent quant for the purpose. Explicit assumptions cannot excuse invalid mathematics or financial incoherence.
- Evaluate task quality as well as correctness: purpose, substantive reasoning, meaningful outputs, well-posedness, data suitability, feasibility and grading. Difficulty, realism and historical model failure rate are not quality scores. Do not impose a preferred model or make every educational task more complex.
- Separate financial correctness, instruction compliance, reference correctness, grader behavior and responsibility. An undocumented implementation choice is not made authoritative by a numeric test pin.
- Distinguish evidence from repair status. A **confirmed, unfixed defect** is known and open. **Unverified historical claim** means the cited event lacks adequate evidence; an unverified repair lacks closure checks. **Unresolved** attribution means the cause cannot yet be distinguished. Never use these interchangeably.
- Preserve original attempts, versions and labels. Repairs and reclassifications supplement the record. Apply symmetric evidence standards to candidate-side and task-side claims; neither confidence thresholds nor model votes determine responsibility.
- Keep repairs minimal after completing necessary checks. Separate required corrections from optional improvements. Do not weaken the task's objective or tolerance merely to obtain a pass.
- Respect authorized scope. Review does not by itself authorize source edits, paid provider runs, publication or merging. Reuse existing authorization where it applies.

## Review workflow

### 1. Establish purpose, scope and evidence

Identify the intended skill, audience and use of the result. Freeze instructions, inputs, reference, evaluator and outputs by version/hash or other provenance. Read complete relevant materials and actual executable entry points, including embedded code, generated expectations, input mapping and scoring aggregation. Record missing evidence and the conclusions it prevents.

For a trial, inspect submitted code, final artifacts, detailed logs and source pairing. Native status/reward is an observation; missing rewards, partial credit, timeouts and infrastructure failures are distinct from mathematical errors. Text printed in a trajectory is not necessarily a submitted artifact. Truncation and short code alone do not justify labels.

Before reusing a historical example, verify its version, executed path, actual candidate versus injected control and supporting evidence. See [the example audit](references/example-audit.md). A condensed anecdote or passing test count cannot establish a new task's correctness.

### 2. Assess the task and intended quantities

For each material output identify the model/payoff, measure, funding, timing, units, signs, parameterization, estimator and approximation. Check data lineage, information availability, domain restrictions and non-uniqueness. Read [specification citation guidance](references/spec_citation_patterns.md) when a requirement is disputed.

Assess whether solving the task exercises its claimed quantitative skill and whether the outputs support its stated conclusion. Look for degenerate solutions, answer leakage, unsupported interpretations and missing constraints. A simple exercise can be good for its purpose; administrative burden or hidden conventions do not establish useful difficulty. Use the [task-quality criteria](references/task-review.md#task-quality).

Allow equivalent mathematics and valid representations within the contract. A particular algorithm or random-call sequence is binding only when actually required and sufficiently specified. Assess consequential ambiguity against the complete context and standard domain knowledge; do not demand every derivation or solver choice be supplied.

### 3. Verify finance, mathematics and numerics independently

Re-derive material formulas or consult applicable primary sources. Recompute material results from inputs using a separate method where practical. Check financial identities, limiting cases, complete affected matrices/paths/ledgers, stability, convergence, conditioning and simulation uncertainty. [Industry guidance](INDUSTRY_STANDARDS.md) is conditional, not a universal rulebook.

For calibrations compare the same objective and admissible domain: optimizer success is not proof of an adequate optimum; different parameters are not proof of error. Justify simulation discrepancies against sampling/discretization uncertainty; equal seeds need not imply equal draws. Distinguish implementation error, approximation bias and claims exceeding an approximation's scope. Inspect actual visual deliverables when their meaning matters.

### 4. Test evaluation quality

Full task review covers every material requirement and output family; focused review covers its stated scope. Record independent basis, assertion or explicit manual inspection, justified tolerance, valid control and plausible incorrect controls. See [review evidence](references/review-evidence.md).

Test valid alternatives and material mistakes: degenerate/constant outputs, coherent wrong models, wrong units/signs/timing, missing data and nonfinite values where relevant. Reference and empty controls alone are insufficient. Check independent validity as well as consistency between files. Exercise the actual scorer where available; inspect duplicate credit, alternative paths and tolerance scales.

Verify each control's final contents and membership before grading; remove intended missing-file targets after overlays. Preserve unexpected outcomes and invalid experiments. Distinguish automatic and manual coverage. If no grader exists and none is required, document independent/manual assessment without inventing native PASS. A material false acceptance or rejection reopens the affected acceptance conclusion.

### 5. Classify findings and recommend minimal corrections

Identify the affected component and consequence. Use the ten mechanisms in [TAXONOMY.md](TAXONOMY.md) where helpful, but do not force every quality defect into a candidate-error mode. Group dependent observations from one causal defect; retain independent errors.

Task findings separately record evidence, attribution, repair status, minimum correction and verification needed. Label optional enhancements. A proposed or applied fix is not verified until the relevant independent checks and evaluation controls have been rerun on the final version.

For trial labels, `match` describes an observed candidate error, not automatic blame. Faithfully implementing an invalid formula can match a mode with task-side responsibility. A correct candidate rejected by a bad test has no candidate error for that mode, while the task-side defect remains reportable. Missing candidate evidence does not become assessed negatives.

### 6. Report the conclusion and limits

Use [the task-review report](references/task-review.md#report-contract) for task correctness/quality and [schema 4.0](references/output-schema.md) for candidate diagnoses. Keep task quality, reference correctness, candidate correctness and grader adequacy separate. State the version, checks performed, evidence gaps, required fixes, optional improvements and verification.

Review completion and task readiness differ. Known material defects mean changes are needed even when other checks are incomplete. A clean conclusion is bounded by scope; do not certify a batch from sampled cases or treat a completed report as a repaired task.

## Full review and local execution

Full acceptance uses three evidence categories: **(1)** independent financial, mathematical and numerical review, including task quality and grading; **(2)** Lean-assisted verification of selected material mathematical cores under explicit assumptions; **(3)** fresh blind interpretation and solving from instructions and permitted inputs. Record completed, partial, not-run or justified not-applicable status for each. A narrow review can use a subset, but must not claim full acceptance.

For a requested full review or fresh solve, use a distinct agent with fresh context. Give only final instructions and permitted inputs; withhold references, checkers, earlier attempts, findings and proof results. Record interpretation before coding, execute task code in a local Docker sandbox, preserve limits, seal code/outputs before separate grading and give no hidden feedback. Existing inspected attempts are not blind. Unless stronger controls are verified, host-agent file restrictions are instruction-enforced; Docker isolates executed code.

Lean proofs support only their explicit assumptions and mathematical scope, not economic suitability or floating-point programs. Missing tools or skipped required rounds remain evidence gaps. Full review can yield bounded acceptance when required evidence is complete and no required defect remains; universal formal certification and universal model success are not required.

Use local tools/app agents under the active execution policy. Do not run separately paid provider trials or load keys without explicit authorization; API flags do not replace it. Local execution does not imply offline inference or free app usage. See [OPS.md](OPS.md) and [scripts/README.md](scripts/README.md).

## Compatibility

Package 4.1 adds task review and quality assessment while preserving trial schema **4.0** and its ten keys. The separate task-review report is version **1.0** and is not imported by trial scripts. Preserve historical labels/calibration; policy changes require refreshed evidence requests. See [CALIBRATION.md](CALIBRATION.md) and [CHANGELOG.md](CHANGELOG.md).
