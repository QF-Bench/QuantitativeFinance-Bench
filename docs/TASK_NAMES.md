# Task identifiers, decoded

QF-Bench task IDs are compressed descriptions — `13f-amendment-aware-crowding`,
`mtm-xccy-basis-desk`, `regime-riskparity-cvar`. They are readable to a practitioner and
opaque to everyone else, which makes the per-task tables hard to navigate without a key.

This page lists all 86 tasks with the plain-language title each task's
`instruction.md` already carries, grouped by domain so that readers can find the area they
know. Times are the author-declared estimates in `task.toml` (`expert_time_estimate_min` /
`junior_time_estimate_min`) — development-stage estimates, not measurements under exam
conditions. Difficulty here is the author's a-priori label in `task.toml`; it is *not* the
empirical difficulty tier used for reporting, which is derived from frontier-model pass rates.

Generated from the repository (`instruction.md` H1 + `task.toml`); see `docs/` for how to
regenerate. Domain grouping is a reading aid — the raw `category` value is shown for each task.

## Derivatives Pricing (22)

| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |
|---|---|---|---|---|
| `american-option-fd-new` | American Option Pricing with Crank-Nicolson Finite Differences | hard | 60 / 180 | `derivatives-pricing` |
| `asian-option-levy-curran` | Arithmetic Asian Options: Exact, Levy, and Curran Approximations | hard | 90 / 240 | `derivatives-pricing` |
| `bs-greeks-pde` | Black-Scholes Greeks Surface & PDE Verification | medium | — | `derivatives-pricing` |
| `cliquet-ratchet-pricing` | Cliquet (Ratchet) Option Pricing | hard | 45 / 150 | `derivatives-pricing` |
| `cme-hdd-option-pricing` | CME HDD Option Pricing: Burn Analysis, OU Model, and Greeks | medium | 50 / 120 | `derivatives` |
| `delta-hedging-pnl-simulation` | Discrete Delta Hedging with Transaction Costs, Discrete Dividends, and Time-Varying Implied Vol | medium | 45 / 120 | `derivatives-pricing` |
| `digital-barrier-options` | Digital Options & Barrier-Style Binary Pricing | medium-hard | — | `derivatives-pricing` |
| `fx-forward-cross-rate` | FX Forward Portfolio Valuation and Risk Analysis | easy | 50 / 150 | `fx-pricing` |
| `hull-white-swaption` | Hull-White Swaption Pricing: Calibration, Jamshidian Decomposition, and Trinomial Tree | very hard | 75 / 240 | `interest-rate-derivatives` |
| `implied-vol-approximations` | Closed-Form Implied Volatility Approximations | hard | 55 / 170 | `derivatives-pricing` |
| `interest-rate-cap-floor` | Interest Rate Cap and Floor Pricing | hard | 30 / 85 | `pricing` |
| `localvol-barrier` | Local-Vol Surface Cleaning and Barrier Pricing | hard | 120 / 360 | `derivatives-pricing` |
| `lookback-options` | Lookback Option Pricing and Monte Carlo Validation | hard | — | `derivatives_pricing` |
| `mc-greek-surface-1` | Monte Carlo Greeks: Pathwise, Likelihood Ratio, and Finite Difference Methods | hard | 75 / 240 | `derivatives-pricing` |
| `merton-jump-diffusion` | Merton Jump-Diffusion: Calibration & Option Pricing | hard | 60 / 180 | `derivatives-pricing` |
| `ohlc-realized-vol-estimators` | OHLC Realized Volatility Estimators | medium | — | `volatility-modeling` |
| `option-put-call-parity-forward-audit` | Option Put-Call Parity Forward Audit | hard | 50 / 135 | `derivatives` |
| `ou-jump-commodity` | OU Process with Jumps: Commodity Modeling | hard | 75 / 210 | `stochastic-processes` |
| `spread-option-kirk-margrabe` | Spread Options: Kirk's Approximation & Margrabe Exchange Options | hard | 60 / 180 | `derivatives-pricing` |
| `stochvol-implied-surface-new` | Implied Volatility Surface Under a Two-Factor Heston Model | hard | 60 / 180 | `derivatives-pricing` |
| `variance-swap-replication` | Variance Swap Fair Strike from a Dirty Option Chain | medium | 45 / 120 | `derivatives-pricing` |
| `zero-coupon-bootstrapping` | Zero-Coupon Yield Curve Bootstrapping | hard | 35 / 95 | `pricing` |

## Fixed Income & Rates (7)

| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |
|---|---|---|---|---|
| `cir-bond-pricing` | CIR Short-Rate Model: Calibration & Bond Pricing | hard | 90 / 240 | `fixed-income` |
| `fomc-tone-event-study` | FOMC Tone Surprise and Treasury Yield Event Study | medium | 35 / 90 | `fixed-income-nlp` |
| `geometric-mean-reverting-jd` | Geometric Mean-Reverting Jump-Diffusion Model | hard | — | `fixed-income` |
| `mtm-xccy-basis-desk` | USD-Collateralized MTM GBP/USD Cross-Currency Basis Swap | hard | 90 / 300 | `cross-currency-rates` |
| `swap-curve-bootstrap-ois` | USD Swap Curve Bootstrap (OIS + 3M LIBOR) — Debug and Fix | medium | 40 / 120 | `fixed-income` |
| `yield-curve-bond-immunization` | Yield Curve Bond Immunization With Market Conventions | hard | 180 / 480 | `fixed-income` |
| `yield-curve-bootstrap-immunization` | Yield Curve Bootstrapping, Key Rate Durations, and Portfolio Immunization | hard | 60 / 180 | `fixed-income` |

## Risk Management (10)

| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |
|---|---|---|---|---|
| `copula-equity-fitting` | Copula Fitting for Equity Pairs | hard | — | `risk-management` |
| `creditmetrics-portfolio-var` | CreditMetrics Portfolio Credit VaR | hard | 120 / 300 | `risk-management` |
| `dcc-garch-portfolio-var` | DCC-GARCH Multivariate Portfolio Value-at-Risk | hard | 60 / 180 | `risk-modeling` |
| `evt-pot-var` | Tail-Risk VaR/ES with EVT and GARCH-EVT | medium | 90 / 180 | `risk-management` |
| `ewma-portfolio-risk-decomposition` | EWMA Portfolio Risk Decomposition — Debug and Fix | medium | 20 / 60 | `risk-management` |
| `fft-compound-poisson` | Aggregate Loss Distribution via FFT-Based Characteristic Function Inversion | hard | 60 / 180 | `risk-management` |
| `historical-var-data-prep` | Historical Portfolio Value-at-Risk with Data Cleaning | easy | 15 / 45 | `risk-management` |
| `smith-tail-index` | Smith (1987) Tail Index Estimation | hard | — | `extreme-value-theory` |
| `standard-var-methods` | Standard VaR Methods Comparison | hard | 60 / 180 | `risk-management` |
| `var-es-estimation` | VaR and ES Estimation Methods | medium | 45 / 150 | `risk-management` |

## Credit (4)

| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |
|---|---|---|---|---|
| `copula-sampling-rank-correlation` | Copula Sampling and Rank Correlation Analysis | medium | — | `dependence-modeling` |
| `credit-migration-matrix` | Credit Rating Migration Matrix Analysis | medium | 30 / 90 | `credit-risk` |
| `credit-portfolio-var-cvar` | Portfolio Credit VaR with Copula Default Correlation | hard | 45 / 120 | `credit-risk` |
| `credit-spread-decomposition` | Credit Spread Decomposition with HAC Inference and Variance Attribution | medium | 60 / 180 | `credit-analysis` |

## Factor Research (7)

| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |
|---|---|---|---|---|
| `cross-sectional-momentum` | Cross-Sectional Momentum Long/Short Portfolio | hard | 35 / 120 | `cross-sectional-strategies` |
| `double-sort` | Betting Against Beta × Momentum Corner Portfolio | hard | 45 / 150 | `factor-research` |
| `event-study-earnings` | Earnings Event Study — Abnormal Returns and CAAR | hard | 50 / 130 | `factor-models` |
| `fama-french-factor-model-new` | Fama-French 3-Factor Model — Stock Factor Analysis (Enhanced) | easy | 30 / 90 | `factor-models` |
| `lob-pc-signal` | LOB PC Signal: Weighted OFI, PCA, and Rolling Regression | medium | 60 / 120 | `predictive-alpha-modeling` |
| `residual-momentum` | Residual Momentum vs. Raw Momentum | medium | 90 / 300 | `factor-research` |
| `stable-residual` | Stable Residual Alpha with Beta-Neutral, Turnover-Capped Execution | medium | 120 / 420 | `factor-research` |

## Systematic Strategies & Backtesting (5)

| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |
|---|---|---|---|---|
| `bollinger-backtest-aapl` | Bollinger Band Mean Reversion Backtest with Risk Management (AAPL) | medium | 45 / 120 | `backtesting` |
| `fx-carry-forward-hedge` | FX Carry Trade with Dealer-Style Forward and Option Hedges | hard | 180 / 480 | `fx-strategy` |
| `momentum-backtest` | EMA Crossover Momentum Backtest (SPY) | easy | 30 / 90 | `backtesting` |
| `pca-factor-portfolio` | PCA Factor Portfolio Construction | hard | 40 / 110 | `strategy` |
| `sma-crossover-spy` | SMA Crossover Momentum Backtest (SPY) | easy | 30 / 90 | `backtesting` |

