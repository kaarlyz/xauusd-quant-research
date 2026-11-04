#!/usr/bin/env python3
"""
EXP-2026-000003: 12-Year Multi-Decade Validation on XAUUSD M1 (2015 - 2026).
Dataset: 4,182,209 Continuous M1 Candles
Evaluates year-by-year stability, Win Rate, Expectancy, and Drawdown across 12 years.
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD_COST = 0.50

def run_12year_validation():
    print("=== Loading 12-Year Dataset (4,182,209 M1 Candles) ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    
    df = df.with_columns(
        (pl.col("timestamp") // 1000).alias("ts_sec"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.minute().alias("minute"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    # Filter rollover
    df = df.filter(~pl.col("hour").is_between(21, 23))

    opens = df["open"].to_numpy()
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    closes = df["close"].to_numpy()
    hours = df["hour"].to_numpy()
    minutes = df["minute"].to_numpy()
    years = df["year"].to_numpy()
    n = len(df)
    unique_years = sorted(list(np.unique(years)))
    print(f"Candles after filter: {n:,} (Years: {unique_years})")

    # 60-bar rolling ATR
    ranges = highs - lows
    cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr = np.zeros(n)
    diff = (cumsum[60:] - cumsum[:-60]) / 60.0
    atr[60:] = diff[:n - 60]
    atr[:60] = np.mean(ranges[:60])

    # 1. London 17:30 WIB (10:30 UTC) Reversal
    london_by_year = {y: [] for y in unique_years}
    # 2. Tokyo 09:30 WIB (02:30 UTC) Momentum
    tokyo_by_year = {y: [] for y in unique_years}

    for i in range(30, n - 35):
        if minutes[i] != 29:
            continue
        h = hours[i]
        if h not in (2, 10):
            continue
        if minutes[i - 29] != 0 or hours[i - 29] != h:
            continue

        o_00 = opens[i - 29]; c_29 = closes[i]
        h_30 = np.max(highs[i - 29 : i + 1]); l_30 = np.min(lows[i - 29 : i + 1])
        disp = c_29 - o_00
        curr_atr = atr[i]
        yr = years[i]

        if curr_atr <= 0: continue
        min_move = max(curr_atr * 0.8, 2.0)
        if abs(disp) < min_move:
            continue

        # Tokyo 09:30 WIB (02:30 UTC) -> Ikut Trend
        if h == 2:
            if disp > 0 and (h_30 - c_29) < 0.25 * (h_30 - l_30):
                entry = c_29 + (SPREAD_COST / 2.0); sl = o_00 - (SPREAD_COST / 2.0); risk = entry - sl
                if 0.80 <= risk <= 15.0:
                    tp = entry + (1.5 * risk)
                    r_val = 0.0; outcome = 0
                    for s in range(1, 31):
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                        elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0:
                        exit_p = closes[i + 30]
                        r_val = (exit_p - entry) / risk
                    tokyo_by_year[yr].append(r_val)

            elif disp < 0 and (c_29 - l_30) < 0.25 * (h_30 - l_30):
                entry = c_29 - (SPREAD_COST / 2.0); sl = o_00 + (SPREAD_COST / 2.0); risk = sl - entry
                if 0.80 <= risk <= 15.0:
                    tp = entry - (1.5 * risk)
                    r_val = 0.0; outcome = 0
                    for s in range(1, 31):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                        elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0:
                        exit_p = closes[i + 30]
                        r_val = (entry - exit_p) / risk
                    tokyo_by_year[yr].append(r_val)

        # London 17:30 WIB (10:30 UTC) -> Lawan Trend
        elif h == 10:
            if disp > 0 and (h_30 - c_29) > 0.30 * (h_30 - l_30):
                entry = c_29 - (SPREAD_COST / 2.0); sl = h_30 + (SPREAD_COST / 2.0); risk = sl - entry
                if 0.80 <= risk <= 15.0:
                    tp = entry - (1.5 * risk)
                    r_val = 0.0; outcome = 0
                    for s in range(1, 31):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                        elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0:
                        exit_p = closes[i + 30]
                        r_val = (entry - exit_p) / risk
                    london_by_year[yr].append(r_val)

            elif disp < 0 and (c_29 - l_30) > 0.30 * (h_30 - l_30):
                entry = c_29 + (SPREAD_COST / 2.0); sl = l_30 - (SPREAD_COST / 2.0); risk = entry - sl
                if 0.80 <= risk <= 15.0:
                    tp = entry + (1.5 * risk)
                    r_val = 0.0; outcome = 0
                    for s in range(1, 31):
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                        elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0:
                        exit_p = closes[i + 30]
                        r_val = (exit_p - entry) / risk
                    london_by_year[yr].append(r_val)

    def print_strategy_report(title, year_dict):
        print("\n" + "=" * 80)
        print(f"12-YEAR STATISTICAL REPORT: {title}")
        print("Friction: $0.50 spread | Fixed RR: 1.5 : 1 | Horizon: 2015 - 2026")
        print("=" * 80)
        print(f"{'Year':<6} | {'Trades':<8} | {'Win Rate':<10} | {'Expectancy':<12} | {'Profit Factor':<14} | {'Net Return'}")
        print("-" * 80)

        all_r = []
        for y in sorted(year_dict.keys()):
            r_list = year_dict[y]
            if not r_list:
                print(f"{y:<6} | {'0':<8} | {'N/A':<10} | {'N/A':<12} | {'N/A':<14} | 0.0R")
                continue
            all_r.extend(r_list)
            wins = sum(1 for r in r_list if r > 0)
            wr = (wins / len(r_list)) * 100.0
            exp = np.mean(r_list)
            gw = sum(r for r in r_list if r > 0)
            gl = abs(sum(r for r in r_list if r < 0))
            pf = gw / gl if gl > 0 else 99.0
            total_r = sum(r_list)
            print(f"{y:<6} | {len(r_list):<8} | {wr:6.1f}%    | {exp:>+8.3f}R   | {pf:>10.2f}    | {total_r:>+6.1f}R")

        if all_r:
            tot_w = sum(1 for r in all_r if r > 0)
            tot_wr = (tot_w / len(all_r)) * 100.0
            tot_exp = np.mean(all_r)
            gw = sum(r for r in all_r if r > 0)
            gl = abs(sum(r for r in all_r if r < 0))
            tot_pf = gw / gl if gl > 0 else 99.0
            cum = np.cumsum(all_r)
            mdd = np.max(np.maximum.accumulate(cum) - cum)
            print("-" * 80)
            print(f"12-YEAR SUMMARY: N = {len(all_r):,} trades | WR = {tot_wr:.1f}% | Net Exp = {tot_exp:+.3f}R | PF = {tot_pf:.2f} | Max DD = -{mdd:.1f}R | Total Profit = {cum[-1]:+.1f}R")

    print_strategy_report("LONDON 17:30 WIB (10:30 UTC) REVERSAL", london_by_year)
    print_strategy_report("TOKYO 09:30 WIB (02:30 UTC) MOMENTUM RUN", tokyo_by_year)

if __name__ == "__main__":
    run_12year_validation()
