# Reading requirements and citations

Use this reference when the task's intended convention or method is disputed. Scan helpers locate potential evidence; they do not decide correctness, completeness or responsibility.

## Find the relevant requirement

Look for author/year or textbook references, cross-file specifications, equations, pseudocode, named parameters, library arguments, dates/day counts, schema lists and prose constraints. Follow permitted referenced files. Record the exact statement and its scope.

A schema enumerates output shape; it does not pin the estimator. A named distribution does not always identify scale/rate or variance normalization. A paper may define several variants or require assumptions absent from the task. A cross-file path may point only to data, not a formula. A seed does not usually specify random-call ordering. Plain prose can be precise without TeX or an eponym.

Assess whether the complete context and standard domain knowledge resolve the material choice. Explain competing interpretations only when they are defensible and change the financial result or acceptance. Do not manufacture ambiguity from harmless algebraic rearrangements or the absence of a preferred library.

## Four distinct questions

1. What result or procedure does the task actually require?
2. Is that requirement financially and mathematically valid for its declared purpose?
3. Does the candidate implement it, or a permitted equivalent?
4. Does the grader test it with a justified error budget?

A strong specification can still contain a wrong formula. A correct formula can still be graded unfairly. Different formulations can be algebraically equivalent while different stochastic programs can be equivalent in distribution rather than path-by-path. If exact paths are required, verify that the algorithm, generator and call ordering needed to reproduce them are specified; otherwise examine statistical accuracy.

## Citation handling

Verify nontrivial or uncertain claims against applicable primary sources. Distinguish a definition, mathematical theorem, recommended practice and library default. Check model/version, domain and boundary assumptions. Do not treat “industry standard” as a universal rule when conventions vary by instrument, jurisdiction, sample or purpose.

The local scan_citations_v2.py helper returns candidate patterns only. Its historical regime names, if retained for compatibility, are not judgments that a task is self-contained or that task-side defects are impossible. An unmatched regex is not evidence that an instruction omitted the requirement. Do not apply a global authorship regime to every output family.
