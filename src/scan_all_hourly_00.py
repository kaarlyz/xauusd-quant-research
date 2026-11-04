#!/usr/bin/env python3
"""
Quantitative Scan: All Hourly Open (:00) Windows on XAUUSD (00:00 - 23:00 UTC / 07:00 - 06:00 WIB).
Tests:
- Model A: Previous Hour High/Low Sweep Reversal at :00-:05 (Liquidity Trap)
- Model B: Hourly Open Momentum Drive at :00-:05 (Directional Breakout)
Evaluates across 4,182,209 M1 candles (2015-2026) with $0.50 spread friction.
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD_COST = 0.50

def run_hourly_scan():
    print("=== Loading 12-Year M1 Dataset (4,182,209 candles) ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    
    df = df.with_columns(
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

    # 60-bar rolling ATR
    ranges = highs - lows
    cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr = (cumsum[60:] - cumsum[:-60]) / 60.0
    atr = np.pad(atr, (60, 0), mode="edge")[:n]

    target_hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    
    # Store results per hour, per mode: train (2015-2023) vs test (2024-2026)
    results = {
        h: {
            "sweep_reversal": {"train": [], "test": []},
            "momentum_drive": {"train": [], "test": []}
        }
        for h in target_hours
    }

    # Pre-identify hourly boundaries
    # A new hour starts when minutes[i] == 0
    for i in range(65, n - 65):
        if minutes[i] != 0:
            continue
        h = hours[i]
        if h not in target_hours:
            continue

        # Get previous hour High, Low, Range (bars i-60 to i-1)
        prev_h = np.max(highs[i - 60 : i])
        prev_l = np.min(lows[i - 60 : i])
        prev_range = prev_h - prev_l
        o_hour = opens[i]
        curr_atr = atr[i]
        yr = years[i]
        is_test = (yr >= 2024)
        split = "test" if is_test else "train"

        if curr_atr <= 0.2 or prev_range < 2.0:
            continue

        # Inspect first 5 minutes of new hour (minutes 0 to 4: bars i to i+4)
        # Check Model A: Sweep of Previous Hour High/Low and Reversal back inside
        # 1. High Sweep Reversal (Short)
        five_high = np.max(highs[i : i + 5])
        five_low = np.min(lows[i : i + 5])
        c_04 = closes[i + 4] # close of minute 4 (end of 5-min open window)

        # Bullish sweep of previous hour high + close back below
        if five_high > prev_h + 0.30 and c_04 < prev_h and c_04 < o_hour:
            entry = c_04 - (SPREAD_COST / 2.0)
            sl = five_high + (SPREAD_COST / 2.0)
            risk = sl - entry
            if 0.80 <= risk <= 15.0:
                tp = entry - (1.5 * risk)
                outcome = 0; r_val = 0.0
                for s in range(5, 55): # forward test within the current hour
                    if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                    elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                if outcome == 0:
                    exit_p = closes[i + 54]
                    r_val = (entry - exit_p) / risk
                results[h]["sweep_reversal"][split].append(r_val)

        # Bearish sweep of previous hour low + close back above
        elif five_low < prev_l - 0.30 and c_04 > prev_l and c_04 > o_hour:
            entry = c_04 + (SPREAD_COST / 2.0)
            sl = five_low - (SPREAD_COST / 2.0)
            risk = entry - sl
            if 0.80 <= risk <= 15.0:
                tp = entry + (1.5 * risk)
                outcome = 0; r_val = 0.0
                for s in range(5, 55):
                    if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                    elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                if outcome == 0:
                    exit_p = closes[i + 54]
                    r_val = (exit_p - entry) / risk
                results[h]["sweep_reversal"][split].append(r_val)

        # Check Model B: Momentum Drive (Clean breakout in first 5 mins)
        disp_5m = c_04 - o_hour
        if abs(disp_5m) > max(curr_atr * 0.7, 1.5):
            # Bullish drive
            if disp_5m > 0 and (five_high - c_04) < 0.20 * (five_high - five_low):
                entry = c_04 + (SPREAD_COST / 2.0)
                sl = o_hour - (SPREAD_COST / 2.0)
                risk = entry - sl
                if 0.80 <= risk <= 15.0:
                    tp = entry + (1.5 * risk)
                    outcome = 0; r_val = 0.0
                    for s in range(5, 55):
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                        elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0:
                        exit_p = closes[i + 54]
                        r_val = (exit_p - entry) / risk
                    results[h]["momentum_drive"][split].append(r_val)

            # Bearish drive
            elif disp_5m < 0 and (c_04 - five_low) < 0.20 * (five_high - five_low):
                entry = c_04 - (SPREAD_COST / 2.0)
                sl = o_hour + (SPREAD_COST / 2.0)
                risk = sl - entry
                if 0.80 <= risk <= 15.0:
                    tp = entry - (1.5 * risk)
                    outcome = 0; r_val = 0.0
                    for s in range(5, 55):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                        elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0:
                        exit_p = closes[i + 54]
                        r_val = (entry - exit_p) / risk
                    results[h]["momentum_drive"][split].append(r_val)

    def stats_summary(r_list):
        if not r_list or len(r_list) < 20:
            return None
        n_t = len(r_list)
        wins = sum(1 for r in r_list if r > 0)
        wr = (wins / n_t) * 100.0
        avg_r = np.mean(r_list)
        gw = sum(r for r in r_list if r > 0)
        gl = abs(sum(r for r in r_list if r < 0))
        pf = gw / gl if gl > 0 else 99.0
        return {"n": n_t, "wr": round(wr, 1), "exp": round(float(avg_r), 3), "pf": round(float(pf), 2)}

    print("\n" + "=" * 95)
    print("HOURLY OPEN (:00) TIMING MATRIX ON XAUUSD (2015 - 2026 / 12 YEARS)")
    print("Split: 9-Yr Train (2015-2023) vs 3-Yr Test (2024-2026) | Target RR: 1.5 : 1 | Spread: $0.50")
    print("=" * 95)
    print(f"{'Hour (UTC / WIB)':<22} | {'Optimal Model':<14} | {'Train WR':<9} | {'Train Exp':<10} | {'Test WR':<8} | {'Test Exp':<9} | {'Test PF':<7} | {'Verdict'}")
    print("-" * 95)

    for h in target_hours:
        wib_h = (h + 7) % 24
        label = f"{h:02d}:00 UTC ({wib_h:02d}:00 WIB)"

        sw_tr = stats_summary(results[h]["sweep_reversal"]["train"])
        sw_te = stats_summary(results[h]["sweep_reversal"]["test"])
        mo_tr = stats_summary(results[h]["momentum_drive"]["train"])
        mo_te = stats_summary(results[h]["momentum_drive"]["test"])

        best_model = "None"
        best_tr = None
        best_te = None
        verdict = "REJECTED"

        # Check if Sweep Reversal works across train and test
        if sw_tr and sw_te and sw_tr["exp"] > 0 and sw_te["exp"] > 0 and sw_tr["pf"] >= 1.05 and sw_te["pf"] >= 1.05:
            best_model = "Sweep Reversal"
            best_tr = sw_tr
            best_te = sw_te
            verdict = "VALID (Profitable)"
        # Check if Momentum Drive works
        elif mo_tr and mo_te and mo_tr["exp"] > 0 and mo_te["exp"] > 0 and mo_tr["pf"] >= 1.05 and mo_te["pf"] >= 1.05:
            best_model = "Momentum Drive"
            best_tr = mo_tr
            best_te = mo_te
            verdict = "VALID (Profitable)"
        else:
            # Report the better one
            sw_score = (sw_tr["exp"] if sw_tr else -1) + (sw_te["exp"] if sw_te else -1)
            mo_score = (mo_tr["exp"] if mo_tr else -1) + (mo_te["exp"] if mo_te else -1)
            if sw_score >= mo_score and sw_te:
                best_model = "Sweep Reversal"
                best_tr = sw_tr
                best_te = sw_te
            elif mo_te:
                best_model = "Momentum Drive"
                best_tr = mo_tr
                best_te = mo_te

        tr_wr = f"{best_tr['wr']}%" if best_tr else "N/A"
        tr_exp = f"{best_tr['exp']:+.3f}R" if best_tr else "N/A"
        te_wr = f"{best_te['wr']}%" if best_te else "N/A"
        te_exp = f"{best_te['exp']:+.3f}R" if best_te else "N/A"
        te_pf = f"{best_te['pf']:.2f}" if best_te else "N/A"

        print(f"{label:<22} | {best_model:<14} | {tr_wr:<9} | {tr_exp:<10} | {te_wr:<8} | {te_exp:<9} | {te_pf:<7} | {verdict}")

if __name__ == "__main__":
    run_hourly_scan()
