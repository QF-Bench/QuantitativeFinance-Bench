# General quantitative task review

Use this route for task correctness and quality, including specification-only tasks and new tasks outside QF-Bench. A prior solver attempt, reward, reference implementation or fixed harness layout is not required. Missing components limit only conclusions that require them.

## Scope and evidence

State purpose, audience, requested depth and version. If purpose must be inferred, label that inference and avoid imposing a more advanced objective. Manifest the specification, inputs, reference, grader, example outputs and any candidate, recording paths, hashes/provenance and missing/inapplicable components. An optional absent grader is not a defect; an unavailable grader required for an automated-readiness claim is an evidence gap.

Read the complete relevant contract and actual reference/scoring entry points. Derive intended quantities independently before accepting reference agreement. Cover specifications, data, models, mathematics, numerics, outputs and evaluation as applicable. A correct formula can coexist with a poorly specified or poorly evaluated task.

## Task quality

Assess fitness for the stated purpose with concrete evidence. Do not substitute an unexplained overall score or historical model success rate.

| Dimension | Review question and evidence |
|---|---|
| Purpose and quantitative substance | Does the work exercise the claimed modelling, derivation, estimation, implementation or interpretation skill? Can a solver bypass it by copying an answer, emitting a constant or satisfying superficial metadata? Separate design defects from grader defects. Simple teaching/implementation exercises can be appropriate. |
| Financial and mathematical validity | Are economic quantities, measures, cashflows, identities and domains coherent? Are results correct, including under explicitly supplied formulas? Verify assumptions and material results independently. |
| Assumptions and approximation scope | Are simplifications defensible to a competent quant for this purpose? Are approximation limits and conclusions aligned? A scope caveat does not establish numerical accuracy or excuse an invalid identity. |
| Well-posedness and identifiability | Do sufficient inputs, constraints, objectives and boundary conditions exist? Is a solution feasible and identifiable where required? For nonunique valid solutions, define admissible equivalence or assess objective/output quality rather than arbitrary parameter pins. |
| Data and information integrity | Are inputs available, aligned and adequate for the claim? Trace timestamps, corporate actions, leakage, selection/survivorship effects and sample size where relevant. Synthetic data and in-sample analysis are legitimate within an honest scope. |
| Instruction and output clarity | Can a capable quant infer material conventions and deliverables? Are formulas, terms, examples, schemas and units consistent? Distinguish consequential ambiguity from reasonable solver discretion. |
| Meaningful outputs and interpretation | Do outputs answer the stated financial/statistical question? Are economic interpretations supported? Are material quantities/diagnostics needed to establish the result inspectable? Do not require essays or extra plots unless their absence undermines the objective or verification. |
| Numerical adequacy and reproducibility | Are conditioning, discretization, optimization, sampling error and tolerances compatible? Does reproducibility mean statistical consistency or a specified deterministic stream? A seed alone does not define every implementation's random allocation. |
| Feasibility and useful difficulty | Can a capable solver finish within stated time, compute, dependency and data constraints? Separate substantive challenge from hidden conventions, missing dependencies and clerical burden. Low historical success is not evidence of high quality. |
| Discriminative and fair assessment | Do meaningful wrong solutions fail and valid alternatives pass? Cover material outputs, scoring aggregation and visual/manual requirements. Check answer leakage, duplicate credit, hidden reference-specific recipes and tolerances accepting material errors. |

Apply relevant dimensions and explain inapplicability. Do not demand maximum realism, advanced models or harder mathematics universally. Simplified tasks can be high quality. Reproducing an explicitly invalid formula does not make a task sound.

### Required fixes versus optional improvements

- **Required correction:** demonstrated correctness error, consequential ambiguity, unsupported core claim, infeasibility, missing essential data, leakage invalidating the claimed analysis, or unfair/ineffective assessment of a material requirement. Repair the smallest cause that restores the intended valid task; expected answers may need to change.
- **Optional improvement:** additional realism, richer sensitivity analysis, harder extensions or extra explanations/diagnostics that improve an already sound task. State the benefit and burden; do not hold acceptance hostage to preference.
- **Evidence gap:** a concern that cannot yet be established or dismissed. Name the missing observation/requirement, consequence and next discriminating check. A known unfixed bug is not an evidence gap.