## Execution & Microstructure (2)

| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |
|---|---|---|---|---|
| `binance-btc-participation-tca` | Binance BTC Participation TCA | hard | 60 / 150 | `execution` |
| `intraday-volume-fitting-and-execution-scheduling` | Intraday Volume Fitting And Execution Scheduling | hard | 90 / 150 | `execution` |

## Digital Assets (1)

| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |
|---|---|---|---|---|
| `crypto-funding-rate-basis-carry` | Crypto Perpetual Funding Rate Economics & Basis Carry Analysis | medium | 50 / 120 | `crypto` |

## Portfolio & Attribution (4)

| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |
|---|---|---|---|---|
| `brinson-sector-attribution` | Brinson-Fachler Sector Attribution | medium | 30 / 60 | `performance-attribution` |
| `etf-cross-asset-lead-lag` | ETF Cross-Asset Lead-Lag Discovery | medium | 55 / 140 | `cross-asset-analysis` |
| `etf-overlap-redemption-pressure` | ETF overlap-aware redemption pressure attribution | medium | 60 / 150 | `portfolio-analysis` |
| `yield-curve-pca-dynamics` | Yield Curve PCA Dynamics | medium | 60 / 180 | `statistical-analysis` |

## Cross-Domain & Data Engineering (20)

| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |
|---|---|---|---|---|
| `13f-amendment-aware-crowding` | 13F Amendment-Aware Crowding, Overlap, and Turnover | medium | 75 / 210 | `cross-domain` |
| `alpha-hedge-strategy` | Alpha Signal Construction with Factor Exposure Analysis | hard | 60 / 120 | `cross-domain` |
| `barrier-garch-var` | Barrier Option GARCH VaR | hard | 55 / 110 | `cross-domain` |
| `bl-regime-hmm` | Black-Litterman with Regime-Switching HMM | hard | 65 / 130 | `cross-domain` |
| `corporate-action-adjustment` | Corporate Action Price Adjustment | medium | 25 / 60 | `tool-using` |
| `cta-basel-capital` | CTA Strategy Basel Capital Charge | hard | 60 / 120 | `cross-domain` |
| `earnings-surprise-calculator` | Earnings Surprise and SUE Calculator | medium | 20 / 50 | `tool-using` |
| `form4-cross-sectional-sale-pressure` | Cross-sectional insider sale-pressure reconstruction from Form 4 filings | hard | 150 / 360 | `cross-domain` |
| `ipca-latent-factors` | IPCA: Instrumented Principal Components Analysis | hard | 60 / 120 | `cross-domain` |
| `kelly-var-sizing` | Kelly Criterion Sizing with VaR Constraint | hard | 55 / 110 | `cross-domain` |
| `multimodal-alpha-fusion-edgar-cot-gdelt` | Hard Multimodal Quantamental Alpha with Committee Disagreement and Process Filtering | hard | 180 / 480 | `cross-domain` |
| `polars-api-migration` | Polars API 0.x to 1.x Migration | medium | 20 / 40 | `debug-migration` |
| `prediction-markets-cross-venue-dislocation` | Cross-Venue Prediction-Market Dislocation | hard | 120 / 300 | `cross-domain` |
| `realized-vol-estimators` | Multi-Frequency Realized Volatility with Microstructure-Noise Correction | medium | 40 / 120 | `cross-domain` |
| `regime-cta-vol-target` | Regime-Aware CTA Strategy Analysis | hard | 55 / 110 | `cross-domain` |
| `regime-riskparity-cvar` | Eigenvalue Regime Detection with Risk-Parity and CVaR | hard | 60 / 120 | `cross-domain` |
| `sec-10k-report-long` | SEC 10-K Report Information and Fundamental Metric Extraction | medium | 60 / 120 | `cross-domain` |
| `sec-8k-event-alpha` | 8-K Event Alpha | medium | 30 / 75 | `event-driven-analysis, data-processing` |
| `sentiment-factor-alpha` | Sentiment Momentum Factor with IC and Regression Alpha | hard | 60 / 120 | `cross-domain` |
| `structured-note-risk` | Structured Note Valuation and Risk | hard | 50 / 100 | `cross-domain` |

## Uncategorised (4)

| Task ID | What it is | Difficulty | Expert / junior (min) | `category` |
|---|---|---|---|---|
| `barone-adesi-whaley` | Barone-Adesi & Whaley American Option Approximation | — | — | `—` |
| `compound-option-geske` | Compound Options Pricing with Geske Formula | hard | — | `—` |
| `dupire-local-vol` | Dupire Local Volatility Surface Extraction from Market Prices | — | — | `—` |
| `first-passage-time` | First Passage Time & Running Extrema of Geometric Brownian Motion | — | — | `—` |
