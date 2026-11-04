#!/usr/bin/env python3
"""
Comprehensive Multi-Timeframe Research: Two-Bar Counter Impulse with Pending Orders.
Tests:
- Order Types: Sell Stop vs Buy Stop (Breakout of Bar 2 extreme vs Fade of Pattern extreme)
- Timeframes: M1, M5, M15
- RR Ratios: 0.5:1 (Negative RR), 0.7:1, 1.0:1, 1.5:1
- Costs: $0.50 spread friction per trade + intrabar pessimistic SL checking
- Dataset: 12 Years (2015 - 2026 / 4,182,209 M1 bars)
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD = 0.50

def run_research():
    print("=== Loading 12-Year M1 Dataset ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    df = df.filter(~pl.col("hour").is_between(21, 23))

    # Helper to resample bars
    def build_tf(minutes_agg):
        if minutes_agg == 1:
            return (
                df["open"].to_numpy(),
                df["high"].to_numpy(),
                df["low"].to_numpy(),
                df["close"].to_numpy(),
                df["year"].to_numpy()
            )
        col_name = f"m{minutes_agg}_ts"
        df_tf = df.with_columns(
            (pl.col("timestamp") // (minutes_agg * 60 * 1000) * (minutes_agg * 60 * 1000)).alias(col_name)
        )
        agg = df_tf.group_by(col_name).agg([
            pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
            pl.col("year").first()
        ]).sort(col_name)
        return (
            agg["open"].to_numpy(),
            agg["high"].to_numpy(),
            agg["low"].to_numpy(),
            agg["close"].to_numpy(),
            agg["year"].to_numpy()
        )

    for tf_min, tf_name in [(1, "M1"), (5, "M5"), (15, "M15")]:
        print(f"\n" + "=" * 95)
        print(f"ANALYZING TWO-BAR SETUP ON {tf_name} (PENDING BUY STOP VS SELL STOP)")
        print(f"=" * 95)
        o, h, l, c, yrs = build_tf(tf_min)
        n = len(o)

        # 30-period ATR
        ranges = h - l
        cumsum = np.cumsum(np.insert(ranges, 0, 0))
        atr = (cumsum[30:] - cumsum[:-30]) / 30.0
        atr = np.pad(atr, (30, 0), mode="edge")[:n]

        # Test both order approaches:
        # Approach 1: BREAKOUT OF BAR 2 (Sell Stop below Bar 2 Low on Bull-Bear; Buy Stop above Bar 2 High on Bear-Bull)
        # Approach 2: FADE / BREAKOUT OF PATTERN EXTREME (Buy Stop above Pattern High on Bull-Bear; Sell Stop below Pattern Low on Bear-Bull)
        for approach_name, is_breakout_bar2 in [
            ("BREAKOUT (Sell Stop on Bull-Bear / Buy Stop on Bear-Bull)", True),
            ("FADE / TRAP BREAKOUT (Buy Stop on Bull-Bear / Sell Stop on Bear-Bull)", False)
        ]:
            print(f"\n--- Strategy: {approach_name} ---")
            print(f"{'Target RR':<10} | {'Trades':<8} | {'Win Rate':<10} | {'Profit Factor':<14} | {'Net Expectancy':<16} | {'Status'}")
            print("-" * 75)

            for rr in [0.5, 0.7, 1.0, 1.5]:
                trades = []
                last_exit = -1
                max_hold_bars = 20 # 20 bars holding limit

                for i in range(35, n - max_hold_bars - 5):
                    if i <= last_exit: continue
                    cur_atr = atr[i]
                    if cur_atr < 0.2: continue

                    rng1 = h[i-1] - l[i-1]; body1 = abs(c[i-1] - o[i-1])
                    rng2 = h[i] - l[i]; body2 = abs(c[i] - o[i])
                    if rng1 == 0 or rng2 == 0: continue
                    if (body1 / rng1) < 0.60 or (body2 / rng2) < 0.60: continue
                    if not (0.50 <= rng2 / rng1 <= 2.0): continue

                    is_c1_bull = c[i-1] > o[i-1]; is_c2_bear = c[i] < o[i]
                    is_c1_bear = c[i-1] < o[i-1]; is_c2_bull = c[i] > o[i]

                    pattern_high = max(h[i-1], h[i])
                    pattern_low = min(l[i-1], l[i])

                    # -----------------------------------------------
                    # Setup 1: Bull -> Bear (Green then Red)
                    # -----------------------------------------------
                    if is_c1_bull and is_c2_bear:
                        if is_breakout_bar2:
                            # Sell Stop below Bar 2 Low
                            trigger_price = l[i]
                            # Check next 3 bars if pending order triggered
                            triggered = False
                            trig_bar = -1
                            for b in range(1, 4):
                                if l[i + b] < trigger_price:
                                    triggered = True
                                    trig_bar = i + b
                                    break
                            if not triggered: continue

                            entry = trigger_price - (SPREAD / 2.0)
                            sl = pattern_high + (SPREAD / 2.0)
                            risk = sl - entry
                            if 0.80 <= risk <= 20.0:
                                tp = entry - (rr * risk)
                                outcome = 0; r_val = 0.0; exit_idx = trig_bar + max_hold_bars
                                for s in range(1, max_hold_bars + 1):
                                    cur_idx = trig_bar + s
                                    if cur_idx >= n: break
                                    if h[cur_idx] >= sl: r_val = -1.0; outcome = -1; exit_idx = cur_idx; break
                                    elif l[cur_idx] <= tp: r_val = rr; outcome = 1; exit_idx = cur_idx; break
                                if outcome == 0 and exit_idx < n:
                                    r_val = (entry - c[exit_idx]) / risk
                                last_exit = exit_idx
                                trades.append(r_val)

                        else:
                            # Fade it: Buy Stop above Pattern High (expecting bear trap)
                            trigger_price = pattern_high
                            triggered = False
                            trig_bar = -1
                            for b in range(1, 4):
                                if h[i + b] > trigger_price:
                                    triggered = True
                                    trig_bar = i + b
                                    break
                            if not triggered: continue

                            entry = trigger_price + (SPREAD / 2.0)
                            sl = pattern_low - (SPREAD / 2.0)
                            risk = entry - sl
                            if 0.80 <= risk <= 20.0:
                                tp = entry + (rr * risk)
                                outcome = 0; r_val = 0.0; exit_idx = trig_bar + max_hold_bars
                                for s in range(1, max_hold_bars + 1):
                                    cur_idx = trig_bar + s
                                    if cur_idx >= n: break
                                    if l[cur_idx] <= sl: r_val = -1.0; outcome = -1; exit_idx = cur_idx; break
                                    elif h[cur_idx] >= tp: r_val = rr; outcome = 1; exit_idx = cur_idx; break
                                if outcome == 0 and exit_idx < n:
                                    r_val = (c[exit_idx] - entry) / risk
                                last_exit = exit_idx
                                trades.append(r_val)

                    # -----------------------------------------------
                    # Setup 2: Bear -> Bull (Red then Green)
                    # -----------------------------------------------
                    elif is_c1_bear and is_c2_bull:
                        if is_breakout_bar2:
                            # Buy Stop above Bar 2 High
                            trigger_price = h[i]
                            triggered = False
                            trig_bar = -1
                            for b in range(1, 4):
                                if h[i + b] > trigger_price:
                                    triggered = True
                                    trig_bar = i + b
                                    break
                            if not triggered: continue

                            entry = trigger_price + (SPREAD / 2.0)
                            sl = pattern_low - (SPREAD / 2.0)
                            risk = entry - sl
                            if 0.80 <= risk <= 20.0:
                                tp = entry + (rr * risk)
                                outcome = 0; r_val = 0.0; exit_idx = trig_bar + max_hold_bars
                                for s in range(1, max_hold_bars + 1):
                                    cur_idx = trig_bar + s
                                    if cur_idx >= n: break
                                    if l[cur_idx] <= sl: r_val = -1.0; outcome = -1; exit_idx = cur_idx; break
                                    elif h[cur_idx] >= tp: r_val = rr; outcome = 1; exit_idx = cur_idx; break
                                if outcome == 0 and exit_idx < n:
                                    r_val = (c[exit_idx] - entry) / risk
                                last_exit = exit_idx
                                trades.append(r_val)

                        else:
                            # Fade it: Sell Stop below Pattern Low
                            trigger_price = pattern_low
                            triggered = False
                            trig_bar = -1
                            for b in range(1, 4):
                                if l[i + b] < trigger_price:
                                    triggered = True
                                    trig_bar = i + b
                                    break
                            if not triggered: continue

                            entry = trigger_price - (SPREAD / 2.0)
                            sl = pattern_high + (SPREAD / 2.0)
                            risk = sl - entry
                            if 0.80 <= risk <= 20.0:
                                tp = entry - (rr * risk)
                                outcome = 0; r_val = 0.0; exit_idx = trig_bar + max_hold_bars
                                for s in range(1, max_hold_bars + 1):
                                    cur_idx = trig_bar + s
                                    if cur_idx >= n: break
                                    if h[cur_idx] >= sl: r_val = -1.0; outcome = -1; exit_idx = cur_idx; break
                                    elif l[cur_idx] <= tp: r_val = rr; outcome = 1; exit_idx = cur_idx; break
                                if outcome == 0 and exit_idx < n:
                                    r_val = (entry - c[exit_idx]) / risk
                                last_exit = exit_idx
                                trades.append(r_val)

                if trades:
                    n_t = len(trades)
                    wr = sum(1 for r in trades if r > 0) / n_t * 100
                    gw = sum(r for r in trades if r > 0); gl = abs(sum(r for r in trades if r < 0))
                    pf = gw / gl if gl > 0 else 99.0
                    avg_r = np.mean(trades)
                    status = "PROFITABLE (Edge!)" if pf >= 1.05 and avg_r > 0 else "RUGI / BEP"
                    print(f"RR {rr:3.1f}:1  | {n_t:<8,} | {wr:5.1f}%    | {pf:10.2f}    | {avg_r:>+9.3f} R / trade | {status}")

if __name__ == "__main__":
    run_research()
