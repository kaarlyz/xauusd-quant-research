#!/usr/bin/env python3
"""
Quantitative Research: Two-Bar Solid Counter-Impulse ("Railroad Tracks" / Tweezer Reversal).
Pattern definition:
- Bar 1: Strong solid body (body ratio >= 65%, wicks <= 20%).
- Bar 2: Strong solid body in opposite direction (body ratio >= 65%, wicks <= 20%), similar size.

Tests:
1. Bull -> Bear (Green then Red): Sell at close of Bar 2? Or Buy?
2. Bear -> Bull (Red then Green): Buy at close of Bar 2? Or Sell?
3. Evaluates on M1 and M5 timeframes across 12 years (2015-2026).
4. Tests RR 1.0, 1.2, 1.5, 2.0 with $0.50 spread friction.
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD = 0.50

def run_two_bar_research():
    print("=== Loading 12-Year M1 Data (4.18M bars) ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    df = df.filter(~pl.col("hour").is_between(21, 23))

    opens = df["open"].to_numpy()
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    closes = df["close"].to_numpy()
    hours = df["hour"].to_numpy()
    years = df["year"].to_numpy()
    n = len(df)

    # 60-bar ATR
    ranges = highs - lows
    cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr = (cumsum[60:] - cumsum[:-60]) / 60.0
    atr = np.pad(atr, (60, 0), mode="edge")[:n]

    print(f"Total M1 candles: {n:,}")

    def evaluate_pattern(tf_name, o_arr, h_arr, l_arr, c_arr, atr_arr, yr_arr, hr_arr):
        total_len = len(o_arr)
        print(f"\n=======================================================")
        print(f"EVALUATING TWO-BAR PATTERN ON {tf_name} (12-YEAR VERIFICATION)")
        print(f"=======================================================")

        # Find all valid pattern pairs: Bar i-1 and Bar i
        # We test:
        # Pattern A: Bull -> Bear (Green then Red)
        # Pattern B: Bear -> Bull (Red then Green)

        for mode_name, direction_type in [("FOLLOW CANDLE 2 (Standard Reversal)", "follow"), ("FADE CANDLE 2 (Continuation)", "fade")]:
            print(f"\n--- Strategy Mode: {mode_name} ---")
            for rr in [1.0, 1.2, 1.5, 2.0]:
                bull_bear_trades = []
                bear_bull_trades = []
                last_exit = -1

                for i in range(65, total_len - 35):
                    if i <= last_exit: continue

                    cur_atr = atr_arr[i]
                    if cur_atr < 0.2: continue

                    # Candle 1 (i-1)
                    rng1 = h_arr[i-1] - l_arr[i-1]
                    body1 = abs(c_arr[i-1] - o_arr[i-1])
                    if rng1 < 0.5 * cur_atr or rng1 == 0: continue
                    body_ratio1 = body1 / rng1

                    # Candle 2 (i)
                    rng2 = h_arr[i] - l_arr[i]
                    body2 = abs(c_arr[i] - o_arr[i])
                    if rng2 < 0.5 * cur_atr or rng2 == 0: continue
                    body_ratio2 = body2 / rng2

                    # Shape condition: solid bodies (>= 65% body ratio)
                    if body_ratio1 < 0.65 or body_ratio2 < 0.65: continue

                    # Size similarity (0.6x to 1.6x)
                    size_ratio = rng2 / rng1
                    if not (0.60 <= size_ratio <= 1.60): continue

                    is_c1_bull = c_arr[i-1] > o_arr[i-1]
                    is_c1_bear = c_arr[i-1] < o_arr[i-1]
                    is_c2_bull = c_arr[i] > o_arr[i]
                    is_c2_bear = c_arr[i] < o_arr[i]

                    # 1. Bull -> Bear (Green then Red)
                    if is_c1_bull and is_c2_bear:
                        if direction_type == "follow":
                            # Enter SHORT at close of red candle
                            entry = c_arr[i] - (SPREAD / 2.0)
                            sl = max(h_arr[i-1], h_arr[i]) + (SPREAD / 2.0)
                            risk = sl - entry
                            if 0.80 <= risk <= 15.0:
                                tp = entry - (rr * risk)
                                outcome = 0; r_val = 0.0; exit_idx = i + 25
                                for s in range(1, 26):
                                    if h_arr[i+s] >= sl: r_val = -1.0; outcome = -1; exit_idx = i+s; break
                                    elif l_arr[i+s] <= tp: r_val = rr; outcome = 1; exit_idx = i+s; break
                                if outcome == 0: r_val = (entry - c_arr[i+25]) / risk
                                last_exit = exit_idx
                                bull_bear_trades.append(r_val)

                        elif direction_type == "fade":
                            # Fade it: Enter LONG
                            entry = c_arr[i] + (SPREAD / 2.0)
                            sl = min(l_arr[i-1], l_arr[i]) - (SPREAD / 2.0)
                            risk = entry - sl
                            if 0.80 <= risk <= 15.0:
                                tp = entry + (rr * risk)
                                outcome = 0; r_val = 0.0; exit_idx = i + 25
                                for s in range(1, 26):
                                    if l_arr[i+s] <= sl: r_val = -1.0; outcome = -1; exit_idx = i+s; break
                                    elif h_arr[i+s] >= tp: r_val = rr; outcome = 1; exit_idx = i+s; break
                                if outcome == 0: r_val = (c_arr[i+25] - entry) / risk
                                last_exit = exit_idx
                                bull_bear_trades.append(r_val)

                    # 2. Bear -> Bull (Red then Green)
                    elif is_c1_bear and is_c2_bull:
                        if direction_type == "follow":
                            # Enter LONG at close of green candle
                            entry = c_arr[i] + (SPREAD / 2.0)
                            sl = min(l_arr[i-1], l_arr[i]) - (SPREAD / 2.0)
                            risk = entry - sl
                            if 0.80 <= risk <= 15.0:
                                tp = entry + (rr * risk)
                                outcome = 0; r_val = 0.0; exit_idx = i + 25
                                for s in range(1, 26):
                                    if l_arr[i+s] <= sl: r_val = -1.0; outcome = -1; exit_idx = i+s; break
                                    elif h_arr[i+s] >= tp: r_val = rr; outcome = 1; exit_idx = i+s; break
                                if outcome == 0: r_val = (c_arr[i+25] - entry) / risk
                                last_exit = exit_idx
                                bear_bull_trades.append(r_val)

                        elif direction_type == "fade":
                            # Fade it: Enter SHORT
                            entry = c_arr[i] - (SPREAD / 2.0)
                            sl = max(h_arr[i-1], h_arr[i]) + (SPREAD / 2.0)
                            risk = sl - entry
                            if 0.80 <= risk <= 15.0:
                                tp = entry - (rr * risk)
                                outcome = 0; r_val = 0.0; exit_idx = i + 25
                                for s in range(1, 26):
                                    if h_arr[i+s] >= sl: r_val = -1.0; outcome = -1; exit_idx = i+s; break
                                    elif l_arr[i+s] <= tp: r_val = rr; outcome = 1; exit_idx = i+s; break
                                if outcome == 0: r_val = (entry - c_arr[i+25]) / risk
                                last_exit = exit_idx
                                bear_bull_trades.append(r_val)

                def print_stats(name, t_list):
                    if not t_list: return
                    n_t = len(t_list)
                    wr = sum(1 for r in t_list if r > 0) / n_t * 100
                    gw = sum(r for r in t_list if r > 0); gl = abs(sum(r for r in t_list if r < 0))
                    pf = gw / gl if gl > 0 else 99.0
                    print(f"  {name:<25} | RR {rr:.1f}:1 | N = {n_t:,} | WR = {wr:4.1f}% | Net Exp = {np.mean(t_list):+.3f}R | PF = {pf:.2f}")

                print_stats("Bull -> Bear (Tweezer Top)", bull_bear_trades)
                print_stats("Bear -> Bull (Tweezer Bottom)", bear_bull_trades)

    # 1. Run on M1
    evaluate_pattern("M1 TIMEFRAME", opens, highs, lows, closes, atr, years, hours)

    # 2. Downsample to M5 and run
    df_m5 = df.with_columns((pl.col("timestamp") // (5 * 60 * 1000) * (5 * 60 * 1000)).alias("m5_ts"))
    m5 = df_m5.group_by("m5_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("hour").first()
    ]).sort("m5_ts")

    o_m5 = m5["open"].to_numpy(); h_m5 = m5["high"].to_numpy(); l_m5 = m5["low"].to_numpy(); c_m5 = m5["close"].to_numpy()
    yr_m5 = m5["year"].to_numpy(); hr_m5 = m5["hour"].to_numpy()
    n_m5 = len(o_m5)
    rng_m5 = h_m5 - l_m5; cs_m5 = np.cumsum(np.insert(rng_m5, 0, 0))
    atr_m5 = (cs_m5[30:] - cs_m5[:-30]) / 30.0
    atr_m5 = np.pad(atr_m5, (30, 0), mode="edge")[:n_m5]

    evaluate_pattern("M5 TIMEFRAME", o_m5, h_m5, l_m5, c_m5, atr_m5, yr_m5, hr_m5)

if __name__ == "__main__":
    run_two_bar_research()