For example, a coarse numerical surface can suit a declared diagnostic exercise. If a fabricated constant surface passes despite violating the requested model, grader repair is required. A refinement study may be optional for that diagnostic; it becomes required evidence if the task claims convergence or specified accuracy. This principle does not assign a verdict to another task merely because its title is similar.

## Three-round full review

The rounds are evidence categories, not permission to disclose answers in sequence. Preserve blindness even after reference review.

### Round 1 — Independent task, finance, mathematics and numerical review

1. Map every material requirement/output family to intended quantities, assumptions and input lineage. Inventory material formulas; do not stop at the first discrepancy.
2. Derive or justify formulas with applicable primary sources; check dimensions, financial identities, boundaries and limits. Recompute outputs independently where practical. Assess the quality dimensions above.
3. Inspect reference and evaluator independently. Compare calibration objectives under the same convention, simulation differences against uncertainty and approximations against their scope.
4. Build output coverage: requirement; independent basis; artifacts and full matrix/path/ledger extent; assertion or manual check; tolerance/error budget; valid controls; plausible wrong controls; observed results; gaps.
5. Exercise representative valid alternatives and meaningful wrong controls through the actual scorer when present. Include coherent wrong outputs, not only empty files. Seal and verify mutations before grading. Preserve all unexpected outcomes and invalid experiments with exact versions.

A plot's existence or nonblank pixels do not establish its meaning. Inspect the actual figure when it matters, recording automatic/manual coverage. Manual inspection of one reference figure does not show that automation rejects wrong candidate figures.

### Round 2 — Selected Lean verification

Select consequential identities/recurrences appropriate for formal checking. Record propositions, assumptions, sources, actual Lean commands/results and unformalized remainder. Proofs under model equations do not establish their economic suitability or floating-point implementation correctness.

Mark irrelevant checks not applicable with reasons. If a relevant selected core is unchecked because Lean or time is unavailable, record not run/partial and the resulting limit. Textual reasoning and Python assertions are not Lean proofs. Full three-round acceptance cannot silently substitute a passing reference for a missing round.

### Round 3 — Fresh blind interpretation and solving

Use an agent distinct from the editor/reference reviewer, with fresh context and only instructions and permitted inputs. Record interpretation before coding. Withhold references, hidden tests, earlier attempts, findings, proofs and solution-derived hints. Execute task code in fresh local Docker with recorded limits and network disabled when inputs are local. For non-executable work, preserve independent derivation/interpretation.

Stop execution and seal code, outputs, hashes and metadata before separate grading. Do not give hidden feedback or iterate that blind attempt after grading. Compare sealed interpretation and result with the reference and adjudicate independently. Distinguish completion, timeout, error and collection timing. Candidate correctness does not imply task or grader correctness.

Docker isolates executed code. Unless verified technical controls exist, host-file restrictions on the agent are instruction-enforced; disclose that limit. App inference is not an offline/free model claim. No separate paid provider calls or key loading under the active no-API policy.

Full acceptance requires each applicable round and material output coverage. Narrow source/formula/quality audits may omit rounds with explicit scope and no full-readiness claim. Do not launch fresh benchmarking for a narrow diagnostic request.

## Findings and closure

Record each independently evidenced cause once, linking dependent symptoms. Keep these dimensions distinct:

