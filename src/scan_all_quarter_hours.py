#!/usr/bin/env python3
"""
Quantitative Discovery Engine: Quarter-Hour Timing (:15 & :45) on XAUUSD M1.
Tests every single hour across the 24-hour cycle:
- Decision Point 1: Minute :15 (Close of minute 14)
- Decision Point 2: Minute :45 (Close of minute 44)
Tests:
- Mode A: Ikut Trend (15m Momentum Continuation)
- Mode B: Lawan Trend (15m Exhaustion Reversal)

Dataset: 4,182,209 Continuous M1 Candles (2015 - 2026).
Friction: $0.50 spread cost per round-trip + intrabar pessimistic SL execution.
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD_COST = 0.50

def run_quarter_scan():
    print("=== Loading 12-Year M1 Dataset (4,182,209 candles) ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.minute().alias("minute"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )
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

    # Matrix storage: (hour, minute_mark) -> mode -> train/test -> list of r
    # minute_mark in (15, 45)
    matrix = {
        (h, m_mark): {
            "ikut_trend": {"train": [], "test": []},
            "lawan_trend": {"train": [], "test": []}
        }
        for h in target_hours
        for m_mark in (15, 45)
    }

    for i in range(65, n - 45):
        m = minutes[i]
        h = hours[i]
        if h not in target_hours: continue
        yr = years[i]
        split = "test" if yr >= 2024 else "train"
        curr_atr = atr[i]
        if curr_atr <= 0.2: continue

        # ====================================================
        # DECISION POINT 1: MINUTE :15 (evaluates at minute 14)
        # ====================================================
        if m == 14:
            if minutes[i - 14] != 0 or hours[i - 14] != h: continue
            o_00 = opens[i - 14]; c_14 = closes[i]
            h_15 = np.max(highs[i - 14 : i + 1]); l_15 = np.min(lows[i - 14 : i + 1])
            disp = c_14 - o_00
            if abs(disp) < max(curr_atr * 0.7, 1.5): continue

            # Mode A: Ikut Trend at :15 (solid impulse, wick < 25%)
            if disp > 0 and (h_15 - c_14) < 0.25 * (h_15 - l_15):
                entry = c_14 + (SPREAD_COST / 2.0); sl = o_00 - (SPREAD_COST / 2.0); risk = entry - sl
                if 0.80 <= risk <= 15.0:
                    tp = entry + (1.5 * risk)
                    outcome = 0; r_val = 0.0
                    for s in range(1, 31):
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                        elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0: r_val = (closes[i + 30] - entry) / risk
                    matrix[(h, 15)]["ikut_trend"][split].append(r_val)

            elif disp < 0 and (c_14 - l_15) < 0.25 * (h_15 - l_15):
                entry = c_14 - (SPREAD_COST / 2.0); sl = o_00 + (SPREAD_COST / 2.0); risk = sl - entry
                if 0.80 <= risk <= 15.0:
                    tp = entry - (1.5 * risk)
                    outcome = 0; r_val = 0.0
                    for s in range(1, 31):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                        elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0: r_val = (entry - closes[i + 30]) / risk
                    matrix[(h, 15)]["ikut_trend"][split].append(r_val)

            # Mode B: Lawan Trend at :15 (rejection wick > 35%)
            if disp > 0 and (h_15 - c_14) > 0.35 * (h_15 - l_15):
                entry = c_14 - (SPREAD_COST / 2.0); sl = h_15 + (SPREAD_COST / 2.0); risk = sl - entry
                if 0.80 <= risk <= 15.0:
                    tp = entry - (1.5 * risk)
                    outcome = 0; r_val = 0.0
                    for s in range(1, 31):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                        elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0: r_val = (entry - closes[i + 30]) / risk
                    matrix[(h, 15)]["lawan_trend"][split].append(r_val)

            elif disp < 0 and (c_14 - l_15) > 0.35 * (h_15 - l_15):
                entry = c_14 + (SPREAD_COST / 2.0); sl = l_15 - (SPREAD_COST / 2.0); risk = entry - sl
                if 0.80 <= risk <= 15.0:
                    tp = entry + (1.5 * risk)
                    outcome = 0; r_val = 0.0
                    for s in range(1, 31):
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                        elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0: r_val = (closes[i + 30] - entry) / risk
                    matrix[(h, 15)]["lawan_trend"][split].append(r_val)

        # ====================================================
        # DECISION POINT 2: MINUTE :45 (evaluates at minute 44)
        # ====================================================
        elif m == 44:
            if minutes[i - 14] != 30 or hours[i - 14] != h: continue
            o_30 = opens[i - 14]; c_44 = closes[i]
            h_45 = np.max(highs[i - 14 : i + 1]); l_45 = np.min(lows[i - 14 : i + 1])
            disp = c_44 - o_30
            if abs(disp) < max(curr_atr * 0.7, 1.5): continue

            # Mode A: Ikut Trend at :45
            if disp > 0 and (h_45 - c_44) < 0.25 * (h_45 - l_45):
                entry = c_44 + (SPREAD_COST / 2.0); sl = o_30 - (SPREAD_COST / 2.0); risk = entry - sl
                if 0.80 <= risk <= 15.0:
                    tp = entry + (1.5 * risk)
                    outcome = 0; r_val = 0.0
                    for s in range(1, 20): # hold up to end of hour / 20 mins
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                        elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0: r_val = (closes[i + 15] - entry) / risk
                    matrix[(h, 45)]["ikut_trend"][split].append(r_val)

            elif disp < 0 and (c_44 - l_45) < 0.25 * (h_45 - l_45):
                entry = c_44 - (SPREAD_COST / 2.0); sl = o_30 + (SPREAD_COST / 2.0); risk = sl - entry
                if 0.80 <= risk <= 15.0:
                    tp = entry - (1.5 * risk)
                    outcome = 0; r_val = 0.0
                    for s in range(1, 20):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                        elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0: r_val = (entry - closes[i + 15]) / risk
                    matrix[(h, 45)]["ikut_trend"][split].append(r_val)

            # Mode B: Lawan Trend at :45
            if disp > 0 and (h_45 - c_44) > 0.35 * (h_45 - l_45):
                entry = c_44 - (SPREAD_COST / 2.0); sl = h_45 + (SPREAD_COST / 2.0); risk = sl - entry
                if 0.80 <= risk <= 15.0:
                    tp = entry - (1.5 * risk)
                    outcome = 0; r_val = 0.0
                    for s in range(1, 20):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                        elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0: r_val = (entry - closes[i + 15]) / risk
                    matrix[(h, 45)]["lawan_trend"][split].append(r_val)

            elif disp < 0 and (c_44 - l_45) > 0.35 * (h_45 - l_45):
                entry = c_44 + (SPREAD_COST / 2.0); sl = l_45 - (SPREAD_COST / 2.0); risk = entry - sl
                if 0.80 <= risk <= 15.0:
                    tp = entry + (1.5 * risk)
                    outcome = 0; r_val = 0.0
                    for s in range(1, 20):
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                        elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0: r_val = (closes[i + 15] - entry) / risk
                    matrix[(h, 45)]["lawan_trend"][split].append(r_val)

    def stats_summary(r_list):
        if not r_list or len(r_list) < 20: return None
        n_t = len(r_list)
        wins = sum(1 for r in r_list if r > 0)
        wr = (wins / n_t) * 100.0
        avg_r = np.mean(r_list)
        gw = sum(r for r in r_list if r > 0); gl = abs(sum(r for r in r_list if r < 0))
        pf = gw / gl if gl > 0 else 99.0
        return {"n": n_t, "wr": round(wr, 1), "exp": round(float(avg_r), 3), "pf": round(float(pf), 2)}

    print("\n" + "=" * 105)
    print("QUARTER-HOUR (:15 & :45) TIMING MATRIX ON XAUUSD (12 YEARS: 2015-2026)")
    print("Split: 9-Yr Train (2015-2023) vs 3-Yr Test (2024-2026) | Target RR: 1.5 : 1 | Friction: $0.50 spread")
    print("=" * 105)
    print(f"{'Timing (UTC / WIB)':<22} | {'Optimal Mode':<13} | {'Train WR':<9} | {'Train Exp':<10} | {'Test WR':<8} | {'Test Exp':<9} | {'Test PF':<7} | {'Verdict'}")
    print("-" * 105)

    all_keys = sorted(list(matrix.keys()))
    validated_quarters = []

    for (h, m_mark) in all_keys:
        wib_h = (h + 7) % 24
        label = f"{h:02d}:{m_mark:02d} UTC ({wib_h:02d}:{m_mark:02d} WIB)"

        ik_tr = stats_summary(matrix[(h, m_mark)]["ikut_trend"]["train"])
        ik_te = stats_summary(matrix[(h, m_mark)]["ikut_trend"]["test"])
        lw_tr = stats_summary(matrix[(h, m_mark)]["lawan_trend"]["train"])
        lw_te = stats_summary(matrix[(h, m_mark)]["lawan_trend"]["test"])

        best_mode = "None"
        best_tr = None
        best_te = None
        verdict = "REJECTED"

        # Check if Ikut Trend passes both
        if ik_tr and ik_te and ik_tr["exp"] > 0 and ik_te["exp"] > 0 and ik_tr["pf"] >= 1.05 and ik_te["pf"] >= 1.05:
            best_mode = "Ikut Trend"
            best_tr = ik_tr
            best_te = ik_te
            verdict = "VALID (Profitable)"
            validated_quarters.append(((h, m_mark), "ikut_trend", best_tr, best_te))
        # Check if Lawan Trend passes both
        elif lw_tr and lw_te and lw_tr["exp"] > 0 and lw_te["exp"] > 0 and lw_tr["pf"] >= 1.05 and lw_te["pf"] >= 1.05:
            best_mode = "Lawan Trend"
            best_tr = lw_tr
            best_te = lw_te
            verdict = "VALID (Profitable)"
            validated_quarters.append(((h, m_mark), "lawan_trend", best_tr, best_te))
        else:
            # Pick the higher test score for display
            ik_score = (ik_tr["exp"] if ik_tr else -1) + (ik_te["exp"] if ik_te else -1)
            lw_score = (lw_tr["exp"] if lw_tr else -1) + (lw_te["exp"] if lw_te else -1)
            if ik_score >= lw_score and ik_te:
                best_mode = "Ikut Trend"
                best_tr = ik_tr
                best_te = ik_te
            elif lw_te:
                best_mode = "Lawan Trend"
                best_tr = lw_tr
                best_te = lw_te

        tr_wr = f"{best_tr['wr']}%" if best_tr else "N/A"
        tr_exp = f"{best_tr['exp']:+.3f}R" if best_tr else "N/A"
        te_wr = f"{best_te['wr']}%" if best_te else "N/A"
        te_exp = f"{best_te['exp']:+.3f}R" if best_te else "N/A"
        te_pf = f"{best_te['pf']:.2f}" if best_te else "N/A"

        # Print all or print significant ones
        if verdict.startswith("VALID") or (best_te and best_te["pf"] >= 1.15):
            print(f"{label:<22} | {best_mode:<13} | {tr_wr:<9} | {tr_exp:<10} | {te_wr:<8} | {te_exp:<9} | {te_pf:<7} | {verdict}")

if __name__ == "__main__":
    run_quarter_scan()
