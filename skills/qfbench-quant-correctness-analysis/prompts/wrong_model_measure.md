# A1 — Wrong Model or Measure

Use this mode when the implemented stochastic model, payoff, measure or mathematical object is incompatible with the requested problem. Names and variable notation do not establish the model actually computed.

## Diagnostic checks

1. Write the candidate's dynamics, payoff, numeraire/measure and boundary conditions. Compare them with explicit requirements and defensible interpretations.
2. Distinguish the continuous model from its numerical approximation. CRR and Jarrow–Rudd trees can approximate the same diffusion; Euler and Milstein can discretize the same SDE. An explicitly required algorithm can still be a compliance obligation.
3. Verify pricing drift for the actual numeraire, carry, funding and dividends. Physical drift is legitimate for forecasting or physical-measure risk simulation.
4. Identify a diagnostic's domain. An ATM-only check cannot establish a required surface-wide condition. A finite grid also needs additional reasoning to prove a continuum condition.
5. For a lattice, check conditional moments, probabilities, curve fit and convergence. Do not require universal Hull–White spacing, boundary indices, branch counts, or a minimum number of structural deviations.

## Mechanisms and boundaries

- **A1.a / A1.b:** replacing a required stochastic-volatility process with constant volatility, or using physical drift in a specified money-market risk-neutral valuation.
- **A1.c:** presenting a pointwise calculation as the required domain-wide diagnostic.
- **A1.d:** equations implement a different process despite using the requested name. One decisive contradiction can suffice; several numerical choices do not by themselves prove substitution.
- A missing term may be A2; a parameter mapping may be A3. Choose the description of that mechanism without suppressing separate findings.
- A coherent simpler model is not an error when model choice is permitted merely because the grader uses a richer one.

See [conditional model guidance](../INDUSTRY_STANDARDS.md).

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
