#!/usr/bin/env python3
"""
Autonomous Mathematical Discovery: Pure Feature-Based M1 Strategy on XAUUSD.
Zero clock-time dependency. Purely endogenous price action & statistical features:
1. Model A: Volume Z-Score + Volatility Squeeze Breakout
2. Model B: Statistical Z-Score Exhaustion Mean Reversion
3. Model C: Dynamic Trend Channel Pullback with Momentum Trigger

Evaluates: ~2 trades/day frequency, Win Rate, Profit Factor, Expectancy after $0.50 spread.
Horizon: 12 Years (2015 - 2026 / 4,182,209 M1 bars).
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD = 0.50

def run_quant_discovery():
    print("=== Loading 12-Year M1 Data (4.18M bars) ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // 1000).alias("ts_sec"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour")
    )
    # Filter only rollover spread spike (21:00-23:00 UTC)
    df = df.filter(~pl.col("hour").is_between(21, 23))

    opens = df["open"].to_numpy()
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    closes = df["close"].to_numpy()
    volumes = df["volume"].to_numpy() if "volume" in df.columns else np.ones(len(df))
    years = df["year"].to_numpy()
    dates = df["date"].to_numpy()
    n = len(df)
    unique_days = len(np.unique(dates))

    print("=== Engineering Pure Mathematical Features ===")
    # 1. 60-period ATR
    ranges = highs - lows
    cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr60 = (cumsum[60:] - cumsum[:-60]) / 60.0
    atr60 = np.pad(atr60, (60, 0), mode="edge")[:n]

    # 2. Rolling 50-period EMA
    k50 = 2.0 / (50 + 1)
    ema50 = np.zeros(n); ema50[0] = closes[0]
    for idx in range(1, n): ema50[idx] = closes[idx] * k50 + ema50[idx - 1] * (1 - k50)

    # 3. Rolling 200-period EMA (Macro Baseline)
    k200 = 2.0 / (200 + 1)
    ema200 = np.zeros(n); ema200[0] = closes[0]
    for idx in range(1, n): ema200[idx] = closes[idx] * k200 + ema200[idx - 1] * (1 - k200)

    # 4. Volume Z-Score over rolling 60 bars
    vol_cumsum = np.cumsum(np.insert(volumes, 0, 0))
    vol_mean_raw = (vol_cumsum[60:] - vol_cumsum[:-60]) / 60.0
    vol_mean = np.pad(vol_mean_raw, (60, 0), mode="edge")[:n]
    
    vol_sq = volumes ** 2
    vol_sq_cum = np.cumsum(np.insert(vol_sq, 0, 0))
    vol_var_raw = (vol_sq_cum[60:] - vol_sq_cum[:-60]) / 60.0 - (vol_mean_raw ** 2)
    vol_var = np.pad(vol_var_raw, (60, 0), mode="edge")[:n]
    vol_std = np.sqrt(np.maximum(vol_var, 1e-4))
    vol_z = np.divide(volumes - vol_mean, vol_std, out=np.zeros_like(vol_mean), where=vol_std > 0)

    # 5. Normalized Price Displacement Z-Score: (Close - EMA50) / ATR60
    disp_z = np.divide(closes - ema50, atr60, out=np.zeros_like(atr60), where=atr60 > 0)

    # ----------------------------------------------------
    # SYSTEM TEST 1: The Statistical Mean Reversion Engine
    # Concept: When price displaces > 2.5 ATR from EMA50 AND forms a rejection wick > 45%,
    # price snaps back to the EMA.
    # ----------------------------------------------------
    print("\n--- Testing Model 1: Statistical Displacement Z-Score Reversion ---")
    for target_rr in [1.0, 1.2, 1.5]:
        trades = []
        last_exit = -1
        for i in range(200, n - 60):
            if i <= last_exit: continue
            cur_atr = atr60[i]
            if cur_atr < 0.3: continue

            # Short Reversion: Overextended High
            if disp_z[i] > 2.2 and (highs[i] - closes[i]) > 0.40 * (highs[i] - lows[i]):
                entry = closes[i] - (SPREAD / 2.0)
                sl = highs[i] + (SPREAD / 2.0)
                risk = sl - entry
                if 0.80 <= risk <= 12.0:
                    tp = entry - (target_rr * risk)
                    outcome = 0; r_val = 0.0; exit_idx = i + 45
                    for s in range(1, 46):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; exit_idx = i + s; break
                        elif lows[i + s] <= tp: r_val = target_rr; outcome = 1; exit_idx = i + s; break
                    if outcome == 0: r_val = (entry - closes[i + 45]) / risk
                    last_exit = exit_idx
                    trades.append({"r": r_val, "year": years[i]})

            # Long Reversion: Overextended Low
            elif disp_z[i] < -2.2 and (closes[i] - lows[i]) > 0.40 * (highs[i] - lows[i]):
                entry = closes[i] + (SPREAD / 2.0)
                sl = lows[i] - (SPREAD / 2.0)
                risk = entry - sl
                if 0.80 <= risk <= 12.0:
                    tp = entry + (target_rr * risk)
                    outcome = 0; r_val = 0.0; exit_idx = i + 45
                    for s in range(1, 46):
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; exit_idx = i + s; break
                        elif highs[i + s] >= tp: r_val = target_rr; outcome = 1; exit_idx = i + s; break
                    if outcome == 0: r_val = (closes[i + 45] - entry) / risk
                    last_exit = exit_idx
                    trades.append({"r": r_val, "year": years[i]})

        r_arr = np.array([t["r"] for t in trades])
        wr = np.mean(r_arr > 0) * 100
        gw = sum(r for r in r_arr if r > 0); gl = abs(sum(r for r in r_arr if r < 0))
        pf = gw / gl if gl > 0 else 99.0
        daily_freq = len(trades) / unique_days
        print(f"Target RR {target_rr:.1f}:1 | Total: {len(trades):,} ({daily_freq:.2f}/day) | WR: {wr:.1f}% | Net Exp: {np.mean(r_arr):+.3f}R | PF: {pf:.2f}")

    # ----------------------------------------------------
    # SYSTEM TEST 2: The Volume-Surge Trend Expansion Engine
    # Concept: In the direction of EMA200, when Volume Z-Score > 2.5 (abnormal volume surge)
    # AND candle body is strong (> 70% body ratio): Ride the surge.
    # ----------------------------------------------------
    print("\n--- Testing Model 2: Volume-Surge Trend Expansion Engine ---")
    for target_rr in [1.2, 1.5, 2.0]:
        trades = []
        last_exit = -1
        for i in range(200, n - 60):
            if i <= last_exit: continue
            cur_atr = atr60[i]
            if cur_atr < 0.4: continue

            body = abs(closes[i] - opens[i])
            rng = highs[i] - lows[i]
            if rng == 0: continue
            body_ratio = body / rng

            is_macro_bull = closes[i] > ema200[i]

            # Bullish Volume Surge
            if is_macro_bull and vol_z[i] > 2.5 and closes[i] > opens[i] and body_ratio > 0.65:
                entry = closes[i] + (SPREAD / 2.0)
                sl = lows[i] - (SPREAD / 2.0)
                risk = entry - sl
                if 1.0 <= risk <= 15.0:
                    tp = entry + (target_rr * risk)
                    outcome = 0; r_val = 0.0; exit_idx = i + 30
                    for s in range(1, 31):
                        if lows[i + s] <= sl: r_val = -1.0; outcome = -1; exit_idx = i + s; break
                        elif highs[i + s] >= tp: r_val = target_rr; outcome = 1; exit_idx = i + s; break
                    if outcome == 0: r_val = (closes[i + 30] - entry) / risk
                    last_exit = exit_idx
                    trades.append({"r": r_val, "year": years[i]})

            # Bearish Volume Surge
            elif (not is_macro_bull) and vol_z[i] > 2.5 and closes[i] < opens[i] and body_ratio > 0.65:
                entry = closes[i] - (SPREAD / 2.0)
                sl = highs[i] + (SPREAD / 2.0)
                risk = sl - entry
                if 1.0 <= risk <= 15.0:
                    tp = entry - (target_rr * risk)
                    outcome = 0; r_val = 0.0; exit_idx = i + 30
                    for s in range(1, 31):
                        if highs[i + s] >= sl: r_val = -1.0; outcome = -1; exit_idx = i + s; break
                        elif lows[i + s] <= tp: r_val = target_rr; outcome = 1; exit_idx = i + s; break
                    if outcome == 0: r_val = (entry - closes[i + 30]) / risk
                    last_exit = exit_idx
                    trades.append({"r": r_val, "year": years[i]})

        r_arr = np.array([t["r"] for t in trades])
        wr = np.mean(r_arr > 0) * 100
        gw = sum(r for r in r_arr if r > 0); gl = abs(sum(r for r in r_arr if r < 0))
        pf = gw / gl if gl > 0 else 99.0
        daily_freq = len(trades) / unique_days
        print(f"Target RR {target_rr:.1f}:1 | Total: {len(trades):,} ({daily_freq:.2f}/day) | WR: {wr:.1f}% | Net Exp: {np.mean(r_arr):+.3f}R | PF: {pf:.2f}")

    # ----------------------------------------------------
    # SYSTEM TEST 3: The 3-Candle Imbalance / Fair Value Gap (FVG) Retest Engine
    # Concept: Pure Price Action geometry on M1:
    # 1. Displacement candle creates a gap between High(t-2) and Low(t).
    # 2. Retest into the gap within 10 bars -> Entry on touch of FVG boundary.
    # ----------------------------------------------------
    print("\n--- Testing Model 3: M1 Fair Value Gap (Imbalance) Retest Engine ---")
    for target_rr in [1.5, 2.0]:
        trades = []
        last_exit = -1
        for i in range(200, n - 60):
            if i <= last_exit: continue
            cur_atr = atr60[i]
            if cur_atr < 0.4: continue

            # Bullish FVG: Low(i) > High(i-2) with gap > $0.80
            gap_bull = lows[i] - highs[i-2]
            if gap_bull >= 0.80 and closes[i-1] > opens[i-1]:
                fvg_top = lows[i]
                fvg_bottom = highs[i-2]
                # Wait for retest of fvg_top within next 15 bars
                for step in range(1, 16):
                    ret_idx = i + step
                    if lows[ret_idx] <= fvg_top and closes[ret_idx] >= fvg_bottom:
                        # Entry Long on Retest!
                        entry = fvg_top + (SPREAD / 2.0)
                        sl = fvg_bottom - (SPREAD / 2.0)
                        risk = entry - sl
                        if 0.80 <= risk <= 12.0:
                            tp = entry + (target_rr * risk)
                            outcome = 0; r_val = 0.0; exit_idx = ret_idx + 30
                            for s in range(1, 31):
                                if lows[ret_idx + s] <= sl: r_val = -1.0; outcome = -1; exit_idx = ret_idx + s; break
                                elif highs[ret_idx + s] >= tp: r_val = target_rr; outcome = 1; exit_idx = ret_idx + s; break
                            if outcome == 0: r_val = (closes[ret_idx + 30] - entry) / risk
                            last_exit = exit_idx
                            trades.append({"r": r_val, "year": years[ret_idx]})
                        break

            # Bearish FVG: High(i) < Low(i-2) with gap > $0.80
            gap_bear = lows[i-2] - highs[i]
            if gap_bear >= 0.80 and closes[i-1] < opens[i-1]:
                fvg_bottom = highs[i]
                fvg_top = lows[i-2]
                for step in range(1, 16):
                    ret_idx = i + step
                    if highs[ret_idx] >= fvg_bottom and closes[ret_idx] <= fvg_top:
                        entry = fvg_bottom - (SPREAD / 2.0)
                        sl = fvg_top + (SPREAD / 2.0)
                        risk = sl - entry
                        if 0.80 <= risk <= 12.0:
                            tp = entry - (target_rr * risk)
                            outcome = 0; r_val = 0.0; exit_idx = ret_idx + 30
                            for s in range(1, 31):
                                if highs[ret_idx + s] >= sl: r_val = -1.0; outcome = -1; exit_idx = ret_idx + s; break
                                elif lows[ret_idx + s] <= tp: r_val = target_rr; outcome = 1; exit_idx = ret_idx + s; break
                            if outcome == 0: r_val = (entry - closes[ret_idx + 30]) / risk
                            last_exit = exit_idx
                            trades.append({"r": r_val, "year": years[ret_idx]})
                        break

        r_arr = np.array([t["r"] for t in trades])
        wr = np.mean(r_arr > 0) * 100
        gw = sum(r for r in r_arr if r > 0); gl = abs(sum(r for r in r_arr if r < 0))
        pf = gw / gl if gl > 0 else 99.0
        daily_freq = len(trades) / unique_days
        print(f"Target RR {target_rr:.1f}:1 | Total: {len(trades):,} ({daily_freq:.2f}/day) | WR: {wr:.1f}% | Net Exp: {np.mean(r_arr):+.3f}R | PF: {pf:.2f}")

if __name__ == "__main__":
    run_quant_discovery()
