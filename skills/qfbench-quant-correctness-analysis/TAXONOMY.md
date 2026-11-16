# Quantitative error taxonomy

Ten mode identifiers remain stable. For trial schema 4.0, a mode describes a concrete mechanism in submitted code or outputs; responsibility and assessment status are separate dimensions. Native reward is not a taxonomy label.

For general [task review](references/task-review.md), mechanism descriptions can also tag defects in instructions, inputs, models, references or graders. Task-quality findings need not fit these ten modes. Use the separate task-review findings/report; do not reinterpret candidate `match` booleans as task-quality labels. No candidate means no assessed candidate positives or negatives.

A confirmed but unfixed defect has open repair status. It is not unresolved merely because no fix has been applied. Evidence, causal attribution and remediation are separate dimensions in the task-review report.

## Assessment semantics

- `assessed` + `match: true`: evidence establishes this candidate error and its material consequence within the inspected scope.
- `assessed` + `match: false`: the available evidence supports absence of this error within that scope. This does not certify the whole candidate or task.
- `insufficient_evidence`, `not_assessed` or `error` + `match: null`: no supported binary conclusion. Confidence is also null.

A candidate can implement an explicitly required but invalid formula. Its mathematical error can match a mode while responsibility is `task_side`. If the candidate is mathematically correct and only the checker is wrong, use `match: false` with task-side evidence. Describe the faulty reference/assertion separately rather than inventing a candidate error.

## Attribution

| Value | Evidence needed |
|---|---|
| `agent` | A candidate defect relative to a coherent, sufficiently specified or reasonably inferable requirement |
| `task_side` | A material instruction, input, reference, tolerance, grader or scoring defect causing the discrepancy |
| `mixed` | Independent evidence of both candidate and task defects, with their effects distinguished |
| `infrastructure` | A demonstrated execution, packaging, dependency or protocol failure affecting the observation |
| `unresolved` | Evidence does not yet distinguish causes or establish the intended result |

No confidence cutoff automatically converts a task defect into an agent error. Explicit formulas, citations, numeric assertions and sister-trial agreement can guide inspection; none prevents a task-side finding. Missing output or a timeout alone does not distinguish agent inefficiency from infrastructure failure. Report evidence rather than inferred psychological explanations.

For an assessed negative with no associated defect, use `root_cause_class: unresolved` and `root_cause_id: null`; here the cause is inapplicable, not evidence against the supported negative. A negative may instead carry a concrete task-side or infrastructure cause when explaining an unjustified rejection.

## A — Model and formula

### A1 · Wrong model or measure — `wrong_model_measure`

The implemented economic model, payoff, probability measure, state dynamics or exercise rights differ materially from the valid intended model. Examples include pricing a risk-neutral payoff with an unadjusted physical drift or replacing an American exercise problem with a European problem when that approximation is not the task.

Establish the claimed model, actual equations and resulting difference. Model names or a count of structural differences are not sufficient. A disclosed approximation consistent with a diagnostic's purpose is not automatically wrong.

### A2 · Missing or extra formula term — `missing_extra_formula_term`

Within the intended model, a coefficient, transformation, funding/discount term, Jacobian, boundary condition or operator is missing, duplicated or incorrect. Derive the correct expression and its parameterization; compare equivalent forms before declaring an error.

Examples include omitted residual-cash income in a daily rebalanced portfolio, a duplicated location term in ES, or a density Jacobian omitted from an ordinary-t likelihood. A density already standardized may include that Jacobian. Half a variance in a log-price exponent is not the variance itself.

### A3 · Parameterization or convention mismatch — `wrong_parameterization`

The formula is applied to parameters with a materially different meaning: scale versus rate, variance versus standard deviation, ordinary versus standardized innovations, incompatible initialization or another identified model convention.

Show the relevant parameter definition and a numerical or algebraic consequence. Do not use this mode merely because a solver chose a defensible alternative library or convention. The legacy A3.f automatic “non-industry default” route is retired; a common convention is evidence to assess in context, not an independent mandate.

## B — Units, signs and time

### B1 · Unit or scale error — `unit_scale_error`

The underlying quantity is expressed in the wrong units or normalization: percentage versus decimal, basis points, currency/notional, variance versus volatility units, annual versus period scale, or per-unit versus per-percent sensitivity.

