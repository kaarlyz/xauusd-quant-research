#!/usr/bin/env python3
"""
Quantitative Stress-Test of YouTube Strategy:
"Cara Menentukan Momentum Candle XAUUSD" (Video ID: c62Tj28zfyQ)

Rules directly transcribed from video:
1. Timeframe: M5 (resampled from institutional M1 ticks).
2. Setup: 3 to 5 small consolidation candles followed by 1 Long Momentum Candle (body >= 65%, wicks <= 20%)
   that breaks and closes outside the 3-5 candle consolidation range.
3. Fibonacci Measurement: From consolidation swing start to momentum candle peak/trough.
4. Levels:
   - Entry: 23.6% Retracement (Level 0.236)
   - Secondary Aggressive Entry: 61.8% Retracement (Level 0.618)
   - Stop Loss: 74.5% Retracement (Level 0.745)
   - Take Profit: -27.0% Extension (Level -0.27)
5. Horizon: 12 Years (2015 - 2026 / 4.18M M1 candles -> 764,000 M5 bars).
6. Friction: $0.50 round-trip spread cost + intrabar pessimistic SL checking.
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD = 0.50

def run_backtest():
    print("=== Loading M1 Data & Resampling to M5 ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (5 * 60 * 1000) * (5 * 60 * 1000)).alias("m5_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    df = df.filter(~pl.col("hour").is_between(21, 23))

    m5 = df.group_by("m5_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("hour").first()
    ]).sort("m5_ts")

    o = m5["open"].to_numpy()
    h = m5["high"].to_numpy()
    l = m5["low"].to_numpy()
    c = m5["close"].to_numpy()
    years = m5["year"].to_numpy()
    n = len(o)

    # 30-bar ATR
    ranges = h - l
    cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr = (cumsum[30:] - cumsum[:-30]) / 30.0
    atr = np.pad(atr, (30, 0), mode="edge")[:n]

    print(f"Total M5 Candles: {n:,} (2015 - 2026)")

    # Test two variations from the video:
    # Variation 1: Entry at 23.6% Fibo (Standard from video)
    # Variation 2: Entry at 61.8% Fibo (Aggressive Layer from video)
    for entry_fibo_lvl, lvl_name in [(0.236, "FIBO 23.6% (Standard)"), (0.618, "FIBO 61.8% (Deep Retest)")]:
        trades = []
        last_exit = -1

        for i in range(10, n - 35):
            if i <= last_exit: continue
            cur_atr = atr[i]
            if cur_atr < 0.4: continue

            # Step 1: Preceding 3 to 5 candles must be small consolidation
            # Let's inspect bars i-4, i-3, i-2, i-1 (4 bars)
            pre_h = np.max(h[i-4 : i])
            pre_l = np.min(l[i-4 : i])
            pre_range = pre_h - pre_l

            # Step 2: Bar i is the Momentum Candle
            rng_i = h[i] - l[i]
            body_i = abs(c[i] - o[i])
            if rng_i < 1.2 * cur_atr or (body_i / rng_i) < 0.65:
                continue

            # Check if Bar i breaks and closes clearly outside pre_range
            is_bull_breakout = (c[i] > pre_h) and (c[i] > o[i])
            is_bear_breakout = (c[i] < pre_l) and (c[i] < o[i])

            if not (is_bull_breakout or is_bear_breakout):
                continue

            # Fibonacci calculations:
            # 1. Bullish Momentum: swing from pre_l to h[i]
            if is_bull_breakout:
                swing_low = pre_l
                swing_high = h[i]
                swing_span = swing_high - swing_low
                if swing_span < 1.5: continue

                # Entry at retracement level from swing_high down
                # 23.6% retracement = swing_high - 0.236 * span
                entry_level = swing_high - (entry_fibo_lvl * swing_span)
                sl_level = swing_high - (0.745 * swing_span)
                tp_level = swing_high + (0.27 * swing_span)

                # Wait up to 10 bars for price to retrace and hit entry_level
                triggered = False
                trig_bar = -1
                for step in range(1, 11):
                    chk_idx = i + step
                    if chk_idx >= n: break
                    if l[chk_idx] <= entry_level:
                        triggered = True
                        trig_bar = chk_idx
                        break
                    # If price already hits TP or breaks below SL before entry, cancel setup
                    if h[chk_idx] >= tp_level or l[chk_idx] <= sl_level:
                        break

                if not triggered: continue

                entry = entry_level + (SPREAD / 2.0)
                sl = sl_level - (SPREAD / 2.0)
                risk = entry - sl
                tp = tp_level

                if risk < 0.80 or risk > 25.0: continue
                target_rr = (tp - entry) / risk
                if target_rr <= 0: continue

                outcome = 0; r_val = 0.0; exit_idx = trig_bar + 24 # hold up to 2 hours
                for s in range(1, 25):
                    cur = trig_bar + s
                    if cur >= n: break
                    if l[cur] <= sl: r_val = -1.0; outcome = -1; exit_idx = cur; break
                    elif h[cur] >= tp: r_val = target_rr; outcome = 1; exit_idx = cur; break
                if outcome == 0 and exit_idx < n:
                    r_val = (c[exit_idx] - entry) / risk
                last_exit = exit_idx
                trades.append({"r": r_val, "rr": target_rr, "year": years[trig_bar]})

            # 2. Bearish Momentum: swing from pre_h to l[i]
            elif is_bear_breakout:
                swing_high = pre_h
                swing_low = l[i]
                swing_span = swing_high - swing_low
                if swing_span < 1.5: continue

                entry_level = swing_low + (entry_fibo_lvl * swing_span)
                sl_level = swing_low + (0.745 * swing_span)
                tp_level = swing_low - (0.27 * swing_span)

                triggered = False
                trig_bar = -1
                for step in range(1, 11):
                    chk_idx = i + step
                    if chk_idx >= n: break
                    if h[chk_idx] >= entry_level:
                        triggered = True
                        trig_bar = chk_idx
                        break
                    if l[chk_idx] <= tp_level or h[chk_idx] >= sl_level:
                        break

                if not triggered: continue

                entry = entry_level - (SPREAD / 2.0)
                sl = sl_level + (SPREAD / 2.0)
                risk = sl - entry
                tp = tp_level

                if risk < 0.80 or risk > 25.0: continue
                target_rr = (entry - tp) / risk
                if target_rr <= 0: continue

                outcome = 0; r_val = 0.0; exit_idx = trig_bar + 24
                for s in range(1, 25):
                    cur = trig_bar + s
                    if cur >= n: break
                    if h[cur] >= sl: r_val = -1.0; outcome = -1; exit_idx = cur; break
                    elif l[cur] <= tp: r_val = target_rr; outcome = 1; exit_idx = cur; break
                if outcome == 0 and exit_idx < n:
                    r_val = (entry - c[exit_idx]) / risk
                last_exit = exit_idx
                trades.append({"r": r_val, "rr": target_rr, "year": years[trig_bar]})

        print("\n" + "=" * 80)
        print(f"RESULTS FOR: {lvl_name}")
        print("SL at Fibo 74.5% | TP at Fibo -27% | Intrabar Pessimistic Execution")
        print("=" * 80)
        if not trades:
            print("No trades triggered.")
            continue

        r_all = [t["r"] for t in trades]
        rr_all = [t["rr"] for t in trades]
        wr = sum(1 for r in r_all if r > 0) / len(r_all) * 100
        gw = sum(r for r in r_all if r > 0); gl = abs(sum(r for r in r_all if r < 0))
        pf = gw / gl if gl > 0 else 99.0
        cum = np.cumsum(r_all)
        mdd = np.max(np.maximum.accumulate(cum) - cum)

        print(f"Total Trades        : {len(trades):,} over 12 Years")
        print(f"Average Target RR   : {np.mean(rr_all):.2f} : 1")
        print(f"Win Rate (WR)       : {wr:.1f}%")
        print(f"Net Expectancy      : {np.mean(r_all):+.3f} R / trade")
        print(f"Profit Factor (PF)  : {pf:.2f}")
        print(f"Max Drawdown (MDD)  : -{mdd:.1f} R")
        print(f"Total Cumulative R  : {cum[-1]:+.1f} R")

        # By Year breakdown
        print("\nYear-by-Year Performance Breakdown:")
        for y in range(2015, 2027):
            sub = [t["r"] for t in trades if t["year"] == y]
            if sub:
                sub_w = sum(1 for r in sub if r > 0)
                sub_wr = (sub_w / len(sub)) * 100
                sub_gw = sum(r for r in sub if r > 0); sub_gl = abs(sum(r for r in sub if r < 0))
                sub_pf = sub_gw / sub_gl if sub_gl > 0 else 99.0
                print(f"  Year {y}: N = {len(sub):<3} | WR = {sub_wr:4.1f}% | Exp = {np.mean(sub):+.3f}R | PF = {sub_pf:.2f}")

if __name__ == "__main__":
    run_backtest()
