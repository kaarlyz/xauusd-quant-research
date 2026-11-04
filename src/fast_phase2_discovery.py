#!/usr/bin/env python3
"""
Fast Vectorized Phase 2 Discovery Engine.
Precomputes all rolling features using Polars C++ engine (300x speedup).
Runs all 32 registered experiments in ~25 seconds.
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

SPREAD_BASELINE = 0.380
COMMISSION_ROUND = 0.070
SLIPPAGE_MARKET = 0.050
RISK_BUDGET = 7.50

T_IS_START = int(datetime.datetime(2021, 8, 23, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_IS_END = int(datetime.datetime(2024, 8, 21, 23, 59, 59, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_VAL_START = int(datetime.datetime(2024, 8, 22, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_VAL_END = int(datetime.datetime(2025, 8, 21, 23, 59, 59, tzinfo=datetime.timezone.utc).timestamp() * 1000)

def load_data_and_features():
    print("Loading Master M1 dataset and precomputing features...")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )
    df = df.filter(~pl.col("hour").is_between(21, 23))
    df = df.filter(pl.col("timestamp") <= T_VAL_END)

    # Precompute True Range and ATR14
    df = df.with_columns([
        pl.col("close").shift(1).alias("prev_close"),
    ])
    df = df.with_columns([
        pl.max_horizontal(
            pl.col("high") - pl.col("low"),
            (pl.col("high") - pl.col("prev_close")).abs(),
            (pl.col("low") - pl.col("prev_close")).abs()
        ).alias("tr")
    ])
    df = df.with_columns([
        pl.col("tr").rolling_mean(window_size=14).alias("atr14"),
        # Rolling high and low for lookbacks 15, 30, 45
        pl.col("high").shift(1).rolling_max(window_size=15).alias("h_max_15"),
        pl.col("low").shift(1).rolling_min(window_size=15).alias("l_min_15"),
        pl.col("high").shift(1).rolling_max(window_size=30).alias("h_max_30"),
        pl.col("low").shift(1).rolling_min(window_size=30).alias("l_min_30"),
        pl.col("high").shift(1).rolling_max(window_size=45).alias("h_max_45"),
        pl.col("low").shift(1).rolling_min(window_size=45).alias("l_min_45"),
        # Rolling mean and std for 20 periods
        pl.col("close").shift(1).rolling_mean(window_size=20).alias("mean20"),
        pl.col("close").shift(1).rolling_std(window_size=20).alias("std20"),
        # Relative volume
        pl.col("volume").shift(1).rolling_mean(window_size=20).alias("v_mean20"),
        # EMA9
        pl.col("close").ewm_mean(span=9).alias("ema9"),
    ])

    return df

def run_backtest_fast(o, h, l, c, dates, ts, signals, target_rr, holding_bars):
    n = len(o)
    trades = []
    last_exit_idx = -1

    for sig in signals:
        i, direction, nominal_sl, is_limit, limit_price = sig
        if i <= last_exit_idx or i + holding_bars >= n:
            continue

        exec_bar = i + 1
        trade_ts = ts[exec_bar]
        date_str = str(dates[exec_bar])

        if trade_ts < T_IS_START:
            continue
        elif trade_ts <= T_IS_END:
            partition = "IN_SAMPLE"
        elif trade_ts <= T_VAL_END:
            partition = "VALIDATION"
        else:
            continue

        if direction == "LONG":
            if is_limit:
                if l[exec_bar] > limit_price - 0.10: continue
                entry_fill = limit_price
            else:
                entry_fill = o[exec_bar] + SPREAD_BASELINE + SLIPPAGE_MARKET

            stop_dist = entry_fill - nominal_sl
            if stop_dist < 0.50 or stop_dist > 15.0: continue

            lots = RISK_BUDGET / (stop_dist * 100.0)
            tp_price = entry_fill + (target_rr * stop_dist)

            exit_fill = c[exec_bar + holding_bars]
            exit_reason = "TIMEOUT"
            is_ambiguous = False
            exit_idx = exec_bar + holding_bars

            for b in range(exec_bar, exec_bar + holding_bars + 1):
                hit_sl = (l[b] <= nominal_sl)
                hit_tp = (h[b] >= tp_price)
                if hit_sl and hit_tp:
                    is_ambiguous = True; exit_fill = nominal_sl - SLIPPAGE_MARKET; exit_reason = "AMBIGUOUS"; exit_idx = b; break
                elif hit_sl:
                    exit_fill = nominal_sl - SLIPPAGE_MARKET; exit_reason = "SL"; exit_idx = b; break
                elif hit_tp:
                    exit_fill = tp_price; exit_reason = "TP"; exit_idx = b; break

            gross_pnl = (exit_fill - entry_fill) * lots * 100.0
            comm = COMMISSION_ROUND * lots * 100.0
            net_pnl = gross_pnl - comm
            realized_r = net_pnl / RISK_BUDGET
            last_exit_idx = exit_idx

            trades.append({
                "partition": partition, "direction": "LONG", "date": date_str,
                "gross_pnl": gross_pnl, "comm": comm, "net_pnl": net_pnl,
                "realized_r": realized_r, "is_ambiguous": is_ambiguous,
                "holding_mins": (exit_idx - exec_bar) + 1
            })

        else: # SHORT
            if is_limit:
                if h[exec_bar] < limit_price + 0.10: continue
                entry_fill = limit_price
            else:
                entry_fill = o[exec_bar] - SLIPPAGE_MARKET

            stop_dist = nominal_sl - entry_fill
            if stop_dist < 0.50 or stop_dist > 15.0: continue

            lots = RISK_BUDGET / (stop_dist * 100.0)
            tp_price = entry_fill - (target_rr * stop_dist)

            exit_fill = c[exec_bar + holding_bars] + SPREAD_BASELINE
            exit_reason = "TIMEOUT"
            is_ambiguous = False
            exit_idx = exec_bar + holding_bars

            for b in range(exec_bar, exec_bar + holding_bars + 1):
                hit_sl = (h[b] + SPREAD_BASELINE >= nominal_sl)
                hit_tp = (l[b] + SPREAD_BASELINE <= tp_price)
                if hit_sl and hit_tp:
                    is_ambiguous = True; exit_fill = nominal_sl + SLIPPAGE_MARKET; exit_reason = "AMBIGUOUS"; exit_idx = b; break
                elif hit_sl:
                    exit_fill = nominal_sl + SLIPPAGE_MARKET; exit_reason = "SL"; exit_idx = b; break
                elif hit_tp:
                    exit_fill = tp_price; exit_reason = "TP"; exit_idx = b; break

            gross_pnl = (entry_fill - exit_fill) * lots * 100.0
            comm = COMMISSION_ROUND * lots * 100.0
            net_pnl = gross_pnl - comm
            realized_r = net_pnl / RISK_BUDGET
            last_exit_idx = exit_idx

            trades.append({
                "partition": partition, "direction": "SHORT", "date": date_str,
                "gross_pnl": gross_pnl, "comm": comm, "net_pnl": net_pnl,
                "realized_r": realized_r, "is_ambiguous": is_ambiguous,
                "holding_mins": (exit_idx - exec_bar) + 1
            })

    return trades

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
    wins = r_vals[r_vals > 0]; losses = r_vals[r_vals < 0]
    n_w = len(wins); n_l = len(losses)
    wr = (n_w / n) * 100.0

    z = 1.96; p_hat = n_w / n; denom = 1.0 + (z**2 / n)
    center = (p_hat + (z**2 / (2 * n))) / denom
    margin = (z * np.sqrt((p_hat * (1 - p_hat) / n) + (z**2 / (4 * n**2)))) / denom
    wr_ci = (round((center - margin) * 100.0, 2), round((center + margin) * 100.0, 2))

    avg_w = float(np.mean(wins)) if n_w > 0 else 0.0
    avg_l = float(abs(np.mean(losses))) if n_l > 0 else 0.0
    realized_rr = avg_w / avg_l if avg_l > 0 else 0.0

    gw = float(np.sum(wins)); gl = float(abs(np.sum(losses)))
    pf = gw / gl if gl > 0 else 99.0
    net_exp = float(np.mean(r_vals))

    gross_pnls = np.array([t["gross_pnl"] for t in trades])
    gross_exp = float(np.mean(gross_pnls / RISK_BUDGET))
    tot_comm = sum(t["comm"] for t in trades)
    tot_gross = sum(t["gross_pnl"] for t in trades if t["gross_pnl"] > 0)
    cost_drag = (tot_comm / tot_gross * 100.0) if tot_gross > 0 else 0.0

    cum = np.cumsum(r_vals)
    mdd = float(np.max(np.maximum.accumulate(cum) - cum))
    avg_hold = float(np.mean([t["holding_mins"] for t in trades]))

    unique_dates = len(set(t["date"] for t in trades))
    trades_per_day = n / unique_dates if unique_dates > 0 else 0.0

    ambiguous_count = sum(1 for t in trades if t["is_ambiguous"])
    ambiguous_pct = (ambiguous_count / n) * 100.0

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
    df = load_data_and_features()
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    v = df["volume"].to_numpy()
    dates = df["date"].to_numpy()
    ts = df["timestamp"].to_numpy()
    atr14 = df["atr14"].to_numpy()
    n = len(o)
    print(f"Dataset precomputed: {n:,} bars.")

    # Calculate pre-computed signals
    # H1
    def get_h1_signals(lb, wrick):
        h_max = df[f"h_max_{lb}"].to_numpy()
        l_min = df[f"l_min_{lb}"].to_numpy()
        rng = h - l
        lower_wick = np.minimum(o, c) - l
        upper_wick = h - np.maximum(o, c)

        long_cond = (l <= l_min - 0.50 * atr14) & (c >= l_min) & (rng > 0.05) & ((lower_wick / np.maximum(0.01, rng)) >= wrick)
        short_cond = (h >= h_max + 0.50 * atr14) & (c <= h_max) & (rng > 0.05) & ((upper_wick / np.maximum(0.01, rng)) >= wrick)

        sigs = []
        for i in np.where(long_cond | short_cond)[0]:
            if long_cond[i]:
                sigs.append((i, "LONG", l[i] - 0.30, False, 0.0))
            elif short_cond[i]:
                sigs.append((i, "SHORT", h[i] + 0.30, False, 0.0))
        return sigs

    # H2
    mean20 = df["mean20"].to_numpy()
    std20 = np.maximum(0.001, df["std20"].to_numpy())
    v_mean20 = np.maximum(0.001, df["v_mean20"].to_numpy())
    z_score = (np.roll(c, 1) - mean20) / std20
    rvol = np.roll(v, 1) / v_mean20

    # Fast RSI 7
    diff = np.diff(np.insert(c, 0, c[0]))
    g = np.where(diff > 0, diff, 0.0)
    ls = np.where(diff < 0, -diff, 0.0)
    cg = np.cumsum(np.insert(g, 0, 0)); ag = (cg[7:] - cg[:-7]) / 7.0
    cl = np.cumsum(np.insert(ls, 0, 0)); al = (cl[7:] - cl[:-7]) / 7.0
    rs = np.where(al > 0, ag / al, 10.0)
    rsi7 = 100.0 - (100.0 / (1.0 + rs))
    rsi7 = np.pad(rsi7, (7, 0), mode="edge")[:n]
    rsi7_prev = np.roll(rsi7, 1)

    def get_h2_signals(z_req, rsi_b):
        r_low, r_high = rsi_b
        long_cond = (z_score <= -z_req) & (rsi7_prev <= r_low) & (rvol >= 1.8) & (c > o)
        short_cond = (z_score >= z_req) & (rsi7_prev >= r_high) & (rvol >= 1.8) & (c < o)
        sigs = []
        for i in np.where(long_cond | short_cond)[0]:
            if long_cond[i]:
                sigs.append((i, "LONG", min(l[i], l[i-1]) - 0.40, False, 0.0))
            elif short_cond[i]:
                sigs.append((i, "SHORT", max(h[i], h[i-1]) + 0.40, False, 0.0))
        return sigs

    # H3
    def get_h3_signals(win, dep):
        h_box = df[f"h_max_{win}"].to_numpy()
        l_box = df[f"l_min_{win}"].to_numpy()
        box_w = h_box - l_box
        box_ok = (box_w >= 3.0) & (box_w <= 12.0)
        c_prev = np.roll(c, 1); o_prev = np.roll(o, 1)
        l_prev = np.roll(l, 1); h_prev = np.roll(h, 1)

        long_cond = box_ok & (c_prev < l_box) & (c >= l_box + dep * atr14) & ((c - o) > (o_prev - c_prev))
        short_cond = box_ok & (c_prev > h_box) & (c <= h_box - dep * atr14) & ((o - c) > (c_prev - o_prev))

        sigs = []
        for i in np.where(long_cond | short_cond)[0]:
            if long_cond[i]:
                sigs.append((i, "LONG", l_prev[i] - 0.30, True, l_box[i] + 0.10))
            elif short_cond[i]:
                sigs.append((i, "SHORT", h_prev[i] + 0.30, True, h_box[i] - 0.10))
        return sigs

    # H4
    ema9 = df["ema9"].to_numpy()
    c_prev = np.roll(c, 1); o_3prev = np.roll(o, 3)
    disp3 = c_prev - o_3prev
    rng = h - l
    pullback_ok = (rng <= 0.60 * atr14)

    def get_h4_signals(vel, body_req):
        body1 = np.abs(c - o) / np.maximum(0.01, rng)
        body2 = np.roll(body1, 1)
        body3 = np.roll(body1, 2)
        body_ok = (np.minimum(body1, np.minimum(body2, body3)) >= body_req)

        long_cond = pullback_ok & (disp3 >= vel * atr14) & body_ok & (l >= ema9)
        short_cond = pullback_ok & (disp3 <= -vel * atr14) & body_ok & (h <= ema9)

        sigs = []
        for i in np.where(long_cond | short_cond)[0]:
            if long_cond[i]:
                sigs.append((i, "LONG", l[i] - 0.30, False, 0.0))
            elif short_cond[i]:
                sigs.append((i, "SHORT", h[i] + 0.30, False, 0.0))
        return sigs

    # Run the 32 experiments
    experiments = []

    # H1
    for lb in [15, 30]:
        for wrick in [0.35, 0.45]:
            sigs = get_h1_signals(lb, wrick)
            hold_m = 10 if lb == 15 else 15
            for trr in [0.60, 0.80]:
                experiments.append({
                    "id": f"H1_LB{lb}_W{int(wrick*100)}_RR{int(trr*100)}",
                    "hypothesis": "H1_Liquidity_Sweep",
                    "signals": sigs, "target_rr": trr, "holding_bars": hold_m
                })

    # H2
    for z in [2.0, 2.5]:
        for rsi_b in [(20, 80), (15, 85)]:
            sigs = get_h2_signals(z, rsi_b)
            for trr in [0.50, 0.60]:
                experiments.append({
                    "id": f"H2_Z{str(z).replace('.', '')}_RSI{rsi_b[0]}_{rsi_b[1]}_RR{int(trr*100)}",
                    "hypothesis": "H2_Mean_Reversion",
                    "signals": sigs, "target_rr": trr, "holding_bars": 5
                })

    # H3
    for win in [30, 45]:
        for dep in [0.25, 0.40]:
            sigs = get_h3_signals(win, dep)
            for trr in [0.70, 0.80]:
                experiments.append({
                    "id": f"H3_WIN{win}_DEP{int(dep*100)}_RR{int(trr*100)}",
                    "hypothesis": "H3_Failed_Breakout",
                    "signals": sigs, "target_rr": trr, "holding_bars": 15
                })

    # H4
    for vel in [1.2, 1.8]:
        for body in [0.60, 0.70]:
            sigs = get_h4_signals(vel, body)
            for trr in [0.50, 0.70]:
                experiments.append({
                    "id": f"H4_VEL{str(vel).replace('.', '')}_B{int(body*100)}_RR{int(trr*100)}",
                    "hypothesis": "H4_Micro_Momentum",
                    "signals": sigs, "target_rr": trr, "holding_bars": 5
                })

    print(f"\nRunning {len(experiments)} Pre-Registered Experiments...")
    csv_rows = []
    experiment_results = []

    for idx, exp in enumerate(experiments):
        exp_id = exp["id"]
        hyp_name = exp["hypothesis"]
        sigs = exp["signals"]
        trr = exp["target_rr"]
        hold_m = exp["holding_bars"]

        trades = run_backtest_fast(o, h, l, c, dates, ts, sigs, trr, hold_m)
        is_trades = [t for t in trades if t["partition"] == "IN_SAMPLE"]
        val_trades = [t for t in trades if t["partition"] == "VALIDATION"]

        m_is = calculate_detailed_metrics(is_trades)
        m_val = calculate_detailed_metrics(val_trades)

        val_long = [t for t in val_trades if t["direction"] == "LONG"]
        val_short = [t for t in val_trades if t["direction"] == "SHORT"]
        m_val_l = calculate_detailed_metrics(val_long)
        m_val_s = calculate_detailed_metrics(val_short)

        passed_gates = (
            m_val["wr"] >= 68.0 and
            m_val["pf"] >= 1.30 and
            m_val["net_exp"] >= 0.10 and
            m_val["n"] >= 500 and
            m_val["ambiguous_pct"] <= 5.0
        )

        res_entry = {
            "experiment_id": exp_id, "hypothesis": hyp_name, "target_rr": trr,
            "in_sample": m_is, "validation": m_val,
            "validation_long": m_val_l, "validation_short": m_val_s,
            "passed_validation_gates": passed_gates
        }
        experiment_results.append(res_entry)

        status_str = "PASS" if passed_gates else "FAIL"
        print(f"[{idx+1:02d}/32] {exp_id:<28} | IS WR: {m_is['wr']:4.1f}% PF: {m_is['pf']:4.2f} | VAL WR: {m_val['wr']:4.1f}% PF: {m_val['pf']:4.2f} Exp: {m_val['net_exp']:+.4f}R (N={m_val['n']}) -> {status_str}")

        csv_rows.append({
            "experiment_id": exp_id,
            "hypothesis": hyp_name,
            "target_rr": trr,
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
            "passed_validation_gates": status_str
        })

    # Multiple testing Holm-Bonferroni correction
    raw_p_vals = [r["validation"]["p_val"] for r in experiment_results]
    sorted_indices = np.argsort(raw_p_vals)
    M = len(raw_p_vals)
    holm_p = np.zeros(M)
    for rank, orig_idx in enumerate(sorted_indices):
        holm_p[orig_idx] = min(1.0, raw_p_vals[orig_idx] * (M - rank))

    for idx in range(M):
        experiment_results[idx]["validation"]["holm_adjusted_p"] = round(float(holm_p[idx]), 6)
        csv_rows[idx]["holm_adjusted_p"] = round(float(holm_p[idx]), 6)

    # Save CSV
    with open(LOG_CSV, "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    # Save JSON
    with open(JSON_OUT, "w") as fp:
        json.dump(experiment_results, fp, indent=2)

    print(f"\nAll 32 experiments completed. Log written to {LOG_CSV}")

if __name__ == "__main__":
    main()
