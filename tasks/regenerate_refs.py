#!/usr/bin/env python3
"""
Regenerate reference data for all 4 tasks using the `arch` library as
ground truth for GARCH(1,1) fitting.

Produces: expected.json, checkpoints.json, alt_paths.json for each task.
"""

import json
import math
import os
import sys

import numpy as np
import pandas as pd
from arch import arch_model
from scipy.optimize import brentq
from scipy.stats import norm

BASE = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════
# GARCH fitting via arch library
# ═══════════════════════════════════════════════════════════════════

def fit_garch_arch(returns):
    """Stable zero-mean Gaussian fit; report decimal-return-squared units.

    Use arch's default backcast and bounds. Independent starts reduce the
    chance that nominal optimizer convergence leaves a poor local solution.
    Boundary rolling fits have no finite long-run variance.
    """
    import warnings
    x = np.asarray(returns, dtype=float).ravel()
    y = 100.0 * x
    model = arch_model(y, vol='GARCH', p=1, q=1, mean='Zero',
                       dist='normal', rescale=False)
    scale = float(np.mean(y ** 2))
    starts = [None, [0.1 * scale, 0.1, 0.8], [0.01 * scale, 0.05, 0.94]]
    fits = []
    for start in starts:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            result = model.fit(disp='off', update_freq=0, starting_values=start,
                               options={'ftol': 1e-10, 'maxiter': 2000})
        if result.convergence_flag == 0 and np.isfinite(result.loglikelihood):
            fits.append(result)
    if not fits:
        raise RuntimeError('No converged GARCH fit')
    result = max(fits, key=lambda f: f.loglikelihood)
    omega = float(result.params['omega']) / 10000.0
    alpha = float(result.params['alpha[1]'])
    beta = float(result.params['beta[1]'])
    persistence = alpha + beta
    cond_var = np.asarray(result.conditional_volatility) ** 2 / 10000.0
    if not (omega > 0 and alpha >= 0 and beta >= 0 and persistence <= 1 + 1e-8
            and np.all(np.isfinite(cond_var)) and np.all(cond_var > 0)):
        raise RuntimeError('Invalid GARCH fit')
    return {
        'omega': omega, 'alpha': alpha, 'beta': beta,
        'persistence': persistence,
        'long_run_variance': omega / (1 - persistence) if persistence < 1 else None,
        'cond_var': cond_var,
        'h_next': omega + alpha * x[-1] ** 2 + beta * cond_var[-1],
        'loglikelihood': float(result.loglikelihood + len(x) * math.log(100)),
        'converged_starts': len(fits),
        'likelihood_spread': float(max(f.loglikelihood for f in fits)
                                   - min(f.loglikelihood for f in fits)),
    }


# ═══════════════════════════════════════════════════════════════════
# Barrier option pricing (Reiner-Rubinstein)
# ═══════════════════════════════════════════════════════════════════

def barrier_option_price(S, K, T, r, sigma, H, q=0.0):
    """Down-and-out call, Reiner-Rubinstein closed-form. B < K assumed."""
    if S <= H:
        return 0.0
    if sigma <= 0 or T <= 0:
        return 0.0

    sqrtT = math.sqrt(T)

    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    vanilla = (S * math.exp(-q * T) * norm.cdf(d1)
               - K * math.exp(-r * T) * norm.cdf(d2))

    lam = (r - q + 0.5 * sigma ** 2) / (sigma ** 2)
    ratio = H / S

    d1_h = (math.log(H ** 2 / (S * K)) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrtT)
    d2_h = d1_h - sigma * sqrtT

    c_di = (S * math.exp(-q * T) * (ratio ** (2 * lam)) * norm.cdf(d1_h)
            - K * math.exp(-r * T) * (ratio ** (2 * lam - 2)) * norm.cdf(d2_h))

    return max(vanilla - c_di, 0.0)


# ═══════════════════════════════════════════════════════════════════
# CTA strategy helpers
# ═══════════════════════════════════════════════════════════════════

def sma_seeded_ema(prices_col, span):
    """SMA-seeded EMA."""
    n = len(prices_col)
    out = np.full(n, np.nan)
    if n < span:
        return out
    alpha = 2.0 / (span + 1.0)
    out[span - 1] = np.mean(prices_col[:span])
    for t in range(span, n):
        out[t] = alpha * prices_col[t] + (1.0 - alpha) * out[t - 1]
    return out


