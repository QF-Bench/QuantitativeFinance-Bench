# Review evidence and diagnostic controls

This revision draws on the existing 86-task review record and the later 13-task PQCat/Foxie recheck. Those records have different source versions and evidence levels. They are not a new 86-task benchmark run or a calibration corpus for this skill. The update's evidence package preserves the source map and hashes.

## Transferable lessons

| Review examples | Lesson supported by the recheck |
|---|---|
| #5, #29, #47, #82: incomplete output checks | Native PASS can admit materially wrong outputs. Establish the real candidate's correctness independently; never attribute an injected control defect to that candidate. #5 includes a passing solver with incorrect IVs. |
| #1, #7, #84: representation | Test permitted label, pair and list representations. For PCA, distinguish valid coherent sign changes from rotations that preserve a hedge subspace but violate ordered component requirements. |
| #8, #14: multiple causes | A candidate accounting or exported-unit error can coexist with a task convention gap or definite reference funding defect. Trace the executed cause; an unexecuted fallback branch is not a demonstrated cause of an observed result. |
| #4, #27: calibration | Compare the same objective, feasible domain and economically relevant outputs. Fresh controls show optimizer success with materially inferior fits. Finite multistart is not a global proof. |
| #9, #16–19, #21, #52: conventions | Read the exact contract. #18 supports an unstated percentile-interpolation issue, not ambiguity about its explicitly fixed median/ddof rules. #19 illustrates initialization-dependent objectives. #9 also has an independent formula error; ambiguity does not excuse it. |
| #29, #69, #86: approximation scope | The repaired #29 declares a coarse diagnostic. #69 still overstates its approximate dividend adjustment as fully adjusted. #86's finite-grid endpoint comparison is sensitivity, not a bound on omitted tails or total error. |
| #5–7, #22: tolerances | Check units, rounding, conditioning and simulation uncertainty. #22's full-Kelly financing omission can fit broad Monte Carlo bands; its repaired checker separately verifies same-draw funding/moment identities. |
| #2, #4, #15–17, #19: native scoring | Verify checkpoint identity, duplicate credit and coherent alternative paths. #18 has a different pytest checker and does not support the alias-scoring example. Distinguish historical defects from repaired checkers. |
| #1, #4, #70, #71: protocol | Native outcomes and terminal or collection status are distinct. #70/#71 show late collection despite early completed output; this is not evidence of solver timeout. Historical status records were reread, not recreated as new failures. |
| #11, #44, #48, #71, #73, #75: independent mathematics | Re-derive cashflows, measures and formulas from inputs. Fresh checks reproduce reference defects despite native agreement; passing checks do not rule out an independent mathematical error. |
| #47, #62, #77, #82: artifacts | Inspect the actual versioned figures and accounting path. Fresh repaired reference outputs pass, while unrelated nonblank PNGs still pass #47/#82 automation; their meaning needs separate inspection. Older artifacts may fail repaired conventions. |

The [example audit](example-audit.md) identifies every cited task, source snapshots, current limits and the five retired worked examples. Queue numbers are review-order positions, not PR numbers. These are review-derived prompts, not labels for every trial of those tasks. Historical findings may have been repaired. Use the run's exact source version and evidence.

## Coverage record

For full task review, cover every material requirement and output family. For a narrow diagnosis, cover the explicitly inspected scope. Use the [general task-review protocol](task-review.md) to assess task quality independently of candidate performance.

For each materially distinct family record:

1. Requirement and financial interpretation, including complete matrix/path/ledger scope.
2. Independent mathematical or numerical basis and applicable assumptions.
3. Grader assertion or explicit manual inspection that covers it.
4. Error budget: serialization, numerical approximation, conditioning or simulation uncertainty.
5. Valid control, including defensible alternatives where relevant.
6. Plausible wrong controls, including internally coherent errors.
7. Actual native status/reward when a scorer was used, artifact hashes and uncovered portions. If no grader exists or native execution was not performed, record the independent/manual evidence and limit; never invent a native outcome.

Use complete independent calculation where practical. Spot checks, basic ranges and agreement between submitted files can all miss a coherent wrong model. Manual review can cover an aspect that automation does not, but its scope must be explicit.

## Running a diagnostic control

Describe the intended mutation before running it. Construct the artifact in an isolated copy; confirm its final contents and membership. Explicitly delete missing-file targets after overlays. Seal it before native grading and record the actual entry point, source hash, logs, status, reward and expanded test counts.

Preserve unexpected results. If the mutation was not actually present, classify the experiment as invalid rather than blaming the grader. Correct and rerun under a new case label. If a material false acceptance or rejection is established, reopen the affected acceptance conclusion; retain the original candidate outcome.

Reference and empty controls establish only basic execution behavior. Meaningful wrong-answer and valid-alternative controls are needed for disputed grading claims. A scalar self-reported identity is weaker than recomputing the identity from the underlying outputs and inputs.

## Three-round review scope

The private-PR review method contributes three evidence categories:

- Independent financial, mathematical and numerical review.
- Lean-assisted checks of selected identities/recurrences with explicit assumptions.
- Fresh blind interpretation and solving from instructions and permitted inputs, sealed before reference comparison.

These categories do not authorize disclosing answers sequentially. A fresh solver must not inherit the reference review, proofs, earlier attempt or grader feedback. Code can run in a network-disabled local Docker sandbox; unless separately verified, host-agent file restrictions are instruction-enforced. Record that limitation.

Selected real-number proofs do not certify assumptions, floating-point programs or every numerical output. Manual figures, native control results and fresh model runs support different conclusions. A narrow diagnostic can reuse evidence from these rounds without launching fresh benchmarking. The skill also supports full task acceptance through the task-review route: complete each applicable requested round, task-quality assessment and material coverage, and state a bounded conclusion. Do not claim full acceptance from a narrow classification or silently skip required evidence.
