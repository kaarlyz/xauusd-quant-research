#!/usr/bin/env python3
"""
Fast Vectorized Scan: Fibonacci Structures & Levels on XAUUSD (2015 - 2026).
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD = 0.50

def run_fast_fibo():
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour")
    )
    df = df.filter(~pl.col("hour").is_between(21, 23))

    m15 = df.group_by("m15_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first(), pl.col("hour").first()
    ]).sort("m15_ts")

    o_15 = m15["open"].to_numpy(); h_15 = m15["high"].to_numpy(); l_15 = m15["low"].to_numpy(); c_15 = m15["close"].to_numpy()
    dates_15 = m15["date"].to_numpy(); hours_15 = m15["hour"].to_numpy(); years_15 = m15["year"].to_numpy()
    n_15 = len(o_15)

    unique_days = np.unique(dates_15)
    fibo_levels = [0.382, 0.500, 0.618, 0.705, 0.786]

    # Pre-aggregate day boundaries to speed up 100x
    day_indices = {}
    for i, d in enumerate(dates_15):
        if d not in day_indices:
            day_indices[d] = []
        day_indices[d].append(i)

    print("=" * 95)
    print("STRUCTURE 1: ASIAN RANGE (00:00 - 06:00 UTC) RETRACEMENT IN LONDON")
    print("=" * 95)
    print(f"{'Fibo Level':<12} | {'Trades':<8} | {'Win Rate (1.0R)':<16} | {'Win Rate (1.5R)':<16} | {'PF (1.5R)':<10} | {'Net Exp (1.5R)'}")
    print("-" * 95)

    for lvl in fibo_levels:
        trades_15r = []; trades_10r = []
        for d, d_idx in day_indices.items():
            if len(d_idx) < 30: continue
            asia = [i for i in d_idx if hours_15[i] <= 5]
            if len(asia) < 15: continue
            a_h = np.max(h_15[asia]); a_l = np.min(l_15[asia])
            a_span = a_h - a_l
            if not (3.0 <= a_span <= 35.0): continue

            asia_trend = c_15[asia[-1]] > o_15[asia[0]]
            lon = [i for i in d_idx if 7 <= hours_15[i] <= 13]
            if not lon: continue

            if asia_trend:
                bounce = a_h - (lvl * a_span)
                sl = a_l - (SPREAD / 2.0); risk = (bounce + (SPREAD / 2.0)) - sl
                if 1.5 <= risk <= 25.0:
                    entry = bounce + (SPREAD / 2.0); tp_10 = entry + (1.0 * risk); tp_15 = entry + (1.5 * risk)
                    for pos, i in enumerate(lon):
                        if l_15[i] <= bounce:
                            sub = lon[pos:]
                            r_15 = -1.0; r_10 = -1.0
                            for j in sub:
                                if l_15[j] <= sl: break
                                if h_15[j] >= tp_10 and r_10 < 0: r_10 = 1.0
                                if h_15[j] >= tp_15: r_15 = 1.5; break
                            trades_15r.append(r_15); trades_10r.append(r_10)
                            break
            else:
                bounce = a_l + (lvl * a_span)
                sl = a_h + (SPREAD / 2.0); risk = sl - (bounce - (SPREAD / 2.0))
                if 1.5 <= risk <= 25.0:
                    entry = bounce - (SPREAD / 2.0); tp_10 = entry - (1.0 * risk); tp_15 = entry - (1.5 * risk)
                    for pos, i in enumerate(lon):
                        if h_15[i] >= bounce:
                            sub = lon[pos:]
                            r_15 = -1.0; r_10 = -1.0
                            for j in sub:
                                if h_15[j] >= sl: break
                                if l_15[j] <= tp_10 and r_10 < 0: r_10 = 1.0
                                if l_15[j] <= tp_15: r_15 = 1.5; break
                            trades_15r.append(r_15); trades_10r.append(r_10)
                            break

        wr_10 = sum(1 for r in trades_10r if r > 0) / len(trades_10r) * 100 if trades_10r else 0
        wr_15 = sum(1 for r in trades_15r if r > 0) / len(trades_15r) * 100 if trades_15r else 0
        gw = sum(r for r in trades_15r if r > 0); gl = abs(sum(r for r in trades_15r if r < 0))
        pf_15 = gw / gl if gl > 0 else 99.0
        exp_15 = np.mean(trades_15r) if trades_15r else 0.0
        print(f"Fibo {lvl*100:4.1f}%  | {len(trades_15r):<8,} | {wr_10:5.1f}%          | {wr_15:5.1f}%          | {pf_15:6.2f}     | {exp_15:+.3f} R")

    print("\n" + "=" * 95)
    print("STRUCTURE 2: PREVIOUS DAY RANGE (PDH to PDL) RETRACEMENT TODAY")
    print("=" * 95)
    print(f"{'Fibo Level':<12} | {'Trades':<8} | {'Win Rate (1.0R)':<16} | {'Win Rate (1.5R)':<16} | {'PF (1.5R)':<10} | {'Net Exp (1.5R)'}")
    print("-" * 95)

    daily_h = {}; daily_l = {}; daily_c = {}; daily_o = {}
    for d, d_idx in day_indices.items():
        if len(d_idx) >= 30:
            daily_h[d] = np.max(h_15[d_idx]); daily_l[d] = np.min(l_15[d_idx])
            daily_o[d] = o_15[d_idx[0]]; daily_c[d] = c_15[d_idx[-1]]

    for lvl in fibo_levels:
        trades_15r = []; trades_10r = []
        for idx_d in range(1, len(unique_days)):
            prev_d = unique_days[idx_d - 1]; cur_d = unique_days[idx_d]
            if prev_d not in daily_h or cur_d not in daily_h: continue
            pdh = daily_h[prev_d]; pdl = daily_l[prev_d]; pd_span = pdh - pdl
            if not (5.0 <= pd_span <= 70.0): continue
            is_bull = daily_c[prev_d] > daily_o[prev_d]
            cur_idx = day_indices[cur_d]

            if is_bull:
                bounce = pdh - (lvl * pd_span); sl = pdl - (SPREAD / 2.0); risk = (bounce + (SPREAD / 2.0)) - sl
                if 2.0 <= risk <= 40.0:
                    entry = bounce + (SPREAD / 2.0); tp_10 = entry + (1.0 * risk); tp_15 = entry + (1.5 * risk)
                    for pos, i in enumerate(cur_idx):
                        if l_15[i] <= bounce:
                            sub = cur_idx[pos:]
                            r_15 = -1.0; r_10 = -1.0
                            for j in sub:
                                if l_15[j] <= sl: break
                                if h_15[j] >= tp_10 and r_10 < 0: r_10 = 1.0
                                if h_15[j] >= tp_15: r_15 = 1.5; break
                            trades_15r.append(r_15); trades_10r.append(r_10)
                            break
            else:
                bounce = pdl + (lvl * pd_span); sl = pdh + (SPREAD / 2.0); risk = sl - (bounce - (SPREAD / 2.0))
                if 2.0 <= risk <= 40.0:
                    entry = bounce - (SPREAD / 2.0); tp_10 = entry - (1.0 * risk); tp_15 = entry - (1.5 * risk)
                    for pos, i in enumerate(cur_idx):
                        if h_15[i] >= bounce:
                            sub = cur_idx[pos:]
                            r_15 = -1.0; r_10 = -1.0
                            for j in sub:
                                if h_15[j] >= sl: break
                                if l_15[j] <= tp_10 and r_10 < 0: r_10 = 1.0
                                if l_15[j] <= tp_15: r_15 = 1.5; break
                            trades_15r.append(r_15); trades_10r.append(r_10)
                            break

        wr_10 = sum(1 for r in trades_10r if r > 0) / len(trades_10r) * 100 if trades_10r else 0
        wr_15 = sum(1 for r in trades_15r if r > 0) / len(trades_15r) * 100 if trades_15r else 0
        gw = sum(r for r in trades_15r if r > 0); gl = abs(sum(r for r in trades_15r if r < 0))
        pf_15 = gw / gl if gl > 0 else 99.0
        exp_15 = np.mean(trades_15r) if trades_15r else 0.0
        print(f"Fibo {lvl*100:4.1f}%  | {len(trades_15r):<8,} | {wr_10:5.1f}%          | {wr_15:5.1f}%          | {pf_15:6.2f}     | {exp_15:+.3f} R")

    print("\n" + "=" * 95)
    print("STRUCTURE 3: LONDON OPENING IMPULSE (07:00 - 08:30 UTC) PULLBACK IN NY")
    print("=" * 95)
    print(f"{'Fibo Level':<12} | {'Trades':<8} | {'Win Rate (1.0R)':<16} | {'Win Rate (1.5R)':<16} | {'PF (1.5R)':<10} | {'Net Exp (1.5R)'}")
    print("-" * 95)

    for lvl in fibo_levels:
        trades_15r = []; trades_10r = []
        for d, d_idx in day_indices.items():
            if len(d_idx) < 30: continue
            # London impulse: 07:00 to 09:00 UTC (8 bars of M15)
            lon_imp = [i for i in d_idx if 7 <= hours_15[i] <= 8]
            if len(lon_imp) < 6: continue
            l_h = np.max(h_15[lon_imp]); l_l = np.min(l_15[lon_imp])
            span = l_h - l_l
            if not (4.0 <= span <= 30.0): continue

            is_bull_lon = c_15[lon_imp[-1]] > o_15[lon_imp[0]]
            ny_window = [i for i in d_idx if 9 <= hours_15[i] <= 16]
            if not ny_window: continue

            if is_bull_lon:
                bounce = l_h - (lvl * span); sl = l_l - (SPREAD / 2.0); risk = (bounce + (SPREAD / 2.0)) - sl
                if 1.5 <= risk <= 20.0:
                    entry = bounce + (SPREAD / 2.0); tp_10 = entry + (1.0 * risk); tp_15 = entry + (1.5 * risk)
                    for pos, i in enumerate(ny_window):
                        if l_15[i] <= bounce:
                            sub = ny_window[pos:]
                            r_15 = -1.0; r_10 = -1.0
                            for j in sub:
                                if l_15[j] <= sl: break
                                if h_15[j] >= tp_10 and r_10 < 0: r_10 = 1.0
                                if h_15[j] >= tp_15: r_15 = 1.5; break
                            trades_15r.append(r_15); trades_10r.append(r_10)
                            break
            else:
                bounce = l_l + (lvl * span); sl = l_h + (SPREAD / 2.0); risk = sl - (bounce - (SPREAD / 2.0))
                if 1.5 <= risk <= 20.0:
                    entry = bounce - (SPREAD / 2.0); tp_10 = entry - (1.0 * risk); tp_15 = entry - (1.5 * risk)
                    for pos, i in enumerate(ny_window):
                        if h_15[i] >= bounce:
                            sub = ny_window[pos:]
                            r_15 = -1.0; r_10 = -1.0
                            for j in sub:
                                if h_15[j] >= sl: break
                                if l_15[j] <= tp_10 and r_10 < 0: r_10 = 1.0
                                if l_15[j] <= tp_15: r_15 = 1.5; break
                            trades_15r.append(r_15); trades_10r.append(r_10)
                            break

        wr_10 = sum(1 for r in trades_10r if r > 0) / len(trades_10r) * 100 if trades_10r else 0
        wr_15 = sum(1 for r in trades_15r if r > 0) / len(trades_15r) * 100 if trades_15r else 0
        gw = sum(r for r in trades_15r if r > 0); gl = abs(sum(r for r in trades_15r if r < 0))
        pf_15 = gw / gl if gl > 0 else 99.0
        exp_15 = np.mean(trades_15r) if trades_15r else 0.0
        print(f"Fibo {lvl*100:4.1f}%  | {len(trades_15r):<8,} | {wr_10:5.1f}%          | {wr_15:5.1f}%          | {pf_15:6.2f}     | {exp_15:+.3f} R")

if __name__ == "__main__":
    run_fast_fibo()