def run_cta_strategy(prices, returns, fast_span, slow_span, vol_lookback,
                     vol_targets, max_lev, n_assets, rf_annual, annualization=252,
                     drop_warmup=False, geometric_return=False, ddof=1):
    """One price-date weight lag; a weighted-log-return strategy proxy.

    returns[k] ends on price date k+1. Targets[k], the EWMA[k], and the
    price-date k+1 signal form that close's weight, executed on return k+1.
    """
    signals = np.zeros_like(prices, dtype=float)
    for i in range(n_assets):
        fast = sma_seeded_ema(prices[:, i], fast_span)
        slow = sma_seeded_ema(prices[:, i], slow_span)
        valid = np.isfinite(fast) & np.isfinite(slow)
        signals[valid, i] = np.where(fast[valid] > slow[valid], 1.0, -1.0)
    a = 2.0 / (vol_lookback + 1)
    variance = np.empty_like(returns)
    variance[0] = returns[0] ** 2
    for k in range(1, len(returns)):
        variance[k] = a * returns[k] ** 2 + (1-a) * variance[k-1]
    targets = np.broadcast_to(np.asarray(vol_targets), (len(returns),))
    close_weights = signals[1:] * targets[:, None] / n_assets / np.sqrt(annualization * variance)
    close_weights = np.clip(close_weights, -max_lev, max_lev)
    positions = np.vstack([np.zeros(n_assets), close_weights[:-1]])
    x = np.sum(positions * returns, axis=1)
    if drop_warmup:
        x = x[slow_span-1:]
        positions = positions[slow_span-1:]
    log_return = float(annualization * np.mean(x))
    ann_return = float(np.expm1(log_return)) if geometric_return else log_return
    ann_vol = float(np.std(x, ddof=ddof) * math.sqrt(annualization))
    wealth = np.exp(np.r_[0.0, np.cumsum(x)])
    drawdown = float(np.max(1 - wealth / np.maximum.accumulate(wealth)))
    return {
        'annualized_return': ann_return, 'annualized_volatility': ann_vol,
        'sharpe_ratio': (log_return - rf_annual) / ann_vol,
        'max_drawdown': -drawdown if geometric_return else drawdown,
        'calmar_ratio': ann_return / drawdown,
        'avg_abs_leverage': float(np.mean(np.abs(positions).sum(axis=1))),
        'portfolio_returns': x,
    }


def garch_multistep_forecast(omega, alpha, beta, last_ret, last_h, holding_period):
    """Multi-step ahead variance forecasts."""
    forecasts = np.empty(holding_period)
    forecasts[0] = omega + alpha * last_ret ** 2 + beta * last_h
    ab = alpha + beta
    for k in range(1, holding_period):
        forecasts[k] = omega + ab * forecasts[k - 1]
    return forecasts, float(np.sum(forecasts))


# ═══════════════════════════════════════════════════════════════════
# Task 1: barrier-garch-var
# ═══════════════════════════════════════════════════════════════════

def _bgv_pipeline(S0, K, B, r, T, confidence_level, n_contracts,
                   garch_vol, omega, alpha, beta, persistence, long_run_variance,
                   vol_of_vol, fd_dS_pct=0.01, fd_dsigma=0.01):
    """Centered Gaussian quadratic moments; vol_of_vol is a DAILY change
    in the annualized volatility argument. Return normal-moment relative VaR.
    """
    def price(spot, vol):
        return barrier_option_price(spot, K, T, r, vol, B)
    value = price(S0, garch_vol)
    ds = fd_dS_pct * S0
    delta = (price(S0+ds, garch_vol) - price(S0-ds, garch_vol)) / (2*ds)
    gamma = (price(S0+ds, garch_vol) - 2*value + price(S0-ds, garch_vol)) / ds**2
    vega = (price(S0, garch_vol+fd_dsigma) - price(S0, garch_vol-fd_dsigma)) / (2*fd_dsigma)
    s2 = S0**2 * garch_vol**2 / 252
    components = np.array([delta**2*s2, 0.5*gamma**2*s2**2,
                           vega**2*vol_of_vol**2])
    values = dict(zip(['delta_var_pct', 'gamma_var_pct', 'vega_var_pct'],
                      100*components/components.sum()))
    values['portfolio_var'] = abs(n_contracts)*norm.ppf(confidence_level)*np.sqrt(components.sum())
    cp = {'garch_omega': omega, 'garch_alpha': alpha, 'garch_beta': beta,
          'garch_persistence': persistence, 'long_run_variance': long_run_variance,
          'garch_vol': garch_vol, 'analytical_price': value,
          'delta': delta, 'gamma': gamma, 'vega': vega}
    return values, cp


