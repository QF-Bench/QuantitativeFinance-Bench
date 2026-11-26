# Quantitative reference: conditional identities and conventions

This catalog supports mathematical review; it does not impose hidden industry defaults. Judge a coherent model and defensible assumptions against the actual question. Distinguish mathematical validity, explicit compliance and grader validity. A more sophisticated or more popular model is not automatically required. Neither passed tests nor a reference implementation establish truth.

Use sources to resolve a concrete claim, including their assumptions and notation. A citation may define a method without pinning its every numerical choice. Where evidence remains incomplete, report uncertainty. Do not infer responsibility from model tiers, candidate votes or historical failure counts.

## A. Returns, volatility and risk statistics

### A.1 — Return definitions and aggregation

For successive simple returns with consistent cashflow treatment, total return is `∏(1+r_t)−1`; log returns add, and convert back using `exp(Σ log(1+r_t))−1`. Summing simple returns can be an approximation or a specified signal, but is not exact compounded performance. Under constant-parameter GBM, expected log-growth is `μ−σ²/2`; this does not make `CAGR = arithmetic mean − variance/2` exact for arbitrary sampled returns.

For stationary additive returns, `Var(Σ_{t=1}^m r_t)=mγ_0+2Σ_{k=1}^{m−1}(m−k)γ_k`. Square-root volatility and Sharpe scaling require the relevant covariance terms to vanish, with consistent mean and benchmark definitions. The annual period count follows the data and market; 252 is a common approximation. [Lo, *The Statistics of Sharpe Ratios*](https://traders.studentorg.berkeley.edu/papers/The-Statistics-of-Sharpe-Ratios.pdf).

### A.2 — Variance and distribution parameters

`ddof=1` gives the usual unbiased sample **variance** for iid observations with finite variance; taking its square root does not generally give unbiased standard deviation. `ddof=0` is defensible for descriptive population variance or Gaussian maximum likelihood. Library defaults are not correctness rules. [NumPy standard deviation](https://numpy.org/doc/stable/reference/generated/numpy.std.html).

For standard Student-t `T_ν`, `Var(T_ν)=ν/(ν−2)` when `ν>2`. Unit-variance innovations are `sqrt((ν−2)/ν)·T_ν`; location-scale densities include their Jacobian. A degree-of-freedom bound must follow the moments the model needs, not a universal empirical threshold. [SciPy Student-t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html).

A coefficient of variation is `CV=sd/mean` for a nonzero mean, so `Var(X)=CV²·mean²`. Check whether a model's symbol refers to X or a mean-normalized factor before comparing formulas.

### A.3 — Quantiles and Expected Shortfall

State whether c is confidence or tail probability and whether X represents loss or P&L. For an integrable loss L, confidence `0<c<1`, and `q_c=inf{x:F_L(x)≥c}`:

```text
ES_c = (1/(1−c)) ∫_c^1 q_u du
     = [E(L·1{L>q_c}) + q_c·(F_L(q_c)−c)]/(1−c).
```

The boundary term supplies exactly the remaining tail mass at an atom. For descending equally weighted losses `L_[1]≥…≥L_[N]`, put `h=(1−c)N`, `k=floor(h)`, `θ=h−k`; then `ES_c=[Σ_{j=1}^k L_[j]+θL_[k+1]]/h`. Dropping the fractional term or averaging only strict exceedances generally changes the estimand. Loss-space VaR/ES can be negative when the relevant tail still consists of gains. [Acerbi–Tasche, definitions and quantile integral](https://arxiv.org/abs/cond-mat/0104295).

For the empirical generalized inverse, NumPy provides `method='inverted_cdf'`. `higher` is based on `(N−1)c` and is not equivalent in general. Interpolated sample quantiles can be legitimate estimates of a continuous population quantile; identify the requested target. [NumPy quantile](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html).

### A.4 — HAC and realized variation

HAC results depend on the kernel, bandwidth selection, prewhitening, sample and finite-sample adjustment. `floor(4(T/100)^(2/9))` is the documented default lag rule in statsmodels `cov_hac`. R sandwich `NeweyWest` defaults to `floor(bwNeweyWest(...))`, with data-dependent Newey–West bandwidth selection and prewhitening. Do not label the simple rule “the universal NW1994 default” or distinguish 1987 and 1994 merely by rounding. [statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html), [sandwich](https://sandwich.r-forge.r-project.org/reference/NeweyWest.html).

For adjacent-return bipower variation, the normal-moment normalization is `μ_1^(−2)=π/2`, since `μ_1=E|N(0,1)|=sqrt(2/π)`. Finite-sample factors, lag structure, sampling interval and noise correction must match the particular estimator. A coefficient cannot be judged without its sum definition. [Barndorff-Nielsen–Shephard, bipower variation](https://users.ox.ac.uk/~ofrcinfo/file_links/finecon_papers/2004fe01.pdf).

## B. Time-series models

For scalar `x_t=c+φx_(t−1)+ε_t` with `0<φ<1`, deviations decay as `φ^k` and half-life is `−log(2)/log(φ)` observation intervals. Exact sampling of `dx=κ(θ−x)dt+σdW` gives `φ=exp(−κΔ)` and half-life `log(2)/κ`. Negative φ implies oscillation; `|φ|<1` gives an envelope-decay interpretation, not monotone mean reversion. Fit the actual mean-reverting quantity. A cointegration residual may be that quantity; Kalman innovations are a different object and need not be white under model misspecification.

A rank-one VECM with no lagged differences gives a spread autoregressive coefficient `1+β'α`. Lagged differences, multiple cointegration relations and deterministic components require the full transition dynamics; a single adjustment coefficient is not a general half-life formula. These statements follow directly by projecting the stated state equations.

Exact stationary AR likelihoods include the stationary initial density; conditional likelihoods condition on initial observations. Both can be legitimate without a fixed sample-size cutoff. Compare likelihood criteria on a consistent observation and conditioning basis. Do not add a stationary initial density to a nonstationary model merely to equalize row counts.

Cointegration procedures, lag/trend choices and Kalman initialization depend on the statistical model. Residual cointegration tests use the relevant residual-test distribution, not automatically ordinary ADF critical values. A random-walk coefficient model with OLS initialization is one choice; OLS errors are not inherently “diffuse.” [statsmodels Engle–Granger test](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html).

## C. Numerical methods

Rannacher startup uses backward-Euler steps to damp nonsmooth-payoff oscillations before Crank–Nicolson. The appropriate number and step size depend on the problem, desired derivatives and convergence analysis; there is no universal requirement for four full steps. Other stable convergent schemes are possible. [Giles–Carter](https://people.maths.ox.ac.uk/~gilesm/files/giles_carter.pdf).

A Hull–White lattice must approximate the specified conditional moments and, when required, fit the initial curve. Spacing `sqrt(3·conditional variance)` is a common construction; using `σsqrt(3Δt)` employs a small-step variance approximation. Boundary treatments and node selection are construction-specific, not universal requirements of the continuous model. [QuantLib trinomial implementation](https://github.com/lballabio/QuantLib/blob/master/ql/methods/lattices/trinomialtree.cpp).

Common random numbers can improve finite-difference precision; independent draws are not intrinsically biased. Check sampling uncertainty, bump bias and any discretization error. Seeds support reproducibility but do not fully specify random streams across algorithms, libraries or call order. Greek estimators require their differentiation/interchange conditions; payoff smoothing or hybrid methods can handle cases where naive pathwise differentiation fails. [Haugh, Monte Carlo Greeks](https://martin-haugh.github.io/files/MonteCarlo/MCS_Greeks.pdf).

Solver success, boundary parameters, iteration counts and agreement with reference parameters are evidence to inspect, not verdicts. Examine objective values, residuals, constraints, numerical error and identifiability. A legitimate constrained optimum may lie on a boundary. Coupled constraints cannot generally be replaced exactly by independent boxes.

## D. Pricing and calibration

### D.1 — Units, carry and model choices

Black–Scholes formulas require compatible rate, time and volatility units. Under deterministic continuous carry, `F=S exp((r−q)T)`; that relationship needs modification for other financing/dividend models. Spot ATM and forward ATM are distinct valid definitions. A Greek must specify the held-fixed inputs and reporting units.

Calibration can use prices, implied volatilities or weighted errors, depending on the objective, quotes and conditioning. There is no universal volatility-space loss, strike grid, liquidity cutoff or maximum useful maturity. Surface arbitrage checks must match the claimed model/domain; local arbitrage defects do not prove every downstream Greek wrong. [Gatheral–Jacquier, arbitrage-free SVI conditions](https://arxiv.org/abs/1204.0646).

For Carr–Madan FFT, frequency spacing η and log-strike spacing λ satisfy `λη=2π/N`. Thus `η=0.25,N=4096` gives `λ≈0.00614` and a centered half-width `π/η≈12.57`, not 512. Damping must satisfy the model's moment/integrability conditions; fixed recommended grids are not universal. [Carr–Madan](https://engineering.nyu.edu/sites/default/files/2018-08/CarrMadan2_0.pdf).

### D.2 — Hull–White variance versus drift correction

For `dr=(θ(t)−ar)dt+σdW`, constant `a>0,σ`, deterministic initial rate, and a fitted initial discount curve:

```text
B(t,T) = (1−exp(−a(T−t)))/a
P(t,T) = A(t,T) exp(−B(t,T)r_t)
Var(r_t) = σ²(1−exp(−2at))/(2a)
Var(log P(t,T)) = B(t,T)² Var(r_t)
log A(t,T) = log(P(0,T)/P(0,t)) + B(t,T)f(0,t)
             − σ²(1−exp(−2at))B(t,T)²/(4a).
```

The final correction is half the log-bond variance; they are different quantities. Use the continuous limits as `a→0`. [QuantLib Hull–White implementation](https://github.com/lballabio/QuantLib/blob/master/ql/models/shortrate/onefactormodels/hullwhite.cpp).

### D.3 — Approximate prices and contract details

Margrabe is exact for the exchange payoff under its joint-lognormal assumptions; Kirk approximates a nonzero-strike spread. Neither an “extreme regime” nor multiple candidates' agreement proves approximation bias caused a particular failed check. Inspect the actual inputs, formula and comparator uncertainty. See [spread-option assessment](references/spread_option_approximations.md).

Cliquet caps, floors, reset dates and aggregation depend on the contract. Closed-form availability depends on payoff structure and model; Heston does not universally require Monte Carlo. For discrete dividends and American exercise, use a coherent stock/dividend model and the original-stock exercise payoff even if solving in transformed coordinates.

## E. Curves, bonds and calendars

Day counts, coupon schedules, compounding, collateral remuneration and forward projection follow the instrument and agreement. Currency labels alone do not specify them. Collateralized discounting is linked to the collateral setup; a single-curve model can be a defensible specified abstraction. [FTSE fixed-income calculation conventions](https://www.lseg.com/content/dam/ftse-russell/en_us/documents/policy-documents/ftse-fixed-income-index-guide-to-calculation-new.pdf).

For known deterministic cashflows, `P=Σ_i C_i D(t_i)`. Bootstrapping solves compatible instrument-price equations, recursively or jointly; no universal scalar formula converts a coupon par yield to its zero rate. For a unit-principal par coupon instrument with coupon rate c and accruals α_i:

```text
1 = c Σ_(i=1)^n α_i D_i + D_n
D_n = [1−c Σ_(i=1)^(n−1) α_i D_i]/(1+cα_n)
z_n = −log(D_n)/t_n.
```

For a zero-coupon nominal yield y compounded m times per year, `z=m log(1+y/m)`. A simple-rate deposit instead has `D=1/(1+rτ)`. These formulas follow from the stated cashflows and compounding. Negative rates can produce increasing discount factors; nonmonotonicity alone is not proof of an invalid curve.

Nelson–Siegel may use decay scale τ or reciprocal decay speed λ. Reconcile the definition before comparison; for the scale convention, use `x=T/τ`, `L1=(1−e^(−x))/x`, `L2=L1−e^(−x)`, and `z=β0+β1L1+β2L2`, with limits at zero maturity.

## F. Portfolios, backtests and data

Momentum windows, skip periods, aggregation, weighting, shrinkage, band widths and winsorization order are strategy/model choices. There is no universal Bollinger coefficient, covariance sample-size cutoff or market-impact participation threshold. A fixed-bps cost or square-root impact model is an assumption to assess against scope and evidence, not an automatic failure label.

For differentiable portfolio volatility `σ_p=sqrt(w'Σw)>0`, volatility contribution is `w_i(Σw)_i/σ_p`. Equal contributions imply equal `w_i(Σw)_i`; for a positive diagonal covariance and positive weights, weights are proportional to inverse individual volatilities. Constraints, covariance and risk-budget definitions matter.

For a claimed implementable backtest, inputs must be available by the decision time and execution must respect the stated trading model. Same-date data can be valid; a mandatory one-row lag is not a universal rule. Use actual release/vintage information, historical eligibility and corporate-action treatment relevant to the estimand. Do not assert fixed survivorship-bias magnitudes or assume every vendor timestamp has the same meaning.

Stable sorting preserves existing tie order, not the economic meaning of “latest.” Specify or establish duplicate resolution, sample filtering, imputation and joining rules before assigning error. Consistent PCA sign changes preserve the model; repeated eigenspaces also admit rotations. A presentation anchor requires a contract or a downstream orientation-sensitive purpose.

## G. Output conventions

Formats follow the output contract. Dates may be date-only, timestamps or epoch values when clearly defined; numeric strings and sentinel codes may also be legitimate schema choices. Strict JSON excludes NaN and Infinity literals. Serialization precision must be judged against the actual representation and accuracy requirement, not an assumed universal tolerance. [RFC 8259](https://datatracker.ietf.org/doc/html/rfc8259).

## Application

For each suspected error, state the claim, assumptions, applicable identity or contract, actual implementation, consequence and uncertainty. Assign one `root_cause_id` to one mechanism and retain independent causes. If a coherent candidate conflicts only with an unjustified grader choice, report the grader issue without a candidate-mode match. No entry in this catalog automatically forces or forbids `task_side`.