| Field | Values and meaning |
|---|---|
| `kind` | `required_fix` or `optional_improvement`. Suspected required defects keep that kind with explicit evidence status. |
| `evidence_status` | `confirmed`, `suspected`, `insufficient_evidence`. Confirmation needs source, derivation or observed behavior supporting the claim. |
| `attribution` | `task_side`, `agent`, `mixed`, `infrastructure`, `unresolved`, or `not_applicable`. Unknown cause differs from unknown existence of an error. |
| `repair_status` | `open`, `proposed`, `implemented_unverified`, `verified`, or `not_applicable` for an unadopted optional recommendation or a disproved finding. Closing an actual defect by repair requires `verified`. |
| `disposition` | `active`, `closed_fixed`, or `closed_not_a_defect`. Use `closed_fixed` only with a verified repair. Close a disproved concern as `closed_not_a_defect` only with explicit refuting evidence and rationale; preserve its original claim and evidence history. |

Also record ID/root cause, affected component, consequence, evidence references, minimum correction, verification needed/results and affected version. Optional taxonomy tags describe mechanisms without becoming candidate-mode booleans. Use descriptive mechanisms for quality issues outside the ten modes.

A later refutation or reclassification is not a repair. Preserve the earlier assessment and explain the new evidence rather than silently erasing the finding. Do not dismiss a real defect merely because its fix is inconvenient or a valid candidate happened to pass.

**Confirmed/open** means established and unfixed. **Implemented/unverified** means changed without closure evidence. **Unverified historical claim** means the cited event/version lacks adequate proof, not a new confirmed task bug. Identify genuinely undecided conventions separately even when a formula error is already confirmed.

For authorized repairs, preserve the original counterexample, make the smallest correction retaining the intended valid objective, and recheck final sources. Verify independent math, outputs, valid alternatives, wrong controls and actual scoring as affected. Do not broaden tolerances until a bad answer passes. Fresh post-change blind validation needs another fresh agent and final instructions/inputs only.

## Report contract

Use a readable report or equivalent JSON with `report_type: quant_task_review` and `report_version: "1.0"`. This is separate from trial schema 4.0; the trial importer does not validate/import it.

Include:

1. **Task and scope:** title/ID if available, purpose/audience, version, requested depth, scope assumptions and exclusions.
2. **Packet manifest:** available/missing/inapplicable artifact roles, hashes/provenance and reasons. Existing candidate/run/reward is optional.
3. **Coverage:** material requirements/output families, independent basis, inspected extent, tolerances, controls, actual outcomes, automatic/manual status and gaps.
4. **Quality assessment:** applicable dimensions, evidence and supported/needs-changes/incomplete/unassessed judgments. Explain inapplicability; separate optional enhancements.
5. **Round record:** `completed`, `partial`, `not_run` or `not_applicable`, with evidence/scope/reasons. Do not fabricate blind solves, native results or formal proofs.
6. **Separate decisions:** specification/input suitability, financial/mathematical validity, reference correctness, grader adequacy and task quality; candidate correctness only when evidence exists. Use `supported`, `needs_changes`, `incomplete`, `not_assessed` or justified `not_applicable`, with evidence and limits.
7. **Findings:** fields above, minimal fixes, effects on answers/grading, verification and remaining questions. Source optional author attribution; do not infer authorship from reviewer/committer alone.
8. **Conclusion and completion:** version, `review_complete` boolean, `conclusion`, remaining work and limitations. Completion concerns requested evidence gathering; a completed review may find an unfixed defective task.

Conclusion rules:

- `needs_changes`: at least one active confirmed required defect remains open/proposed/implemented without verification. Explain severity and whether it blocks the stated use. Keep this visible even with incomplete coverage; use `review_complete: false` if required checks are missing.
- `incomplete`: no confirmed open required defect determines the outcome, but required evidence, an active material suspected defect or an applicable requested round prevents a supported conclusion. Name what is unknown and the next check.
- `no_material_issues_found`: required evidence is complete within scope, no active required defect remains, and optional improvements are separated. Evidenced dismissals and verified repairs remain in the history. This is a bounded assessment, not universal certification.

Never substitute candidate correctness for task quality or grader adequacy. Do not mark a task accepted because a report was completed. Benchmark-wide conclusions require per-task evidence rather than extrapolation from examples.
