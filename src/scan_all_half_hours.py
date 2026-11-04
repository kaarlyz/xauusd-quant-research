#!/usr/bin/env python3
"""
Systematic Quantitative Scan: All Half-Hour (:30) Windows on XAUUSD (00:30 - 20:30 UTC).
Tests deterministic rules:
- Mode A: Reversal / Lawan Trend (Fade the 00-30 sweep)
- Mode B: Continuation / Ikut Trend (Ride the 00-30 momentum)
Evaluates across 648,677 M1 bars (2025 In-Sample vs 2026 Out-of-Sample) with realistic $0.50 spread.
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD_COST = 0.50  # 50 cents institutional spread

def run_half_hour_scan():
    print("=== Loading M1 Dataset ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    
    df = df.with_columns(
        (pl.col("timestamp") // 1000).alias("ts_sec"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.minute().alias("minute"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    # Exclude rollover spread hole (21-23 UTC)
    df = df.filter(~pl.col("hour").is_between(21, 23))

    opens = df["open"].to_numpy()
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    closes = df["close"].to_numpy()
    hours = df["hour"].to_numpy()
    minutes = df["minute"].to_numpy()
    years = df["year"].to_numpy()
    n = len(df)

    # Rolling 60-bar ATR
    ranges = highs - lows
    cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr = np.zeros(n)
    diff = (cumsum[60:] - cumsum[:-60]) / 60.0
    atr[60:] = diff[:n - 60]
    atr[:60] = np.mean(ranges[:60])

    # We test every hour from 0 to 20, plus 23 (Asian Open)
    target_hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 23]
    
    # Storage for results per hour and mode
    # hour -> mode -> is/oos -> list of r-multiples
    hour_results = {h: {"reversal": {"is": [], "oos": []}, "continuation": {"is": [], "oos": []}} for h in target_hours}

    # Iterate over all bars
    for i in range(30, n - 35):
        if minutes[i] != 29:
            continue
        h = hours[i]
        if h not in hour_results:
            continue
        if minutes[i - 29] != 0 or hours[i - 29] != h:
            continue

        o_00 = opens[i - 29]
        c_29 = closes[i]
        h_30 = np.max(highs[i - 29 : i + 1])
        l_30 = np.min(lows[i - 29 : i + 1])
        disp = c_29 - o_00
        curr_atr = atr[i]

        # Require minimum meaningful displacement in first 30 mins (at least 0.8 * ATR or $2.00)
        min_move = max(curr_atr * 0.8, 2.0)
        if abs(disp) < min_move:
            continue

        is_oos = (years[i] >= 2026)
        split_key = "oos" if is_oos else "is"

        # ----------------------------------------------------
        # Mode 1: REVERSAL (Lawan Trend)
        # ----------------------------------------------------
        # If bullish push, enter SHORT if upper rejection wick > 30% of range
        if disp > 0 and (h_30 - c_29) > 0.30 * (h_30 - l_30):
            entry = c_29 - (SPREAD_COST / 2.0)
            sl = h_30 + (SPREAD_COST / 2.0)
            risk = sl - entry
            if 0.80 <= risk <= 15.0:
                rr_target = 1.5
                tp = entry - (rr_target * risk)
                r_val = 0.0
                outcome = 0
                for s in range(1, 31):
                    fut_idx = i + s
                    if highs[fut_idx] >= sl:
                        r_val = -1.0; outcome = -1; break
                    elif lows[fut_idx] <= tp:
                        r_val = rr_target; outcome = 1; break
                if outcome == 0:
                    exit_p = closes[i + 30]
                    r_val = (entry - exit_p) / risk
                    outcome = 1 if r_val > 0 else -1
                hour_results[h]["reversal"][split_key].append(r_val)

        elif disp < 0 and (c_29 - l_30) > 0.30 * (h_30 - l_30):
            entry = c_29 + (SPREAD_COST / 2.0)
            sl = l_30 - (SPREAD_COST / 2.0)
            risk = entry - sl
            if 0.80 <= risk <= 15.0:
                rr_target = 1.5
                tp = entry + (rr_target * risk)
                r_val = 0.0
                outcome = 0
                for s in range(1, 31):
                    fut_idx = i + s
                    if lows[fut_idx] <= sl:
                        r_val = -1.0; outcome = -1; break
                    elif highs[fut_idx] >= tp:
                        r_val = rr_target; outcome = 1; break
                if outcome == 0:
                    exit_p = closes[i + 30]
                    r_val = (exit_p - entry) / risk
                    outcome = 1 if r_val > 0 else -1
                hour_results[h]["reversal"][split_key].append(r_val)

        # ----------------------------------------------------
        # Mode 2: CONTINUATION (Ikut Trend)
        # ----------------------------------------------------
        # If bullish push, enter LONG if close near high (wick < 25%)
        if disp > 0 and (h_30 - c_29) < 0.25 * (h_30 - l_30):
            entry = c_29 + (SPREAD_COST / 2.0)
            sl = o_00 - (SPREAD_COST / 2.0)
            risk = entry - sl
            if 0.80 <= risk <= 15.0:
                rr_target = 1.5
                tp = entry + (rr_target * risk)
                r_val = 0.0
                outcome = 0
                for s in range(1, 31):
                    fut_idx = i + s
                    if lows[fut_idx] <= sl:
                        r_val = -1.0; outcome = -1; break
                    elif highs[fut_idx] >= tp:
                        r_val = rr_target; outcome = 1; break
                if outcome == 0:
                    exit_p = closes[i + 30]
                    r_val = (exit_p - entry) / risk
                    outcome = 1 if r_val > 0 else -1
                hour_results[h]["continuation"][split_key].append(r_val)

        elif disp < 0 and (c_29 - l_30) < 0.25 * (h_30 - l_30):
            entry = c_29 - (SPREAD_COST / 2.0)
            sl = o_00 + (SPREAD_COST / 2.0)
            risk = sl - entry
            if 0.80 <= risk <= 15.0:
                rr_target = 1.5
                tp = entry - (rr_target * risk)
                r_val = 0.0
                outcome = 0
                for s in range(1, 31):
                    fut_idx = i + s
                    if highs[fut_idx] >= sl:
                        r_val = -1.0; outcome = -1; break
                    elif lows[fut_idx] <= tp:
                        r_val = rr_target; outcome = 1; break
                if outcome == 0:
                    exit_p = closes[i + 30]
                    r_val = (entry - exit_p) / risk
                    outcome = 1 if r_val > 0 else -1
                hour_results[h]["continuation"][split_key].append(r_val)

    def stats_summary(r_list):
        if not r_list or len(r_list) < 15:
            return None
        n_t = len(r_list)
        wins = sum(1 for r in r_list if r > 0)
        wr = (wins / n_t) * 100.0
        avg_r = np.mean(r_list)
        gw = sum(r for r in r_list if r > 0)
        gl = abs(sum(r for r in r_list if r < 0))
        pf = gw / gl if gl > 0 else 99.0
        return {"n": n_t, "wr": round(wr, 1), "exp": round(float(avg_r), 3), "pf": round(float(pf), 2)}

    print("\n" + "=" * 90)
    print("HOURLY MINUTE-30 TIMING MATRIX (00:30 to 20:30 UTC / 07:30 to 03:30 WIB)")
    print("Target RR: 1.5 : 1 | Friction: $0.50 spread | Dataset: 2025 (IS) & 2026 (OOS)")
    print("=" * 90)
    print(f"{'Timing (UTC / WIB)':<22} | {'Optimal Mode':<14} | {'IS WR':<8} | {'IS Exp':<8} | {'OOS WR':<8} | {'OOS Exp':<8} | {'OOS PF':<6} | {'Verdict'}")
    print("-" * 90)

    summary_table = []
    for h in target_hours:
        wib_h = (h + 7) % 24
        label = f"{h:02d}:30 UTC ({wib_h:02d}:30 WIB)"
        
        rev_is = stats_summary(hour_results[h]["reversal"]["is"])
        rev_oos = stats_summary(hour_results[h]["reversal"]["oos"])
        cont_is = stats_summary(hour_results[h]["continuation"]["is"])
        cont_oos = stats_summary(hour_results[h]["continuation"]["oos"])

        # Decide which mode is viable
        # Viable requires OOS Exp > 0 and OOS PF > 1.05 and IS Exp > -0.05
        best_mode = "None"
        best_stat_is = None
        best_stat_oos = None
        verdict = "REJECTED (No Edge)"

        # Check if reversal qualifies
        if rev_oos and rev_oos["exp"] > 0 and rev_oos["pf"] >= 1.05:
            best_mode = "Lawan Trend"
            best_stat_is = rev_is
            best_stat_oos = rev_oos
            if rev_is and rev_is["exp"] >= -0.05:
                verdict = "VALID (Profitable)"
            else:
                verdict = "INCONCLUSIVE"
        # Check if continuation qualifies
        elif cont_oos and cont_oos["exp"] > 0 and cont_oos["pf"] >= 1.05:
            best_mode = "Ikut Trend"
            best_stat_is = cont_is
            best_stat_oos = cont_oos
            if cont_is and cont_is["exp"] >= -0.05:
                verdict = "VALID (Profitable)"
            else:
                verdict = "INCONCLUSIVE"
        else:
            # Fallback to display the better of the two
            r_exp = rev_oos["exp"] if rev_oos else -99
            c_exp = cont_oos["exp"] if cont_oos else -99
            if r_exp >= c_exp and rev_oos:
                best_mode = "Lawan Trend (Weak)"
                best_stat_is = rev_is
                best_stat_oos = rev_oos
            elif cont_oos:
                best_mode = "Ikut Trend (Weak)"
                best_stat_is = cont_is
                best_stat_oos = cont_oos

        is_wr_str = f"{best_stat_is['wr']}%" if best_stat_is else "N/A"
        is_exp_str = f"{best_stat_is['exp']:+.2f}R" if best_stat_is else "N/A"
        oos_wr_str = f"{best_stat_oos['wr']}%" if best_stat_oos else "N/A"
        oos_exp_str = f"{best_stat_oos['exp']:+.2f}R" if best_stat_oos else "N/A"
        oos_pf_str = f"{best_stat_oos['pf']:.2f}" if best_stat_oos else "N/A"

        print(f"{label:<22} | {best_mode:<14} | {is_wr_str:<8} | {is_exp_str:<8} | {oos_wr_str:<8} | {oos_exp_str:<8} | {oos_pf_str:<6} | {verdict}")
        summary_table.append({
            "timing_utc": f"{h:02d}:30",
            "timing_wib": f"{wib_h:02d}:30",
            "mode": best_mode,
            "is_wr": is_wr_str,
            "is_exp": is_exp_str,
            "oos_wr": oos_wr_str,
            "oos_exp": oos_exp_str,
            "oos_pf": oos_pf_str,
            "verdict": verdict
        })

if __name__ == "__main__":
    run_half_hour_scan()
