# C3 — Statistical Method Variant Mismatch

Use this mode for a consequential estimator/procedure variant difference. A valid alternate variant is not automatically candidate error; a name or citation need not settle every implementation detail.

## Diagnostic checks

1. Identify estimand, candidate estimator, assumptions and explicit variant requirements. Read the source when the task delegates a definition.
2. Compare observation selection, weighting, kernel, bandwidth, conditioning, normalization and finite-sample treatment.
3. Decide separately whether the candidate is valid, meets clear requirements, and is rejected by a grader that excludes defensible alternatives.
4. An arbitrary wrong formula is not a defensible variant merely because instructions are vague.
5. Ignore publication-date cutoffs, model tiers, training-data guesses and votes.

## Examples and limitations

- **C3.a — HAC:** bandwidth, kernel, prewhitening and finite-sample correction are separate choices. `floor(4(T/100)^(2/9))` is statsmodels `cov_hac`'s documented default. sandwich `NeweyWest` uses `floor(bwNeweyWest(...))`, a data-dependent selector, with prewhitening. These are not NW1987/NW1994 rules differing only in rounding.
- **C3.a — ES:** for loss confidence c, upper-tail ES is `(1−c)^−1 ∫_c^1 q_u du`. Atoms require fractional boundary mass. Strict exceedance means generally differ; check the requested quantity.
- **C3.a — Half-life:** scalar AR(1) half-life is `−log(2)/log(φ)` for `0<φ<1`. A VECM spread has coefficient `1+β'α` only under additional restrictions, such as one cointegration relation and no lagged differences. General dynamics require the full transition system.
- **C3.b — Legacy heuristic retired:** publication year predicts neither ambiguity nor correctness.
- **C3.c:** a grader enforces an unstated estimator, smoothing rule or procedural definition that excludes a defensible interpretation. Cite the conflict; presume neither side authoritative.
- **C3.d:** NumPy `inverted_cdf` gives the empirical generalized inverse. `higher` uses the `(n−1)q` interpolation convention and can differ. Interpolation may be a valid estimator of continuous-population quantiles; identify the target.

Sources: [statsmodels HAC](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html), [sandwich HAC](https://sandwich.r-forge.r-project.org/reference/NeweyWest.html), [Acerbi–Tasche](https://arxiv.org/abs/cond-mat/0104295), [NumPy quantile](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html).

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
