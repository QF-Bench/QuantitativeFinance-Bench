# regime-riskparity-cvar: why it is hard, and what it actually tests

**Date:** 2026-08-18
**Task:** `tasks/regime-riskparity-cvar` (difficulty `hard`, agent bar 1800 s)
**Scope:** measurement and analysis only. No task files were changed.

## Summary

Five models were run against the task as it stands on `main`. All five failed,
and all five failed for the same underlying reason: they estimated each day's
rolling correlation matrix from a window that **includes that day's own return**,
while the reference estimates it from the window **strictly preceding** the day.

That single boundary choice is the difference between a backtest that could have
been traded and one that could not. The task never states the convention, and it
should not have to: avoiding look-ahead bias is baseline professional practice,
not a house convention. **This is the task's real discriminator, and it is
implicit by design.**

## Test setup

Each run is a fresh Docker sandbox built from the task's own `environment/`,
with the Claude CLI driven against `instruction.md`. Bar 1800 s; no run came
close to it, so nothing failed on time.

## Results

| model | time | classification | deliverables within tolerance |
|-------|------|----------------|-------------------------------|
| Sonnet 4.5 | 205 s | WRONG | 3 / 6 |
| Sonnet 4.6 | 306 s | WRONG | 3 / 6 |
| Opus 4.8   | 175 s | WRONG | 4 / 6 |
| Opus 5     | 125 s | WRONG | 4 / 6 |
| Fable 5    | 140 s | WRONG | 4 / 6 |

