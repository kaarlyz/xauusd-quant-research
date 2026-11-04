#!/usr/bin/env python3
"""
Updates H3_SIGNAL_TO_FILL_FUNNEL.csv with complete side-by-side diagnosis:
1. The Phase 2 discovery script indexing (shift(1), which included bar t-1 in box).
2. The corrected pre-registered specification (shift(2), k=2..31).
Shows exact funnel: Breakouts -> Re-entries -> Orders Placed -> Touch Fills -> 0.10 Fills -> 0.20 Fills -> Realized WR & PF.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import csv
import polars as pl
import numpy as np
from fast_phase2_discovery import (
    load_data_and_features, run_backtest_fast, calculate_detailed_metrics,
    T_IS_START, T_IS_END, T_VAL_START, T_VAL_END
)

df = load_data_and_features()
o = df["open"].to_numpy(); h = df["high"].to_numpy(); l = df["low"].to_numpy(); c = df["close"].to_numpy()
dates = df["date"].to_numpy(); ts = df["timestamp"].to_numpy(); atr14 = df["atr14"].to_numpy()
n = len(o)

# Compute both shift(1) and shift(2) boxes
df = df.with_columns([
    pl.col("high").shift(1).rolling_max(30).alias("h_box_30_s1"),
    pl.col("low").shift(1).rolling_min(30).alias("l_box_30_s1"),
    pl.col("high").shift(2).rolling_max(30).alias("h_box_30_s2"),
    pl.col("low").shift(2).rolling_min(30).alias("l_box_30_s2"),
    pl.col("high").shift(1).rolling_max(45).alias("h_box_45_s1"),
    pl.col("low").shift(1).rolling_min(45).alias("l_box_45_s1"),
    pl.col("high").shift(2).rolling_max(45).alias("h_box_45_s2"),
    pl.col("low").shift(2).rolling_min(45).alias("l_box_45_s2"),
])

c_prev = np.roll(c, 1); o_prev = np.roll(o, 1)
l_prev = np.roll(l, 1); h_prev = np.roll(h, 1)

rows = []

for impl, s_tag in [("Phase2_Discovery_Buggy_Shift1", "s1"), ("Corrected_Spec_Shift2", "s2")]:
    for win in [30, 45]:
        h_box = df[f"h_box_{win}_{s_tag}"].to_numpy()
        l_box = df[f"l_box_{win}_{s_tag}"].to_numpy()
        box_w = h_box - l_box
        box_ok = (box_w >= 3.0) & (box_w <= 12.0)

        bo_long = box_ok & (c_prev < l_box)
        bo_short = box_ok & (c_prev > h_box)
        tot_bo = int(np.sum(bo_long | bo_short))

        for dep in [0.25, 0.40]:
            re_long = bo_long & (c >= l_box + dep * atr14) & ((c - o) > (o_prev - c_prev))
            re_short = bo_short & (c <= h_box - dep * atr14) & ((o - c) > (c_prev - o_prev))
            tot_re = int(np.sum(re_long | re_short))

            sig_indices = np.where(re_long | re_short)[0]
            val_sigs = [i for i in sig_indices if T_VAL_START <= ts[i+1] <= T_VAL_END]

            touch_fills = 0; pen_010_fills = 0; pen_020_fills = 0
            for i in val_sigs:
                if i + 4 >= n: continue
                if re_long[i]:
                    lim_p = l_box[i] + 0.10
                    sub_l = l[i+1 : i+4]; min_l = np.min(sub_l)
                    if min_l <= lim_p: touch_fills += 1
                    if min_l <= lim_p - 0.10: pen_010_fills += 1
                    if min_l <= lim_p - 0.20: pen_020_fills += 1
                else:
                    lim_p = h_box[i] - 0.10
                    sub_h = h[i+1 : i+4]; max_h = np.max(sub_h)
                    if max_h >= lim_p: touch_fills += 1
                    if max_h >= lim_p + 0.10: pen_010_fills += 1
                    if max_h >= lim_p + 0.20: pen_020_fills += 1

            for trr in [0.70, 0.80]:
                exp_id = f"H3_WIN{win}_DEP{int(dep*100)}_RR{int(trr*100)}"
                sigs = []
                for i in sig_indices:
                    if re_long[i]: sigs.append((i, "LONG", l_prev[i] - 0.30, True, l_box[i] + 0.10))
                    elif re_short[i]: sigs.append((i, "SHORT", h_prev[i] + 0.30, True, h_box[i] - 0.10))

                tr = run_backtest_fast(o, h, l, c, dates, ts, sigs, trr, 15)
                val_tr = [t for t in tr if t["partition"] == "VALIDATION"]
                m = calculate_detailed_metrics(val_tr)

                rows.append({
                    "implementation": impl,
                    "experiment_id": exp_id,
                    "window_bars": win,
                    "reentry_depth": dep,
                    "target_rr": trr,
                    "breakouts_count": tot_bo,
                    "reentries_count": tot_re,
                    "val_signals": len(val_sigs),
                    "touch_fills": touch_fills,
                    "pen_010_fills": pen_010_fills,
                    "pen_020_fills": pen_020_fills,
                    "val_executed_trades": m["n"],
                    "val_win_rate": m["wr"],
                    "val_profit_factor": m["pf"],
                    "val_net_exp_r": m["net_exp"]
                })

out_path = "/home/vallencia/xauusd_research/H3_SIGNAL_TO_FILL_FUNNEL.csv"
with open(out_path, "w", newline="") as fp:
    writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print("Updated H3_SIGNAL_TO_FILL_FUNNEL.csv successfully.")
