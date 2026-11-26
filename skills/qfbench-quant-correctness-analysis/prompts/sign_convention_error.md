# B2 — Sign or Orientation Error

Use this mode for an incorrect sign relative to a quantity's definition, or inconsistent mapping between valid conventions. A negative ratio to a reference is only a hypothesis.

## Diagnostic checks

1. Define positive/negative profit, loss, position, derivative, lag or shape parameter.
2. Trace the convention through formulas and labels. A consistent relabeling is not a mathematical defect.
3. For latent factors, inspect invariants and loadings before treating a sign or rotation as wrong. A hidden reference anchor is not mathematical authority.
4. Assess sampling uncertainty before labeling a negative stochastic estimate a sign bug. Establish positivity for the actual model and variable held fixed.

## Common cases

- **B2.a:** read the density and support. SciPy `genpareto` and R `ismev::gpd.fit` both use positive ξ for an unbounded heavy GPD tail; do not automatically negate between them.
- **B2.b:** `L=−PnL` is a valid mapping. VaR/ES need not be strictly positive even in loss units if the relevant tail contains gains.
- **B2.c:** shorts can use negative quantity or positive quantity plus side flag. Applying both reversals creates an error. Long and short versions of one claim have opposite values; that alone is not a model-class change.
- **B2.d:** positive k in `corr(A_t,B_(t+k))` relates A to future B. Correlation sign is separate from lag direction.
- **B2.e:** eigenvector signs are free; repeated eigenvalues also permit basis rotation. A specified presentation anchor is compliance. Changing factor signs without corresponding loadings can change the reconstructed model and be a real defect.

Sources: [SciPy GPD](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.genpareto.html), [ismev implementation](https://github.com/cran/ismev/blob/master/R/gpd.R).

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