def regenerate_bgv():
    task = os.path.join(BASE, 'barrier-garch-var')
    with open(os.path.join(task, 'environment/data/params.json')) as f:
        p = json.load(f)
    x = pd.read_csv(os.path.join(task, 'environment/data/returns.csv')).log_return.to_numpy()
    fit = fit_garch_arch(x)
    if fit['long_run_variance'] is None:
        raise RuntimeError('Full-sample GARCH must be stationary')
    values, cp = _bgv_pipeline(**p, garch_vol=math.sqrt(252*fit['h_next']),
        omega=fit['omega'], alpha=fit['alpha'], beta=fit['beta'],
        persistence=fit['persistence'], long_run_variance=fit['long_run_variance'],
        vol_of_vol=float(np.std(np.diff(np.sqrt(252*fit['cond_var'])), ddof=1)))
    tolerances = {'portfolio_var': {'rtol': 0.002},
                  'delta_var_pct': {'atol': 0.05},
                  'gamma_var_pct': {'atol': 0.005},
                  'vega_var_pct': {'atol': 0.05}}
    cp_tol = {k: {'rtol': 0.002} for k in cp}
    cp_tol.update({k: {'rtol': 0.03} for k in ['garch_omega', 'garch_alpha']})
    cp_tol['long_run_variance'] = {'rtol': 0.01}
    _write_canonical_refs(task, values, cp, tolerances, cp_tol)
    return {'values': values, 'checkpoints': cp, 'fit': fit}


# ═══════════════════════════════════════════════════════════════════
# Task 2: structured-note-risk
# ═══════════════════════════════════════════════════════════════════

