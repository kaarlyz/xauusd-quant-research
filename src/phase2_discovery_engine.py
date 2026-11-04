#!/usr/bin/env python3
"""
Phase 2: High-Frequency Strategy Discovery Engine.
Runs all 32 pre-registered variants (H1: 8, H2: 8, H3: 8, H4: 8).
Evaluates strictly across:
- Partition 1: In-Sample Discovery (2021-08-23 to 2024-08-21 UTC, 3 Years).
- Partition 2: Walk-Forward Validation (2024-08-22 to 2025-08-21 UTC, 1 Year).
- Partition 3 (Blind Holdout: 2025-08-22 to 2026-08-21) remains STRICTLY SEALED.

Outputs:
- /home/vallencia/xauusd_research/PHASE_2_EXPERIMENT_LOG.csv
- /home/vallencia/xauusd_research/data/phase2_discovery_results.json
"""

import os
import csv
import json
import datetime
import numpy as np
import polars as pl
from scipy import stats

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
LOG_CSV = "/home/vallencia/xauusd_research/PHASE_2_EXPERIMENT_LOG.csv"
JSON_OUT = "/home/vallencia/xauusd_research/data/phase2_discovery_results.json"

# Invariants from Phase 1B/1C
SPREAD_BASELINE = 0.380 # Observed median London/NY spread
COMMISSION_ROUND = 0.070 # $7.00 per lot
SLIPPAGE_MARKET = 0.050 # 0.5 tick
RISK_BUDGET = 7.50

