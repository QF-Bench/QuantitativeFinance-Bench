# C2 — Numerical or Optimization Failure

Use this mode for evidenced numerical failure to achieve the required result or accuracy. A different parameter vector, boundary hit, warning, solver or random stream is insufficient.

## Diagnostic checks

1. Identify the mathematical target and computational procedure. Formula and numerical defects can coexist independently.
2. Examine available residuals, feasibility, objective values, conditioning, tolerances, convergence, discretization and sampling uncertainty. Reference parameters do not establish a unique optimum.
3. A success flag does not prove accuracy; a failure flag does not by itself prove the delivered value inaccurate. Boundary optima can be legitimate without advance notice in the task.
4. If optimization, identifiability or approximation bias cannot be distinguished from available artifacts, report uncertainty rather than inventing failure.
5. Separate numerical error, intrinsic approximation bias and test-tolerance mismatch. See [spread options](../references/spread_option_approximations.md).

## Common mechanisms

- **C2.a / C2.b:** demonstrated inferior objective, residual or infeasible output caused by setup/stopping. Different settings alone are not defects.
- **C2.c:** invalid restriction or failed search causes a boundary result. A wrong likelihood is a formula cause; do not duplicate its boundary symptom.
- **C2.d:** counting repeated barrier hits as separate paths when estimating the probability of at least one hit. The intended indicator is at most one per path.
- **C2.e / C2.f:** inaccurate integration, branch handling, overflow, bracketing or iteration for the actual inputs. Reconcile conventions before alleging error.
- **C2.g / C2.h:** a fallback changes the problem or an edge case produces a misleading result; replacing a correlation factor by identity changes the joint distribution.
- **C2.i:** discontinuous penalties can obstruct gradients; demonstrate the actual failure. Independent box bounds cannot generally encode `a+b<1` exactly. Constrained optimization, reparameterization or justified barriers are alternatives.
- **C2.j:** insufficient precision in MC finite differences. For N independent pairs, `Var(D_hat)=[Var(Y+)+Var(Y−)−2Cov(Y+,Y−)]/(4Nh²)`. Common random numbers can reduce variance; independent streams remain valid with sufficient accuracy. A seed alone does not fix draws across different call sequences or libraries.

A negative noisy gamma alone proves neither a sign bug nor faulty RNG. Assess uncertainty and the actual model's convexity.

Source: [Haugh, finite-difference variance](https://martin-haugh.github.io/files/MonteCarlo/MCS_Greeks.pdf).

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