def _snr_pipeline(S0, K, B, r, T, notional, participation, garch_vol,
                   omega, alpha, beta, persistence, long_run_variance):
    """Run SNR pipeline from garch_vol onward. Returns deliverables + checkpoints."""
    bond_pv = notional * math.exp(-r * T)
    n_options = participation * notional / S0
    option_unit_price = barrier_option_price(S0, K, T, r, garch_vol, B)
    option_value = n_options * option_unit_price
    fair_value = bond_pv + option_value
    markup_pct = (notional - fair_value) / fair_value * 100.0

    def breakeven_obj(sigma_star):
        return bond_pv + n_options * barrier_option_price(S0, K, T, r, sigma_star, B) - notional
    try:
        breakeven_vol = brentq(breakeven_obj, 0.01, 3.0)
    except ValueError:
        breakeven_vol = float('nan')

    dS = 0.01 * S0
    price_up = barrier_option_price(S0 + dS, K, T, r, garch_vol, B)
    price_dn = barrier_option_price(S0 - dS, K, T, r, garch_vol, B)
    option_delta = (price_up - price_dn) / (2.0 * dS)
    note_delta = n_options * option_delta

    daily_vol = garch_vol / math.sqrt(252)
    z_99 = abs(norm.ppf(0.01))
    note_var_99 = z_99 * abs(note_delta) * S0 * daily_vol
    phi_z = norm.pdf(z_99)
    note_es_99 = abs(note_delta) * S0 * daily_vol * phi_z / 0.01

    deliverables = [
        {'name': 'fair_value', 'value': fair_value, 'path': 'results.json:fair_value', 'tolerance': {'rtol': 0.02, 'atol': 1.0}},
        {'name': 'markup_pct', 'value': markup_pct, 'path': 'results.json:markup_pct', 'tolerance': {'rtol': 0.05, 'atol': 0.5}},
        {'name': 'note_var_99', 'value': note_var_99, 'path': 'results.json:note_var_99', 'tolerance': {'rtol': 0.05, 'atol': 0.5}},
        {'name': 'note_es_99', 'value': note_es_99, 'path': 'results.json:note_es_99', 'tolerance': {'rtol': 0.05, 'atol': 0.5}},
        {'name': 'breakeven_vol', 'value': breakeven_vol, 'path': 'results.json:breakeven_vol', 'tolerance': {'rtol': 0.05, 'atol': 0.01}},
        {'name': 'garch_persistence', 'value': persistence, 'path': 'results.json:garch_persistence', 'tolerance': {'rtol': 0.02}},
        {'name': 'long_run_variance', 'value': long_run_variance, 'path': 'results.json:long_run_variance', 'tolerance': {'rtol': 0.1}},
        {'name': 'garch_vol', 'value': garch_vol, 'path': 'results.json:garch_vol', 'tolerance': {'rtol': 0.05}},
        {'name': 'bond_pv', 'value': bond_pv, 'path': 'results.json:bond_pv', 'tolerance': {'rtol': 0.001, 'atol': 0.1}},
        {'name': 'option_unit_price', 'value': option_unit_price, 'path': 'results.json:option_unit_price', 'tolerance': {'rtol': 0.02, 'atol': 0.1}},
        {'name': 'option_value', 'value': option_value, 'path': 'results.json:option_value', 'tolerance': {'rtol': 0.02, 'atol': 0.5}},
        {'name': 'n_options', 'value': n_options, 'path': 'results.json:n_options', 'tolerance': {'rtol': 0.001}},
        {'name': 'option_delta', 'value': option_delta, 'path': 'results.json:option_delta', 'tolerance': {'rtol': 0.02, 'atol': 0.01}},
        {'name': 'note_delta', 'value': note_delta, 'path': 'results.json:note_delta', 'tolerance': {'rtol': 0.02, 'atol': 0.1}},
    ]

    # Fix 2: Only 12 intermediates in checkpoints — deliverable-only entries removed
    # (fair_value, markup_pct, note_var_99, note_es_99, breakeven_vol are in results.json only)
    checkpoints = {
        'garch_omega': {'value': omega, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.15}, 'siblings': {}},
        'garch_alpha': {'value': alpha, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.15}, 'siblings': {}},
        'garch_beta': {'value': beta, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.05}, 'siblings': {}},
        'garch_persistence': {'value': persistence, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.02}, 'siblings': {}},
        'long_run_variance': {'value': long_run_variance, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.1}, 'siblings': {}},
        'garch_vol': {'value': garch_vol, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.05}, 'siblings': {}},
        'bond_pv': {'value': bond_pv, 'concept': '', 'domain': 'DV', 'tolerance': {'rtol': 0.001, 'atol': 0.1}, 'siblings': {}},
        'option_unit_price': {'value': option_unit_price, 'concept': 'dv.barrier_option', 'domain': 'DV', 'tolerance': {'rtol': 0.02, 'atol': 0.1}, 'siblings': {}},
        'option_value': {'value': option_value, 'concept': 'dv.barrier_option', 'domain': 'DV', 'tolerance': {'rtol': 0.02, 'atol': 0.5}, 'siblings': {}},
        'n_options': {'value': n_options, 'concept': '', 'domain': 'DV', 'tolerance': {'rtol': 0.001}, 'siblings': {}},
        'option_delta': {'value': option_delta, 'concept': 'dv.bsm_analytical', 'domain': 'DV', 'tolerance': {'rtol': 0.02, 'atol': 0.01}, 'siblings': {}},
        'note_delta': {'value': note_delta, 'concept': '', 'domain': 'DV', 'tolerance': {'rtol': 0.02, 'atol': 0.1}, 'siblings': {}},
    }

    return deliverables, checkpoints


