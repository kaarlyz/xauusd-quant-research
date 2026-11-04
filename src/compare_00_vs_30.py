#!/usr/bin/env python3
"""
Direct Side-by-Side Comparison: Minute :00 vs Minute :30 Strategies on XAUUSD (2015 - 2026).
Compares:
1. London 17:30 WIB Reversal (:30)
2. Tokyo 09:30 WIB Momentum (:30)
3. Tokyo 08:00 WIB Sweep Reversal (:00)
4. London 17:00 WIB Sweep Reversal (:00)
5. London 19:00 WIB Sweep Reversal (:00)
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD_COST = 0.50

def run_comparison():
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.minute().alias("minute"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )
    df = df.filter(~pl.col("hour").is_between(21, 23))

    opens = df["open"].to_numpy(); highs = df["high"].to_numpy(); lows = df["low"].to_numpy(); closes = df["close"].to_numpy()
    hours = df["hour"].to_numpy(); minutes = df["minute"].to_numpy(); years = df["year"].to_numpy()
    n = len(df)

    ranges = highs - lows; cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr = (cumsum[60:] - cumsum[:-60]) / 60.0
    atr = np.pad(atr, (60, 0), mode="edge")[:n]

    # Track trades for each of the candidates
    # 1. 17:30 WIB (:30)
    # 2. 09:30 WIB (:30)
    # 3. 08:00 WIB (:00)
    # 4. 17:00 WIB (:00)
    # 5. 19:00 WIB (:00)
    streams = {
        "17:30 WIB (:30 Reversal)": [],
        "09:30 WIB (:30 Momentum)": [],
        "08:00 WIB (:00 Sweep)": [],
        "17:00 WIB (:00 Sweep)": [],
        "19:00 WIB (:00 Sweep)": []
    }

    for i in range(65, n - 65):
        m = minutes[i]
        h = hours[i]
        curr_atr = atr[i]
        yr = years[i]

        # --- A. Minute 29 (enters at :30) ---
        if m == 29:
            if minutes[i - 29] != 0 or hours[i - 29] != h: continue
            o_00 = opens[i - 29]; c_29 = closes[i]
            h_30 = np.max(highs[i - 29 : i + 1]); l_30 = np.min(lows[i - 29 : i + 1])
            disp = c_29 - o_00
            if curr_atr <= 0.2 or abs(disp) < max(curr_atr * 0.8, 2.0): continue

            # 1. London 17:30 (h=10)
            if h == 10:
                if disp > 0 and (h_30 - c_29) > 0.30 * (h_30 - l_30):
                    entry = c_29 - (SPREAD_COST / 2.0); sl = h_30 + (SPREAD_COST / 2.0); risk = sl - entry
                    if 0.80 <= risk <= 15.0:
                        tp = entry - (1.5 * risk); r_val = 0.0; outcome = 0
                        for s in range(1, 31):
                            if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                            elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                        if outcome == 0: r_val = (entry - closes[i + 30]) / risk
                        streams["17:30 WIB (:30 Reversal)"].append({"year": yr, "r": r_val})
                elif disp < 0 and (c_29 - l_30) > 0.30 * (h_30 - l_30):
                    entry = c_29 + (SPREAD_COST / 2.0); sl = l_30 - (SPREAD_COST / 2.0); risk = entry - sl
                    if 0.80 <= risk <= 15.0:
                        tp = entry + (1.5 * risk); r_val = 0.0; outcome = 0
                        for s in range(1, 31):
                            if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                            elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                        if outcome == 0: r_val = (closes[i + 30] - entry) / risk
                        streams["17:30 WIB (:30 Reversal)"].append({"year": yr, "r": r_val})

            # 2. Tokyo 09:30 (h=2)
            elif h == 2:
                if disp > 0 and (h_30 - c_29) < 0.25 * (h_30 - l_30):
                    entry = c_29 + (SPREAD_COST / 2.0); sl = o_00 - (SPREAD_COST / 2.0); risk = entry - sl
                    if 0.80 <= risk <= 15.0:
                        tp = entry + (1.5 * risk); r_val = 0.0; outcome = 0
                        for s in range(1, 31):
                            if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                            elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                        if outcome == 0: r_val = (closes[i + 30] - entry) / risk
                        streams["09:30 WIB (:30 Momentum)"].append({"year": yr, "r": r_val})
                elif disp < 0 and (c_29 - l_30) < 0.25 * (h_30 - l_30):
                    entry = c_29 - (SPREAD_COST / 2.0); sl = o_00 + (SPREAD_COST / 2.0); risk = sl - entry
                    if 0.80 <= risk <= 15.0:
                        tp = entry - (1.5 * risk); r_val = 0.0; outcome = 0
                        for s in range(1, 31):
                            if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                            elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                        if outcome == 0: r_val = (entry - closes[i + 30]) / risk
                        streams["09:30 WIB (:30 Momentum)"].append({"year": yr, "r": r_val})

        # --- B. Minute 00 (enters at :05 after sweep) ---
        elif m == 0:
            if h not in (1, 10, 12): continue
            prev_h = np.max(highs[i - 60 : i]); prev_l = np.min(lows[i - 60 : i])
            if (prev_h - prev_l) < 1.5: continue
            five_h = np.max(highs[i : i + 5]); five_l = np.min(lows[i : i + 5])
            c_04 = closes[i + 4]; o_hour = opens[i]

            target_key = "08:00 WIB (:00 Sweep)" if h == 1 else ("17:00 WIB (:00 Sweep)" if h == 10 else "19:00 WIB (:00 Sweep)")

            if five_h > prev_h + 0.30 and c_04 < prev_h and c_04 < o_hour:
                entry = c_04 - (SPREAD_COST / 2.0); sl = five_h + (SPREAD_COST / 2.0); risk = sl - entry
                if 0.80 <= risk <= 15.0:
                    tp = entry - (1.5 * risk); r_val = 0.0; outcome = 0
                    for s in range(5, 55):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                        elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0: r_val = (entry - closes[i + 54]) / risk
                    streams[target_key].append({"year": yr, "r": r_val})

            elif five_l < prev_l - 0.30 and c_04 > prev_l and c_04 > o_hour:
                entry = c_04 + (SPREAD_COST / 2.0); sl = five_l - (SPREAD_COST / 2.0); risk = entry - sl
                if 0.80 <= risk <= 15.0:
                    tp = entry + (1.5 * risk); r_val = 0.0; outcome = 0
                    for s in range(5, 55):
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                        elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0: r_val = (closes[i + 54] - entry) / risk
                    streams[target_key].append({"year": yr, "r": r_val})

    print("\n" + "=" * 105)
    print("HEAD-TO-HEAD COMPARISON: MINUTE :00 VS MINUTE :30 (12-YEAR STATISTICAL VERIFICATION)")
    print("Dataset: 2015-2026 (4,182,209 M1 candles) | Spread: $0.50 | Fixed RR: 1.5 : 1")
    print("=" * 105)
    print(f"{'Strategy Name':<26} | {'12-Yr Trades':<12} | {'12-Yr WR':<9} | {'12-Yr PF':<9} | {'Recent PF (24-26)':<18} | {'Max DD':<9} | {'Net Return'}")
    print("-" * 105)

    for name, stream in streams.items():
        if not stream: continue
        r_all = [t["r"] for t in stream]
        r_recent = [t["r"] for t in stream if t["year"] >= 2024]

        n_all = len(r_all)
        wr_all = sum(1 for r in r_all if r > 0) / n_all * 100
        gw_all = sum(r for r in r_all if r > 0); gl_all = abs(sum(r for r in r_all if r < 0))
        pf_all = gw_all / gl_all if gl_all > 0 else 99.0

        gw_rec = sum(r for r in r_recent if r > 0); gl_rec = abs(sum(r for r in r_recent if r < 0))
        pf_rec = gw_rec / gl_rec if gl_rec > 0 else 99.0
        wr_rec = sum(1 for r in r_recent if r > 0) / len(r_recent) * 100 if r_recent else 0.0

        cum = np.cumsum(r_all)
        mdd = np.max(np.maximum.accumulate(cum) - cum)
        tot_r = cum[-1]

        print(f"{name:<26} | {n_all:<12} | {wr_all:5.1f}%   | {pf_all:7.2f}   | {pf_rec:5.2f} (WR {wr_rec:.1f}%)     | -{mdd:<7.1f}R | {tot_r:>+7.1f}R")

if __name__ == "__main__":
    run_comparison()
