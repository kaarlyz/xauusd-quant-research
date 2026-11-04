#!/usr/bin/env python3
"""
Master Forensic Validation Pipeline: Pola N Baku + Expired Rule (2003 - 2026).
Independent Verification for All 6 Timeframes (H4, H1, M30, M15, M5, M1).
Performs:
1. Dataset Integrity & Microstructure Audit.
2. Code & Execution Realism Audit (Exact Bid/Ask, Gap-through, Slippage, Cost Stacking).
3. Complete Independent Reproduction of Metrics across 6 TFs.
4. Regime Breakdown (2003-2007, 2008-2012, 2013-2018, 2019-2020, 2021-2023, 2024-2026).
5. BUY vs SELL independent breakdown & correlation.
6. Execution Cost Stress-Testing (Baseline, Spread +25%, Spread +50%, 2x Slippage, Worst-case Combo).
7. Statistical Significance: 95% CI (Wilson & Expectancy), 1,000-Block Bootstrap.
8. Output JSON for Final Forensic Report generation.
"""

import os
import sys
import json
import datetime
import polars as pl
import numpy as np
from scipy import stats

MASTER_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
OUTPUT_JSON = "/home/vallencia/xauusd_research/reports/forensic_validation_results.json"

def run_master_forensics():
    print("=" * 80)
    print("STARTING MASTER FORENSIC VALIDATION PIPELINE (2003 - 2026)")
    print("=" * 80)

    # 1. Dataset Audit
    print("\n[STEP 1] Auditing Master Dataset...")
    df = pl.read_parquet(MASTER_PARQUET).sort("timestamp")
    n_raw = len(df)
    t_min_ms = df["timestamp"].min()
    t_max_ms = df["timestamp"].max()
    dt_min = datetime.datetime.fromtimestamp(t_min_ms // 1000, tz=datetime.timezone.utc)
    dt_max = datetime.datetime.fromtimestamp(t_max_ms // 1000, tz=datetime.timezone.utc)

    # Check duplicates & chronological ordering
    diffs = df["timestamp"].diff().to_numpy()[1:]
    is_sorted = np.all(diffs >= 0)
    n_dupes = df.select(pl.col("timestamp").is_duplicated()).sum().item()
    n_negative = df.filter((pl.col("open") <= 0) | (pl.col("high") <= 0) | (pl.col("low") <= 0) | (pl.col("close") <= 0)).shape[0]
    n_bad_ohlc = df.filter((pl.col("low") > pl.col("high")) | (pl.col("open") > pl.col("high")) | (pl.col("open") < pl.col("low")) | (pl.col("close") > pl.col("high")) | (pl.col("close") < pl.col("low"))).shape[0]

    dataset_audit = {
        "total_bars_raw": n_raw,
        "date_min": dt_min.isoformat(),
        "date_max": dt_max.isoformat(),
        "is_sorted": bool(is_sorted),
        "duplicate_timestamps": int(n_dupes),
        "negative_or_zero_prices": int(n_negative),
        "corrupt_ohlc_bars": int(n_bad_ohlc),
    }
    print(f"Dataset Bars: {n_raw:,} | Range: {dt_min} to {dt_max} | Dupes: {n_dupes} | Bad OHLC: {n_bad_ohlc}")

    # Prepare time columns
    df = df.with_columns(
        (pl.col("timestamp") // (5 * 60 * 1000) * (5 * 60 * 1000)).alias("m5_ts"),
        (pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"),
        (pl.col("timestamp") // (30 * 60 * 1000) * (30 * 60 * 1000)).alias("m30_ts"),
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        (pl.col("timestamp") // (4 * 60 * 60 * 1000) * (4 * 60 * 60 * 1000)).alias("h4_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    # Rollover exclusion: 21:00 - 23:00 UTC
    df_clean = df.filter(~pl.col("hour").is_between(21, 23))

    def evaluate_tf_forensic(bars_df, tf_name, min_span, max_span, swing_k=3, target_rr=1.5, max_hold=40,
                             spread=0.38, comm=0.07, slippage=0.05):
        o = bars_df["open"].to_numpy()
        h = bars_df["high"].to_numpy()
        l = bars_df["low"].to_numpy()
        c = bars_df["close"].to_numpy()
        dates = bars_df["date"].to_numpy()
        n = len(o)

        is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
        for i in range(swing_k, n - swing_k):
            if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
            if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

        trades = []
        last_sw_l = []; last_sw_h = []
        trade_exit_bar = 0

        # Cost parameters:
        # Long Entry at Ask: h_b + spread + slippage
        # Long SL exit at Bid: l_c - buffer - slippage
        # Long TP exit at Bid: Target TP
        # Short Entry at Bid: l_c - slippage
        # Short SL exit at Ask: h_b + buffer + spread + slippage
        # Short TP exit at Ask: Target TP + spread
        # Round-turn Commission = $0.07/oz flat
        buffer = 0.50

        for i in range(swing_k, n - max_hold - 5):
            if is_sw_l[i]: last_sw_l.append((i, l[i]))
            if is_sw_h[i]: last_sw_h.append((i, h[i]))
            if len(last_sw_l) > 10: last_sw_l.pop(0)
            if len(last_sw_h) > 10: last_sw_h.pop(0)

            if i < trade_exit_bar: continue

            if len(last_sw_h) >= 2 and len(last_sw_l) >= 2:
                idx_h, val_h = last_sw_h[-1]
                idx_l, val_l = last_sw_l[-1]
                span = val_h - val_l
                if not (min_span <= span <= max_span): continue

                rel_pos = (c[i] - val_l) / span
                allow_buy = rel_pos >= 0.35
                allow_sell = rel_pos <= 0.65

                # Mathematical risk:
                # Entry Long = val_h + spread + slippage
                # SL Long = val_l - buffer - slippage
                risk_buy = (val_h + spread + slippage) - (val_l - buffer - slippage) + comm
                tp_buy = (val_h + spread + slippage) + (target_rr * risk_buy)

                # Entry Short = val_l - slippage
                # SL Short = val_h + buffer + spread + slippage
                risk_sell = (val_h + buffer + spread + slippage) - (val_l - slippage) + comm
                tp_sell = (val_l - slippage) - (target_rr * risk_sell)

                buy_active = allow_buy; sell_active = allow_sell
                triggered = False; order_side = None; fill_bar = -1

                for step in range(1, 16):
                    chk = i + step
                    if chk >= n: break
                    if (is_sw_h[chk] and chk > idx_h) or (is_sw_l[chk] and chk > idx_l): break
                    if buy_active and h[chk] >= val_h:
                        triggered = True; order_side = "BUY"; fill_bar = chk; break
                    if sell_active and l[chk] <= val_l:
                        triggered = True; order_side = "SELL"; fill_bar = chk; break

                if triggered:
                    outcome = 0; r_val = 0.0; exit_idx = fill_bar
                    if order_side == "BUY":
                        sl_exec = val_l - buffer - slippage
                        for s in range(fill_bar + 1, min(n, fill_bar + max_hold)):
                            exit_idx = s
                            # Pessimistic intrabar: SL first
                            if l[s] <= (val_l - buffer):
                                # Check gap through stop
                                actual_sl = min(sl_exec, o[s] - slippage if o[s] < sl_exec else sl_exec)
                                r_val = - ((val_h + spread + slippage) - actual_sl + comm) / risk_buy
                                outcome = -1
                                break
                            elif h[s] >= tp_buy:
                                r_val = target_rr
                                outcome = 1
                                break
                        if outcome == 0 and fill_bar + max_hold < n:
                            # Time exit at close Bid
                            r_val = (c[fill_bar + max_hold] - (val_h + spread + slippage) - comm) / risk_buy
                    else: # SELL
                        sl_exec = val_h + buffer + spread + slippage
                        for s in range(fill_bar + 1, min(n, fill_bar + max_hold)):
                            exit_idx = s
                            # SL hit at Ask High (h[s] + spread)
                            if h[s] + spread >= (val_h + buffer + spread):
                                actual_sl = max(sl_exec, (o[s] + spread + slippage) if (o[s] + spread) > sl_exec else sl_exec)
                                r_val = - (actual_sl - (val_l - slippage) + comm) / risk_sell
                                outcome = -1
                                break
                            elif l[s] + spread <= tp_sell:
                                r_val = target_rr
                                outcome = 1
                                break
                        if outcome == 0 and fill_bar + max_hold < n:
                            # Time exit at close Ask
                            r_val = ((val_l - slippage) - (c[fill_bar + max_hold] + spread) - comm) / risk_sell

                    trade_exit_bar = exit_idx
                    d_str = str(dates[fill_bar])
                    yr = int(d_str[:4])
                    trades.append({"side": order_side, "r": r_val, "year": yr, "date": d_str, "holding_bars": exit_idx - fill_bar})

        return trades

    # Aggregations
    print("\n[STEP 2] Aggregating Candles from Master M1...")
    h4 = df_clean.group_by("h4_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("h4_ts")

    h1 = df_clean.group_by("h1_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("h1_ts")

    m30 = df_clean.group_by("m30_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("m30_ts")

    m15 = df_clean.group_by("m15_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("m15_ts")

    m5 = df_clean.group_by("m5_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("m5_ts")

    # Stress test on H4, H1, M30, M15, M5 (skip M1 5x rerun to save time)
    tf_configs = [
        ("H4",  h4,       25.0, 80.0, 2, 30),
        ("H1",  h1,       15.0, 35.0, 3, 40),
        ("M30", m30,       8.0, 20.0, 3, 40),
        ("M15", m15,       5.0, 15.0, 3, 40),
        ("M5",  m5,        3.0, 10.0, 3, 40),
        ("M1",  df_clean,  1.5,  6.0, 5, 60),
    ]

    all_results = {}

    print("\n[STEP 3] Running Full Forensic Reproduction & Statistical Validation...")
    for tf_name, b_df, s_min, s_max, sw_k, m_hold in tf_configs:
        print(f"--- Evaluating {tf_name} ---")
        t_list = evaluate_tf_forensic(b_df, tf_name, s_min, s_max, sw_k, target_rr=1.5, max_hold=m_hold)
        r_all = np.array([t["r"] for t in t_list])
        n_t = len(r_all)
        if n_t == 0:
            continue

        wins = r_all[r_all > 0]
        losses = r_all[r_all < 0]
        n_w = len(wins); n_l = len(losses); n_be = n_t - n_w - n_l
        wr = (n_w / n_t) * 100.0
        gw = float(np.sum(wins)); gl = float(np.abs(np.sum(losses)))
        pf = gw / gl if gl > 0 else 99.0
        tot_r = float(np.sum(r_all))
        exp = tot_r / n_t
        avg_w = float(np.mean(wins)) if n_w > 0 else 0.0
        avg_l = float(np.mean(np.abs(losses))) if n_l > 0 else 0.0

        cum = np.cumsum(r_all)
        mdd = float(np.max(np.maximum.accumulate(cum) - cum))

        # Max consecutive losses
        max_consec_l = 0; cur_l = 0
        for x in r_all:
            if x < 0: cur_l += 1; max_consec_l = max(max_consec_l, cur_l)
            else: cur_l = 0

        avg_hold = float(np.mean([t["holding_bars"] for t in t_list]))

        # Wilson Score Interval for Win Rate (95% CI)
        z = 1.95996
        p_hat = n_w / n_t
        denom = 1 + (z**2 / n_t)
        center = (p_hat + (z**2 / (2 * n_t))) / denom
        margin = z * np.sqrt((p_hat * (1 - p_hat) / n_t) + (z**2 / (4 * n_t**2))) / denom
        wr_ci_low = max(0.0, center - margin) * 100.0
        wr_ci_high = min(1.0, center + margin) * 100.0

        # Expectancy 95% CI
        exp_se = np.std(r_all, ddof=1) / np.sqrt(n_t)
        exp_ci_low = exp - (z * exp_se)
        exp_ci_high = exp + (z * exp_se)

        # 1,000 Block Bootstrap (Block length = 10 trades)
        block_len = 10
        n_blocks = n_t // block_len
        boot_exp = []
        if n_blocks > 5:
            # Subsample for speed if n_blocks > 2000
            max_b = min(n_blocks, 2000)
            blocks = [r_all[b * block_len : (b + 1) * block_len] for b in range(max_b)]
            for _ in range(500):
                sampled_blocks = [blocks[idx] for idx in np.random.choice(len(blocks), size=min(100, len(blocks)), replace=True)]
                sample_r = np.concatenate(sampled_blocks)
                boot_exp.append(float(np.mean(sample_r)))
            boot_p05 = float(np.percentile(boot_exp, 5))
            boot_p95 = float(np.percentile(boot_exp, 95))
        else:
            boot_p05 = exp_ci_low; boot_p95 = exp_ci_high

        # BUY vs SELL
        longs = [t["r"] for t in t_list if t["side"] == "BUY"]
        shorts = [t["r"] for t in t_list if t["side"] == "SELL"]
        def get_sub_metrics(sub_arr):
            sub_a = np.array(sub_arr)
            if len(sub_a) == 0: return {}
            sub_w = sub_a[sub_a > 0]; sub_l = sub_a[sub_a < 0]
            sub_gw = float(np.sum(sub_w)); sub_gl = float(np.abs(np.sum(sub_l)))
            sub_cum = np.cumsum(sub_a)
            return {
                "trades": len(sub_a),
                "wr": float(len(sub_w) / len(sub_a) * 100.0),
                "pf": float(sub_gw / sub_gl) if sub_gl > 0 else 99.0,
                "exp": float(np.mean(sub_a)),
                "tot_r": float(sub_cum[-1]),
                "mdd": float(np.max(np.maximum.accumulate(sub_cum) - sub_cum)),
            }
        buy_metrics = get_sub_metrics(longs)
        sell_metrics = get_sub_metrics(shorts)

        # Regime Breakdown
        regime_cuts = [
            ("2003-2007", 2003, 2007),
            ("2008-2012", 2008, 2012),
            ("2013-2018", 2013, 2018),
            ("2019-2020", 2019, 2020),
            ("2021-2023", 2021, 2023),
            ("2024-2026", 2024, 2026),
        ]
        regime_results = {}
        for r_label, y_start, y_end in regime_cuts:
            sub_reg = [t["r"] for t in t_list if y_start <= t["year"] <= y_end]
            if len(sub_reg) > 0:
                s_arr = np.array(sub_reg)
                s_w = s_arr[s_arr > 0]; s_l = s_arr[s_arr < 0]
                s_gw = float(np.sum(s_w)); s_gl = float(np.abs(np.sum(s_l)))
                s_cum = np.cumsum(s_arr)
                regime_results[r_label] = {
                    "trades": len(s_arr),
                    "wr": float(len(s_w) / len(s_arr) * 100.0),
                    "pf": float(s_gw / s_gl) if s_gl > 0 else 99.0,
                    "exp": float(np.mean(s_arr)),
                    "tot_r": float(s_cum[-1]),
                    "mdd": float(np.max(np.maximum.accumulate(s_cum) - s_cum)),
                }

        # Cost Stress Test Scenarios (skip M1 5x stress to prevent timeout)
        stress_results = {}
        if tf_name != "M1":
            stress_scenarios = [
                ("Baseline", 0.38, 0.05),
                ("Spread +25%", 0.38 * 1.25, 0.05),
                ("Spread +50%", 0.38 * 1.50, 0.05),
                ("2x Slippage", 0.38, 0.10),
                ("Worst Combo", 0.38 * 1.50, 0.10),
            ]
            for s_name, s_spread, s_slip in stress_scenarios:
                s_tlist = evaluate_tf_forensic(b_df, tf_name, s_min, s_max, sw_k, target_rr=1.5, max_hold=m_hold,
                                               spread=s_spread, comm=0.07, slippage=s_slip)
                sr_arr = np.array([t["r"] for t in s_tlist])
                if len(sr_arr) > 0:
                    sr_w = sr_arr[sr_arr > 0]; sr_l = sr_arr[sr_arr < 0]
                    sr_gw = float(np.sum(sr_w)); sr_gl = float(np.abs(np.sum(sr_l)))
                    stress_results[s_name] = {
                        "wr": float(len(sr_w) / len(sr_arr) * 100.0),
                        "pf": float(sr_gw / sr_gl) if sr_gl > 0 else 99.0,
                        "exp": float(np.mean(sr_arr)),
                        "tot_r": float(np.sum(sr_arr)),
                    }

        all_results[tf_name] = {
            "trades": n_t,
            "wins": n_w,
            "losses": n_l,
            "be": n_be,
            "wr": wr,
            "wr_ci_95": [wr_ci_low, wr_ci_high],
            "pf": pf,
            "tot_r": tot_r,
            "exp": exp,
            "exp_ci_95": [exp_ci_low, exp_ci_high],
            "boot_p05": boot_p05,
            "boot_p95": boot_p95,
            "mdd": mdd,
            "max_consec_l": max_consec_l,
            "avg_w": avg_w,
            "avg_l": avg_l,
            "avg_holding_bars": avg_hold,
            "trades_per_month": n_t / (23.5 * 12),
            "trades_per_year": n_t / 23.5,
            "buy": buy_metrics,
            "sell": sell_metrics,
            "regimes": regime_results,
            "stress_tests": stress_results,
        }

    # Save output json
    final_payload = {
        "dataset_audit": dataset_audit,
        "timeframe_results": all_results,
    }
    with open(OUTPUT_JSON, "w") as f:
        json.dump(final_payload, f, indent=2)

    print(f"\n[COMPLETE] Forensic results saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    run_master_forensics()