def regenerate_snr():
    task_dir = os.path.join(BASE, 'structured-note-risk')
    data_dir = os.path.join(task_dir, 'environment', 'data')

    with open(os.path.join(data_dir, 'params.json')) as f:
        params = json.load(f)
    df = pd.read_csv(os.path.join(data_dir, 'returns.csv'))
    returns = df['log_return'].values

    notional = params['notional']
    S0 = params['S0']
    K = params['K']
    B = params['B']
    r = params['r']
    T = params['T']
    participation = params['participation']

    # Phase 1: GARCH
    fit = fit_garch_arch(returns)
    omega = fit['omega']
    alpha = fit['alpha']
    beta = fit['beta']
    persistence = fit['persistence']
    long_run_variance = fit['long_run_variance']
    if long_run_variance is None or not 0 <= persistence < 1:
        raise ValueError('Structured-note pricing requires a stationary GARCH fit.')
    cond_var_last = float(fit['cond_var'][-1])

    # Two vol variants
    vol_conditional = math.sqrt(cond_var_last * 252)
    vol_unconditional = math.sqrt(long_run_variance * 252)

    print(f"\n=== structured-note-risk ===")
    print(f"  omega={omega:.10e}, alpha={alpha:.6f}, beta={beta:.6f}")
    print(f"  persistence={persistence:.6f}, LRV={long_run_variance:.10e}")
    print(f"  vol_conditional={vol_conditional:.6f}, vol_unconditional={vol_unconditional:.6f}")

    common_args = dict(S0=S0, K=K, B=B, r=r, T=T, notional=notional,
                       participation=participation, omega=omega, alpha=alpha,
                       beta=beta, persistence=persistence, long_run_variance=long_run_variance)

    paths = []
    for vol_name, vol_val in [('conditional', vol_conditional), ('unconditional', vol_unconditional)]:
        is_primary = (vol_name == 'conditional')
        d, c = _snr_pipeline(garch_vol=vol_val, **common_args)
        for item in d:
            if item['name'] in c:
                assert item['value'] == c[item['name']]['value']
        paths.append({
            'name': 'primary' if is_primary else f'{vol_name}_vol',
            'description': f'vol={vol_name} ({"sqrt(cond_var[-1]*252)" if vol_name == "conditional" else "sqrt(LRV*252)"})',
            'primary': is_primary,
            'deliverables': d,
            'checkpoints': c,
        })
        if is_primary:
            print(f"  garch_vol={vol_val:.6f}")
            print(f"  bond_pv={c['bond_pv']['value']:.6f}, n_options={c['n_options']['value']:.6f}")
            print(f"  option_unit_price={c['option_unit_price']['value']:.6f}")
            print(f"  fair_value={d[0]['value']:.6f}, markup_pct={d[1]['value']:.6f}")
            print(f"  note_var_99={d[2]['value']:.6f}, note_es_99={d[3]['value']:.6f}")

    primary_d = paths[0]['deliverables']
    primary_c = paths[0]['checkpoints']
    write_refs_multipath(task_dir, paths, primary_d, primary_c,
                         'structured-note-risk', ['DV', 'VOL', 'RISK'])
    for filename in ('expected.json', 'checkpoints.json'):
        with open(os.path.join(task_dir, 'tests', 'reference_data', filename)) as f:
            _write_json(os.path.join(task_dir, 'solution', filename), json.load(f))


# ═══════════════════════════════════════════════════════════════════
# Task 3: cta-basel-capital (canonical strategy-risk capital proxy)
# ═══════════════════════════════════════════════════════════════════

