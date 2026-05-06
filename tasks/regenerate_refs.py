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
    """Fit GARCH(1,1) using the arch library.

    Args:
        returns: 1-D array of decimal log-returns

    Returns:
        dict with omega, alpha, beta (decimal scale), persistence,
        long_run_variance, conditional variance series (decimal scale)
    """
    returns_arr = np.asarray(returns, dtype=float).ravel()
    returns_pct = returns_arr * 100.0
    am = arch_model(returns_pct, vol='Garch', p=1, q=1, mean='Zero', dist='normal')
    res = am.fit(disp='off')

    omega = res.params['omega'] / 10000.0
    alpha = res.params['alpha[1]']
    beta = res.params['beta[1]']
    persistence = alpha + beta

    # Fallback to sample variance when IGARCH (persistence >= 1)
    if persistence < 1.0:
        long_run_var = omega / (1.0 - persistence)
    else:
        long_run_var = float(np.var(returns_arr, ddof=1))

    cond_var = (res.conditional_volatility ** 2) / 10000.0  # decimal scale

    return {
        'omega': float(omega),
        'alpha': float(alpha),
        'beta': float(beta),
        'persistence': float(persistence),
        'long_run_variance': float(long_run_var),
        'cond_var': np.asarray(cond_var),
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
                     vol_targets, max_lev, n_assets, rf_annual, annualization=252):
    """EMA-crossover CTA with vol-targeted sizing. Returns perf dict."""
    n_days_p = prices.shape[0]
    n_ret = returns.shape[0]

    signal = np.zeros((n_days_p, n_assets))
    for i in range(n_assets):
        ef = sma_seeded_ema(prices[:, i], fast_span)
        es = sma_seeded_ema(prices[:, i], slow_span)
        diff = ef - es
        valid = ~np.isnan(ef) & ~np.isnan(es)
        signal[valid, i] = np.sign(diff[valid])

    alpha_vol = 2.0 / (vol_lookback + 1)
    ewma_var = np.zeros((n_ret, n_assets))
    ewma_var[0] = returns[0] ** 2
    for t in range(1, n_ret):
        ewma_var[t] = alpha_vol * returns[t] ** 2 + (1.0 - alpha_vol) * ewma_var[t - 1]
    ann_vol_ts = np.sqrt(ewma_var * annualization)

    positions = np.zeros((n_ret, n_assets))
    for t in range(1, n_ret):
        sig = signal[t]
        av = ann_vol_ts[t - 1]
        safe_vol = np.where(av > 1e-10, av, 1e-10)
        vt = vol_targets[t] if hasattr(vol_targets, '__len__') else vol_targets
        pos = sig * (vt / safe_vol) * (1.0 / n_assets)
        pos = np.clip(pos, -max_lev, max_lev)
        positions[t] = pos

    portfolio_returns = np.sum(positions * returns, axis=1)

    daily_rf = rf_annual / annualization
    mean_ret = float(np.mean(portfolio_returns))
    std_ret = float(np.std(portfolio_returns, ddof=1))
    ann_ret = mean_ret * annualization
    ann_vol = std_ret * math.sqrt(annualization)
    sharpe = (mean_ret - daily_rf) / std_ret * math.sqrt(annualization) if std_ret > 0 else 0.0

    cum_wealth = np.exp(np.cumsum(portfolio_returns))
    running_max = np.maximum.accumulate(cum_wealth)
    dd = (running_max - cum_wealth) / running_max
    max_dd = float(np.max(dd))
    calmar = ann_ret / max_dd if max_dd > 0 else 0.0

    avg_abs_lev = float(np.mean(np.sum(np.abs(positions), axis=1)))

    return {
        'annualized_return': float(ann_ret),
        'annualized_volatility': float(ann_vol),
        'sharpe_ratio': float(sharpe),
        'max_drawdown': float(max_dd),
        'calmar_ratio': float(calmar),
        'avg_abs_leverage': float(avg_abs_lev),
        'portfolio_returns': portfolio_returns,
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
                   decomp_method='squared'):
    """Run BGV pipeline from garch_vol onward. Returns deliverables + checkpoints dicts.

    decomp_method: 'squared' (variance-based) or 'linear' (simple attribution)
    """
    sigma = garch_vol
    H = B
    analytical_price = barrier_option_price(S0, K, T, r, sigma, H)

    dS = 0.01 * S0
    price_up = barrier_option_price(S0 + dS, K, T, r, sigma, H)
    price_dn = barrier_option_price(S0 - dS, K, T, r, sigma, H)
    delta = (price_up - price_dn) / (2 * dS)
    gamma = (price_up - 2 * analytical_price + price_dn) / (dS ** 2)

    dsigma = 0.01
    price_sig_up = barrier_option_price(S0, K, T, r, sigma + dsigma, H)
    price_sig_dn = barrier_option_price(S0, K, T, r, max(sigma - dsigma, 1e-6), H)
    vega = (price_sig_up - price_sig_dn) / (2 * dsigma)

    z = abs(norm.ppf(1.0 - confidence_level))
    daily_vol = garch_vol / math.sqrt(252)
    delta_S_vol = S0 * daily_vol
    vol_of_vol = 0.10 * garch_vol

    delta_var = abs(n_contracts * delta * z * delta_S_vol)
    gamma_var = 0.5 * abs(n_contracts * gamma * (z * delta_S_vol) ** 2)
    vega_var = abs(n_contracts * vega * z * vol_of_vol)

    if decomp_method == 'squared':
        portfolio_var = math.sqrt(delta_var ** 2 + gamma_var ** 2 + vega_var ** 2)
        total_sq = delta_var ** 2 + gamma_var ** 2 + vega_var ** 2
        if total_sq > 0:
            delta_var_pct = delta_var ** 2 / total_sq * 100.0
            gamma_var_pct = gamma_var ** 2 / total_sq * 100.0
            vega_var_pct = vega_var ** 2 / total_sq * 100.0
        else:
            delta_var_pct = gamma_var_pct = vega_var_pct = 0.0
    else:  # linear
        portfolio_var = delta_var + gamma_var + vega_var
        total_lin = delta_var + gamma_var + vega_var
        if total_lin > 0:
            delta_var_pct = delta_var / total_lin * 100.0
            gamma_var_pct = gamma_var / total_lin * 100.0
            vega_var_pct = vega_var / total_lin * 100.0
        else:
            delta_var_pct = gamma_var_pct = vega_var_pct = 0.0

    deliverables = [
        {'name': 'portfolio_var', 'value': portfolio_var, 'path': 'results.json:portfolio_var', 'tolerance': {'rtol': 0.05, 'atol': 0.1}},
        {'name': 'delta_var_pct', 'value': delta_var_pct, 'path': 'results.json:delta_var_pct', 'tolerance': {'rtol': 0.05, 'atol': 1.0}},
        {'name': 'gamma_var_pct', 'value': gamma_var_pct, 'path': 'results.json:gamma_var_pct', 'tolerance': {'rtol': 0.1, 'atol': 1.0}},
        {'name': 'vega_var_pct', 'value': vega_var_pct, 'path': 'results.json:vega_var_pct', 'tolerance': {'rtol': 0.1, 'atol': 1.0}},
    ]

    checkpoints = {
        'garch_omega': {'value': omega, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.15}, 'siblings': {}},
        'garch_alpha': {'value': alpha, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.15}, 'siblings': {}},
        'garch_beta': {'value': beta, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.05}, 'siblings': {}},
        'garch_persistence': {'value': persistence, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.1}, 'siblings': {}},
        'long_run_variance': {'value': long_run_variance, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.1}, 'siblings': {}},
        'garch_vol': {'value': garch_vol, 'concept': 'vol.garch', 'domain': 'DV', 'tolerance': {'rtol': 0.05}, 'siblings': {}},
        'analytical_price': {'value': analytical_price, 'concept': 'dv.barrier_option', 'domain': 'DV', 'tolerance': {'rtol': 0.02, 'atol': 0.1}, 'siblings': {}},
        'delta': {'value': delta, 'concept': 'dv.bsm_analytical', 'domain': 'DV', 'tolerance': {'rtol': 0.02, 'atol': 0.01}, 'siblings': {}},
        'gamma': {'value': gamma, 'concept': 'dv.bsm_analytical', 'domain': 'DV', 'tolerance': {'rtol': 0.05, 'atol': 0.001}, 'siblings': {}},
        'vega': {'value': vega, 'concept': 'dv.bsm_analytical', 'domain': 'DV', 'tolerance': {'rtol': 0.05, 'atol': 0.01}, 'siblings': {}},
    }

    return deliverables, checkpoints