# Partition timestamps (ms)
T_IS_START = int(datetime.datetime(2021, 8, 23, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_IS_END = int(datetime.datetime(2024, 8, 21, 23, 59, 59, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_VAL_START = int(datetime.datetime(2024, 8, 22, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_VAL_END = int(datetime.datetime(2025, 8, 21, 23, 59, 59, tzinfo=datetime.timezone.utc).timestamp() * 1000)

def load_data():
    print("Loading Master M1 dataset...")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
    )
    # Exclude 21:00 - 23:00 UTC rollover
    df = df.filter(~pl.col("hour").is_between(21, 23))
    # Filter strictly up to end of Validation (Partition 2) to KEEP HOLDOUT SEALED!
    df = df.filter(pl.col("timestamp") <= T_VAL_END)
    return df

def run_backtest_vectorized(o, h, l, c, v, hours, dates, ts, n, candidate_fn, params):
    """
    Executes a candidate strategy across bars, respecting execution specification.
    """
    trades = []
    signals = candidate_fn(o, h, l, c, v, hours, n, params)
    
    # signals is list of tuples: (bar_idx, direction, nominal_sl, nominal_tp, max_holding_bars, is_limit, limit_price)
    holding_bars = params["holding_bars"]
    target_rr = params["target_rr"]

    last_exit_idx = -1

    for sig in signals:
        i, direction, nominal_sl, is_limit, limit_price = sig
        if i <= last_exit_idx:
            continue
        if i + holding_bars >= n:
            continue

        exec_bar = i + 1
        trade_ts = ts[exec_bar]
        date_str = str(dates[exec_bar])

        # Partition tag
        if trade_ts < T_IS_START:
            continue
        elif trade_ts <= T_IS_END:
            partition = "IN_SAMPLE"
        elif trade_ts <= T_VAL_END:
            partition = "VALIDATION"
        else:
            continue # Holdout sealed

        # Execution pricing
        if direction == "LONG":
            if is_limit:
                # 1-pip penetration rule
                if l[exec_bar] > limit_price - 0.10:
                    continue # Non-fill
                entry_fill = limit_price
            else:
                entry_fill = o[exec_bar] + SPREAD_BASELINE + SLIPPAGE_MARKET

            stop_dist = entry_fill - nominal_sl
            if stop_dist < 0.50 or stop_dist > 15.0:
                continue

            lots = RISK_BUDGET / (stop_dist * 100.0)
            tp_price = entry_fill + (target_rr * stop_dist)

            # Intrabar resolution forward
            exit_fill = c[exec_bar + holding_bars]
            exit_reason = "TIMEOUT"
            is_ambiguous = False
            exit_idx = exec_bar + holding_bars

            for b in range(exec_bar, exec_bar + holding_bars + 1):
                hit_sl = (l[b] <= nominal_sl)
                hit_tp = (h[b] >= tp_price)

                if hit_sl and hit_tp:
                    is_ambiguous = True
                    exit_fill = nominal_sl - SLIPPAGE_MARKET
                    exit_reason = "AMBIGUOUS_STOP"
                    exit_idx = b
                    break
                elif hit_sl:
                    exit_fill = nominal_sl - SLIPPAGE_MARKET
                    exit_reason = "SL"
                    exit_idx = b
                    break
                elif hit_tp:
                    exit_fill = tp_price
                    exit_reason = "TP"
                    exit_idx = b
                    break

            gross_pnl = (exit_fill - entry_fill) * lots * 100.0
            comm = COMMISSION_ROUND * lots * 100.0
            net_pnl = gross_pnl - comm
            realized_r = net_pnl / RISK_BUDGET
            last_exit_idx = exit_idx

            trades.append({
                "partition": partition,
                "direction": "LONG",
                "date": date_str,
                "entry_price": entry_fill,
                "exit_price": exit_fill,
                "exit_reason": exit_reason,
                "is_ambiguous": is_ambiguous,
                "gross_pnl": gross_pnl,
                "comm": comm,
                "net_pnl": net_pnl,
                "realized_r": realized_r,
                "holding_time_mins": (exit_idx - exec_bar) + 1
            })

        else: # SHORT
            if is_limit:
                if h[exec_bar] < limit_price + 0.10:
                    continue
                entry_fill = limit_price
            else:
                entry_fill = o[exec_bar] - SLIPPAGE_MARKET

            stop_dist = nominal_sl - entry_fill
            if stop_dist < 0.50 or stop_dist > 15.0:
                continue

            lots = RISK_BUDGET / (stop_dist * 100.0)
            tp_price = entry_fill - (target_rr * stop_dist)

            exit_fill = c[exec_bar + holding_bars] + SPREAD_BASELINE
            exit_reason = "TIMEOUT"
            is_ambiguous = False
            exit_idx = exec_bar + holding_bars

            for b in range(exec_bar, exec_bar + holding_bars + 1):
                # Short stops evaluated on Ask (Bid + Spread)
                hit_sl = (h[b] + SPREAD_BASELINE >= nominal_sl)
                hit_tp = (l[b] + SPREAD_BASELINE <= tp_price)

                if hit_sl and hit_tp:
                    is_ambiguous = True
                    exit_fill = nominal_sl + SLIPPAGE_MARKET
                    exit_reason = "AMBIGUOUS_STOP"
                    exit_idx = b
                    break
                elif hit_sl:
                    exit_fill = nominal_sl + SLIPPAGE_MARKET
                    exit_reason = "SL"
                    exit_idx = b
                    break
                elif hit_tp:
                    exit_fill = tp_price
                    exit_reason = "TP"
                    exit_idx = b
                    break

            gross_pnl = (entry_fill - exit_fill) * lots * 100.0
            comm = COMMISSION_ROUND * lots * 100.0
            net_pnl = gross_pnl - comm
            realized_r = net_pnl / RISK_BUDGET
            last_exit_idx = exit_idx

            trades.append({
                "partition": partition,
                "direction": "SHORT",
                "date": date_str,
                "entry_price": entry_fill,
                "exit_price": exit_fill,
                "exit_reason": exit_reason,
                "is_ambiguous": is_ambiguous,
                "gross_pnl": gross_pnl,
                "comm": comm,
                "net_pnl": net_pnl,
                "realized_r": realized_r,
                "holding_time_mins": (exit_idx - exec_bar) + 1
            })

    return trades

# -----------------------------------------------------------------------------
# CANDIDATE LOGIC DEFINITIONS (H1, H2, H3, H4)
# -----------------------------------------------------------------------------
def get_atr(h, l, c, period=14):
    n = len(h)
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)), np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    cumsum = np.cumsum(np.insert(tr, 0, 0))
    atr = (cumsum[period:] - cumsum[:-period]) / float(period)
    return np.pad(atr, (period, 0), mode="edge")[:n]

def evaluate_h1(o, h, l, c, v, hours, n, p):
    # Liquidity Sweep & Reclaim
    lookback = p["lookback"]
    wick_ratio_req = p["wick_ratio"]
    atr = get_atr(h, l, c, 14)
    signals = []

    for i in range(lookback + 5, n - 35):
        cur_atr = atr[i]
        if cur_atr < 0.3: continue
        rng = h[i] - l[i]
        if rng < 0.05: continue

        # Swings in lookback window
        h_pivot = np.max(h[i - lookback : i])
        l_pivot = np.min(l[i - lookback : i])

        # Long: Sweep of Lows
        if l[i] <= l_pivot - (0.50 * cur_atr) and c[i] >= l_pivot:
            lower_wick = min(o[i], c[i]) - l[i]
            if (lower_wick / rng) >= wick_ratio_req:
                nominal_sl = l[i] - 0.30
                signals.append((i, "LONG", nominal_sl, False, 0.0))

        # Short: Sweep of Highs
        elif h[i] >= h_pivot + (0.50 * cur_atr) and c[i] <= h_pivot:
            upper_wick = h[i] - max(o[i], c[i])
            if (upper_wick / rng) >= wick_ratio_req:
                nominal_sl = h[i] + 0.30
                signals.append((i, "SHORT", nominal_sl, False, 0.0))

    return signals

def evaluate_h2(o, h, l, c, v, hours, n, p):
    # Intraday Mean Reversion
    z_req = p["z_score"]
    rsi_low, rsi_high = p["rsi_bounds"]
    atr = get_atr(h, l, c, 14)
    
    # 20-period rolling mean and std
    cumsum_c = np.cumsum(np.insert(c, 0, 0))
    raw_mean20 = (cumsum_c[20:] - cumsum_c[:-20]) / 20.0
    
    cumsum_c2 = np.cumsum(np.insert(c**2, 0, 0))
    raw_mean_c2 = (cumsum_c2[20:] - cumsum_c2[:-20]) / 20.0
    raw_var20 = np.maximum(0.0001, raw_mean_c2 - raw_mean20**2)
    raw_std20 = np.sqrt(raw_var20)

    mean20 = np.pad(raw_mean20, (20, 0), mode="edge")[:n]
    std20 = np.pad(raw_std20, (20, 0), mode="edge")[:n]

    # Relative volume
    cumsum_v = np.cumsum(np.insert(v, 0, 0))
    raw_v_mean20 = (cumsum_v[20:] - cumsum_v[:-20]) / 20.0
    v_mean20 = np.pad(raw_v_mean20, (20, 0), mode="edge")[:n]
    rvol = np.where(v_mean20 > 0, v / v_mean20, 1.0)

    # RSI 7
    diff = np.diff(c)
    gain = np.where(diff > 0, diff, 0.0)
    loss = np.where(diff < 0, -diff, 0.0)
    c_g = np.cumsum(np.insert(gain, 0, 0)); avg_g = (c_g[7:] - c_g[:-7]) / 7.0
    c_l = np.cumsum(np.insert(loss, 0, 0)); avg_l = (c_l[7:] - c_l[:-7]) / 7.0
    rs = np.where(avg_l > 0, avg_g / avg_l, 10.0)
    raw_rsi7 = 100.0 - (100.0 / (1.0 + rs))
    rsi7 = np.pad(raw_rsi7, (8, 0), mode="edge")[:n]

    signals = []
    for i in range(25, n - 35):
        cur_z = (c[i-1] - mean20[i-1]) / std20[i-1]
        cur_rvol = rvol[i-1]
        cur_rsi = rsi7[i-1]
        if cur_rvol < 1.8: continue

        # Long: Oversold snapback
        if cur_z <= -z_req and cur_rsi <= rsi_low and c[i] > o[i]:
            nominal_sl = min(l[i], l[i-1]) - 0.40
            signals.append((i, "LONG", nominal_sl, False, 0.0))

        # Short: Overbought snapback
        elif cur_z >= z_req and cur_rsi >= rsi_high and c[i] < o[i]:
            nominal_sl = max(h[i], h[i-1]) + 0.40
            signals.append((i, "SHORT", nominal_sl, False, 0.0))

    return signals

def evaluate_h3(o, h, l, c, v, hours, n, p):
    # Failed Breakout (Trap)
    window = p["range_window"]
    re_entry_depth = p["re_entry_depth"]
    atr = get_atr(h, l, c, 14)
    signals = []

    for i in range(window + 10, n - 35):
        cur_atr = atr[i]
        if cur_atr < 0.3: continue

        h_box = np.max(h[i - window : i - 1])
        l_box = np.min(l[i - window : i - 1])
        box_width = h_box - l_box
        if not (3.0 <= box_width <= 12.0): continue

        # Long: Bear Trap (bar i-1 broke below l_box, bar i closed back inside)
        if c[i-1] < l_box and c[i] >= l_box + (re_entry_depth * cur_atr):
            if (c[i] - o[i]) > (o[i-1] - c[i-1]): # bullish engulfing
                limit_p = l_box + 0.10
                nominal_sl = l[i-1] - 0.30
                signals.append((i, "LONG", nominal_sl, True, limit_p))

        # Short: Bull Trap (bar i-1 broke above h_box, bar i closed back inside)
        elif c[i-1] > h_box and c[i] <= h_box - (re_entry_depth * cur_atr):
            if (o[i] - c[i]) > (c[i-1] - o[i-1]): # bearish engulfing
                limit_p = h_box - 0.10
                nominal_sl = h[i-1] + 0.30
                signals.append((i, "SHORT", nominal_sl, True, limit_p))

    return signals

def evaluate_h4(o, h, l, c, v, hours, n, p):
    # Micro-Momentum Continuation
    vel_mult = p["vel_mult"]
    body_ratio_req = p["body_ratio"]
    atr = get_atr(h, l, c, 14)

    # EMA 9
    alpha = 2.0 / (9.0 + 1.0)
    ema9 = np.zeros(n)
    ema9[0] = c[0]
    for k in range(1, n):
        ema9[k] = alpha * c[k] + (1 - alpha) * ema9[k-1]

    signals = []
    for i in range(15, n - 35):
        cur_atr = atr[i]
        if cur_atr < 0.3: continue

        # 3-bar impulse wave check (bars i-3, i-2, i-1)
        disp_3 = c[i-1] - o[i-3]
        rng_pullback = h[i] - l[i]
        if rng_pullback > 0.60 * cur_atr: continue

        # Long impulse
        if disp_3 >= vel_mult * cur_atr:
            # Body ratio check on impulse
            body1 = (c[i-3] - o[i-3]) / max(0.01, h[i-3] - l[i-3])
            body2 = (c[i-2] - o[i-2]) / max(0.01, h[i-2] - l[i-2])
            body3 = (c[i-1] - o[i-1]) / max(0.01, h[i-1] - l[i-1])
            if min(body1, body2, body3) >= body_ratio_req and l[i] >= ema9[i]:
                nominal_sl = l[i] - 0.30
                signals.append((i, "LONG", nominal_sl, False, 0.0))

        # Short impulse
        elif disp_3 <= -vel_mult * cur_atr:
            body1 = (o[i-3] - c[i-3]) / max(0.01, h[i-3] - l[i-3])
            body2 = (o[i-2] - c[i-2]) / max(0.01, h[i-2] - l[i-2])
            body3 = (o[i-1] - c[i-1]) / max(0.01, h[i-1] - l[i-1])
            if min(body1, body2, body3) >= body_ratio_req and h[i] <= ema9[i]:
                nominal_sl = h[i] + 0.30
                signals.append((i, "SHORT", nominal_sl, False, 0.0))

    return signals

def calculate_detailed_metrics(trades):
    if not trades:
        return {
            "n": 0, "wr": 0.0, "wr_ci_low": 0.0, "wr_ci_high": 0.0,
            "realized_rr": 0.0, "pf": 0.0, "net_exp": 0.0, "gross_exp": 0.0,
            "mdd_r": 0.0, "avg_holding_mins": 0.0, "trades_per_day": 0.0,
            "cost_drag_pct": 0.0, "ambiguous_pct": 0.0, "p_val": 1.0
        }
    
    r_vals = np.array([t["realized_r"] for t in trades])
    n = len(r_vals)
    wins = r_vals[r_vals > 0]
    losses = r_vals[r_vals < 0]
    n_w = len(wins); n_l = len(losses)
    wr = (n_w / n) * 100.0

    # Wilson Score CI for WR
    z = 1.96
    p_hat = n_w / n
    denom = 1.0 + (z**2 / n)
    center = (p_hat + (z**2 / (2 * n))) / denom
    margin = (z * np.sqrt((p_hat * (1 - p_hat) / n) + (z**2 / (4 * n**2)))) / denom
    wr_ci = (round((center - margin) * 100.0, 2), round((center + margin) * 100.0, 2))

    avg_w = float(np.mean(wins)) if n_w > 0 else 0.0
    avg_l = float(abs(np.mean(losses))) if n_l > 0 else 0.0
    realized_rr = avg_w / avg_l if avg_l > 0 else 0.0

    gw = float(np.sum(wins))
    gl = float(abs(np.sum(losses)))
    pf = gw / gl if gl > 0 else 99.0
    net_exp = float(np.mean(r_vals))

    # Gross expectancy
    gross_pnls = np.array([t["gross_pnl"] for t in trades])
    gross_exp = float(np.mean(gross_pnls / RISK_BUDGET))
    tot_comm = sum(t["comm"] for t in trades)
    tot_gross = sum(t["gross_pnl"] for t in trades if t["gross_pnl"] > 0)
    cost_drag = (tot_comm / tot_gross * 100.0) if tot_gross > 0 else 0.0

    cum = np.cumsum(r_vals)
    mdd = float(np.max(np.maximum.accumulate(cum) - cum))
    avg_hold = float(np.mean([t["holding_time_mins"] for t in trades]))

    unique_dates = len(set(t["date"] for t in trades))
    trades_per_day = n / unique_dates if unique_dates > 0 else 0.0

    ambiguous_count = sum(1 for t in trades if t["is_ambiguous"])
    ambiguous_pct = (ambiguous_count / n) * 100.0

    # t-test p-value
    std_r = float(np.std(r_vals, ddof=1)) if n > 1 else 1.0
    t_stat = (net_exp / (std_r / np.sqrt(n))) if std_r > 0 else 0.0
    p_val = float(2.0 * (1.0 - stats.t.cdf(abs(t_stat), df=n - 1))) if n > 1 else 1.0

    return {
        "n": n, "wr": round(wr, 2), "wr_ci_low": wr_ci[0], "wr_ci_high": wr_ci[1],
        "realized_rr": round(realized_rr, 3), "pf": round(pf, 3),
        "net_exp": round(net_exp, 4), "gross_exp": round(gross_exp, 4),
        "mdd_r": round(mdd, 2), "avg_holding_mins": round(avg_hold, 1),
        "trades_per_day": round(trades_per_day, 2),
        "cost_drag_pct": round(cost_drag, 2), "ambiguous_pct": round(ambiguous_pct, 2),
        "p_val": round(p_val, 6)
    }

def main():
    df = load_data()
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    v = df["volume"].to_numpy()
    hours = df["hour"].to_numpy()
    dates = df["date"].to_numpy()
    ts = df["timestamp"].to_numpy()
    n = len(o)
    print(f"Dataset Loaded: {n:,} candles (Strictly up to 2025-08-21; Holdout is SEALED).")

    # Define the 32 pre-registered variants
    experiments = []

    # H1: 8 variants
    for lb in [15, 30]:
        for wrick in [0.35, 0.45]:
            for trr in [0.60, 0.80]:
                hold_m = 10 if lb == 15 else 15
                experiments.append({
                    "id": f"H1_LB{lb}_W{int(wrick*100)}_RR{int(trr*100)}",
                    "hypothesis": "H1_Liquidity_Sweep",
                    "fn": evaluate_h1,
                    "params": {"lookback": lb, "wick_ratio": wrick, "target_rr": trr, "holding_bars": hold_m}
                })

    # H2: 8 variants
    for z in [2.0, 2.5]:
        for rsi_b in [(20, 80), (15, 85)]:
            for trr in [0.50, 0.60]:
                experiments.append({
                    "id": f"H2_Z{str(z).replace('.', '')}_RSI{rsi_b[0]}_{rsi_b[1]}_RR{int(trr*100)}",
                    "hypothesis": "H2_Mean_Reversion",
                    "fn": evaluate_h2,
                    "params": {"z_score": z, "rsi_bounds": rsi_b, "target_rr": trr, "holding_bars": 5}
                })

    # H3: 8 variants
    for win in [30, 45]:
        for dep in [0.25, 0.40]:
            for trr in [0.70, 0.80]:
                experiments.append({
                    "id": f"H3_WIN{win}_DEP{int(dep*100)}_RR{int(trr*100)}",
                    "hypothesis": "H3_Failed_Breakout",
                    "fn": evaluate_h3,
                    "params": {"range_window": win, "re_entry_depth": dep, "target_rr": trr, "holding_bars": 15}
                })

    # H4: 8 variants
    for vel in [1.2, 1.8]:
        for body in [0.60, 0.70]:
            for trr in [0.50, 0.70]:
                experiments.append({
                    "id": f"H4_VEL{str(vel).replace('.', '')}_B{int(body*100)}_RR{int(trr*100)}",
                    "hypothesis": "H4_Micro_Momentum",
                    "fn": evaluate_h4,
                    "params": {"vel_mult": vel, "body_ratio": body, "target_rr": trr, "holding_bars": 5}
                })

    print(f"\nTotal Registered Experiments to Run: {len(experiments)} (Budget = 32)")

    experiment_results = []
    csv_rows = []

    for idx, exp in enumerate(experiments):
        exp_id = exp["id"]
        hyp_name = exp["hypothesis"]
        fn = exp["fn"]
        p = exp["params"]
        print(f"[{idx+1}/32] Executing {exp_id}...")

        trades = run_backtest_vectorized(o, h, l, c, v, hours, dates, ts, n, fn, p)
        
        is_trades = [t for t in trades if t["partition"] == "IN_SAMPLE"]
        val_trades = [t for t in trades if t["partition"] == "VALIDATION"]

        m_is = calculate_detailed_metrics(is_trades)
        m_val = calculate_detailed_metrics(val_trades)

        # Long vs Short on Validation
        val_long = [t for t in val_trades if t["direction"] == "LONG"]
        val_short = [t for t in val_trades if t["direction"] == "SHORT"]
        m_val_l = calculate_detailed_metrics(val_long)
        m_val_s = calculate_detailed_metrics(val_short)

        # Check pre-registered candidate gates on Validation:
        # WR >= 68.0%, PF >= 1.30, Net Exp >= +0.10R, N >= 500
        passed_gates = (
            m_val["wr"] >= 68.0 and
            m_val["pf"] >= 1.30 and
            m_val["net_exp"] >= 0.10 and
            m_val["n"] >= 500 and
            m_val["ambiguous_pct"] <= 5.0
        )

        res_entry = {
            "experiment_id": exp_id,
            "hypothesis": hyp_name,
            "params": p,
            "in_sample": m_is,
            "validation": m_val,
            "validation_long": m_val_l,
            "validation_short": m_val_s,
            "passed_validation_gates": passed_gates
        }
        experiment_results.append(res_entry)

        csv_rows.append({
            "experiment_id": exp_id,
            "hypothesis": hyp_name,
            "target_rr": p["target_rr"],
            "is_trades": m_is["n"],
            "is_win_rate": m_is["wr"],
            "is_profit_factor": m_is["pf"],
            "is_net_exp_r": m_is["net_exp"],
            "is_mdd_r": m_is["mdd_r"],
            "val_trades": m_val["n"],
            "val_win_rate": m_val["wr"],
            "val_wr_ci": f"[{m_val['wr_ci_low']}%, {m_val['wr_ci_high']}%]",
            "val_profit_factor": m_val["pf"],
            "val_net_exp_r": m_val["net_exp"],
            "val_mdd_r": m_val["mdd_r"],
            "val_trades_per_day": m_val["trades_per_day"],
            "val_ambiguous_pct": m_val["ambiguous_pct"],
            "val_long_wr": m_val_l["wr"],
            "val_short_wr": m_val_s["wr"],
            "raw_p_value": m_val["p_val"],
            "passed_validation_gates": "PASS" if passed_gates else "FAIL"
        })

    # Multiple testing correction across all 32 experiments (Holm-Bonferroni on Validation p-values)
    raw_p_vals = [r["validation"]["p_val"] for r in experiment_results]
    sorted_indices = np.argsort(raw_p_vals)
    M = len(raw_p_vals)
    holm_adjusted_p = np.zeros(M)
    for rank, orig_idx in enumerate(sorted_indices):
        holm_adjusted_p[orig_idx] = min(1.0, raw_p_vals[orig_idx] * (M - rank))

    for idx, r in enumerate(experiment_results):
        r["validation"]["holm_adjusted_p"] = round(float(holm_adjusted_p[idx]), 6)
        csv_rows[idx]["holm_adjusted_p"] = round(float(holm_adjusted_p[idx]), 6)

    # Write CSV
    print(f"\nWriting experiment log to {LOG_CSV}...")
    fieldnames = list(csv_rows[0].keys())
    with open(LOG_CSV, "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    # Write JSON
    with open(JSON_OUT, "w") as fp:
        json.dump(experiment_results, fp, indent=2)

    print("Phase 2 discovery execution complete!")

if __name__ == "__main__":
    main()