Graded deliverables (`*` = within the deliverable's own tolerance):

| deliverable | expected | Sonnet 4.5 | Sonnet 4.6 | Opus 4.8 / Opus 5 / Fable 5 |
|---|---|---|---|---|
| `num_valid_observations` | 726 | 504 | 504 | 726 * |
| `annualized_return` | 0.0875373 | 0.0821251 | 0.0803535 | 0.1094960 |
| `annualized_volatility` | 0.0611054 | 0.0550097 | 0.0550069 | 0.0565279 * |
| `sharpe_ratio` | 1.4325628 | 1.4929188 * | 1.4607899 * | 1.9370278 |
| `max_drawdown` | 0.0520848 | 0.0503698 * | 0.0505636 * | 0.0501916 * |
| `cvar` | 0.0106965 | 0.0107451 * | 0.0107302 * | 0.0107292 * |

Opus 4.8, Opus 5 and Fable 5 produced **identical values on every deliverable**,
across two model families. Convergence that tight indicates a single shared
reading of the specification rather than independent numerical error.

## Where the divergence starts

The task's `solution.json` intermediates localise it precisely:

| checkpoint | expected | Opus 4.8 / Fable 5 | Sonnet 4.5 |
|---|---|---|---|
| `mp_threshold` | 2.213995 | **2.213995** | **2.213995** |
| `num_regime_observations` | **441** | **442** | **442** |
| `regime_count_crisis` | 14 | 14 | 13 |
| `regime_count_risk_off` | **427** | **428** | 429 |
| `num_rebalances` | **21** | **22** | 21 |
| `mean_absorption_ratio` | 0.589261 | 0.589213 | 0.585949 |

The Marchenko-Pastur threshold matches to six decimal places. The crisis-day
count is exact for the top three models. The machinery is right. What differs is
one observation:

```
estimation_window_days = 504
rolling_window         = 63

strictly-preceding window:  504 - 63     = 441   <- reference
inclusive of the current day: 504 - 63 + 1 = 442   <- every model
```

The reference is explicit about it in the generator:

```python
# Start at index rolling_window (using preceding window rows)
start_idx = rolling_window
n_obs = returns_data.shape[0] - rolling_window
```

## Why one observation moves the headline metric by 25%

The extra observation shifts the regime series by one day. That shifts which
calendar days fall in which month, which shifts every monthly rebalance date
downstream — 22 rebalances instead of 21. The weight path differs from that point
on, so return and Sharpe move materially.

Drawdown and CVaR barely move, and that asymmetry is itself diagnostic: those two
are dominated by the shape of the return distribution, which is largely unchanged,
whereas return and Sharpe depend on the weight path. Every model gets drawdown and
CVaR right while missing return. The pipeline is correct; the alignment is not.

## The substantive point: rebalancing requires consistent timing

It is tempting to state the rule as "never use today's return." That is too
strong, and it is worth being precise, because the correct rule is about
**pairing**, not about the window alone.

The freshest observation is genuinely valuable for covariance estimation —
volatility clusters, so recent data carries the most information. Using today's
return is legitimate **provided the weights it produces do not earn today's
return**. Two coherent conventions exist:

| estimation window | weights start earning | verdict |
|---|---|---|
| through day `t-1` | day `t` | consistent — the reference's choice |
| through day `t` | day `t+1` | consistent — rebalance at the close of `t` |
| through day `t` | day `t` | **look-ahead** — circular |

The third row is the error. Sizing a position using the very return that position
is about to be paid on is circular: the backtest reports a P&L that no one could
have earned, because at the moment of trading the input did not yet exist.

The reference enforces the first row structurally:

```python
for t in range(n_trading):
    portfolio_returns[t] = np.sum(weights * returns_from_start[t])  # earn on weights held coming in
    if t in rebal_set:
        window_rets = full_returns[abs_t - rolling_window : abs_t]  # estimate strictly before t
        weights = ...                                               # new weights earn from t+1
```

Weights never depend on the return they are about to earn. What the models did
was take the inclusive window **without** correspondingly shifting the holding
period — they mixed row two's window with row one's holding period, landing on
row three.

This matters more for this task than for a generic backtest. The quantity being
estimated is a **regime classifier**: the correlation matrix determines the
absorption ratio, which determines the regime, which sets the risk budget and
therefore the position size. The crisis days a regime detector exists to identify
are exactly the days whose own returns would reveal the regime. Contaminating the
window with the current day does not merely add noise — it leaks the answer, and
it does so hardest precisely when the classifier matters most.

## Why the task is correctly specified

The instruction says:

> When `estimation_window_days` is set, use only the most recent N valid
> observations for the rolling eigenvalue analysis and backtesting.

It is **silent** on window alignment — not misleading. Its `## Conventions`
section pins the choices that are genuinely arbitrary (Kritzman-Page absorption
ratio, symmetric eigendecomposition, thresholds held constant rather than
adaptive to the rolling mean) and leaves the professional standard unstated.

That split is right. The test that matters is whether an instruction is
*misleading* or merely *reliant on knowledge*. Look-ahead avoidance is knowledge.
Unlike an arbitrary convention — a unit choice, a key name — one reading here is
professionally wrong. Stating it would remove the discriminator while leaving the
rest of the task, which every model already executes competently, intact.

## Conclusion

`regime-riskparity-cvar` is legitimately `hard`, and it is hard for a reason
worth keeping. Five models across three families reproduce Marchenko-Pastur
thresholding, absorption-ratio classification, inverse-volatility risk parity and
historical CVaR — and then fail on a one-observation boundary that separates a
tradeable backtest from an untradeable one.

That is a realistic failure. Look-ahead through an inclusive estimation window is
among the most common defects in production backtests, and it is invisible in the
output: the numbers look plausible, the Sharpe merely looks better than it should
(1.94 against the reference 1.43 — the models' portfolios appear to earn more with
less risk, which is exactly the signature of a leaked estimate).

Recommendation: leave the convention unstated.

## Note on stale artefacts

`tasks/regime-riskparity-cvar/oracle_logs/diagnostic.json` contains superseded
expected values (e.g. `annualized_return = 0.0615297` against the current
`0.0875373`). It is not used in grading, but it is committed and it misleads
anyone diagnosing the task by hand. Worth deleting.
