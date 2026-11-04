#!/usr/bin/env python3
"""
Interactive Visual Trade-by-Trade Simulator for XAUUSD M1.
Focus Strategy: London 17:30 WIB (10:30 UTC) Mean Reversion & Tokyo 09:30 WIB (02:30 UTC) Trend Acceleration.
Prints detailed execution tickets, excursion metrics (MAE/MFE), and equity progression in R.
"""

import os
import sys
import numpy as np
import polars as pl
import datetime

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD = 0.50

def run_simulation(strategy="london_1730"):
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // 1000).alias("ts_sec"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.minute().alias("minute"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    # Exclude rollover
    df = df.filter(~pl.col("hour").is_between(21, 23))
    
    target_hour = 10 if strategy == "london_1730" else 2
    strat_title = "LONDON 17:30 WIB (10:30 UTC) MEAN REVERSION" if strategy == "london_1730" else "TOKYO 09:30 WIB (02:30 UTC) MOMENTUM RUN"
    is_reversal = (strategy == "london_1730")

    print("=" * 80)
    print(f"VISUAL SIMULATOR: {strat_title}")
    print(f"Execution: M1 Candlestick Level | Spread Cost: ${SPREAD:.2f} | Target RR: 1.5 : 1")
    print("=" * 80)

    opens = df["open"].to_numpy()
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    closes = df["close"].to_numpy()
    hours = df["hour"].to_numpy()
    minutes = df["minute"].to_numpy()
    dates = df["date"].to_numpy()
    ts_sec = df["ts_sec"].to_numpy()
    n = len(df)

    # 60-bar ATR
    ranges = highs - lows
    cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr = np.zeros(n)
    diff = (cumsum[60:] - cumsum[:-60]) / 60.0
    atr[60:] = diff[:n - 60]
    atr[:60] = np.mean(ranges[:60])

    trades = []
    equity_r = 0.0

    for i in range(30, n - 35):
        if minutes[i] != 29 or hours[i] != target_hour:
            continue
        if minutes[i - 29] != 0 or hours[i - 29] != target_hour:
            continue

        o_00 = opens[i - 29]
        c_29 = closes[i]
        h_30 = np.max(highs[i - 29 : i + 1])
        l_30 = np.min(lows[i - 29 : i + 1])
        disp = c_29 - o_00
        curr_atr = atr[i]
        min_move = max(curr_atr * 0.8, 2.0)

        if abs(disp) < min_move:
            continue

        dt_utc = datetime.datetime.fromtimestamp(ts_sec[i], tz=datetime.timezone.utc)
        dt_wib = dt_utc + datetime.timedelta(hours=7)

        if is_reversal:
            # Reversal logic
            if disp > 0 and (h_30 - c_29) > 0.30 * (h_30 - l_30):
                direction = "SHORT"
                entry = c_29 - (SPREAD / 2.0)
                sl = h_30 + (SPREAD / 2.0)
                risk = sl - entry
                if not (0.80 <= risk <= 15.0):
                    continue
                tp = entry - (1.5 * risk)

                # Simulate next 30 bars
                outcome = 0
                r_val = 0.0
                max_fav = 0.0
                max_adv = 0.0
                exit_bar = 30
                exit_price = closes[i + 30]

                for s in range(1, 31):
                    idx = i + s
                    cur_h = highs[idx]
                    cur_l = lows[idx]
                    
                    fav = entry - cur_l
                    adv = cur_h - entry
                    if fav > max_fav: max_fav = fav
                    if adv > max_adv: max_adv = adv

                    if cur_h >= sl:
                        outcome = -1
                        r_val = -1.0
                        exit_price = sl
                        exit_bar = s
                        break
                    elif cur_l <= tp:
                        outcome = 1
                        r_val = 1.5
                        exit_price = tp
                        exit_bar = s
                        break

                if outcome == 0:
                    exit_price = closes[i + 30]
                    r_val = (entry - exit_price) / risk
                    outcome = 1 if r_val > 0 else -1

                equity_r += r_val
                trades.append({
                    "date_wib": dt_wib.strftime("%Y-%m-%d %H:%M"),
                    "dir": direction,
                    "entry": round(entry, 2),
                    "sl": round(sl, 2),
                    "tp": round(tp, 2),
                    "risk": round(risk, 2),
                    "exit_price": round(exit_price, 2),
                    "outcome": "WIN" if outcome == 1 else "LOSS",
                    "r_val": round(r_val, 2),
                    "exit_min": exit_bar,
                    "mfe_r": round(max_fav / risk, 2),
                    "mae_r": round(max_adv / risk, 2),
                    "cum_r": round(equity_r, 2)
                })

            elif disp < 0 and (c_29 - l_30) > 0.30 * (h_30 - l_30):
                direction = "LONG"
                entry = c_29 + (SPREAD / 2.0)
                sl = l_30 - (SPREAD / 2.0)
                risk = entry - sl
                if not (0.80 <= risk <= 15.0):
                    continue
                tp = entry + (1.5 * risk)

                outcome = 0
                r_val = 0.0
                max_fav = 0.0
                max_adv = 0.0
                exit_bar = 30
                exit_price = closes[i + 30]

                for s in range(1, 31):
                    idx = i + s
                    cur_h = highs[idx]
                    cur_l = lows[idx]

                    fav = cur_h - entry
                    adv = entry - cur_l
                    if fav > max_fav: max_fav = fav
                    if adv > max_adv: max_adv = adv

                    if cur_l <= sl:
                        outcome = -1
                        r_val = -1.0
                        exit_price = sl
                        exit_bar = s
                        break
                    elif cur_h >= tp:
                        outcome = 1
                        r_val = 1.5
                        exit_price = tp
                        exit_bar = s
                        break

                if outcome == 0:
                    exit_price = closes[i + 30]
                    r_val = (exit_price - entry) / risk
                    outcome = 1 if r_val > 0 else -1

                equity_r += r_val
                trades.append({
                    "date_wib": dt_wib.strftime("%Y-%m-%d %H:%M"),
                    "dir": direction,
                    "entry": round(entry, 2),
                    "sl": round(sl, 2),
                    "tp": round(tp, 2),
                    "risk": round(risk, 2),
                    "exit_price": round(exit_price, 2),
                    "outcome": "WIN" if outcome == 1 else "LOSS",
                    "r_val": round(r_val, 2),
                    "exit_min": exit_bar,
                    "mfe_r": round(max_fav / risk, 2),
                    "mae_r": round(max_adv / risk, 2),
                    "cum_r": round(equity_r, 2)
                })
        else:
            # Tokyo 09:30 WIB (02:30 UTC) Trend Acceleration Logic
            if disp > 0 and (h_30 - c_29) < 0.25 * (h_30 - l_30):
                direction = "LONG"
                entry = c_29 + (SPREAD / 2.0)
                sl = o_00 - (SPREAD / 2.0)
                risk = entry - sl
                if 0.80 <= risk <= 15.0:
                    tp = entry + (1.5 * risk)
                    outcome = 0; r_val = 0.0; max_fav = 0.0; max_adv = 0.0; exit_bar = 30; exit_price = closes[i + 30]
                    for s in range(1, 31):
                        idx = i + s; cur_h = highs[idx]; cur_l = lows[idx]
                        fav = cur_h - entry; adv = entry - cur_l
                        if fav > max_fav: max_fav = fav
                        if adv > max_adv: max_adv = adv
                        if cur_l <= sl:
                            outcome = -1; r_val = -1.0; exit_price = sl; exit_bar = s; break
                        elif cur_h >= tp:
                            outcome = 1; r_val = 1.5; exit_price = tp; exit_bar = s; break
                    if outcome == 0:
                        exit_price = closes[i + 30]
                        r_val = (exit_price - entry) / risk
                        outcome = 1 if r_val > 0 else -1
                    equity_r += r_val
                    trades.append({
                        "date_wib": dt_wib.strftime("%Y-%m-%d %H:%M"), "dir": direction,
                        "entry": round(entry, 2), "sl": round(sl, 2), "tp": round(tp, 2), "risk": round(risk, 2),
                        "exit_price": round(exit_price, 2), "outcome": "WIN" if outcome == 1 else "LOSS",
                        "r_val": round(r_val, 2), "exit_min": exit_bar, "mfe_r": round(max_fav / risk, 2),
                        "mae_r": round(max_adv / risk, 2), "cum_r": round(equity_r, 2)
                    })
            elif disp < 0 and (c_29 - l_30) < 0.25 * (h_30 - l_30):
                direction = "SHORT"
                entry = c_29 - (SPREAD / 2.0)
                sl = o_00 + (SPREAD / 2.0)
                risk = sl - entry
                if 0.80 <= risk <= 15.0:
                    tp = entry - (1.5 * risk)
                    outcome = 0; r_val = 0.0; max_fav = 0.0; max_adv = 0.0; exit_bar = 30; exit_price = closes[i + 30]
                    for s in range(1, 31):
                        idx = i + s; cur_h = highs[idx]; cur_l = lows[idx]
                        fav = entry - cur_l; adv = cur_h - entry
                        if fav > max_fav: max_fav = fav
                        if adv > max_adv: max_adv = adv
                        if cur_h >= sl:
                            outcome = -1; r_val = -1.0; exit_price = sl; exit_bar = s; break
                        elif cur_l <= tp:
                            outcome = 1; r_val = 1.5; exit_price = tp; exit_bar = s; break
                    if outcome == 0:
                        exit_price = closes[i + 30]
                        r_val = (entry - exit_price) / risk
                        outcome = 1 if r_val > 0 else -1
                    equity_r += r_val
                    trades.append({
                        "date_wib": dt_wib.strftime("%Y-%m-%d %H:%M"), "dir": direction,
                        "entry": round(entry, 2), "sl": round(sl, 2), "tp": round(tp, 2), "risk": round(risk, 2),
                        "exit_price": round(exit_price, 2), "outcome": "WIN" if outcome == 1 else "LOSS",
                        "r_val": round(r_val, 2), "exit_min": exit_bar, "mfe_r": round(max_fav / risk, 2),
                        "mae_r": round(max_adv / risk, 2), "cum_r": round(equity_r, 2)
                    })

    print(f"\nTotal Qualifying Trades: {len(trades)}")
    print("\nSAMPLE RECENT TRADES (Last 15 Executions):")
    print(f"{'Date & Time (WIB)':<18} | {'Side':<5} | {'Entry':<8} | {'SL':<8} | {'TP':<8} | {'Result':<6} | {'Return':<7} | {'Hold':<6} | {'Cum R'}")
    print("-" * 88)
    
    for t in trades[-15:]:
        tag = "[+WIN ]" if t["outcome"] == "WIN" else "[-LOSS]"
        print(f"{t['date_wib']:<18} | {t['dir']:<5} | {t['entry']:<8.2f} | {t['sl']:<8.2f} | {t['tp']:<8.2f} | {tag:<6} | {t['r_val']:>+5.2f}R | {t['exit_min']:>2}m   | {t['cum_r']:>+6.2f}R")

    # Overall Metrics
    wins = sum(1 for t in trades if t["outcome"] == "WIN")
    wr = (wins / len(trades)) * 100.0 if trades else 0.0
    gw = sum(t["r_val"] for t in trades if t["r_val"] > 0)
    gl = abs(sum(t["r_val"] for t in trades if t["r_val"] < 0))
    pf = gw / gl if gl > 0 else 99.0

    cum_series = np.array([t["cum_r"] for t in trades])
    peak = np.maximum.accumulate(cum_series)
    max_dd = np.max(peak - cum_series)

    print("\n" + "=" * 80)
    print("FINAL STRATEGY PERFORMANCE SCORECARD")
    print("=" * 80)
    print(f"Total Sample Size    : {len(trades)} trades")
    print(f"Win Rate (WR)        : {wr:.1f}%")
    print(f"Reward-to-Risk (RR)  : 1.50 : 1 (fixed)")
    print(f"Profit Factor (PF)   : {pf:.2f}")
    print(f"Average Expectancy   : {equity_r / len(trades):+.3f} R / trade")
    print(f"Cumulative Profit    : {equity_r:+.2f} R")
    print(f"Max Drawdown (MDD)   : -{max_dd:.2f} R")
    print("=" * 80)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "london_1730"
    run_simulation(mode)
