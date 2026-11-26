# A2 — Missing, Extra or Incorrect Formula Term

Use this mode for an identifiable algebraic, probabilistic or calculus error. Establish assumptions and symbol definitions first; equivalent formulas can look different.

## Diagnostic checks

1. Derive or source the identity under the applicable model. Check normalization, Jacobians, discounting, covariance terms, boundaries and derivatives.
2. Show the specific omission, duplication or wrong coefficient and its consequence. Reference disagreement alone is insufficient.
3. Distinguish a defect from a disclosed approximation. Assess accuracy on the case's inputs; a method name or broad regime does not determine the verdict.
4. Separate a wrong task formula followed faithfully from a candidate-introduced error. Record both when supported.

## Formula checks

- **A2.a — Transformation or derivative.** For `X=μ+sZ`, `s>0`, `log f_X(x)=log f_Z((x−μ)/s)−log s`. If fitted parameters enter s, the normalization affects estimation; omission has no universal direction of parameter bias. For constant-parameter GBM with deterministic carry, `∂S_T/∂σ=S_T(Z√T−σT)`. Call pathwise vega also includes discounting and the exercise indicator, when differentiation can pass through expectation.
- **A2.b / A2.e — Composition or duplication.** Portfolio variance is `w'Σw`; covariance terms can be omitted only under a justified diagonal model. Entry and exit costs can be distinct legitimate costs; count each actual charge once.
- **A2.c — Likelihood comparison.** Information criteria require comparable observations and conditioning. An initial stationary density is one exact-AR likelihood treatment, not a universal repair for every model.
- **A2.d — Estimator validity.** Naively differentiating a discontinuous pathwise delta misses call gamma. Smoothing, conditioning or mixed estimators can recover it. Gamma and likelihood-ratio theta are not universally unavailable. Required null fields are interface obligations.
- **A2.f — Domain or boundary.** For an American put before maturity, `V≈payoff≈0` far out of the money does not identify a meaningful exercise boundary.
- **A2.g — Coefficient.** In constant-parameter Hull–White with deterministic initial rate, `Var[log P(t,T)]=B(t,T)²σ²(1−e^(−2at))/(2a)`. The negative correction in `log A(t,T)` is half this variance. Thus `2a` is correct for the variance, while `4a` appears in the correction. Reconcile Fourier signs and branch conventions before alleging a characteristic-function error.
- **A2.h — Invalid extension.** An adjusted-stock American dividend model must enforce exercise using the original stock's payoff. A coherent transformed-coordinate solution is possible; adjusted coordinates alone are not a defect.

Sources: [SciPy location-scale density](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html), [Haugh, Greeks](https://martin-haugh.github.io/files/MonteCarlo/MCS_Greeks.pdf), [QuantLib Hull–White](https://github.com/lballabio/QuantLib/blob/master/ql/models/shortrate/onefactormodels/hullwhite.cpp).

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
