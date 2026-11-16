# D1 — Output and Interface Compliance

Use this mode for evidenced output-contract violations or data/interface implementation defects. Assess quantitative validity separately; passed numerical tests do not establish correctness.

## Diagnostic checks

1. Identify required files, fields, types, labels, shapes, order, precision and representation. Separate explicit contracts from private grader preferences.
2. Inspect artifacts when available. If only code exists, label conclusions static evidence rather than observed output.
3. Determine whether missing files show noncompliance, interrupted execution or missing evidence. Do not route automatically.
4. A schema defect and unrelated formula bug are independent. One parsing defect changing both a field and its downstream number is one cause.
5. Neither a one-keyword repair nor imagined candidate reasoning distinguishes engineering and quantitative error. Classify the actual operation and requirement.

## Common cases

- **D1.a / D1.b:** labels/shapes conflict with requirements. Hidden exact-match expectations can instead be task-side faults.
- **D1.c / D1.d:** columns, order, identity or types violate a supported contract. JSON numbers and strings differ.
- **D1.e:** explicit rounding loses required accuracy. JSON does not inherently justify a fixed tolerance; inspect serialization and precision requirements.
- **D1.f:** correct date, wrong required representation; an incorrect instant/date is B3.
- **D1.g:** sorting, deduplication, joining, parsing or coercion demonstrably changes intended values. Stable sorting preserves existing tie order but does not decide which duplicate is economically correct. Inspect required tie-breaks and library/version behavior. Integer dtype does not always truncate Python division; groupby is not inherently hash-random.

Strict JSON excludes NaN and Infinity literals. Missing-value encodings, dates and sentinels otherwise depend on the contract. Zero and missing are not interchangeable merely because a verifier accepts one.

Source: [RFC 8259](https://datatracker.ietf.org/doc/html/rfc8259).

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
