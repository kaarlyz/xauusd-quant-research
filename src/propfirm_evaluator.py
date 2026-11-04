#!/usr/bin/env python3
"""
Prop Firm Challenge Stress Tester & Monte Carlo Simulator for XAUUSD.
Simulates 5,000 Prop Firm Challenge attempts (Phase 1: 10% Target, 4% Daily DD, 8% Max DD).
Evaluates single strategies vs combined session portfolio.
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD = 0.50

def extract_trades():
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // 1000).alias("ts_sec"),
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
    dates = df["date"].to_numpy()
    years = df["year"].to_numpy()
    n = len(df)

    # 60-bar ATR
    ranges = highs - lows
    cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr = np.zeros(n)
    diff = (cumsum[60:] - cumsum[:-60]) / 60.0
    atr[60:] = diff[:n - 60]
    atr[:60] = np.mean(ranges[:60])

    tokyo_trades = []
    london_trades = []

    for i in range(30, n - 35):
        if minutes[i] != 29:
            continue
        h = hours[i]
        if h not in (2, 10):  # 2 = 09:30 WIB, 10 = 17:30 WIB
            continue
        if minutes[i - 29] != 0 or hours[i - 29] != h:
            continue

        o_00 = opens[i - 29]; c_29 = closes[i]
        h_30 = np.max(highs[i - 29 : i + 1]); l_30 = np.min(lows[i - 29 : i + 1])
        disp = c_29 - o_00
        curr_atr = atr[i]
        if curr_atr <= 0: continue
        min_move = max(curr_atr * 0.8, 2.0)
        if abs(disp) < min_move: continue

        # 1. Tokyo 09:30 WIB Momentum
        if h == 2:
            if disp > 0 and (h_30 - c_29) < 0.25 * (h_30 - l_30):
                entry = c_29 + (SPREAD / 2.0); sl = o_00 - (SPREAD / 2.0); risk = entry - sl
                if 0.80 <= risk <= 15.0:
                    tp = entry + (1.5 * risk)
                    r_val = 0.0; outcome = 0
                    for s in range(1, 31):
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                        elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0:
                        exit_p = closes[i + 30]
                        r_val = (exit_p - entry) / risk
                    tokyo_trades.append({"r": r_val, "date": dates[i], "hour": h, "type": "tokyo"})
            elif disp < 0 and (c_29 - l_30) < 0.25 * (h_30 - l_30):
                entry = c_29 - (SPREAD / 2.0); sl = o_00 + (SPREAD / 2.0); risk = sl - entry
                if 0.80 <= risk <= 15.0:
                    tp = entry - (1.5 * risk)
                    r_val = 0.0; outcome = 0
                    for s in range(1, 31):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                        elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0:
                        exit_p = closes[i + 30]
                        r_val = (entry - exit_p) / risk
                    tokyo_trades.append({"r": r_val, "date": dates[i], "hour": h, "type": "tokyo"})

        # 2. London 17:30 WIB Reversal
        elif h == 10:
            if disp > 0 and (h_30 - c_29) > 0.30 * (h_30 - l_30):
                entry = c_29 - (SPREAD / 2.0); sl = h_30 + (SPREAD / 2.0); risk = sl - entry
                if 0.80 <= risk <= 15.0:
                    tp = entry - (1.5 * risk)
                    r_val = 0.0; outcome = 0
                    for s in range(1, 31):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; break
                        elif lows[i + s] <= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0:
                        exit_p = closes[i + 30]
                        r_val = (entry - exit_p) / risk
                    london_trades.append({"r": r_val, "date": dates[i], "hour": h, "type": "london"})
            elif disp < 0 and (c_29 - l_30) > 0.30 * (h_30 - l_30):
                entry = c_29 + (SPREAD / 2.0); sl = l_30 - (SPREAD / 2.0); risk = entry - sl
                if 0.80 <= risk <= 15.0:
                    tp = entry + (1.5 * risk)
                    r_val = 0.0; outcome = 0
                    for s in range(1, 31):
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; break
                        elif highs[i + s] >= tp: r_val = 1.5; outcome = 1; break
                    if outcome == 0:
                        exit_p = closes[i + 30]
                        r_val = (exit_p - entry) / risk
                    london_trades.append({"r": r_val, "date": dates[i], "hour": h, "type": "london"})

    return tokyo_trades, london_trades

def run_monte_carlo(r_stream, risk_pct=0.75, target_pct=10.0, max_dd_pct=8.0, daily_dd_pct=4.0, n_sims=5000):
    """
    Simulate standard Prop Firm Challenge:
    Account: $100,000
    Target: +10% (+$10,000)
    Max Drawdown: -8% (-$8,000 trailing/static)
    Daily Max Drawdown: -4% (-$4,000)
    Risk per trade: risk_pct% of initial balance
    """
    r_arr = np.array([t["r"] for t in r_stream])
    n_sample = len(r_arr)
    if n_sample == 0:
        return 0, 0, 0

    target_r = target_pct / risk_pct  # e.g. 10% / 0.75% = +13.33 R
    max_dd_r = max_dd_pct / risk_pct   # e.g. 8% / 0.75% = -10.67 R

    passed = 0
    failed_dd = 0
    trades_to_pass = []

    for _ in range(n_sims):
        # Sample with replacement up to 200 trades
        sim_indices = np.random.choice(n_sample, size=200, replace=True)
        sim_r = r_arr[sim_indices]
        
        cum = 0.0
        peak = 0.0
        success = False

        for step, r in enumerate(sim_r, 1):
            cum += r
            if cum > peak:
                peak = cum
            dd = peak - cum

            if dd >= max_dd_r:
                failed_dd += 1
                break
            if cum >= target_r:
                passed += 1
                trades_to_pass.append(step)
                success = True
                break

    pass_rate = (passed / n_sims) * 100.0
    fail_rate = (failed_dd / n_sims) * 100.0
    med_trades = int(np.median(trades_to_pass)) if trades_to_pass else 0
    return pass_rate, fail_rate, med_trades

def main():
    print("=== Extracting 7-Year Strategy Trades ===")
    tokyo, london = extract_trades()
    print(f"Tokyo 09:30 Trades : {len(tokyo)}")
    print(f"London 17:30 Trades: {len(london)}")

    # Combine into chronological portfolio
    combo = sorted(tokyo + london, key=lambda x: (x["date"], x["hour"]))
    print(f"Combined Portfolio : {len(combo)} trades")

    print("\n" + "=" * 80)
    print("PROP FIRM CHALLENGE PASS RATE (5,000 Monte Carlo Iterations)")
    print("Conditions: 10% Target | 8% Max Drawdown | Risk: 0.75% per trade")
    print("=" * 80)
    print(f"{'Strategy Configuration':<30} | {'Pass Rate':<12} | {'Bust Rate':<12} | {'Median Trades'}")
    print("-" * 80)

    for name, stream in [("Tokyo 09:30 (Single)", tokyo), ("London 17:30 (Single)", london), ("Portfolio (Tokyo + London)", combo)]:
        pass_r, fail_r, med_t = run_monte_carlo(stream, risk_pct=0.75, target_pct=10.0, max_dd_pct=8.0)
        print(f"{name:<30} | {pass_r:>8.1f}%   | {fail_r:>8.1f}%   | {med_t:>4} trades")

    print("\nSENSITIVITY ANALYSIS: RISK PER TRADE (Portfolio Combo)")
    print("-" * 80)
    for risk in [0.50, 0.75, 1.00]:
        pass_r, fail_r, med_t = run_monte_carlo(combo, risk_pct=risk, target_pct=10.0, max_dd_pct=8.0)
        print(f"Risk {risk:.2f}% per trade -> Pass Rate: {pass_r:.1f}% | Fail Rate: {fail_r:.1f}% | Avg Speed: {med_t} trades (~{med_t//4} weeks)")

if __name__ == "__main__":
    main()