def regenerate_bgv():
    task_dir = os.path.join(BASE, 'barrier-garch-var')
    data_dir = os.path.join(task_dir, 'environment', 'data')

    with open(os.path.join(data_dir, 'params.json')) as f:
        params = json.load(f)
    df = pd.read_csv(os.path.join(data_dir, 'returns.csv'))
    returns = df['log_return'].values

    S0 = params['S0']
    K = params['K']
    B = params['B']
    r = params['r']
    T = params['T']
    confidence_level = params['confidence_level']
    n_contracts = params['n_contracts']

    # Phase 1: GARCH
    fit = fit_garch_arch(returns)
    omega = fit['omega']
    alpha = fit['alpha']
    beta = fit['beta']
    persistence = fit['persistence']
    long_run_variance = fit['long_run_variance']
    cond_var_last = float(fit['cond_var'][-1])

    # Two vol variants
    vol_conditional = math.sqrt(cond_var_last * 252)
    vol_unconditional = math.sqrt(long_run_variance * 252)

    print(f"\n=== barrier-garch-var ===")
    print(f"  omega={omega:.10e}, alpha={alpha:.6f}, beta={beta:.6f}")
    print(f"  persistence={persistence:.6f}, LRV={long_run_variance:.10e}")
    print(f"  vol_conditional={vol_conditional:.6f}, vol_unconditional={vol_unconditional:.6f}")

    # Build 4 paths: (conditional × squared) + (conditional × linear) + (unconditional × squared) + (unconditional × linear)
    common_args = dict(S0=S0, K=K, B=B, r=r, T=T, confidence_level=confidence_level,
                       n_contracts=n_contracts, omega=omega, alpha=alpha, beta=beta,
                       persistence=persistence, long_run_variance=long_run_variance)

    paths = []
    for vol_name, vol_val in [('conditional', vol_conditional), ('unconditional', vol_unconditional)]:
        for decomp in ['squared', 'linear']:
            path_name = f'{vol_name}_{decomp}'
            is_primary = (vol_name == 'conditional' and decomp == 'squared')
            d, c = _bgv_pipeline(garch_vol=vol_val, decomp_method=decomp, **common_args)
            paths.append({
                'name': 'primary' if is_primary else path_name,
                'description': f'vol={vol_name} ({"sqrt(cond_var[-1]*252)" if vol_name == "conditional" else "sqrt(LRV*252)"}), decomp={decomp}',
                'primary': is_primary,
                'deliverables': d,
                'checkpoints': c,
            })
            if is_primary:
                print(f"  garch_vol={vol_val:.6f}")
                print(f"  analytical_price={c['analytical_price']['value']:.6f}")
                print(f"  delta={c['delta']['value']:.6f}, gamma={c['gamma']['value']:.6f}, vega={c['vega']['value']:.6f}")
                print(f"  portfolio_var={d[0]['value']:.6f}")
                print(f"  delta_var_pct={d[1]['value']:.2f}, gamma_var_pct={d[2]['value']:.2f}, vega_var_pct={d[3]['value']:.2f}")

    # Primary = first path (conditional × squared)
    primary_d = paths[0]['deliverables']
    primary_c = paths[0]['checkpoints']
    write_refs_multipath(task_dir, paths, primary_d, primary_c,
                         'barrier-garch-var', ['DV', 'VOL', 'RISK'])


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
    note_es_99 = note_var_99 * phi_z / 0.01

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


