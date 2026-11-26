# Worked diagnostic examples

These are constructed illustrations of reasoning, not quotations from task instructions or records of particular model runs. Their links to audited cases and their limits are recorded in [the example audit](references/example-audit.md). A similar task name does not transfer the verdict.

## 1. A plausible surface passes an incomplete grader

The task requests a model-derived local-volatility matrix. In the illustrative wrong control, every cell is replaced with the same positive number. Shape/range checks pass, but independent model prices and the prescribed finite-difference calculation produce a varying matrix.

Record the native PASS unchanged. The control's constant computation is a concrete quantitative error, and the missing grader coverage is a separate task-side defect. Match the mode supported by the actual code; use mixed attribution only after independently establishing both contributions. Propose a complete numerical or well-justified consistency check and test a coherent wrong matrix as well as valid rounded outputs. A correct reference alone would not have revealed the gap.

## 2. Correct outputs fail because of hidden implementation choices

The contract specifies a probability law and sample size but does not pin generator call ordering. Two independently valid simulation programs produce statistically consistent estimates with different seeded paths. The grader requires one reference realization at a much tighter tolerance than the estimator uncertainty.

The different RNG stream does not establish a candidate error. Inspect the complete contract for any actual path-reproduction requirement, verify the distribution and uncertainty, and demonstrate a valid rejected alternative. If those checks support the claim, record candidate mode match false and task-side responsibility. Do not infer a hidden requirement from “sample from,” an exact expected value or the fact that another model matched it.

## 3. Missing financing hides inside Monte Carlo bands

The required daily portfolio return is w'R+(1-sum(w))*rf. A candidate uses only w'R. Its median wealth can remain within an otherwise defensible simulation tolerance.

Derive the cash identity and recompute the missing contribution. This supports an A2 finding irrespective of a grader PASS. To distinguish the error fairly, validate actual same-draw asset/portfolio moments or an equivalent accounting observable rather than arbitrarily tightening all Monte Carlo bands. If code and grader are both defective, report the separate evidence. If the task explicitly instructed omission while claiming a funded portfolio, task-side responsibility may dominate.

## 4. A converged optimizer is not necessarily a good fit

The candidate and an independent fit use the same likelihood, admissible domain and initialization convention. The candidate reports success, but a feasible independently checked solution has a materially better objective and changes required risk forecasts.

This supports C2 when poor numerical fitting is the mechanism. A global-optimum proof is not implied. Conversely, different parameter vectors with equivalent objective values and outputs in a poorly identified model are not automatically errors. Calibrate parameter tolerance from identification and relevant output sensitivity, not a universal bound copied from another task.

## 5. A coarse approximation is being assessed for the wrong purpose

The task explicitly asks for a specified coarse-grid diagnostic. The candidate implements that diagnostic correctly; a refined continuous-model calculation differs materially in a poorly conditioned wing.

Separate implementation correctness from approximation accuracy and intended use. A valid diagnostic is not an agent error merely because a refined estimate is better. If the task claims the diagnostic is an accurate continuous surface, investigate a task-model/numerical defect. Report the approximation's limits; do not hide them behind a successful native check.

## 6. No output, limited evidence

A run has no final artifacts. Logs may show a provider failure, a blocked container, a code exception or nothing useful. Do not turn this observation into ten finance-error negatives or automatically blame infrastructure.

A visible omitted required write can support D1; a meaningful formula in nonexecuted code can support a carefully bounded mathematical finding. With no evaluable code/output, financial modes remain insufficient_evidence. Classify infrastructure only when the logs establish it. Native status, execution cause and mathematical assessment remain distinct.

## 7. Explicit specification, invalid formula

In this hypothetical specification, loss is standard normal and the task prescribes `ES_c = VaR_c + phi(z_c)/(1-c)`. The candidate follows it exactly. Direct tail integration gives `ES_c = phi(z_c)/(1-c)`; the extra VaR term is wrong. At c=0.99, correct ES is about 2.6652, versus 4.9916 under the hypothetical formula. This is not a quotation from a benchmark task.

Instruction compliance and financial correctness disagree. Record the mathematical mechanism with task-side attribution, identify the bad formula and propose the smallest repair. Do not convert the result into agent error because the specification is explicit, nor certify the finance because it was followed literally.
