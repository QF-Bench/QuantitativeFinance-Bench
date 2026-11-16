# A3 — Parameter or Metric Definition Mismatch

Use this mode when a parameter, metric or state variable has an incompatible meaning. Distinguish inconsistency from a coherent alternative permitted by the task.

## Diagnostic checks

1. State candidate and required definitions, including units, normalization and conditioning. If unspecified, assess defensibility for the objective.
2. Trace consistency from inputs to formulas and labels. Passing a Gamma rate as a scale without conversion differs from consistently using either convention.
3. Establish the consequence independently of reference output. A hidden grader convention need not imply candidate error.
4. Do not infer intent or expertise from prose, an omitted keyword, or a one-keyword repair. Attribute the observed mechanism; leave mental causes uncertain when unsupported.

## Common cases

- **A3.a:** Gamma rate and scale are reciprocals. For `ν>2`, a standard Student-t has variance `ν/(ν−2)` and unit-variance scaling `sqrt((ν−2)/ν)`. If `CV=sd/mean`, then `Var(X)=CV²·mean²`; division by mean² converts variance to squared CV. Identify the actual normalized variable in a credit model.
- **A3.b:** vendor weighting, DCC targeting and smoothing require the applicable methodology/version. Popularity does not bind an open task.
- **A3.c:** excess/raw returns, spot/forward ATM, percentage denominators and investment horizons must match the claimed quantity. Raw and excess returns coincide for a zero benchmark.
- **A3.d:** fixed shares imply drifting weights; constant weights imply rebalancing. Either may be valid, but their transaction and financing assumptions must agree with the claimed strategy.
- **A3.f — Legacy heuristic retired:** a less common defensible convention is not a conceptual error. Identify the actual mathematical or contractual conflict.

Named estimator variants generally belong in C3, pure units in B1, and time conventions in B3. These are mechanism boundaries, not a priority hierarchy.

See [conditional conventions](../INDUSTRY_STANDARDS.md) and [SciPy Student-t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html).

## Evidence and judgment

Assess candidate mathematics, requirement compliance, and grader validity separately. A failed test establishes disagreement; a passing test is not proof of correctness. Accept coherent models and defensible assumptions where choices are open. Popularity, model identity, candidate agreement and reference output alone do not establish correctness.

Identify the requirement or mathematical claim, candidate expression and inputs, mechanism and consequence. Use one stable `root_cause_id` for one mechanism across affected outputs. Preserve independently evidenced causes in this or other modes. Follow the system prompt's schema: a candidate mechanism may be task-authored; a correct candidate rejected by a faulty grader is not a candidate-mode match. Report uncertainty when artifacts cannot distinguish hypotheses.

# Inputs

## Solution kind

{{TRAJECTORY_KIND}}

## Task instruction (instruction.md)

{{TASK_INSTRUCTION_MD}}

## Task tests digest

{{TASK_TESTS_DIGEST}}

## Agent solution

{{AGENT_SOLUTION}}

# Output

Return only the JSON object specified in the system prompt.
