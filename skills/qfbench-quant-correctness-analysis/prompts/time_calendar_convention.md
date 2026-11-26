# B3 — Time, Calendar or Compounding Error

Use this mode when intervals, calendars, event order, accrual or compounding are incompatible with the requested quantity.

## Diagnostic checks

1. Establish instrument/data conventions: day-count variant, holidays, timezone, fixing/payment times and endpoint inclusion. Currency or asset class alone does not determine all of them.
2. Trace intervals used in accrual, returns, annualization, discounting and windows. Separate price observations from return intervals.
3. Effective annual-to-monthly conversion is `(1+r)^(1/12)−1`; a nominal annual rate convertible monthly uses `r/12`. Neither is universal.
4. Compare information availability with decision and execution times. Same-date data can be valid; `.shift(1)` is not a universal remedy.
5. If several defensible conventions fit the task and only the grader chooses one, record ambiguity without inventing candidate fault.

## Common cases

- **B3.a / B3.b:** incorrect specified day count or rate compounding. ACT/ACT and 30/360 each have multiple variants.
- **B3.c:** annual observation count inconsistent with the dataset or contract; 252 is a common trading-day approximation, not a constant for every market.
- **B3.d / B3.e:** bar-start/end, fixing time, timezone or daylight-saving mismatch.
- **B3.f / B3.g:** price/return dates, truncation of required fractional expiry, or applying a state update before a cashflow that uses the previous state.
- **B3.h:** 120 observations ending at `i−11` inclusive use Python `[i−130:i−10]`, whose length is 120. `[i−130:i−11]` has 119, absent clipping.

A correct date serialized differently is D1. A time alignment that leaks future information may be C1; use one cause record for that same leak.

Sources: [FTSE fixed-income conventions](https://www.lseg.com/content/dam/ftse-russell/en_us/documents/policy-documents/ftse-fixed-income-index-guide-to-calculation-new.pdf), [Lo, time aggregation](https://traders.studentorg.berkeley.edu/papers/The-Statistics-of-Sharpe-Ratios.pdf).

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
