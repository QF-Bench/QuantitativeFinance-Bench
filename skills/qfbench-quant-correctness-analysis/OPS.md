# Operations

Choose **task review**, **trial diagnosis**, or both from the user's request. Both routes use local evidence and independent analysis without separate provider API calls or credentials. Existing authorization applies; do not ask again merely because a requested full review includes a fresh local solve.

## General task correctness and quality review

1. Freeze the available task packet: purpose, instructions, inputs, reference, grader and outputs, with version/hash or provenance. No candidate, run, reward or QF-Bench layout is required. Record absent components as optional/inapplicable or necessary evidence gaps according to the requested conclusion.
2. Follow [the task-review protocol](references/task-review.md): independently assess the financial model, mathematics, assumptions, numerics and task quality. Check meaningful reasoning, output usefulness, well-posedness, data integrity, feasibility and evaluation fairness. Examples are optional; derive checks from the actual task.
3. Record every material requirement/output family's coverage. Use independent calculations and appropriate valid/wrong controls; run the actual scorer when present and authorized. Keep host diagnostics, native scorer controls, manual inspection and fresh solver attempts distinct.
4. For full acceptance, record all three rounds: independent review, selected Lean cores and fresh blind interpretation/solving. Give the fresh agent only instructions and permitted inputs, seal interpretation before coding and code/outputs before separate grading, and preserve resource/isolation limits. Missing applicable rounds remain gaps. A narrower source audit need not run all rounds and must not claim full readiness.
5. Produce the separate version 1.0 task-review report. Separate confirmed/open defects from unknown evidence, optional improvements and verified repairs. Record task quality, reference correctness, grader adequacy and any candidate correctness independently. A completed review can still conclude that changes are needed.
6. If source repairs are authorized, make minimal changes in a versioned copy and verify final sources with affected independent checks and controls. Preserve old findings/outcomes. Use a new fresh agent for requested post-change blind validation.

The trial scripts below are optional adapters for submitted-trial evidence. They do not validate or import task-review reports. See [scripts/README.md](scripts/README.md) for commands and flags.

## Trial diagnosis

### 1. Define the population

Select the task versions and trial population relevant to the question. Include suspicious passing trials and valid alternative implementations when studying grader reliability. A failed-only cohort can explain failures but cannot estimate false-pass rates. Do not silently pool historical API runs, local app-agent attempts, different source versions or repaired tasks.

Record selection criteria, available/missing artifacts and native statuses. Distinguish PASS, FAIL, PARTIAL, ERROR and UNKNOWN in discovery. Preserve an observed timeout or protocol error from logs even when a reward exists. A boolean, nonfinite or out-of-range reward is invalid evidence, not a clean pass/fail.

### 2. Prepare and inspect evidence

Use task_context.py and extract_solution.py or judge_trial.py's prepare-only workflow. Keep the task tree corresponding to the run; record hashes and Git metadata. Inspect the actual candidate code, final output, execution logs, test assertions and native scoring. Binary figures need a viewer; a digest or hash alone does not verify their meaning.

Preparation is not judging. review_request.v4.json provides the binding hashes and mode prompts for a local reviewer. If evidence is truncated or unresolved, retrieve the needed files before assessing, or record insufficient_evidence. Never let the current main branch silently substitute for the run's task version.

### 3. Review and import

Use an independent app agent or a human reviewer to analyze the prepared evidence and produce the schema 4.0 response. No separate provider API is needed. This is post-hoc diagnosis: the reviewer can inspect references and tests, but must not describe the inspected attempt as a fresh blind solve.

Pass --responses-json and --reviewer to import the response. The binding hashes must match the exact current evidence and prompts. labels.v4.json is separate from legacy labels.json; replaced v4 labels are archived by content hash. Do not bypass a mismatch by changing the response hashes without rereviewing the changed evidence.

A fresh solve, when requested separately or as part of an authorized full review, uses a new agent/context and input-only local Docker sandbox, with interpretation recorded before coding, fixed resource limits, no hidden feedback, stopped execution and sealed artifacts before native grading. Post-change validation needs the appropriate final source version. Record actual runtime/model telemetry only when observed.

### 4. Aggregate honestly

Aggregate only compatible validated labels. Report how many labels/trials were assessed, insufficient, missing, invalid or errored. Keep native outcome separate from analytical verdict. Include task-side findings even when no candidate-error mode matched. Report independent causal counts separately from mode counts; avoid inferring overall model quality from an unrepresentative cohort.

For agreement metrics, match the same trial/version/mode between independent annotators. Exclude unknown/missing pairs explicitly and report how many were excluded. Cohen's kappa is undefined when expected agreement is 1; perfect all-negative agreement is not kappa 1. Report raw agreement, class counts and support. See [CALIBRATION.md](CALIBRATION.md).

## Optional provider integration

The scripts retain optional integration for separately authorized use. It requires --allow-api, a positive --budget-usd and an explicit --pricing-json entry for the exact model. Do not substitute stale price tables or report an unknown price as zero. Fail before client creation when opt-in is absent. These flags are technical controls, not authorization; an active “no API runs” user instruction still governs.

A spending bound depends on token accounting and price assumptions. Reserve the configured maximum charge before requests/retries and stop when it cannot fit. Record actual and estimated usage distinctly. If billing cannot be bounded under the selected provider's semantics, do not claim a hard budget guarantee or start the run without resolving that limitation. Never use a live provider call as a smoke test for this skill when offline mocks suffice.

## Operational boundaries

Do not install global dependencies, fetch private payloads, rerun trials, change benchmark sources, push branches or post comments merely because a diagnostic references them. Respect existing task authorization. When a required tool is unavailable, explain the evidence gap and continue independent work; do not turn skipped validation into success.

Use versioned, reproducible artifacts. Preserve source/control mistakes and their corrections. Check control membership after overlays, native versus expanded test counts, reward aggregation and seal hashes. Stop sandbox processes at terminal outcomes and keep reviewer/solver artifacts separate.
