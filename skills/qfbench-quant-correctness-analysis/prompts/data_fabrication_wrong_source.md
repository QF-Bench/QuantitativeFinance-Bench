# C1 — Unsupported Data or Wrong Source

Use this mode when required analysis relies on fabricated, incorrectly selected, corrupted or unavailable-at-the-time inputs. Random numbers, parsing choices and missing-data handling alone do not prove error.

## Diagnostic checks

1. Identify required sources, fields, frequency, universe, sample and availability timestamps. Compare with data actually used.
2. Trace reliance. Synthetic fixtures and authorized simulation are legitimate; replacing required observations with simulated returns is not.
3. Check parsing, joins, missingness, duplicates and aggregation against source documentation and the estimand. Identify records changed and consequences.
4. For an implementable backtest, verify availability, decision/execution timing, historical universe and revisions. Same-day inclusion is not automatically look-ahead.
5. Do not infer fabrication from round values, model identity, failure counts or absent artifacts. State unavailable input-lineage evidence.

## Common cases

- **C1.a / C1.b:** invented data, assumed constants, wrong source/column, adjusted/raw prices, frequency or population change the required analysis.
- **C1.c:** information released after a decision is treated as available beforehand.
- **C1.d:** a preamble/footer is parsed as observations or another format assumption corrupts ingestion. No fixed `skiprows` value is universal.
- **C1.e:** deletion/imputation conflicts with the estimand. Complete cases across assets can be suitable for a joint estimator; per-asset estimators can require separate samples. Neither is universally correct.
- **C1.f:** documented field meaning is misread. Do not reclassify credit-rating withdrawals as defaults without evidence from that dataset's definitions.

An engineering mechanism in D1.g can describe the same corrupted records; assign one cause. An independent formula error remains reportable.

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