def regenerate_cta():
    task = os.path.join(BASE, 'cta-basel-capital')
    with open(os.path.join(task, 'environment/data/params.json')) as f:
        p = json.load(f)
    prices = pd.read_csv(os.path.join(task, 'environment/data/prices.csv')).filter(like='asset_').to_numpy()
    returns = np.log(prices[1:]/prices[:-1])
    perf = run_cta_strategy(prices, returns, p['fast_ema'], p['slow_ema'],
        p['vol_lookback'], p['vol_target'], p['max_leverage_per_asset'],
        p['n_assets'], p['risk_free_annual'], drop_warmup=True)
    x = perf['portfolio_returns']
    fit = fit_garch_arch(x)
    if fit['long_run_variance'] is None:
        raise RuntimeError('Full-sample GARCH must be stationary')
    z_h = norm.ppf(p['confidence_level']) * math.sqrt(p['holding_period'])
    current = z_h * math.sqrt(fit['h_next'])
    rolling = []
    for end in range(250, len(x)+1):
        f = fit_garch_arch(x[end-250:end])
        rolling.append({'end': end, 'var': z_h*math.sqrt(f['h_next']),
                        'loglikelihood': f['loglikelihood'],
                        'converged_starts': f['converged_starts'],
                        'likelihood_spread': f['likelihood_spread']})
    stressed = max(w['var'] for w in rolling)
    mult = p['basel_multiplier']
    values = {'capital_charge': mult*(current+stressed), 'stressed_var': stressed,
              'var_component': mult*current, 'svar_component': mult*stressed}
    cp = {k: v for k, v in perf.items() if k != 'portfolio_returns'}
    cp.update({'garch_omega': fit['omega'], 'garch_alpha': fit['alpha'],
               'garch_beta': fit['beta'], 'garch_persistence': fit['persistence'],
               'long_run_variance': fit['long_run_variance'], 'var_99': current})
    cp_tol = {k: {'atol': 1e-5} for k in cp}
    cp_tol.update({k: {'rtol': 0.02} for k in ['garch_omega', 'garch_alpha',
                   'garch_beta', 'garch_persistence', 'long_run_variance']})
    cp_tol['var_99'] = {'rtol': 0.005}
    _write_canonical_refs(task, values, cp, {k: {'rtol': 0.005} for k in values}, cp_tol)
    return {'values': values, 'checkpoints': cp, 'fit': fit,
            'portfolio_returns': x, 'rolling_windows': rolling}


# ═══════════════════════════════════════════════════════════════════
# Task 4: regime-cta-vol-target (canonical hindsight comparison)
# ═══════════════════════════════════════════════════════════════════

def regenerate_regime():
    task = os.path.join(BASE, 'regime-cta-vol-target')
    with open(os.path.join(task, 'environment/data/params.json')) as f:
        p = json.load(f)
    prices = pd.read_csv(os.path.join(task, 'environment/data/prices.csv')).filter(like='asset_').to_numpy()
    returns = np.log(prices[1:]/prices[:-1])
    fits = [fit_garch_arch(returns[:, i]) for i in range(p['n_assets'])]
    if any(f['long_run_variance'] is None for f in fits):
        raise RuntimeError('Full-sample GARCH must be stationary')
    composite = np.sqrt(252*np.mean([f['cond_var'] for f in fits], axis=0))
    lo, hi = np.percentile(composite, [p['regime_lo_pct'], p['regime_hi_pct']])
    low, high = composite <= lo, composite >= hi
    scale = np.where(low, p['scale_low_vol'], np.where(high, p['scale_high_vol'], 1))
    def performance(target):
        return run_cta_strategy(prices, returns, p['fast_ema'], p['slow_ema'],
            p['vol_lookback'], target, p['max_leverage_per_asset'],
            p['n_assets'], p['risk_free_annual'], geometric_return=True, ddof=0)
    static = performance(p['vol_target'])
    dynamic = performance(p['vol_target']*scale)
    values = {'dynamic_sharpe_ratio': dynamic['sharpe_ratio'],
              'sharpe_improvement': dynamic['sharpe_ratio']-static['sharpe_ratio'],
              'regime_frac_high': float(high.mean()),
              'composite_vol_mean': float(composite.mean())}
    cp = {f'{prefix}_{key}': perf[key] for prefix, perf in [('static', static), ('dynamic', dynamic)]
          for key in ['annualized_return', 'annualized_volatility', 'max_drawdown', 'calmar_ratio']}
    cp.update({'static_sharpe_ratio': static['sharpe_ratio'],
               'avg_garch_persistence': float(np.mean([f['persistence'] for f in fits])),
               'avg_long_run_variance': float(np.mean([f['long_run_variance'] for f in fits])),
               'regime_frac_low': float(low.mean()), 'regime_frac_mid': float((~low & ~high).mean()),
               'regime_thresh_lo': float(lo), 'regime_thresh_hi': float(hi)})
    tol = {'dynamic_sharpe_ratio': {'atol': 0.002}, 'sharpe_improvement': {'atol': 0.002},
           'regime_frac_high': {'atol': 1e-5}, 'composite_vol_mean': {'rtol': 0.002}}
    cp_tol = {k: {'atol': 1e-5} for k in cp}
    cp_tol.update({k: {'rtol': 0.002} for k in cp if k.startswith('dynamic_') or k.startswith('regime_thresh')})
    cp_tol['dynamic_calmar_ratio'] = {'atol': 0.002}
    cp_tol['dynamic_max_drawdown'] = {'atol': 0.0005}
    cp_tol['avg_garch_persistence'] = {'rtol': 0.002}
    cp_tol['avg_long_run_variance'] = {'rtol': 0.01}
    _write_canonical_refs(task, values, cp, tol, cp_tol)
    return {'values': values, 'checkpoints': cp, 'fits': fits,
            'static_returns': static['portfolio_returns'],
            'dynamic_returns': dynamic['portfolio_returns'], 'composite': composite}


