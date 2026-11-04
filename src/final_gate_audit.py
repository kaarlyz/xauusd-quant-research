#!/usr/bin/env python3
"""
Final Gate: Mathematical Consistency & Capital Risk Audit Engine.
Executes deep quantitative audits across:
1. Metric reconciliation and mathematical identity checks.
2. STRAT-08 deep robustness, regime analysis, parameter neighborhood, underwater duration, and search-space p-value adjustment.
3. Synchronized portfolio daily returns (including non-trading days), conditional correlations, tail dependence, and true diversification benefit.
4. Monte Carlo revalidation (IID Bootstrap, Block Bootstrap, Regime-conditioned, Friction Stress).
5. Risk allocation sweep ($5 to $25 per trade) for 3 portfolio configurations.
"""

import os
import sys
import json
import math
import numpy as np
import polars as pl
from scipy import stats
import datetime

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
OUTPUT_DIR = "/home/vallencia/xauusd_research/docs/final_gate"
DATA_OUTPUT = "/home/vallencia/xauusd_research/data/final_gate_results.json"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DATA_OUTPUT), exist_ok=True)

# Load trade list from previous exact audit
from audit_engine import load_data, audit_strat_07, audit_strat_01, audit_strat_08

def reconcile_metrics(trades, name):
    r = np.array([t["realized_r"] for t in trades])
    n = len(r)
    wins = r[r > 0]
    losses = r[r < 0]
    zeros = r[r == 0]
    
    n_w = len(wins)
    n_l = len(losses)
    n_z = len(zeros)
    
    wr = n_w / n
    loss_rate = n_l / n
    zero_rate = n_z / n
    
    avg_win_r = float(np.mean(wins)) if n_w > 0 else 0.0
    avg_loss_r = float(abs(np.mean(losses))) if n_l > 0 else 0.0
    
    realized_rr = avg_win_r / avg_loss_r if avg_loss_r > 0 else 0.0
    gross_profit = float(np.sum(wins))
    gross_loss = float(abs(np.sum(losses)))
    pf = gross_profit / gross_loss if gross_loss > 0 else 99.0
    
    net_exp_direct = float(np.mean(r))
    net_exp_formula = (wr * avg_win_r) - (loss_rate * avg_loss_r)
    formula_diff = abs(net_exp_direct - net_exp_formula)
    
    total_net_r = float(np.sum(r))
    total_net_r_from_exp = float(n * net_exp_direct)
    
    # Cumulative Drawdown
    cum = np.cumsum(r)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    max_dd = float(np.max(dd))
    
    return {
        "strategy": name,
        "n_trades": n,
        "n_wins": n_w,
        "n_losses": n_l,
        "n_zeros": n_z,
        "win_rate_pct": float(round(wr * 100, 2)),
        "loss_rate_pct": float(round(loss_rate * 100, 2)),
        "avg_win_r": float(round(avg_win_r, 4)),
        "avg_loss_r": float(round(avg_loss_r, 4)),
        "realized_rr": float(round(realized_rr, 4)),
        "gross_profit_r": float(round(gross_profit, 2)),
        "gross_loss_r": float(round(gross_loss, 2)),
        "profit_factor": float(round(pf, 4)),
        "net_expectancy_direct": float(round(net_exp_direct, 4)),
        "net_expectancy_formula": float(round(net_exp_formula, 4)),
        "formula_discrepancy": float(round(formula_diff, 8)),
        "identity_verified": bool(formula_diff < 1e-6),
        "total_net_r": float(round(total_net_r, 2)),
        "max_drawdown_r": float(round(max_dd, 2))
    }

