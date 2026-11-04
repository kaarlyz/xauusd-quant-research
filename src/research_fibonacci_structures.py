#!/usr/bin/env python3
"""
Comprehensive Empirical Scan: Fibonacci Structures & Levels on XAUUSD (2015 - 2026).
Investigates 4 Fundamental Ways to Anchor Fibonacci:
1. Structure A: Previous Day Range (PDL to PDH) Retracement
2. Structure B: Asian Session Range (Asia Low to Asia High) Retracement during London/NY
3. Structure C: M15 Fractal Swing High/Low (Optimal Trade Entry / OTE)
4. Structure D: Opening Session Impulse Range (London 1-Hour Drive)

Scans Retracement Levels:
- 38.2% (0.382)
- 50.0% (0.500)
- 61.8% (0.618 - Golden Ratio)
- 70.5% (0.705 - OTE)
- 78.6% (0.786 - Deep Retrace)

Measures: Bounce probability (WR), Expectancy in R, Profit Factor with $0.50 spread friction.
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD = 0.50

def run_fibo_investigation():
    print("=== Loading 12-Year Dataset ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour")
    )
    df = df.filter(~pl.col("hour").is_between(21, 23))

    # Build M15 bars
    m15 = df.group_by("m15_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("timestamp").first().alias("ts"),
        pl.col("year").first(), pl.col("date").first(), pl.col("hour").first()
    ]).sort("m15_ts")

    o_15 = m15["open"].to_numpy(); h_15 = m15["high"].to_numpy(); l_15 = m15["low"].to_numpy(); c_15 = m15["close"].to_numpy()
    dates_15 = m15["date"].to_numpy(); hours_15 = m15["hour"].to_numpy(); years_15 = m15["year"].to_numpy()
    n_15 = len(o_15)

    # 20-period ATR on M15
    ranges = h_15 - l_15; cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr15 = (cumsum[20:] - cumsum[:-20]) / 20.0
    atr15 = np.pad(atr15, (20, 0), mode="edge")[:n_15]

    unique_days = np.unique(dates_15)
    print(f"Total M15 Bars: {n_15:,} across {len(unique_days):,} Trading Days")

    fibo_levels = [0.382, 0.500, 0.618, 0.705, 0.786]

    # =========================================================================
    # STRUCTURE 1: ASIAN SESSION RANGE (00:00 - 06:00 UTC) RETRACEMENT IN LONDON
    # =========================================================================
    print("\n" + "=" * 90)
    print("STRUCTURE 1: ASIAN SESSION RANGE (Asia Low to Asia High) RETRACEMENT IN LONDON")
    print("Test: When London pulls into Asian Fibo level, does it bounce back in Asia's direction?")
    print("=" * 90)
    print(f"{'Fibo Level':<12} | {'Trades':<8} | {'Win Rate (1.0R)':<16} | {'Win Rate (1.5R)':<16} | {'PF (1.5R)':<10} | {'Net Exp'}")
    print("-" * 90)

    for lvl in fibo_levels:
        trades_15r = []
        trades_10r = []
        for d in unique_days:
            day_mask = (dates_15 == d)
            d_idx = np.where(day_mask)[0]
            if len(d_idx) < 30: continue

            # Asia: hours 0 to 5
            asia_idx = [i for i in d_idx if hours_15[i] <= 5]
            if len(asia_idx) < 15: continue
            a_h = np.max(h_15[asia_idx]); a_l = np.min(l_15[asia_idx])
            a_span = a_h - a_l
            if a_span < 3.0 or a_span > 35.0: continue

            # Asia Trend direction
            asia_trend = c_15[asia_idx[-1]] > o_15[asia_idx[0]] # True if Bullish Asia

            # London: hours 7 to 13
            lon_idx = [i for i in d_idx if 7 <= hours_15[i] <= 13]
            if not lon_idx: continue

            # Bullish Asia: Price pulls down into Fibo level (a_h - lvl * a_span) -> Bounce Long!
            if asia_trend:
                bounce_price = a_h - (lvl * a_span)
                sl_price = a_l - (SPREAD / 2.0)
                risk = (bounce_price + (SPREAD / 2.0)) - sl_price
                if 1.5 <= risk <= 25.0:
                    entry = bounce_price + (SPREAD / 2.0)
                    tp_10 = entry + (1.0 * risk)
                    tp_15 = entry + (1.5 * risk)

                    triggered = False
                    for idx_pos, i in enumerate(lon_idx):
                        if l_15[i] <= bounce_price:
                            triggered = True
                            # Forward test
                            sub = lon_idx[idx_pos:]
                            # 1.5R
                            r_15 = -1.0
                            for j in sub:
                                if l_15[j] <= sl_price: r_15 = -1.0; break
                                elif h_15[j] >= tp_15: r_15 = 1.5; break
                            trades_15r.append(r_15)
                            # 1.0R
                            r_10 = -1.0
                            for j in sub:
                                if l_15[j] <= sl_price: r_10 = -1.0; break
                                elif h_15[j] >= tp_10: r_10 = 1.0; break
                            trades_10r.append(r_10)
                            break

            # Bearish Asia: Price pulls up into Fibo level (a_l + lvl * a_span) -> Bounce Short!
            else:
                bounce_price = a_l + (lvl * a_span)
                sl_price = a_h + (SPREAD / 2.0)
                risk = sl_price - (bounce_price - (SPREAD / 2.0))
                if 1.5 <= risk <= 25.0:
                    entry = bounce_price - (SPREAD / 2.0)
                    tp_10 = entry - (1.0 * risk)
                    tp_15 = entry - (1.5 * risk)

                    triggered = False
                    for idx_pos, i in enumerate(lon_idx):
                        if h_15[i] >= bounce_price:
                            triggered = True
                            sub = lon_idx[idx_pos:]
                            r_15 = -1.0
                            for j in sub:
                                if h_15[j] >= sl_price: r_15 = -1.0; break
                                elif l_15[j] <= tp_15: r_15 = 1.5; break
                            trades_15r.append(r_15)
                            r_10 = -1.0
                            for j in sub:
                                if h_15[j] >= sl_price: r_10 = -1.0; break
                                elif l_15[j] <= tp_10: r_10 = 1.0; break
                            trades_10r.append(r_10)
                            break

        wr_10 = sum(1 for r in trades_10r if r > 0) / len(trades_10r) * 100 if trades_10r else 0
        wr_15 = sum(1 for r in trades_15r if r > 0) / len(trades_15r) * 100 if trades_15r else 0
        gw = sum(r for r in trades_15r if r > 0); gl = abs(sum(r for r in trades_15r if r < 0))
        pf_15 = gw / gl if gl > 0 else 99.0
        exp_15 = np.mean(trades_15r) if trades_15r else 0.0
        print(f"Fibo {lvl*100:4.1f}%  | {len(trades_15r):<8,} | {wr_10:5.1f}%          | {wr_15:5.1f}%          | {pf_15:6.2f}     | {exp_15:+.3f} R")

    # =========================================================================
    # STRUCTURE 2: PREVIOUS DAY HIGH/LOW (PDH to PDL) RETRACEMENT TODAY
    # =========================================================================
    print("\n" + "=" * 90)
    print("STRUCTURE 2: PREVIOUS DAY RANGE (PDH to PDL) EQUILIBRIUM & OTE")
    print("Test: Today's bounce at Previous Day's 50%, 61.8%, 70.5% in the direction of Daily Trend")
    print("=" * 90)
    print(f"{'Fibo Level':<12} | {'Trades':<8} | {'Win Rate (1.0R)':<16} | {'Win Rate (1.5R)':<16} | {'PF (1.5R)':<10} | {'Net Exp'}")
    print("-" * 90)

    daily_h = {}; daily_l = {}; daily_c = {}; daily_o = {}
    for d in unique_days:
        sub = [i for i in range(n_15) if dates_15[i] == d]
        if len(sub) >= 30:
            daily_h[d] = np.max(h_15[sub])
            daily_l[d] = np.min(l_15[sub])
            daily_o[d] = o_15[sub[0]]
            daily_c[d] = c_15[sub[-1]]

    for lvl in fibo_levels:
        trades_15r = []
        trades_10r = []
        for idx_d in range(1, len(unique_days)):
            prev_d = unique_days[idx_d - 1]
            cur_d = unique_days[idx_d]
            if prev_d not in daily_h or cur_d not in daily_h: continue

            pdh = daily_h[prev_d]; pdl = daily_l[prev_d]
            pdo = daily_o[prev_d]; pdc = daily_c[prev_d]
            pd_span = pdh - pdl
            if pd_span < 5.0 or pd_span > 70.0: continue

            is_bull_day = pdc > pdo

            cur_idx = [i for i in range(n_15) if dates_15[i] == cur_d]
            if len(cur_idx) < 30: continue

            # Bullish Day: Retracement down into Fibo level (pdh - lvl * pd_span) -> Buy
            if is_bull_day:
                bounce_price = pdh - (lvl * pd_span)
                sl_price = pdl - (SPREAD / 2.0)
                risk = (bounce_price + (SPREAD / 2.0)) - sl_price
                if 2.0 <= risk <= 40.0:
                    entry = bounce_price + (SPREAD / 2.0)
                    tp_10 = entry + (1.0 * risk)
                    tp_15 = entry + (1.5 * risk)

                    for idx_pos, i in enumerate(cur_idx):
                        if l_15[i] <= bounce_price:
                            sub = cur_idx[idx_pos:]
                            r_15 = -1.0
                            for j in sub:
                                if l_15[j] <= sl_price: r_15 = -1.0; break
                                elif h_15[j] >= tp_15: r_15 = 1.5; break
                            trades_15r.append(r_15)
                            r_10 = -1.0
                            for j in sub:
                                if l_15[j] <= sl_price: r_10 = -1.0; break
                                elif h_15[j] >= tp_10: r_10 = 1.0; break
                            trades_10r.append(r_10)
                            break

            # Bearish Day: Retracement up into Fibo level (pdl + lvl * pd_span) -> Sell
            else:
                bounce_price = pdl + (lvl * pd_span)
                sl_price = pdh + (SPREAD / 2.0)
                risk = sl_price - (bounce_price - (SPREAD / 2.0))
                if 2.0 <= risk <= 40.0:
                    entry = bounce_price - (SPREAD / 2.0)
                    tp_10 = entry - (1.0 * risk)
                    tp_15 = entry - (1.5 * risk)

                    for idx_pos, i in enumerate(cur_idx):
                        if h_15[i] >= bounce_price:
                            sub = cur_idx[idx_pos:]
                            r_15 = -1.0
                            for j in sub:
                                if h_15[j] >= sl_price: r_15 = -1.0; break
                                elif l_15[j] <= tp_15: r_15 = 1.5; break
                            trades_15r.append(r_15)
                            r_10 = -1.0
                            for j in sub:
                                if h_15[j] >= sl_price: r_10 = -1.0; break
                                elif l_15[j] <= tp_10: r_10 = 1.0; break
                            trades_10r.append(r_10)
                            break

        wr_10 = sum(1 for r in trades_10r if r > 0) / len(trades_10r) * 100 if trades_10r else 0
        wr_15 = sum(1 for r in trades_15r if r > 0) / len(trades_15r) * 100 if trades_15r else 0
        gw = sum(r for r in trades_15r if r > 0); gl = abs(sum(r for r in trades_15r if r < 0))
        pf_15 = gw / gl if gl > 0 else 99.0
        exp_15 = np.mean(trades_15r) if trades_15r else 0.0
        print(f"Fibo {lvl*100:4.1f}%  | {len(trades_15r):<8,} | {wr_10:5.1f}%          | {wr_15:5.1f}%          | {pf_15:6.2f}     | {exp_15:+.3f} R")

    # =========================================================================
    # STRUCTURE 3: M15 FRACTAL SWING (OPTIMAL TRADE ENTRY - OTE)
    # =========================================================================
    print("\n" + "=" * 90)
    print("STRUCTURE 3: M15 FRACTAL SWING HIGH/LOW PULLBACK (OTE RETEST)")
    print("Test: Swing High to Swing Low retracements on M15")
    print("=" * 90)
    print(f"{'Fibo Level':<12} | {'Trades':<8} | {'Win Rate (1.0R)':<16} | {'Win Rate (1.5R)':<16} | {'PF (1.5R)':<10} | {'Net Exp'}")
    print("-" * 90)

    # Detect swings: 5-bar swing high/low
    # Swing High at i-2: h[i-2] is highest of i-4, i-3, i-2, i-1, i
    # Swing Low at i-2: l[i-2] is lowest of i-4, i-3, i-2, i-1, i
    for lvl in fibo_levels:
        trades_15r = []
        trades_10r = []
        last_trade_idx = -1

        for i in range(30, n_15 - 35):
            if i <= last_trade_idx: continue
            cur_atr = atr15[i]
            if cur_atr < 0.5: continue

            # Check if there is an impulsive swing in last 15 bars
            lookback = 15
            sub_h = h_15[i-lookback : i]
            sub_l = l_15[i-lookback : i]
            sw_max = np.max(sub_h); max_pos = np.argmax(sub_h)
            sw_min = np.min(sub_l); min_pos = np.argmin(sub_l)
            span = sw_max - sw_min

            if span < 2.0 * cur_atr or span > 40.0: continue

            # Bullish impulse: min occurred BEFORE max (trend up)
            if min_pos < max_pos and (max_pos - min_pos) >= 3:
                # Retracement down into level
                bounce = sw_max - (lvl * span)
                sl = sw_min - (SPREAD / 2.0)
                risk = (bounce + (SPREAD / 2.0)) - sl
                if 1.5 <= risk <= 20.0:
                    entry = bounce + (SPREAD / 2.0)
                    tp_10 = entry + (1.0 * risk)
                    tp_15 = entry + (1.5 * risk)

                    # Check if bar i touches bounce
                    if l_15[i] <= bounce and c_15[i] >= bounce - (0.5 * cur_atr):
                        outcome_15 = -1.0; outcome_10 = -1.0
                        exit_b = i + 20
                        for s in range(1, 21):
                            if l_15[i+s] <= sl: outcome_15 = -1.0; outcome_10 = -1.0; exit_b = i+s; break
                            if h_15[i+s] >= tp_10 and outcome_10 < 0: outcome_10 = 1.0
                            if h_15[i+s] >= tp_15: outcome_15 = 1.5; exit_b = i+s; break
                        trades_15r.append(outcome_15)
                        trades_10r.append(outcome_10)
                        last_trade_idx = exit_b

            # Bearish impulse: max occurred BEFORE min (trend down)
            elif max_pos < min_pos and (min_pos - max_pos) >= 3:
                bounce = sw_min + (lvl * span)
                sl = sw_max + (SPREAD / 2.0)
                risk = sl - (bounce - (SPREAD / 2.0))
                if 1.5 <= risk <= 20.0:
                    entry = bounce - (SPREAD / 2.0)
                    tp_10 = entry - (1.0 * risk)
                    tp_15 = entry - (1.5 * risk)

                    if h_15[i] >= bounce and c_15[i] <= bounce + (0.5 * cur_atr):
                        outcome_15 = -1.0; outcome_10 = -1.0
                        exit_b = i + 20
                        for s in range(1, 21):
                            if h_15[i+s] >= sl: outcome_15 = -1.0; outcome_10 = -1.0; exit_b = i+s; break
                            if l_15[i+s] <= tp_10 and outcome_10 < 0: outcome_10 = 1.0
                            if l_15[i+s] <= tp_15: outcome_15 = 1.5; exit_b = i+s; break
                        trades_15r.append(outcome_15)
                        trades_10r.append(outcome_10)
                        last_trade_idx = exit_b

        wr_10 = sum(1 for r in trades_10r if r > 0) / len(trades_10r) * 100 if trades_10r else 0
        wr_15 = sum(1 for r in trades_15r if r > 0) / len(trades_15r) * 100 if trades_15r else 0
        gw = sum(r for r in trades_15r if r > 0); gl = abs(sum(r for r in trades_15r if r < 0))
        pf_15 = gw / gl if gl > 0 else 99.0
        exp_15 = np.mean(trades_15r) if trades_15r else 0.0
        print(f"Fibo {lvl*100:4.1f}%  | {len(trades_15r):<8,} | {wr_10:5.1f}%          | {wr_15:5.1f}%          | {pf_15:6.2f}     | {exp_15:+.3f} R")

if __name__ == "__main__":
    run_fibo_investigation()