def _write_canonical_refs(task, values, cp, tolerances, cp_tolerances):
    """Synchronize the oracle and checker from a single computation.

    These three tasks have one explicitly specified convention. The empty
    alternative list routes grading to expected.json/checkpoints.json.
    """
    ref = os.path.join(task, 'tests/reference_data')
    with open(os.path.join(ref, 'expected.json')) as f:
        expected = json.load(f)
    with open(os.path.join(ref, 'checkpoints.json')) as f:
        checkpoints = json.load(f)
    with open(os.path.join(task, 'environment/data/params.json')) as f:
        expected['parameters'] = json.load(f)
    for d in expected['deliverables']:
        d['value'] = float(values[d['name']])
        d['tolerance'] = tolerances[d['name']]
    for name, entry in checkpoints['checkpoints'].items():
        entry['value'] = float(cp[name])
        entry['tolerance'] = cp_tolerances[name]
        entry['siblings'] = {}
    for folder in [ref, os.path.join(task, 'solution')]:
        _write_json(os.path.join(folder, 'expected.json'), expected)
        _write_json(os.path.join(folder, 'checkpoints.json'), checkpoints)
    _write_json(os.path.join(ref, 'alt_paths.json'), {'paths': []})


# ═══════════════════════════════════════════════════════════════════
# Output writers
# ═══════════════════════════════════════════════════════════════════

def write_refs(task_dir, deliverables, checkpoints, task_id, domains):
    """Write single-path reference data (BGV, SNR)."""
    ref_dir = os.path.join(task_dir, 'tests', 'reference_data')
    os.makedirs(ref_dir, exist_ok=True)

    expected = {
        'meta': {'seed': 42, 'tier': 3, 'domains': domains, 'task_id': task_id},
        'deliverables': deliverables,
    }
    _write_json(os.path.join(ref_dir, 'expected.json'), expected)

    chk = {'checkpoints': checkpoints}
    _write_json(os.path.join(ref_dir, 'checkpoints.json'), chk)

    # Single path alt_paths
    alt = {
        'paths': [{
            'name': 'primary',
            'description': 'arch library GARCH(1,1)',
            'primary': True,
            'deliverables': deliverables,
            'checkpoints': checkpoints,
        }]
    }
    _write_json(os.path.join(ref_dir, 'alt_paths.json'), alt)

    print(f"  -> Wrote {ref_dir}/{{expected,checkpoints,alt_paths}}.json")


def write_refs_multipath(task_dir, paths, primary_deliverables, primary_checkpoints,
                         task_id, domains):
    """Write multi-path reference data (CTA, Regime)."""
    ref_dir = os.path.join(task_dir, 'tests', 'reference_data')
    os.makedirs(ref_dir, exist_ok=True)

    expected = {
        'meta': {'seed': 42, 'tier': 3, 'domains': domains, 'task_id': task_id},
        'deliverables': primary_deliverables,
    }
    _write_json(os.path.join(ref_dir, 'expected.json'), expected)

    chk = {'checkpoints': primary_checkpoints}
    _write_json(os.path.join(ref_dir, 'checkpoints.json'), chk)

    alt = {'paths': paths}
    _write_json(os.path.join(ref_dir, 'alt_paths.json'), alt)

    print(f"  -> Wrote {ref_dir}/{{expected,checkpoints,alt_paths}}.json ({len(paths)} paths)")


def _write_json(path, data):
    """Write JSON, handling NaN."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, allow_nan=True)
    # Verify round-trip
    with open(path) as f:
        json.load(f)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("Regenerating reference data using arch library...")
    regenerate_bgv()
    regenerate_snr()
    regenerate_cta()
    regenerate_regime()
    print("\nDone. All reference data regenerated.")