# ═══════════════════════════════════════════════════════════════════
# Task 3: cta-basel-capital (4 paths: ann×ret)
# ═══════════════════════════════════════════════════════════════════

def regenerate_cta():
    task_dir = os.path.join(BASE, 'cta-basel-capital')
    data_dir = os.path.join(task_dir, 'environment', 'data')

    with open(os.path.join(data_dir, 'params.json')) as f:
        params = json.load(f)
    prices_df = pd.read_csv(os.path.join(data_dir, 'prices.csv'))
    asset_cols = [c for c in prices_df.columns if c != 'date']
    prices = prices_df[asset_cols].values

    fast_ema = int(params['fast_ema'])
    slow_ema = int(params['slow_ema'])
    vol_lookback = int(params['vol_lookback'])
    vol_target = float(params['vol_target'])
    max_lev = float(params['max_leverage_per_asset'])
    rf_annual = float(params['risk_free_annual'])
    n_assets = int(params['n_assets'])
    conf = float(params['confidence_level'])
    holding_period = int(params['holding_period'])
    multiplier = float(params['basel_multiplier'])

    combos = [
        {'annualization': 252, 'return_type': 'log'},
        {'annualization': 252, 'return_type': 'arithmetic'},
        {'annualization': 260, 'return_type': 'log'},
        {'annualization': 260, 'return_type': 'arithmetic'},
    ]

    paths = []
    primary_deliverables = None
    primary_checkpoints = None

    for idx, combo in enumerate(combos):
        ann = combo['annualization']
        ret_type = combo['return_type']
        is_primary = (ann == 252 and ret_type == 'log')

        # Compute returns
        if ret_type == 'log':
            returns = np.log(prices[1:] / prices[:-1])
        else:
            returns = (prices[1:] - prices[:-1]) / prices[:-1]
        n_ret = len(returns)

        # CTA strategy
        static_targets = np.full(n_ret, vol_target)
        perf = run_cta_strategy(
            prices, returns, fast_ema, slow_ema, vol_lookback,
            static_targets, max_lev, n_assets, rf_annual, annualization=ann,
        )
        portfolio_returns = perf['portfolio_returns']

        # GARCH on portfolio returns
        fit = fit_garch_arch(portfolio_returns)
        omega = fit['omega']
        alpha_g = fit['alpha']
        beta_g = fit['beta']
        persistence = fit['persistence']
        long_run_var = fit['long_run_variance']
        cond_var = fit['cond_var']

        last_h = float(cond_var[-1])
        last_ret = float(portfolio_returns[-1])

        z_val = abs(float(norm.ppf(1.0 - conf)))

        _, cum_var_normal = garch_multistep_forecast(
            omega, alpha_g, beta_g, last_ret, last_h, holding_period
        )
        var_99 = z_val * math.sqrt(cum_var_normal)

        H_FACTOR = 1.5
        stressed_base_var = max(last_h, H_FACTOR * long_run_var)
        _, cum_var_stressed = garch_multistep_forecast(
            omega, alpha_g, beta_g, last_ret, stressed_base_var, holding_period
        )
        svar_99 = z_val * math.sqrt(cum_var_stressed)

        var_component = multiplier * abs(var_99)
        svar_component = multiplier * abs(svar_99)
        capital_charge = var_component + svar_component

        path_name = 'primary' if is_primary else f'ann{ann}_{ret_type}'
        desc = f'annualization={ann}, return_type={ret_type}'

        if is_primary:
            print(f"\n=== cta-basel-capital (primary: {desc}) ===")
            print(f"  omega={omega:.10e}, alpha={alpha_g:.6f}, beta={beta_g:.6f}")
            print(f"  persistence={persistence:.6f}, LRV={long_run_var:.10e}")
            print(f"  ann_ret={perf['annualized_return']:.6f}, ann_vol={perf['annualized_volatility']:.6f}")
            print(f"  sharpe={perf['sharpe_ratio']:.6f}")
            print(f"  var_99={var_99:.6f}, svar_99={svar_99:.6f}")
            print(f"  capital_charge={capital_charge:.6f}")

        path_deliverables = [
            {'name': 'capital_charge', 'value': capital_charge, 'path': 'results.json:capital_charge', 'tolerance': {'rtol': 0.05, 'atol': 0.01}},
            {'name': 'stressed_var', 'value': svar_99, 'path': 'results.json:stressed_var', 'tolerance': {'rtol': 0.05, 'atol': 0.005}},
            {'name': 'var_component', 'value': var_component, 'path': 'results.json:var_component', 'tolerance': {'rtol': 0.05, 'atol': 0.01}},
            {'name': 'svar_component', 'value': svar_component, 'path': 'results.json:svar_component', 'tolerance': {'rtol': 0.05, 'atol': 0.01}},
        ]

        path_checkpoints = {
            'annualized_return': {'value': perf['annualized_return'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.15, 'atol': 0.005}, 'siblings': {}},
            'annualized_volatility': {'value': perf['annualized_volatility'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.15, 'atol': 0.005}, 'siblings': {}},
            'sharpe_ratio': {'value': perf['sharpe_ratio'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.20, 'atol': 0.02}, 'siblings': {}},
            'max_drawdown': {'value': perf['max_drawdown'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.10, 'atol': perf['max_drawdown'] * 1.1}, 'siblings': {}},
            'calmar_ratio': {'value': perf['calmar_ratio'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.25, 'atol': 0.02}, 'siblings': {}},
            'avg_abs_leverage': {'value': perf['avg_abs_leverage'], 'concept': '', 'domain': 'PM', 'tolerance': {'rtol': 0.20, 'atol': 0.01}, 'siblings': {}},
            'garch_omega': {'value': omega, 'concept': 'vol.garch', 'domain': 'PM', 'tolerance': {'rtol': 0.15}, 'siblings': {}},
            'garch_alpha': {'value': alpha_g, 'concept': 'vol.garch', 'domain': 'PM', 'tolerance': {'rtol': 0.15}, 'siblings': {}},
            'garch_beta': {'value': beta_g, 'concept': 'vol.garch', 'domain': 'PM', 'tolerance': {'rtol': 0.05}, 'siblings': {}},
            'garch_persistence': {'value': persistence, 'concept': 'vol.garch', 'domain': 'PM', 'tolerance': {'rtol': 0.1}, 'siblings': {}},
            'long_run_variance': {'value': long_run_var, 'concept': 'vol.garch', 'domain': 'PM', 'tolerance': {'rtol': 0.1}, 'siblings': {}},
            'var_99': {'value': var_99, 'concept': 'risk.var', 'domain': 'PM', 'tolerance': {'rtol': 0.05, 'atol': 0.005}, 'siblings': {}},
        }

        path_entry = {
            'name': path_name,
            'description': desc,
            'primary': is_primary,
            'deliverables': path_deliverables,
            'checkpoints': path_checkpoints,
        }
        paths.append(path_entry)

        if is_primary:
            primary_deliverables = path_deliverables
            primary_checkpoints = path_checkpoints

    write_refs_multipath(task_dir, paths, primary_deliverables, primary_checkpoints,
                         'cta-basel-capital', ['PM', 'VOL', 'RISK', 'BK'])


