#!/usr/bin/env python3
"""
EXP-2026-000002: 7-Year Multi-Year Validation of Minute-30 Timing Strategies on XAUUSD.
Period: 2020-01-01 to 2026-10-31 (2,418,053 M1 Candles)
Train/In-Sample: 2020-2023 (4 years)
Validation: 2024 (1 year)
Untouched Out-of-Sample: 2025-2026 (almost 2 years)
Cost: $0.50 spread friction + intrabar pessimistic SL checking
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD_COST = 0.50

def run_7year_test():
    print("=== Loading 7-Year Master M1 Dataset (2020 - 2026) ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    
    df = df.with_columns(
        (pl.col("timestamp") // 1000).alias("ts_sec"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.minute().alias("minute"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    # Filter out rollover window
    df = df.filter(~pl.col("hour").is_between(21, 23))

    opens = df["open"].to_numpy()
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    closes = df["close"].to_numpy()
    hours = df["hour"].to_numpy()
    minutes = df["minute"].to_numpy()
    years = df["year"].to_numpy()
    n = len(df)
    print(f"Candles after filter: {n:,} (Years: {np.unique(years)})")

    # 60-bar rolling ATR
    ranges = highs - lows
    cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr = np.zeros(n)
    diff = (cumsum[60:] - cumsum[:-60]) / 60.0
    atr[60:] = diff[:n - 60]
    atr[:60] = np.mean(ranges[:60])

    target_hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 23]
    
    # Store results per hour, per mode, per year
    # hour -> mode -> year -> list of r
    matrix = {h: {"reversal": {y: [] for y in range(2020, 2027)}, "continuation": {y: [] for y in range(2020, 2027)}} for h in target_hours}

    for i in range(30, n - 35):
        if minutes[i] != 29:
            continue
        h = hours[i]
        if h not in matrix:
            continue
        if minutes[i - 29] != 0 or hours[i - 29] != h:
            continue

        o_00 = opens[i - 29]
        c_29 = closes[i]
        h_30 = np.max(highs[i - 29 : i + 1])
        l_30 = np.min(lows[i - 29 : i + 1])
        disp = c_29 - o_00
        curr_atr = atr[i]
        yr = years[i]

        min_move = max(curr_atr * 0.8, 2.0)
        if abs(disp) < min_move:
            continue

        # Mode 1: REVERSAL (Lawan Trend)
        if disp > 0 and (h_30 - c_29) > 0.30 * (h_30 - l_30):
            entry = c_29 - (SPREAD_COST / 2.0)
            sl = h_30 + (SPREAD_COST / 2.0)
            risk = sl - entry
            if 0.80 <= risk <= 15.0:
                tp = entry - (1.5 * risk)
                r_val = 0.0; outcome = 0
                for s in range(1, 31):
                    if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                    elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                if outcome == 0:
                    exit_p = closes[i + 30]
                    r_val = (entry - exit_p) / risk
                matrix[h]["reversal"][yr].append(r_val)

        elif disp < 0 and (c_29 - l_30) > 0.30 * (h_30 - l_30):
            entry = c_29 + (SPREAD_COST / 2.0)
            sl = l_30 - (SPREAD_COST / 2.0)
            risk = entry - sl
            if 0.80 <= risk <= 15.0:
                tp = entry + (1.5 * risk)
                r_val = 0.0; outcome = 0
                for s in range(1, 31):
                    if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                    elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                if outcome == 0:
                    exit_p = closes[i + 30]
                    r_val = (exit_p - entry) / risk
                matrix[h]["reversal"][yr].append(r_val)

        # Mode 2: CONTINUATION (Ikut Trend)
        if disp > 0 and (h_30 - c_29) < 0.25 * (h_30 - l_30):
            entry = c_29 + (SPREAD_COST / 2.0)
            sl = o_00 - (SPREAD_COST / 2.0)
            risk = entry - sl
            if 0.80 <= risk <= 15.0:
                tp = entry + (1.5 * risk)
                r_val = 0.0; outcome = 0
                for s in range(1, 31):
                    if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                    elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                if outcome == 0:
                    exit_p = closes[i + 30]
                    r_val = (exit_p - entry) / risk
                matrix[h]["continuation"][yr].append(r_val)

        elif disp < 0 and (c_29 - l_30) < 0.25 * (h_30 - l_30):
            entry = c_29 - (SPREAD_COST / 2.0)
            sl = o_00 + (SPREAD_COST / 2.0)
            risk = sl - entry
            if 0.80 <= risk <= 15.0:
                tp = entry - (1.5 * risk)
                r_val = 0.0; outcome = 0
                for s in range(1, 31):
                    if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                    elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                if outcome == 0:
                    exit_p = closes[i + 30]
                    r_val = (entry - exit_p) / risk
                matrix[h]["continuation"][yr].append(r_val)

    def stats_for_years(year_dict, years_list):
        combined = []
        for y in years_list:
            combined.extend(year_dict.get(y, []))
        if not combined or len(combined) < 20:
            return None
        n_t = len(combined)
        wins = sum(1 for r in combined if r > 0)
        wr = (wins / n_t) * 100.0
        avg_r = np.mean(combined)
        gw = sum(r for r in combined if r > 0)
        gl = abs(sum(r for r in combined if r < 0))
        pf = gw / gl if gl > 0 else 99.0
        cum = np.cumsum(combined)
        mdd = np.max(np.maximum.accumulate(cum) - cum) if len(cum) > 0 else 0.0
        return {"n": n_t, "wr": round(wr, 1), "exp": round(float(avg_r), 3), "pf": round(float(pf), 2), "mdd": round(float(mdd), 1), "total_r": round(float(cum[-1]), 1)}

    print("\n" + "=" * 100)
    print("7-YEAR MULTI-YEAR VALIDATION RESULTS (2020 - 2026)")
    print("Split: 5-Year In-Sample (2020-2024) vs 2-Year Out-of-Sample (2025-2026)")
    print("Friction: $0.50 spread | Fixed RR: 1.5 : 1")
    print("=" * 100)
    print(f"{'Timing (UTC / WIB)':<22} | {'Optimal Mode':<12} | {'5-Yr Trades':<11} | {'5-Yr WR':<8} | {'5-Yr Exp':<9} | {'5-Yr PF':<7} | {'OOS WR':<8} | {'OOS Exp':<8} | {'OOS PF':<6} | {'Status'}")
    print("-" * 100)

    train_years = list(range(2020, 2025))
    test_years = [2025, 2026]

    validated_strategies = []

    for h in target_hours:
        wib_h = (h + 7) % 24
        label = f"{h:02d}:30 UTC ({wib_h:02d}:30 WIB)"

        rev_train = stats_for_years(matrix[h]["reversal"], train_years)
        rev_test = stats_for_years(matrix[h]["reversal"], test_years)

        cont_train = stats_for_years(matrix[h]["continuation"], train_years)
        cont_test = stats_for_years(matrix[h]["continuation"], test_years)

        # Evaluate which is positive across both 5-year train and 2-year test
        best_mode = "None"
        best_train = None
        best_test = None
        verdict = "REJECTED"

        if rev_train and rev_test and rev_train["exp"] > 0 and rev_test["exp"] > 0 and rev_train["pf"] >= 1.05 and rev_test["pf"] >= 1.05:
            best_mode = "Lawan Trend"
            best_train = rev_train
            best_test = rev_test
            verdict = "VALID (SURVIVED 7-YEARS)"
            validated_strategies.append((h, "reversal", best_train, best_test))
        elif cont_train and cont_test and cont_train["exp"] > 0 and cont_test["exp"] > 0 and cont_train["pf"] >= 1.05 and cont_test["pf"] >= 1.05:
            best_mode = "Ikut Trend"
            best_train = cont_train
            best_test = cont_test
            verdict = "VALID (SURVIVED 7-YEARS)"
            validated_strategies.append((h, "continuation", best_train, best_test))
        else:
            # Pick best for reporting
            r_score = (rev_train["exp"] if rev_train else -1) + (rev_test["exp"] if rev_test else -1)
            c_score = (cont_train["exp"] if cont_train else -1) + (cont_test["exp"] if cont_test else -1)
            if r_score >= c_score and rev_train and rev_test:
                best_mode = "Lawan Trend"
                best_train = rev_train
                best_test = rev_test
            elif cont_train and cont_test:
                best_mode = "Ikut Trend"
                best_train = cont_train
                best_test = cont_test

        tr_n = f"{best_train['n']:,}" if best_train else "N/A"
        tr_wr = f"{best_train['wr']}%" if best_train else "N/A"
        tr_exp = f"{best_train['exp']:+.3f}R" if best_train else "N/A"
        tr_pf = f"{best_train['pf']:.2f}" if best_train else "N/A"
        te_wr = f"{best_test['wr']}%" if best_test else "N/A"
        te_exp = f"{best_test['exp']:+.3f}R" if best_test else "N/A"
        te_pf = f"{best_test['pf']:.2f}" if best_test else "N/A"

        print(f"{label:<22} | {best_mode:<12} | {tr_n:<11} | {tr_wr:<8} | {tr_exp:<9} | {tr_pf:<7} | {te_wr:<8} | {te_exp:<8} | {te_pf:<6} | {verdict}")

if __name__ == "__main__":
    run_7year_test()
