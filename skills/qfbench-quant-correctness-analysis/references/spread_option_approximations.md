# Spread options: assessing approximation and implementation error

Use this reference to distinguish a wrong implementation, a model mismatch, intrinsic approximation error and a defective comparison. The assessment applies to the actual case parameters. A method's reputation, a broad parameter regime or agreement across candidates does not settle the cause.

## Model and formula

Consider the European payoff `(S1(T)−S2(T)−K)+`. Assume positive jointly lognormal terminal prices under the relevant pricing measure, deterministic discounting `D(0,T)`, forwards `F_i`, constant volatilities σ_i, correlation `ρ∈[−1,1]`, and matching carry conventions. Under these assumptions Margrabe gives the exact exchange-option value when `K=0`.

For `F1>0` and `F2+K>0`, the common Kirk approximation is:

```text
β = F2/(F2+K)
σ_K² = σ1² + β²σ2² − 2βρσ1σ2
v = σ_K sqrt(T)
d1 = [log(F1/(F2+K)) + v²/2]/v
d2 = d1−v
C_K = D(0,T)[F1 Φ(d1) − (F2+K) Φ(d2)].
```

Use the deterministic limit `D(0,T) max(F1−F2−K,0)` when v tends to zero, and the payoff at expiry. The log formula is outside its domain if `F2+K≤0`; that does not make the financial payoff undefined. Negative strikes require care with domain and approximation conventions.

The ratio's effective volatility depends on the random second asset; Kirk freezes its weight. Setting `K=0` recovers the lognormal exchange formula. Setting `σ2=0` reduces to a Black call with deterministic strike `F2+K` when positive. Neither `ρ=±1` nor `σ1=0` alone generally makes the shifted-lognormal problem exact. No universal bias sign, monotone error relationship or percentage bound follows from the formula. [Harutyunyan–Masip Borràs, formulas and numerical study](https://arxiv.org/abs/1812.04272).

A stated exactness result always belongs to its model. Margrabe need not be exact under stochastic volatility, jumps, different carry assumptions or another payoff. Modified Kirk and other spread approximations must be evaluated under their own assumptions; names alone do not establish a fixed accuracy improvement.

## Review procedure

1. **Establish the target.** Does the task require implementing Kirk, estimating the specified model's exact price to a tolerance, or both? Mathematical validity, contractual compliance and grader validity can differ.
2. **Inspect candidate and comparator.** Reconcile payoff direction, strike, units, time, discounting, spot/forward conversion, volatility, correlation and measure. Check that the comparator simulates or integrates the same model.
3. **Localize the discrepancy.** Record the actual parameter vector, candidate value, comparator value, tolerance and available error information. Identify a specific implementation defect when one exists; do not infer it merely from failure at low correlation or short maturity.
4. **Separate errors.** A Monte Carlo confidence interval describes sampling uncertainty under the estimator's assumptions. It does not include discretization bias, formula approximation bias, input error or systematic implementation error. Antithetic/dependent samples require a suitable standard-error calculation. A finite-level confidence interval can also miss the true price by chance.
5. **Judge the existing evidence.** A correct Kirk implementation rejected solely because a task simultaneously demands an unsupported exact-price tolerance can be task-side. Demonstrate the conflict for the instance using available trustworthy bounds, analytic reductions, documented calculations or validated numerical evidence. If those are unavailable, report uncertainty. Do not run new benchmark tasks unless separately authorized.
6. **Preserve independent causes.** A genuine discounting mistake can coexist with an overly tight grader tolerance. Use separate cause records; do not let “Kirk is approximate” excuse the implementation error.

For `K=0`, formula bias disappears only under the established lognormal exchange model. A failed Monte Carlo comparison still needs investigation of sampling, inputs, simulation and implementation; it is not automatically a candidate error.

## Tolerances and existing evidence

A formula-implementation check can compare against an independently verified evaluation of that formula. An accuracy-to-model check must additionally allow the demonstrated approximation error at its intended inputs. Relative tolerances can be misleading near zero prices. No universal 4% floor, strike exclusion or model switch is justified by this reference.

Published experiments illustrate particular parameter sets; they do not prove universal bounds or the cause of a benchmark failure. Do not import plot-axis limits as measured maxima, transfer positive-strike experiments to a negative-strike case without analysis, or turn repeated failures into proof of formula bias. Use the source's actual assumptions and record any unresolved numerical comparison.
