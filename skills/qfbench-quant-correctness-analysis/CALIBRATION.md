# Validation and calibration

## Current revision

Schema 4.0 changes discovery, evidence handling, attribution and aggregation. Historical agreement scores do not validate this revision. Local structural checks, offline script regressions and independent scenario exercises can establish specific behavior; they do not constitute a new representative human-label calibration or measured production accuracy.

The delivered update report records the checks actually run and their results. Do not promote a small fixture pass rate into Cohen's kappa, benchmark accuracy or a universal guarantee.

## Historical claim

The prior package reported kappa 0.89 on 20 trials and nine modes after seven rounds of rubric/label revisions. Its own table includes unsupported/degenerate classes with no positive observations and describes revisions to human labels during development. The original package and claims are preserved separately with hashes. They are historical development evidence, not independent holdout validation of the current ten-mode rules.

Do not repeat “all formulas verified,” “no errors remaining,” or the old kappa as a current quality certificate. A literature audit establishes only the specific claims checked under their assumptions.

## A defensible new calibration

1. Freeze the skill/schema, source versions and a representative, declared sampling frame. Include agent errors, task/grader defects, mixed cases, valid passes, suspicious passes and insufficient/infrastructure cases where the intended study calls for them.
2. Separate development examples from held-out evaluation. Group related task versions/attempts to prevent leakage across splits; stratify deliberately and disclose sampling weights or limitations.
3. Have independent reviewers annotate the exact evidence without seeing each other's labels or a model prediction. Record uncertainty and exclusions, not forced negative labels.
4. Report per-mode support, prevalence, confusion counts, precision/recall when meaningful, raw agreement and kappa with denominators. For kappa=(observed-expected)/(1-expected), report undefined when expected=1. Missing, invalid and unassessed labels are not true negatives.
5. Evaluate responsibility attribution separately from mode agreement. A mode match does not imply agent fault. Count root causes separately from downstream assertions and overlapping modes.
6. Preserve adjudications. If examples or reference labels are corrected after inspecting predictions, report development versus held-out results separately and use fresh held-out evidence for the final estimate.

The skill should remain cautious when evidence is incomplete even if that reduces the number of classified trials.
