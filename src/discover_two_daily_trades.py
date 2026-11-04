#!/usr/bin/env python3
"""
Autonomous Discovery Engine: Two-Trades-Per-Day Mechanical Edge on XAUUSD M1.
Mandate: Exactly 2 non-overlapping trades per trading day:
- Trade 1 (Asian Window: 07:00 - 12:00 WIB / 00:00 - 05:00 UTC)
- Trade 2 (London/NY Window: 14:00 - 22:00 WIB / 07:00 - 15:00 UTC)

Investigates mathematical features:
- Volume Z-Score & Tick Volume Expansion
- Rolling VWAP / EMA Divergence
- Initial Balance (IB) 30m Breakout vs Fade
- Candle Morphology & Wick Exhaustion
Evaluates across 4,182,209 M1 candles (2015-2026) with $0.50 spread friction.
"""

import os
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD_COST = 0.50

def run_discovery():
    print("=== Loading 12-Year M1 Dataset ===")
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
    volumes = df["volume"].to_numpy() if "volume" in df.columns else np.ones(len(df))
    hours = df["hour"].to_numpy()
    minutes = df["minute"].to_numpy()
    dates = df["date"].to_numpy()
    years = df["year"].to_numpy()
    n = len(df)

    # Precalculate rolling indicators on M1
    print("=== Computing Mathematical Features ===")
    ranges = highs - lows
    cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr = (cumsum[60:] - cumsum[:-60]) / 60.0
    atr = np.pad(atr, (60, 0), mode="edge")[:n]

    # Rolling 30-bar EMA on M1
    k = 2.0 / (30 + 1)
    ema30 = np.zeros(n)
    ema30[0] = closes[0]
    for idx in range(1, n):
        ema30[idx] = closes[idx] * k + ema30[idx - 1] * (1 - k)

    # Rolling Volume 30 SMA
    vol_cumsum = np.cumsum(np.insert(volumes, 0, 0))
    vol_sma = (vol_cumsum[30:] - vol_cumsum[:-30]) / 30.0
    vol_sma = np.pad(vol_sma, (30, 0), mode="edge")[:n]

    # Unique dates
    unique_dates = np.unique(dates)
    print(f"Total Unique Trading Days: {len(unique_dates):,}")

    # We want to test systematic candidate models for:
    # Slot 1: Asian Morning (07:00 - 12:00 WIB / 00:00 - 05:00 UTC)
    # Slot 2: London/NY (14:00 - 22:00 WIB / 07:00 - 15:00 UTC)

    # Let's test 3 Candidate Models for Slot 1:
    # Model 1A: Asian Open Squeeze Breakout (First 30m Range Breakout between 01:00 and 03:00 UTC)
    # Model 1B: Asian Mean Reversion (Deviations > 1.8 ATR from EMA30)
    # Model 1C: 08:00 WIB / 01:00 UTC High/Low Sweep Reversal

    # Let's test 3 Candidate Models for Slot 2:
    # Model 2A: London Open 08:00 UTC (15:00 WIB) Asia Range Expansion
    # Model 2B: US Equity Open 14:00 UTC (21:00 WIB) Volume Drive Breakout
    # Model 2C: London 17:30 WIB (10:30 UTC) Lunch Reversal

    print("\n" + "=" * 80)
    print("TESTING CANDIDATE MODELS FOR SLOT 1 (ASIAN MORNING: 07:00 - 12:00 WIB)")
    print("=" * 80)

    # Simulation helper
    def test_daily_rule(rule_fn, slot_name, rr_target=1.5):
        trades_by_year = {y: [] for y in range(2015, 2027)}
        total_triggered_days = 0
        
        for d in unique_dates:
            day_mask = (dates == d)
            day_indices = np.where(day_mask)[0]
            if len(day_indices) < 200: continue
            
            # Execute rule function for this day
            res = rule_fn(day_indices, rr_target)
            if res is not None:
                total_triggered_days += 1
                yr = years[day_indices[0]]
                trades_by_year[yr].append(res)
                
        all_r = []
        for y in range(2015, 2027):
            all_r.extend(trades_by_year[y])
            
        n_t = len(all_r)
        if n_t == 0: return None
        wins = sum(1 for r in all_r if r > 0)
        wr = (wins / n_t) * 100.0
        exp = np.mean(all_r)
        gw = sum(r for r in all_r if r > 0)
        gl = abs(sum(r for r in all_r if r < 0))
        pf = gw / gl if gl > 0 else 99.0
        cum = np.cumsum(all_r)
        mdd = np.max(np.maximum.accumulate(cum) - cum)
        daily_coverage = (total_triggered_days / len(unique_dates)) * 100.0
        
        print(f"[{slot_name}] Daily Coverage: {daily_coverage:.1f}% ({n_t:,} trades) | WR: {wr:.1f}% | Net Exp: {exp:+.3f}R | PF: {pf:.2f} | MDD: -{mdd:.1f}R | Total R: {cum[-1]:+.1f}R")
        return {"n": n_t, "coverage": daily_coverage, "wr": wr, "exp": exp, "pf": pf, "mdd": mdd, "total_r": cum[-1], "yearly": trades_by_year}

    # --- Rule 1A: Asian 30m Range Breakout with Volume Confirmation ---
    def rule_asian_breakout(idx_list, rr):
        # Look between 00:00 and 04:00 UTC
        # First 30 mins: 00:00 to 00:29 sets H30, L30
        h_idx = [i for i in idx_list if hours[i] == 0 and minutes[i] <= 29]
        if len(h_idx) < 25: return None
        h30 = np.max(highs[h_idx]); l30 = np.min(lows[h_idx]); rng = h30 - l30
        if rng < 1.5 or rng > 20.0: return None
        
        # Scan 00:30 to 04:00 for first clean breakout with volume > vol_sma
        scan_idx = [i for i in idx_list if ((hours[i] == 0 and minutes[i] >= 30) or hours[i] in (1, 2, 3))]
        for i in scan_idx:
            # Long
            if closes[i] > h30 + 0.30 and volumes[i] > vol_sma[i]:
                entry = closes[i] + (SPREAD_COST / 2.0)
                sl = l30 - (SPREAD_COST / 2.0)
                risk = entry - sl
                if not (1.0 <= risk <= 15.0): continue
                tp = entry + (rr * risk)
                # forward trace
                sub_f = [j for j in idx_list if j > i and hours[j] <= 5]
                for j in sub_f:
                    if lows[j] <= sl: return -1.0
                    elif highs[j] >= tp: return rr
                if sub_f: return (closes[sub_f[-1]] - entry) / risk
                return 0.0
            # Short
            elif closes[i] < l30 - 0.30 and volumes[i] > vol_sma[i]:
                entry = closes[i] - (SPREAD_COST / 2.0)
                sl = h30 + (SPREAD_COST / 2.0)
                risk = sl - entry
                if not (1.0 <= risk <= 15.0): continue
                tp = entry - (rr * risk)
                sub_f = [j for j in idx_list if j > i and hours[j] <= 5]
                for j in sub_f:
                    if highs[j] >= sl: return -1.0
                    elif lows[j] <= tp: return rr
                if sub_f: return (entry - closes[sub_f[-1]]) / risk
                return 0.0
        return None

    # --- Rule 1B: Asian EMA30 Mean Reversion Squeeze ---
    def rule_asian_mean_reversion(idx_list, rr):
        # Look between 01:00 and 04:00 UTC (08:00 - 11:00 WIB)
        # Scan for extreme displacement from EMA30 (> 1.8 ATR) then rejection
        scan_idx = [i for i in idx_list if hours[i] in (1, 2, 3)]
        for i in scan_idx:
            diff_ema = closes[i] - ema30[i]
            cur_atr = atr[i]
            if cur_atr <= 0.2: continue
            
            # Short Reversion
            if diff_ema > 1.8 * cur_atr and (highs[i] - closes[i]) > 0.40 * (highs[i] - lows[i]):
                entry = closes[i] - (SPREAD_COST / 2.0)
                sl = highs[i] + (SPREAD_COST / 2.0)
                risk = sl - entry
                if not (0.80 <= risk <= 12.0): continue
                tp = entry - (rr * risk)
                sub_f = [j for j in idx_list if j > i and hours[j] <= 5]
                for j in sub_f:
                    if highs[j] >= sl: return -1.0
                    elif lows[j] <= tp: return rr
                if sub_f: return (entry - closes[sub_f[-1]]) / risk
                return 0.0
            # Long Reversion
            elif diff_ema < -1.8 * cur_atr and (closes[i] - lows[i]) > 0.40 * (highs[i] - lows[i]):
                entry = closes[i] + (SPREAD_COST / 2.0)
                sl = lows[i] - (SPREAD_COST / 2.0)
                risk = entry - sl
                if not (0.80 <= risk <= 12.0): continue
                tp = entry + (rr * risk)
                sub_f = [j for j in idx_list if j > i and hours[j] <= 5]
                for j in sub_f:
                    if lows[j] <= sl: return -1.0
                    elif highs[j] >= tp: return rr
                if sub_f: return (closes[sub_f[-1]] - entry) / risk
                return 0.0
        return None

    # --- Rule 1C: Tokyo 08:00 WIB Sweep Reversal (Guaranteed Daily Candidate) ---
    def rule_tokyo_0800_sweep(idx_list, rr):
        cand = [i for i in idx_list if hours[i] == 1 and minutes[i] == 4]
        if not cand: return None
        i = cand[0]
        # check previous hour (00:00 - 00:59)
        prev_idx = [j for j in idx_list if hours[j] == 0]
        if len(prev_idx) < 40: return None
        prev_h = np.max(highs[prev_idx]); prev_l = np.min(lows[prev_idx])
        if (prev_h - prev_l) < 1.2: return None
        
        five_h = np.max(highs[i-4 : i+1]); five_l = np.min(lows[i-4 : i+1])
        c_04 = closes[i]; o_00 = opens[i-4]
        
        # High sweep -> Short
        if five_h > prev_h + 0.20 and c_04 < prev_h and c_04 < o_00:
            entry = c_04 - (SPREAD_COST / 2.0); sl = five_h + (SPREAD_COST / 2.0); risk = sl - entry
            if 0.80 <= risk <= 12.0:
                tp = entry - (rr * risk)
                sub_f = [j for j in idx_list if j > i and hours[j] <= 3]
                for j in sub_f:
                    if highs[j] >= sl: return -1.0
                    elif lows[j] <= tp: return rr
                if sub_f: return (entry - closes[sub_f[-1]]) / risk
                return 0.0
        # Low sweep -> Long
        elif five_l < prev_l - 0.20 and c_04 > prev_l and c_04 > o_00:
            entry = c_04 + (SPREAD_COST / 2.0); sl = five_l - (SPREAD_COST / 2.0); risk = entry - sl
            if 0.80 <= risk <= 12.0:
                tp = entry + (rr * risk)
                sub_f = [j for j in idx_list if j > i and hours[j] <= 3]
                for j in sub_f:
                    if lows[j] <= sl: return -1.0
                    elif highs[j] >= tp: return rr
                if sub_f: return (closes[sub_f[-1]] - entry) / risk
                return 0.0
        return None

    test_daily_rule(rule_asian_breakout, "Model 1A: Asian Open Breakout", rr_target=1.5)
    test_daily_rule(rule_asian_mean_reversion, "Model 1B: Asian EMA Mean Reversion", rr_target=1.2)
    test_daily_rule(rule_tokyo_0800_sweep, "Model 1C: Tokyo 08:00 WIB Sweep Reversal", rr_target=1.5)

    print("\n" + "=" * 80)
    print("TESTING CANDIDATE MODELS FOR SLOT 2 (LONDON/NY: 14:00 - 22:00 WIB)")
    print("=" * 80)

    # --- Rule 2A: London Open 15:00 WIB (08:00 UTC) Expansion ---
    def rule_london_expansion(idx_list, rr):
        # Asian Range: 00:00 to 06:00 UTC
        asia_idx = [i for i in idx_list if hours[i] < 6]
        if len(asia_idx) < 250: return None
        asia_h = np.max(highs[asia_idx]); asia_l = np.min(lows[asia_idx])
        if (asia_h - asia_l) < 3.0: return None
        
        # Scan London Open: 07:00 to 11:00 UTC (14:00 - 18:00 WIB)
        scan_idx = [i for i in idx_list if hours[i] in (7, 8, 9, 10)]
        for i in scan_idx:
            # Clean breakout of Asia High
            if closes[i] > asia_h + 0.50 and closes[i] > ema30[i]:
                entry = closes[i] + (SPREAD_COST / 2.0)
                sl = closes[i] - (1.5 * atr[i])
                risk = entry - sl
                if not (1.5 <= risk <= 20.0): continue
                tp = entry + (rr * risk)
                sub_f = [j for j in idx_list if j > i and hours[j] <= 16]
                for j in sub_f:
                    if lows[j] <= sl: return -1.0
                    elif highs[j] >= tp: return rr
                if sub_f: return (closes[sub_f[-1]] - entry) / risk
                return 0.0
            # Clean breakout of Asia Low
            elif closes[i] < asia_l - 0.50 and closes[i] < ema30[i]:
                entry = closes[i] - (SPREAD_COST / 2.0)
                sl = closes[i] + (1.5 * atr[i])
                risk = sl - entry
                if not (1.5 <= risk <= 20.0): continue
                tp = entry - (rr * risk)
                sub_f = [j for j in idx_list if j > i and hours[j] <= 16]
                for j in sub_f:
                    if highs[j] >= sl: return -1.0
                    elif lows[j] <= tp: return rr
                if sub_f: return (entry - closes[sub_f[-1]]) / risk
                return 0.0
        return None

    # --- Rule 2B: US Equity Open 21:30 WIB (14:30 UTC) Momentum Run ---
    def rule_us_open_momentum(idx_list, rr):
        cand = [i for i in idx_list if hours[i] == 14 and minutes[i] == 29]
        if not cand: return None
        i = cand[0]
        # Check first 30 mins (14:00 to 14:29)
        first_idx = [j for j in idx_list if hours[j] == 14 and minutes[j] <= 29]
        if len(first_idx) < 25: return None
        o_14 = opens[first_idx[0]]; c_29 = closes[i]
        h_30 = np.max(highs[first_idx]); l_30 = np.min(lows[first_idx])
        disp = c_29 - o_14
        cur_atr = atr[i]
        if abs(disp) < max(cur_atr * 0.8, 2.0): return None
        
        # Bullish momentum
        if disp > 0 and (h_30 - c_29) < 0.25 * (h_30 - l_30):
            entry = c_29 + (SPREAD_COST / 2.0); sl = o_14 - (SPREAD_COST / 2.0); risk = entry - sl
            if 1.0 <= risk <= 15.0:
                tp = entry + (rr * risk)
                sub_f = [j for j in idx_list if j > i and hours[j] <= 17]
                for j in sub_f:
                    if lows[j] <= sl: return -1.0
                    elif highs[j] >= tp: return rr
                if sub_f: return (closes[sub_f[-1]] - entry) / risk
                return 0.0
        # Bearish momentum
        elif disp < 0 and (c_29 - l_30) < 0.25 * (h_30 - l_30):
            entry = c_29 - (SPREAD_COST / 2.0); sl = o_14 + (SPREAD_COST / 2.0); risk = sl - entry
            if 1.0 <= risk <= 15.0:
                tp = entry - (rr * risk)
                sub_f = [j for j in idx_list if j > i and hours[j] <= 17]
                for j in sub_f:
                    if highs[j] >= sl: return -1.0
                    elif lows[j] <= tp: return rr
                if sub_f: return (entry - closes[sub_f[-1]]) / risk
                return 0.0
        return None

    # --- Rule 2C: London 17:30 WIB (10:30 UTC) Reversal ---
    def rule_london_reversal(idx_list, rr):
        cand = [i for i in idx_list if hours[i] == 10 and minutes[i] == 29]
        if not cand: return None
        i = cand[0]
        first_idx = [j for j in idx_list if hours[j] == 10 and minutes[j] <= 29]
        if len(first_idx) < 25: return None
        o_10 = opens[first_idx[0]]; c_29 = closes[i]
        h_30 = np.max(highs[first_idx]); l_30 = np.min(lows[first_idx])
        disp = c_29 - o_10
        cur_atr = atr[i]
        if abs(disp) < max(cur_atr * 0.8, 2.0): return None
        
        if disp > 0 and (h_30 - c_29) > 0.30 * (h_30 - l_30):
            entry = c_29 - (SPREAD_COST / 2.0); sl = h_30 + (SPREAD_COST / 2.0); risk = sl - entry
            if 0.80 <= risk <= 15.0:
                tp = entry - (rr * risk)
                sub_f = [j for j in idx_list if j > i and hours[j] <= 12]
                for j in sub_f:
                    if highs[j] >= sl: return -1.0
                    elif lows[j] <= tp: return rr
                if sub_f: return (entry - closes[sub_f[-1]]) / risk
                return 0.0
        elif disp < 0 and (c_29 - l_30) > 0.30 * (h_30 - l_30):
            entry = c_29 + (SPREAD_COST / 2.0); sl = l_30 - (SPREAD_COST / 2.0); risk = entry - sl
            if 0.80 <= risk <= 15.0:
                tp = entry + (rr * risk)
                sub_f = [j for j in idx_list if j > i and hours[j] <= 12]
                for j in sub_f:
                    if lows[j] <= sl: return -1.0
                    elif highs[j] >= tp: return rr
                if sub_f: return (closes[sub_f[-1]] - entry) / risk
                return 0.0
        return None

    test_daily_rule(rule_london_expansion, "Model 2A: London Asia Breakout", rr_target=1.5)
    test_daily_rule(rule_us_open_momentum, "Model 2B: US Open 21:30 WIB Momentum", rr_target=1.5)
    test_daily_rule(rule_london_reversal, "Model 2C: London 17:30 WIB Reversal", rr_target=1.5)

if __name__ == "__main__":
    run_discovery()
