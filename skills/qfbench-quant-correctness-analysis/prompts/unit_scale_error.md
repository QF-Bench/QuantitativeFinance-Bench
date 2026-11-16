# B1 — Unit or Scale Error

Use this mode when a defined quantity is converted or reported in incompatible units. A ratio near a familiar factor is a clue, not proof.

## Diagnostic checks

1. Identify input, intermediate and output units: fractions, percent, basis points, currency, notional, return periods and Greek bump convention.
2. Trace a missing, duplicated or inconsistent conversion. Compare quantities on a common basis.
3. Use ratios cautiously near zero or where errors offset. A factor of two can be a coefficient error rather than a unit conversion.
4. Check whether units were required or supported by a defensible definition. A hidden grader unit can be a task-side mismatch.

## Common cases

- **B1.a / B1.b:** `1%=0.01`; `1 bp=0.0001`. Convert percentage inputs before using formulas expecting fractions.
- **B1.c:** annualization omitted or duplicated under a fixed time basis. A disputed time basis is B3; square-root scaling also requires suitable return assumptions.
- **B1.e:** vega per percentage point is `0.01·∂V/∂σ` when σ is a decimal; rho per basis point is `0.0001·∂V/∂r`. Consistent alternate units are valid when permitted and labeled.
- **B1.d — Legacy sentinel routing:** null, NaN, infinity and zero are not alternate scales. Assess the edge case and contract; representation is usually D1, a faulty computation A2/C2. Preserve this subcode only when interpreting historical labels.

A chain-rule error that yields a ratio near 100 remains a formula mechanism. A correct formula plus an independent output conversion mistake supports separate findings.

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