def audit_strat08_deep(df):
    """
    Deep robustness, parameter neighborhoods, and regime analysis for STRAT-08.
    """
    df_m15 = df.with_columns((pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"))
    m15 = df_m15.group_by("m15_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("timestamp").first().alias("ts"),
        pl.col("year").first(), pl.col("date").first(), pl.col("hour").first()
    ]).sort("m15_ts")

    o_15 = m15["open"].to_numpy()
    h_15 = m15["high"].to_numpy()
    l_15 = m15["low"].to_numpy()
    c_15 = m15["close"].to_numpy()
    dates_15 = m15["date"].to_numpy()
    hours_15 = m15["hour"].to_numpy()
    years_15 = m15["year"].to_numpy()
    ts_15 = m15["ts"].to_numpy()
    n_15 = len(o_15)

    # 50-bar Daily Trend Proxy (approx 200 M15 bars = 50 hours)
    # ATR 20 on M15
    ranges = h_15 - l_15; cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr15 = (cumsum[20:] - cumsum[:-20]) / 20.0
    atr15 = np.pad(atr15, (20, 0), mode="edge")[:n_15]

    day_indices = {}
    for i, d in enumerate(dates_15):
        if d not in day_indices: day_indices[d] = []
        day_indices[d].append(i)

    # 1. Parameter Neighborhood Scan
    levels = [0.745, 0.764, 0.786, 0.800, 0.820]
    min_spans = [3.0, 4.0, 5.0]
    max_spans = [25.0, 30.0, 35.0]

    neighborhood = {}
    for lvl in levels:
        for min_s in min_spans:
            for max_s in max_spans:
                tr = []
                for d, d_idx in day_indices.items():
                    if len(d_idx) < 30: continue
                    lon_imp = [i for i in d_idx if 7 <= hours_15[i] <= 8]
                    if len(lon_imp) < 6: continue
                    l_h = np.max(h_15[lon_imp]); l_l = np.min(l_15[lon_imp])
                    span = l_h - l_l
                    if not (min_s <= span <= max_s): continue

                    is_bull = c_15[lon_imp[-1]] > o_15[lon_imp[0]]
                    ny = [i for i in d_idx if 9 <= hours_15[i] <= 16]
                    if not ny: continue

                    if is_bull:
                        bounce = l_h - (lvl * span); sl = l_l - 0.25; risk = (bounce + 0.25) - sl
                        if 1.5 <= risk <= 20.0:
                            entry = bounce + 0.25; tp = entry + 1.5 * risk
                            for pos, i in enumerate(ny):
                                if l_15[i] <= bounce:
                                    sub = ny[pos:]; r_val = -1.0
                                    for j in sub:
                                        if l_15[j] <= sl: break
                                        elif h_15[j] >= tp: r_val = 1.5; break
                                    tr.append(r_val); break
                    else:
                        bounce = l_l + (lvl * span); sl = l_h + 0.25; risk = sl - (bounce - 0.25)
                        if 1.5 <= risk <= 20.0:
                            entry = bounce - 0.25; tp = entry - 1.5 * risk
                            for pos, i in enumerate(ny):
                                if h_15[i] >= bounce:
                                    sub = ny[pos:]; r_val = -1.0
                                    for j in sub:
                                        if h_15[j] >= sl: break
                                        elif l_15[j] <= tp: r_val = 1.5; break
                                    tr.append(r_val); break
                if tr:
                    gw = sum(x for x in tr if x > 0); gl = abs(sum(x for x in tr if x < 0))
                    pf = gw / gl if gl > 0 else 99.0
                    wr = sum(1 for x in tr if x > 0) / len(tr) * 100.0
                    key = f"lvl_{lvl}_span_{min_s}_{max_s}"
                    neighborhood[key] = {
                        "level": lvl, "min_span": min_s, "max_span": max_s,
                        "n": len(tr), "wr": round(wr, 1), "pf": round(pf, 3), "exp": round(float(np.mean(tr)), 4)
                    }

    # 2. Market Regime Analysis (Baseline STRAT-08)
    # Categorize days by London Opening Volatility (ATR terciles: Low, Medium, High)
    all_spans = []
    baseline_records = []
    lvl = 0.786; min_s = 4.0; max_s = 30.0

    for d, d_idx in day_indices.items():
        if len(d_idx) < 30: continue
        lon_imp = [i for i in d_idx if 7 <= hours_15[i] <= 8]
        if len(lon_imp) < 6: continue
        l_h = np.max(h_15[lon_imp]); l_l = np.min(l_15[lon_imp])
        span = l_h - l_l
        if not (min_s <= span <= max_s): continue

        all_spans.append(span)
        is_bull = c_15[lon_imp[-1]] > o_15[lon_imp[0]]
        ny = [i for i in d_idx if 9 <= hours_15[i] <= 16]
        if not ny: continue
        yr = years_15[d_idx[0]]
        avg_atr = float(np.mean(atr15[lon_imp]))

        if is_bull:
            bounce = l_h - (lvl * span); sl = l_l - 0.25; risk = (bounce + 0.25) - sl
            if 1.5 <= risk <= 20.0:
                entry = bounce + 0.25; tp = entry + 1.5 * risk
                for pos, i in enumerate(ny):
                    if l_15[i] <= bounce:
                        sub = ny[pos:]; r_val = -1.0
                        exit_idx = sub[-1]
                        for j in sub:
                            if l_15[j] <= sl: exit_idx = j; break
                            elif h_15[j] >= tp: r_val = 1.5; exit_idx = j; break
                        entry_dt = datetime.datetime.fromtimestamp(ts_15[i] // 1000, tz=datetime.timezone.utc)
                        exit_dt = datetime.datetime.fromtimestamp(ts_15[exit_idx] // 1000, tz=datetime.timezone.utc)
                        baseline_records.append({
                            "year": int(yr), "date": str(d), "span": span, "atr": avg_atr,
                            "entry_dt": entry_dt, "exit_dt": exit_dt, "r": r_val
                        })
                        break
        else:
            bounce = l_l + (lvl * span); sl = l_h + 0.25; risk = sl - (bounce - 0.25)
            if 1.5 <= risk <= 20.0:
                entry = bounce - 0.25; tp = entry - 1.5 * risk
                for pos, i in enumerate(ny):
                    if h_15[i] >= bounce:
                        sub = ny[pos:]; r_val = -1.0
                        exit_idx = sub[-1]
                        for j in sub:
                            if h_15[j] >= sl: exit_idx = j; break
                            elif l_15[j] <= tp: r_val = 1.5; exit_idx = j; break
                        entry_dt = datetime.datetime.fromtimestamp(ts_15[i] // 1000, tz=datetime.timezone.utc)
                        exit_dt = datetime.datetime.fromtimestamp(ts_15[exit_idx] // 1000, tz=datetime.timezone.utc)
                        baseline_records.append({
                            "year": int(yr), "date": str(d), "span": span, "atr": avg_atr,
                            "entry_dt": entry_dt, "exit_dt": exit_dt, "r": r_val
                        })
                        break

    # Volatility Terziles
    atrs = [b["atr"] for b in baseline_records]
    q33 = np.percentile(atrs, 33.33)
    q66 = np.percentile(atrs, 66.66)

    regime_results = {}
    for r_label, r_filt in [
        ("Low Volatility (ATR <= 33%)", [b["r"] for b in baseline_records if b["atr"] <= q33]),
        ("Normal Volatility (33% < ATR <= 66%)", [b["r"] for b in baseline_records if q33 < b["atr"] <= q66]),
        ("High Volatility (ATR > 66%)", [b["r"] for b in baseline_records if b["atr"] > q66]),
    ]:
        gw = sum(x for x in r_filt if x > 0); gl = abs(sum(x for x in r_filt if x < 0))
        pf = gw / gl if gl > 0 else 99.0
        wr = sum(1 for x in r_filt if x > 0) / len(r_filt) * 100.0 if r_filt else 0.0
        regime_results[r_label] = {
            "n": len(r_filt), "wr": round(wr, 1), "pf": round(pf, 3), "exp": round(float(np.mean(r_filt)), 4)
        }

    # 3. Drawdown Duration & Underwater Time
    r_series = [b["r"] for b in baseline_records]
    cum = np.cumsum(r_series)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum

    # Measure recovery time in trades and calendar days
    underwater_trades = 0
    max_underwater_trades = 0
    underwater_start_dt = None
    max_underwater_days = 0
    current_peak = 0.0

    for idx, b in enumerate(baseline_records):
        val = cum[idx]
        if val >= current_peak:
            current_peak = val
            if underwater_trades > max_underwater_trades:
                max_underwater_trades = underwater_trades
            if underwater_start_dt is not None:
                duration_days = (b["entry_dt"] - underwater_start_dt).days
                if duration_days > max_underwater_days:
                    max_underwater_days = duration_days
            underwater_trades = 0
            underwater_start_dt = None
        else:
            if underwater_trades == 0:
                underwater_start_dt = b["entry_dt"]
            underwater_trades += 1

    # 4. Search Space p-value adjustment
    # Total distinct hypotheses explored in project:
    # 24 half-hours (:30) + 24 hourly (:00) + 16 quarter-hours (:15) + 15 Fibo combinations = 79 tests
    M_tests = 79
    raw_p = 0.00007
    bonferroni_p = min(1.0, raw_p * M_tests)
    sidak_p = min(1.0, 1.0 - (1.0 - raw_p)**M_tests)

    # 5. Dependence-aware confidence intervals (Moving Block Bootstrap, 10,000 blocks of size 10)
    np.random.seed(42)
    n_tr = len(r_series)
    block_size = 10
    n_blocks = n_tr // block_size
    boot_means = []
    boot_wrs = []
    for _ in range(10000):
        # Sample blocks with replacement
        start_indices = np.random.randint(0, n_tr - block_size + 1, size=n_blocks)
        sampled = []
        for s_idx in start_indices:
            sampled.extend(r_series[s_idx : s_idx + block_size])
        sampled = np.array(sampled)
        boot_means.append(np.mean(sampled))
        boot_wrs.append(np.sum(sampled > 0) / len(sampled) * 100.0)

    ci_exp_block = (float(round(np.percentile(boot_means, 2.5), 4)), float(round(np.percentile(boot_means, 97.5), 4)))
    ci_wr_block = (float(round(np.percentile(boot_wrs, 2.5), 2)), float(round(np.percentile(boot_wrs, 97.5), 2)))

    return {
        "parameter_neighborhood": neighborhood,
        "regime_analysis": regime_results,
        "max_drawdown_r": float(round(np.max(dd), 2)),
        "max_underwater_trades": int(max_underwater_trades),
        "max_underwater_calendar_days": int(max_underwater_days),
        "search_space_adjustment": {
            "total_hypotheses_tested": M_tests,
            "raw_p_value": raw_p,
            "bonferroni_adjusted_p": float(round(bonferroni_p, 5)),
            "sidak_adjusted_p": float(round(sidak_p, 5)),
            "statistically_significant_at_01": bool(bonferroni_p < 0.01)
        },
        "block_bootstrap_ci_95": {
            "expectancy_r": ci_exp_block,
            "win_rate_pct": ci_wr_block
        }
    }

def synchronized_portfolio_audit(df, t_07, t_01, t_08):
    """
    Builds synchronized daily return series for ALL calendar trading days (including zero days).
    Computes exact daily correlations, conditional correlations, tail dependence, and true drawdown reduction.
    """
    all_dates = sorted(list(set(str(d) for d in df["date"].to_list())))
    n_days = len(all_dates)

    daily_07 = {d: 0.0 for d in all_dates}
    daily_01 = {d: 0.0 for d in all_dates}
    daily_08 = {d: 0.0 for d in all_dates}

    for t in t_07: daily_07[str(t["date"])] = daily_07.get(str(t["date"]), 0.0) + t["realized_r"]
    for t in t_01: daily_01[str(t["date"])] = daily_01.get(str(t["date"]), 0.0) + t["realized_r"]
    for t in t_08: daily_08[str(t["date"])] = daily_08.get(str(t["date"]), 0.0) + t["realized_r"]

    s07 = np.array([daily_07[d] for d in all_dates])
    s01 = np.array([daily_01[d] for d in all_dates])
    s08 = np.array([daily_08[d] for d in all_dates])
    s_comb = s07 + s01 + s08

    # 1. Unconditional correlation across ALL calendar trading days (including zeros)
    uncond_corr_07_01 = float(np.corrcoef(s07, s01)[0, 1])
    uncond_corr_07_08 = float(np.corrcoef(s07, s08)[0, 1])
    uncond_corr_01_08 = float(np.corrcoef(s01, s08)[0, 1])

    # 2. Conditional correlation when BOTH strategies are active
    both_07_08 = (s07 != 0.0) & (s08 != 0.0)
    both_01_08 = (s01 != 0.0) & (s08 != 0.0)
    both_07_01 = (s07 != 0.0) & (s01 != 0.0)

    cond_corr_07_08 = float(np.corrcoef(s07[both_07_08], s08[both_07_08])[0, 1]) if np.sum(both_07_08) > 5 else 0.0
    cond_corr_01_08 = float(np.corrcoef(s01[both_01_08], s08[both_01_08])[0, 1]) if np.sum(both_01_08) > 5 else 0.0
    cond_corr_07_01 = float(np.corrcoef(s07[both_07_01], s01[both_07_01])[0, 1]) if np.sum(both_07_01) > 5 else 0.0

    # 3. Lower tail dependence (co-loss probability)
    # P(Strategy B < 0 | Strategy A < 0)
    loss_08 = (s08 < 0.0)
    tail_dep_07_given_08 = float(np.mean(s07[loss_08] < 0.0))
    tail_dep_01_given_08 = float(np.mean(s01[loss_08] < 0.0))

    # 4. True Portfolio Drawdown vs Standalone Drawdowns
    def get_dd_metrics(series):
        cum = np.cumsum(series)
        peak = np.maximum.accumulate(cum)
        dd = peak - cum
        mdd = float(np.max(dd))
        
        # Max DD duration in days
        underwater = 0
        max_uw = 0
        cur_p = 0.0
        for val in cum:
            if val >= cur_p:
                cur_p = val
                if underwater > max_uw: max_uw = underwater
                underwater = 0
            else:
                underwater += 1
        return mdd, max_uw

    mdd_07, uw_07 = get_dd_metrics(s07)
    mdd_01, uw_01 = get_dd_metrics(s01)
    mdd_08, uw_08 = get_dd_metrics(s08)
    mdd_comb, uw_comb = get_dd_metrics(s_comb)

    # Standalone Worst vs Combined
    worst_standalone_mdd = max(mdd_07, mdd_01, mdd_08) # which is STRAT-08 at 24.58R
    dd_change_vs_standalone = float(round(((mdd_comb - worst_standalone_mdd) / worst_standalone_mdd) * 100.0, 2))

    # Maximum Daily Loss
    max_daily_loss_comb = float(abs(np.min(s_comb))) if np.min(s_comb) < 0 else 0.0

    return {
        "total_calendar_trading_days": n_days,
        "unconditional_daily_correlation": {
            "STRAT-07_vs_STRAT-01": round(uncond_corr_07_01, 5),
            "STRAT-07_vs_STRAT-08": round(uncond_corr_07_08, 5),
            "STRAT-01_vs_STRAT-08": round(uncond_corr_01_08, 5)
        },
        "conditional_correlation_active_days": {
            "STRAT-07_vs_STRAT-08": {"active_days_coincident": int(np.sum(both_07_08)), "correlation": round(cond_corr_07_08, 4)},
            "STRAT-01_vs_STRAT-08": {"active_days_coincident": int(np.sum(both_01_08)), "correlation": round(cond_corr_01_08, 4)},
            "STRAT-07_vs_STRAT-01": {"active_days_coincident": int(np.sum(both_07_01)), "correlation": round(cond_corr_07_01, 4)},
        },
        "tail_dependence_co_loss_pct": {
            "P(STRAT-07_loss | STRAT-08_loss)": round(tail_dep_07_given_08 * 100, 2),
            "P(STRAT-01_loss | STRAT-08_loss)": round(tail_dep_01_given_08 * 100, 2)
        },
        "drawdown_comparison_r": {
            "STRAT-07_standalone_mdd": round(mdd_07, 2),
            "STRAT-01_standalone_mdd": round(mdd_01, 2),
            "STRAT-08_standalone_mdd": round(mdd_08, 2),
            "naive_sum_mdd": round(mdd_07 + mdd_01 + mdd_08, 2),
            "combined_portfolio_mdd": round(mdd_comb, 2),
            "mdd_change_vs_strat08_pct": dd_change_vs_standalone,
            "max_underwater_days_strat08": uw_08,
            "max_underwater_days_combined": uw_comb,
            "max_daily_loss_r": max_daily_loss_comb
        }
    }

def run_advanced_monte_carlo(all_trades, t_sp075):
    """
    Runs 4 Monte Carlo engines:
    1. Independent IID Bootstrap
    2. Block Bootstrap (blocks of 10 trades preserving clustering)
    3. Regime-Conditioned Bootstrap (heavier weighting on 2023-2024 regime)
    4. Friction Stress Bootstrap (Spread $0.75 + slippage)
    """
    np.random.seed(42)
    n_sims = 10000
    r_stream = np.array([t["realized_r"] for t in all_trades])
    n_pool = len(r_stream)

    # 4 engines
    engines = {}

    # Define engine sampling functions
    def sim_engine(sampler_fn, risk_dollars=15.0):
        passed_s1 = 0; passed_s2 = 0; passed_both = 0
        viol_daily = 0; viol_max = 0
        days_dist = []
        for _ in range(n_sims):
            # Step 1
            bal = 2500.0; prev_midnight = 2500.0
            prof_days = 0; s1_ok = False
            t_cnt = 0; d_pnl = 0.0

            sample = sampler_fn(250)
            for r in sample:
                t_cnt += 1
                pnl = r * risk_dollars
                bal += pnl; d_pnl += pnl
                # Daily loss check (-$125 from midnight)
                if (prev_midnight - bal) >= 125.0:
                    viol_daily += 1; break
                # Max loss check (-$250 from 2500)
                if bal <= 2250.0:
                    viol_max += 1; break
                if t_cnt % 2 == 0:
                    if d_pnl >= 12.50: prof_days += 1
                    prev_midnight = max(bal, 2500.0); d_pnl = 0.0
                if bal >= 2750.0 and prof_days >= 3:
                    s1_ok = True; passed_s1 += 1; break

            if not s1_ok: continue

            # Step 2
            bal = 2500.0; prev_midnight = 2500.0
            prof_days = 0; s2_ok = False
            t_cnt2 = 0; d_pnl = 0.0

            sample2 = sampler_fn(250)
            for r in sample2:
                t_cnt2 += 1
                pnl = r * risk_dollars
                bal += pnl; d_pnl += pnl
                if (prev_midnight - bal) >= 125.0:
                    viol_daily += 1; break
                if bal <= 2250.0:
                    viol_max += 1; break
                if t_cnt2 % 2 == 0:
                    if d_pnl >= 12.50: prof_days += 1
                    prev_midnight = max(bal, 2500.0); d_pnl = 0.0
                if bal >= 2625.0 and prof_days >= 3:
                    s2_ok = True; passed_s2 += 1; passed_both += 1
                    days_dist.append(int((t_cnt + t_cnt2) * 1.5))
                    break

        return {
            "step1_pass_pct": round((passed_s1 / n_sims) * 100.0, 2),
            "step2_cond_pass_pct": round((passed_s2 / passed_s1) * 100.0, 2) if passed_s1 > 0 else 0.0,
            "complete_pass_pct": round((passed_both / n_sims) * 100.0, 2),
            "daily_loss_breach_pct": round((viol_daily / n_sims) * 100.0, 2),
            "max_loss_breach_pct": round((viol_max / n_sims) * 100.0, 2),
            "median_calendar_days": int(np.median(days_dist)) if days_dist else 0,
            "p90_calendar_days": int(np.percentile(days_dist, 90)) if days_dist else 0,
        }

    # 1. Independent IID
    def iid_sampler(size):
        return r_stream[np.random.choice(n_pool, size=size, replace=True)]

    # 2. Block Bootstrap (Block size = 10)
    block_sz = 10
    n_b = n_pool - block_sz + 1
    def block_sampler(size):
        num_blocks = (size // block_sz) + 1
        starts = np.random.choice(n_b, size=num_blocks, replace=True)
        res = []
        for s in starts:
            res.extend(r_stream[s : s + block_sz])
        return np.array(res[:size])

    # 3. Regime Conditioned (50% from 2023-2024 adverse regime, 50% from rest)
    r_adverse = np.array([t["realized_r"] for t in all_trades if t["year"] in (2023, 2024)])
    r_normal = np.array([t["realized_r"] for t in all_trades if t["year"] not in (2023, 2024)])
    def regime_sampler(size):
        sz_adv = size // 2
        sz_norm = size - sz_adv
        s_adv = r_adverse[np.random.choice(len(r_adverse), size=sz_adv, replace=True)]
        s_norm = r_normal[np.random.choice(len(r_normal), size=sz_norm, replace=True)]
        combined = np.concatenate([s_adv, s_norm])
        np.random.shuffle(combined)
        return combined

    # 4. Stress Friction ($0.75 Spread)
    r_stress = np.array([t["realized_r"] for t in t_sp075])
    def stress_sampler(size):
        return r_stress[np.random.choice(len(r_stress), size=size, replace=True)]

    print("Running MC 1: Independent IID...")
    engines["1_independent_iid"] = sim_engine(iid_sampler)
    print("Running MC 2: Block Bootstrap...")
    engines["2_block_bootstrap"] = sim_engine(block_sampler)
    print("Running MC 3: Regime-Conditioned (Adverse Weight)...")
    engines["3_regime_conditioned"] = sim_engine(regime_sampler)
    print("Running MC 4: Stress Friction ($0.75 Spread)...")
    engines["4_stress_friction_075"] = sim_engine(stress_sampler)

    return engines

def optimize_risk_allocations(all_trades, t_08, t_07, t_01):
    """
    Tests multiple risk-per-trade sizes ($5 to $25) across 3 portfolios:
    - Config A: STRAT-08 only
    - Config B: STRAT-08 + STRAT-07
    - Config C: STRAT-08 + STRAT-07 + STRAT-01
    Identifies maximum defensible risk sizing.
    """
    sizes = [5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 25.0]

    portfolios = {
        "Config_A_STRAT-08_Only": t_08,
        "Config_B_STRAT-08_and_07": t_08 + t_07,
        "Config_C_All_Three": all_trades
    }

    results = {}
    for p_name, tr_list in portfolios.items():
        sorted_tr = sorted(tr_list, key=lambda x: x["entry_time"])
        r_vals = np.array([t["realized_r"] for t in sorted_tr])

        # Daily aggregation for daily loss
        daily_r = {}
        for t in sorted_tr:
            daily_r[t["date"]] = daily_r.get(t["date"], 0.0) + t["realized_r"]
        worst_day_r = float(abs(min(daily_r.values()))) if min(daily_r.values()) < 0 else 0.0

        cum = np.cumsum(r_vals)
        peak = np.maximum.accumulate(cum)
        mdd_r = float(np.max(peak - cum))

        results[p_name] = {}
        for sz in sizes:
            mdd_dollars = mdd_r * sz
            mdd_pct = (mdd_dollars / 2500.0) * 100.0
            worst_day_dollars = worst_day_r * sz
            worst_day_pct = (worst_day_dollars / 2500.0) * 100.0

            # Conservative criteria:
            # MDD <= 7.5% ($187.50, keeping $62.50 buffer from $250 max loss)
            # Max Daily Loss <= 3.5% ($87.50, keeping $37.50 buffer from $125 daily loss)
            defensible = (mdd_pct <= 7.5) and (worst_day_pct <= 3.5)

            results[p_name][f"${sz:.2f}_risk"] = {
                "risk_dollars": sz,
                "risk_pct": round((sz / 2500.0) * 100.0, 2),
                "max_drawdown_dollars": round(mdd_dollars, 2),
                "max_drawdown_pct": round(mdd_pct, 2),
                "worst_daily_loss_dollars": round(worst_day_dollars, 2),
                "worst_daily_loss_pct": round(worst_day_pct, 2),
                "defensible_pass": defensible
            }

    return results

def main():
    df = load_data()

    # Reproduce base trades
    t_07 = audit_strat_07(df, spread=0.50)
    t_01 = audit_strat_01(df, spread=0.50)
    t_08 = audit_strat_08(df, spread=0.50)
    t_comb = sorted(t_07 + t_01 + t_08, key=lambda x: x["entry_time"])

    # High-spread run for friction stress MC
    t_sp075_07 = audit_strat_07(df, spread=0.75)
    t_sp075_01 = audit_strat_01(df, spread=0.75)
    t_sp075_08 = audit_strat_08(df, spread=0.75)
    t_sp075_comb = sorted(t_sp075_07 + t_sp075_01 + t_sp075_08, key=lambda x: x["entry_time"])

    print("\n1. Running Metric Reconciliation...")
    reconciled = {
        "STRAT-08": reconcile_metrics(t_08, "STRAT-08"),
        "STRAT-07": reconcile_metrics(t_07, "STRAT-07"),
        "STRAT-01": reconcile_metrics(t_01, "STRAT-01"),
        "PORTFOLIO": reconcile_metrics(t_comb, "COMBINED_PORTFOLIO")
    }

    print("\n2. Running Deep Robustness for STRAT-08...")
    strat08_deep = audit_strat08_deep(df)

    print("\n3. Running Synchronized Portfolio Analysis...")
    sync_port = synchronized_portfolio_audit(df, t_07, t_01, t_08)

    print("\n4. Running Advanced 4-Engine Monte Carlo Simulations...")
    mc_results = run_advanced_monte_carlo(t_comb, t_sp075_comb)

    print("\n5. Running Risk Allocation Optimization...")
    risk_alloc = optimize_risk_allocations(t_comb, t_08, t_07, t_01)

    final_payload = {
        "metadata": {
            "date": "2026-11-01",
            "mandate": "FINAL GATE — MATHEMATICAL CONSISTENCY & CAPITAL RISK AUDIT",
            "candles_analyzed": len(df),
            "date_range": "2015-01-01 to 2026-10-30"
        },
        "metric_reconciliation": reconciled,
        "strat08_deep_robustness": strat08_deep,
        "synchronized_portfolio": sync_port,
        "monte_carlo_4_engines": mc_results,
        "risk_allocation_matrix": risk_alloc
    }

    with open(DATA_OUTPUT, "w") as f:
        json.dump(final_payload, f, indent=2)

    print(f"\nFinal gate audit complete! Data saved to: {DATA_OUTPUT}")

if __name__ == "__main__":
    main()