Derive the dimensional conversion. A ratio near 100 is a diagnostic clue, not proof. A missing economic exposure term may be better explained by A2; record the causal mechanism once.

### B2 · Sign convention error — `sign_convention_error`

The candidate reverses an established economic direction or output convention: loss/P&L, long/short, payer/receiver, sensitivity direction or trade sign.

Identify the actual sign convention and transformation. VaR need not be positive for every loss distribution; theta and DV01 conventions require care. An unspecified but financially coherent alternative should prompt ambiguity review, not an automatic error finding.

### B3 · Time, calendar or compounding error — `time_calendar_convention`

An incorrect time axis, horizon, accrual basis, compounding convention, information cutoff, trading lag, event side, observation window or calendar changes the required result. Examples include simple discounting when continuous compounding is required, same-close signal execution without available information, off-by-one estimation samples and pre-dividend values reported as post-dividend values.

Trace actual dates and included observations. A date-format serialization error alone belongs in D1. Historical/in-sample exercises are not forward-looking investment strategies unless they claim to be.

## C — Inputs, numerics and estimators

### C1 · Wrong source or unsupported data — `data_fabrication_wrong_source`

The candidate uses incorrect, invented, improperly aligned or materially incomplete inputs. Establish the permitted input and the transformation that changed it. Documented cleaning, simulation or synthetic data supplied by the task is not fabrication. Do not infer intentional deception from a wrong number.

### C2 · Numerical or optimization failure — `numerical_optimization_failure`

A numerical implementation fails the intended mathematical problem: materially inferior feasible objective, failed convergence, unstable evaluation, inadequate integration/grid resolution or excessive simulation error relative to a justified requirement.

Compare the same objective, constraints and initialization convention. Inspect feasibility, residuals, likelihood/objective quality, conditioning and relevant outputs. A different optimizer, boundary estimate, parameter vector or random stream is not itself an error. Common random numbers are useful variance reduction, not universally mandatory. If numerical and model errors are independent, report both; do not suppress C2 because an A-mode is present.

### C3 · Statistical estimator mismatch — `statistical_variant_mismatch`

A different estimator, sample convention, test statistic, covariance normalization, quantile rule or tail statistic changes the required quantity. Demonstrate how the intended estimator is identified and how the implementation differs.

When both estimators remain defensible under the full task context, a failed exact pin may be task-side; record the absence of a supported candidate error. A different estimator that violates a clear, coherent requirement can be agent-side. The legacy C3.b publication-year/training-era heuristic is retired. Never infer error from a method's age.

## D — Output contract

### D1 · Output schema and specification — `spec_output_compliance`

A required artifact, key, vocabulary, type, shape, ordering, date representation or precision does not satisfy a clear contract. Verify the actual final output and the exact requirement. A supplied example may be illustrative rather than exhaustive; distinguish it from an explicit schema.

An empty submission can establish a missing-artifact failure while still leaving finance modes unassessed. Arbitrary grader-only field names, inconsistent null/zero rules or precision tighter than the output contract are task-side defects. Library-default bugs can cause schema or numerical errors: classify the actual mechanism, not the number of keyword arguments needed to fix it. D1.g is no longer a universal override of finance modes.

## Causal grouping and minimal corrections

Assign `root_cause_id` to each independently evidenced causal defect. Several labels may reference the same cause, but aggregate unique causes separately from mode counts and failed assertions. Prefer one primary explanatory mode in the narrative when several descriptions refer to the same defect; no universal A1>A2>... priority applies.

Do not encode “counted elsewhere” as an assessed negative. If a defect independently meets several mode definitions, record the applicable matches with the same cause ID. If an overlapping mode is deliberately not assessed separately, use `not_assessed`, null match/confidence, and a note naming the primary mode and shared cause. A false match requires evidence that the mode's defined mechanism is absent within the stated scope.

A falsifiable local correction is useful evidence: replace a disputed term in an isolated copy, hold other inputs constant, recompute and observe whether the discrepancy changes as predicted. Preserve the original submission. A successful counterfactual supports causality, but does not certify unrelated outputs or authorize editing a live benchmark.

When reporting a proposed task fix, choose it after establishing correctness: clarify a consequential convention, repair a formula/reference, tighten a justified deterministic tolerance, widen an uncertainty budget that was actually too strict, or expose a missing observable. Keep optional model upgrades separate from necessary repairs.