# ═══════════════════════════════════════════════════════════════════
# Task 4: regime-cta-vol-target (4 paths: ann×ret)
# ═══════════════════════════════════════════════════════════════════

def regenerate_regime():
    task_dir = os.path.join(BASE, 'regime-cta-vol-target')
    data_dir = os.path.join(task_dir, 'environment', 'data')

    with open(os.path.join(data_dir, 'params.json')) as f:
        params = json.load(f)
    prices_df = pd.read_csv(os.path.join(data_dir, 'prices.csv'))
    asset_cols = [c for c in prices_df.columns if c.startswith('asset_')]
    prices = prices_df[asset_cols].values

    fast_span = params['fast_ema']
    slow_span = params['slow_ema']
    vol_lookback = params['vol_lookback']
    vol_target_base = params['vol_target']
    max_lev = params['max_leverage_per_asset']
    rf_annual = params['risk_free_annual']
    n_assets = params['n_assets']
    regime_lo_pct = params['regime_lo_pct']
    regime_hi_pct = params['regime_hi_pct']
    scale_low = params['scale_low_vol']
    scale_high = params['scale_high_vol']

    combos = [
        {'annualization': 252, 'return_type': 'log'},
        {'annualization': 252, 'return_type': 'arithmetic'},
        {'annualization': 260, 'return_type': 'log'},
        {'annualization': 260, 'return_type': 'arithmetic'},
    ]

    paths = []
    primary_deliverables = None
    primary_checkpoints = None

    for idx, combo in enumerate(combos):
        ann = combo['annualization']
        ret_type = combo['return_type']
        is_primary = (ann == 252 and ret_type == 'log')

        # Compute returns
        if ret_type == 'log':
            returns = np.log(prices[1:] / prices[:-1])
        else:
            returns = (prices[1:] - prices[:-1]) / prices[:-1]
        n_ret = returns.shape[0]

        # Phase 1: GARCH per asset
        per_asset_cond_var = np.zeros((n_ret, n_assets))
        garch_persistences = []
        garch_long_run_vars = []

        for i in range(n_assets):
            asset_returns = returns[:, i]
            fit = fit_garch_arch(asset_returns)
            garch_persistences.append(fit['persistence'])
            garch_long_run_vars.append(fit['long_run_variance'])

            per_asset_cond_var[:, i] = fit['cond_var']

        avg_garch_persistence = float(np.mean(garch_persistences))
        avg_long_run_variance = float(np.mean(garch_long_run_vars))

        # Phase 2: Composite vol + regime classification
        composite_var = np.mean(per_asset_cond_var, axis=1)
        composite_vol = np.sqrt(composite_var * ann)
        composite_vol_mean = float(np.mean(composite_vol))

        thresh_lo = float(np.percentile(composite_vol, regime_lo_pct))
        thresh_hi = float(np.percentile(composite_vol, regime_hi_pct))

        regime_labels = np.ones(n_ret, dtype=int)
        regime_labels[composite_vol <= thresh_lo] = 0
        regime_labels[composite_vol >= thresh_hi] = 2

        regime_frac_low = float(np.mean(regime_labels == 0))
        regime_frac_mid = float(np.mean(regime_labels == 1))
        regime_frac_high = float(np.mean(regime_labels == 2))

        # Dynamic vol targets
        dynamic_vol_targets = np.full(n_ret, vol_target_base)
        dynamic_vol_targets[regime_labels == 0] = vol_target_base * scale_low
        dynamic_vol_targets[regime_labels == 2] = vol_target_base * scale_high

        # Phase 3: CTA ×2
        static_targets = np.full(n_ret, vol_target_base)

        static_result = run_cta_strategy(
            prices, returns, fast_span, slow_span, vol_lookback,
            static_targets, max_lev, n_assets, rf_annual, annualization=ann,
        )
        dynamic_result = run_cta_strategy(
            prices, returns, fast_span, slow_span, vol_lookback,
            dynamic_vol_targets, max_lev, n_assets, rf_annual, annualization=ann,
        )

        sharpe_improvement = dynamic_result['sharpe_ratio'] - static_result['sharpe_ratio']

        path_name = 'primary' if is_primary else f'ann{ann}_{ret_type}'
        desc = f'annualization={ann}, return_type={ret_type}'

        if is_primary:
            print(f"\n=== regime-cta-vol-target (primary: {desc}) ===")
            print(f"  avg_garch_persistence={avg_garch_persistence:.6f}")
            print(f"  avg_long_run_variance={avg_long_run_variance:.10e}")
            print(f"  composite_vol_mean={composite_vol_mean:.6f}")
            print(f"  regime_frac: low={regime_frac_low:.4f} mid={regime_frac_mid:.4f} high={regime_frac_high:.4f}")
            print(f"  static_sharpe={static_result['sharpe_ratio']:.6f}")
            print(f"  dynamic_sharpe={dynamic_result['sharpe_ratio']:.6f}")
            print(f"  sharpe_improvement={sharpe_improvement:.6f}")

        path_deliverables = [
            {'name': 'dynamic_sharpe_ratio', 'value': dynamic_result['sharpe_ratio'], 'path': 'results.json:dynamic_sharpe_ratio', 'tolerance': {'rtol': 0.05, 'atol': 0.02}},
            {'name': 'sharpe_improvement', 'value': sharpe_improvement, 'path': 'results.json:sharpe_improvement', 'tolerance': {'rtol': 0.1, 'atol': 0.02}},
            {'name': 'regime_frac_high', 'value': regime_frac_high, 'path': 'results.json:regime_frac_high', 'tolerance': {'rtol': 0.05, 'atol': 0.01}},
            {'name': 'composite_vol_mean', 'value': composite_vol_mean, 'path': 'results.json:composite_vol_mean', 'tolerance': {'rtol': 0.05, 'atol': 0.005}},
        ]

        path_checkpoints = {
            'static_annualized_return': {'value': static_result['annualized_return'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.15, 'atol': 0.005}, 'siblings': {}},
            'static_annualized_volatility': {'value': static_result['annualized_volatility'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.15, 'atol': 0.005}, 'siblings': {}},
            'static_sharpe_ratio': {'value': static_result['sharpe_ratio'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.20, 'atol': 0.02}, 'siblings': {}},
            'static_max_drawdown': {'value': static_result['max_drawdown'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.10, 'atol': static_result['max_drawdown'] * 1.1}, 'siblings': {}},
            'static_calmar_ratio': {'value': static_result['calmar_ratio'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.25, 'atol': 0.02}, 'siblings': {}},
            'dynamic_annualized_return': {'value': dynamic_result['annualized_return'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.15, 'atol': 0.005}, 'siblings': {}},
            'dynamic_annualized_volatility': {'value': dynamic_result['annualized_volatility'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.15, 'atol': 0.005}, 'siblings': {}},
            'dynamic_max_drawdown': {'value': dynamic_result['max_drawdown'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.10, 'atol': dynamic_result['max_drawdown'] * 1.1}, 'siblings': {}},
            'dynamic_calmar_ratio': {'value': dynamic_result['calmar_ratio'], 'concept': 'pm.performance_metrics', 'domain': 'PM', 'tolerance': {'rtol': 0.25, 'atol': 0.02}, 'siblings': {}},
            'avg_garch_persistence': {'value': avg_garch_persistence, 'concept': 'vol.garch', 'domain': 'PM', 'tolerance': {'rtol': 0.05}, 'siblings': {}},
            'avg_long_run_variance': {'value': avg_long_run_variance, 'concept': 'vol.garch', 'domain': 'PM', 'tolerance': {'rtol': 0.1}, 'siblings': {}},
            'regime_frac_low': {'value': regime_frac_low, 'concept': '', 'domain': 'PM', 'tolerance': {'rtol': 0.05, 'atol': 0.01}, 'siblings': {}},
            'regime_frac_mid': {'value': regime_frac_mid, 'concept': '', 'domain': 'PM', 'tolerance': {'rtol': 0.05, 'atol': 0.01}, 'siblings': {}},
            'regime_thresh_lo': {'value': thresh_lo, 'concept': '', 'domain': 'PM', 'tolerance': {'rtol': 0.05, 'atol': 0.005}, 'siblings': {}},
            'regime_thresh_hi': {'value': thresh_hi, 'concept': '', 'domain': 'PM', 'tolerance': {'rtol': 0.05, 'atol': 0.005}, 'siblings': {}},
        }

        path_entry = {
            'name': path_name,
            'description': desc,
            'primary': is_primary,
            'deliverables': path_deliverables,
            'checkpoints': path_checkpoints,
        }
        paths.append(path_entry)

        if is_primary:
            primary_deliverables = path_deliverables
            primary_checkpoints = path_checkpoints

    write_refs_multipath(task_dir, paths, primary_deliverables, primary_checkpoints,
                         'regime-cta-vol-target', ['PM', 'VOL'])


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
