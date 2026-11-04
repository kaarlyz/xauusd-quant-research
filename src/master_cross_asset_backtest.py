#!/usr/bin/env python3
"""
Master Cross-Asset Multi-Timeframe Portfolio Backtest.
Evaluates Pola N Baku + Expired Rule across ALL 5 Clean Parquet Datasets:
1. XAUUSD (2003 - 2026 / 23.5 Years)
2. NAS100 (2011 - 2026 / 15.0 Years)
3. EURUSD (2003 - 2026 / 23.5 Years)
4. GBPUSD (2003 - 2026 / 23.5 Years)
5. GBPJPY (2003 - 2026 / 23.5 Years)

Realistic ECN Friction loaded for every asset class:
- Gold: Spread $0.38, Comm $0.07, Slip $0.05
- Nas100: Spread 1.0 pt, Comm $0.20, Slip 0.50 pt
- EURUSD: Spread 0.3 pip, Comm 0.7 pip, Slip 0.2 pip
- GBPUSD: Spread 0.5 pip, Comm 0.7 pip, Slip 0.3 pip
- GBPJPY: Spread 0.8 pip, Comm 0.7 pip, Slip 0.4 pip

Target RR: 1:1.50 (Standard Benchmark)
Timeframes: H1, M30, M15.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import os
import polars as pl
import numpy as np

DATA_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data"

ASSET_SPECS = [
    {
        "symbol": "XAUUSD",
        "file": os.path.join(DATA_DIR, "XAUUSD_M1.parquet"),
        "unit": 1.0, # price is USD
        "spread": 0.38, "comm": 0.07, "slippage": 0.05, "buffer": 0.50,
        "spans": {"H1": (15.0, 35.0), "M30": (8.0, 20.0), "M15": (5.0, 15.0)},
        "rr": 1.5,
    },
    {
        "symbol": "NAS100",
        "file": os.path.join(DATA_DIR, "NAS100_M1.parquet"),
        "unit": 1.0, # index points
        "spread": 1.0, "comm": 0.20, "slippage": 0.50, "buffer": 1.0,
        "spans": {"H1": (80.0, 250.0), "M30": (40.0, 150.0), "M15": (25.0, 80.0)},
        "rr": 1.5,
    },
    {
        "symbol": "EURUSD",
        "file": os.path.join(DATA_DIR, "EURUSD_M1.parquet"),
        "unit": 0.0001, # 1 pip = 0.0001
        "spread": 0.3 * 0.0001, "comm": 0.7 * 0.0001, "slippage": 0.2 * 0.0001, "buffer": 2.0 * 0.0001,
        "spans": {"H1": (30.0*0.0001, 100.0*0.0001), "M30": (18.0*0.0001, 50.0*0.0001), "M15": (12.0*0.0001, 35.0*0.0001)},
        "rr": 1.5,
    },
    {
        "symbol": "GBPUSD",
        "file": os.path.join(DATA_DIR, "GBPUSD_M1.parquet"),
        "unit": 0.0001,
        "spread": 0.5 * 0.0001, "comm": 0.7 * 0.0001, "slippage": 0.3 * 0.0001, "buffer": 2.5 * 0.0001,
        "spans": {"H1": (35.0*0.0001, 120.0*0.0001), "M30": (22.0*0.0001, 65.0*0.0001), "M15": (14.0*0.0001, 45.0*0.0001)},
        "rr": 1.5,
    },
    {
        "symbol": "GBPJPY",
        "file": os.path.join(DATA_DIR, "GBPJPY_M1.parquet"),
        "unit": 0.01, # 1 pip JPY = 0.01
        "spread": 0.8 * 0.01, "comm": 0.7 * 0.01, "slippage": 0.4 * 0.01, "buffer": 3.0 * 0.01,
        "spans": {"H1": (45.0*0.01, 160.0*0.01), "M30": (28.0*0.01, 90.0*0.01), "M15": (18.0*0.01, 60.0*0.01)},
        "rr": 1.5,
    },
]

def evaluate_symbol(spec):
    sym = spec["symbol"]
    fp = spec["file"]
    print(f"\nLoading and Evaluating {sym}...")
    df = pl.read_parquet(fp).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"),
        (pl.col("timestamp") // (30 * 60 * 1000) * (30 * 60 * 1000)).alias("m30_ts"),
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    df_clean = df.filter(~pl.col("hour").is_between(21, 23))

    results = {}
    target_rr = spec["rr"]
    spread = spec["spread"]
    comm = spec["comm"]
    slippage = spec["slippage"]
    buffer = spec["buffer"]

    for tf_name in ["H1", "M30", "M15"]:
        ts_col = f"{tf_name.lower()}_ts"
        b_df = df_clean.group_by(ts_col).agg([
            pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        ]).sort(ts_col)

        o = b_df["open"].to_numpy(); h = b_df["high"].to_numpy()
        l = b_df["low"].to_numpy(); c = b_df["close"].to_numpy()
        n = len(o)

        swing_k = 3
        is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
        for i in range(swing_k, n - swing_k):
            if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
            if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

        min_span, max_span = spec["spans"][tf_name]
        trades = []
        last_sw_l = []; last_sw_h = []
        trade_exit_bar = 0
        max_hold = 40

        for i in range(swing_k, n - max_hold - 5):
            if is_sw_l[i]: last_sw_l.append((i, l[i]))
            if is_sw_h[i]: last_sw_h.append((i, h[i]))
            if len(last_sw_l) > 10: last_sw_l.pop(0)
            if len(last_sw_h) > 10: last_sw_h.pop(0)

            if i < trade_exit_bar: continue

            if len(last_sw_h) >= 2 and len(last_sw_l) >= 2:
                idx_h, val_h = last_sw_h[-1]; idx_l, val_l = last_sw_l[-1]
                span = val_h - val_l
                if not (min_span <= span <= max_span): continue

                rel_pos = (c[i] - val_l) / span
                allow_buy = rel_pos >= 0.35; allow_sell = rel_pos <= 0.65

                risk_buy = (val_h + spread + slippage) - (val_l - buffer - slippage) + comm
                tp_buy = (val_h + spread + slippage) + (target_rr * risk_buy)

                risk_sell = (val_h + buffer + spread + slippage) - (val_l - slippage) + comm
                tp_sell = (val_l - slippage) - (target_rr * risk_sell)

                buy_active = allow_buy; sell_active = allow_sell
                triggered = False; order_side = None; fill_bar = -1

                for step in range(1, 16):
                    chk = i + step
                    if chk >= n: break
                    if (is_sw_h[chk] and chk > idx_h) or (is_sw_l[chk] and chk > idx_l): break
                    if buy_active and h[chk] >= val_h:
                        triggered = True; order_side = "BUY"; fill_bar = chk; break
                    if sell_active and l[chk] <= val_l:
                        triggered = True; order_side = "SELL"; fill_bar = chk; break

                if triggered:
                    outcome = 0; r_val = 0.0; exit_idx = fill_bar
                    if order_side == "BUY":
                        sl_exec = val_l - buffer - slippage
                        for s in range(fill_bar + 1, min(n, fill_bar + max_hold)):
                            exit_idx = s
                            if l[s] <= (val_l - buffer):
                                actual_sl = min(sl_exec, o[s] - slippage if o[s] < sl_exec else sl_exec)
                                r_val = - ((val_h + spread + slippage) - actual_sl + comm) / risk_buy
                                outcome = -1; break
                            elif h[s] >= tp_buy:
                                r_val = target_rr; outcome = 1; break
                        if outcome == 0 and fill_bar + max_hold < n:
                            r_val = (c[fill_bar + max_hold] - (val_h + spread + slippage) - comm) / risk_buy
                    else:
                        sl_exec = val_h + buffer + spread + slippage
                        for s in range(fill_bar + 1, min(n, fill_bar + max_hold)):
                            exit_idx = s
                            if h[s] + spread >= (val_h + buffer + spread):
                                actual_sl = max(sl_exec, (o[s] + spread + slippage) if (o[s] + spread) > sl_exec else sl_exec)
                                r_val = - (actual_sl - (val_l - slippage) + comm) / risk_sell
                                outcome = -1; break
                            elif l[s] + spread <= tp_sell:
                                r_val = target_rr; outcome = 1; break
                        if outcome == 0 and fill_bar + max_hold < n:
                            r_val = ((val_l - slippage) - (c[fill_bar + max_hold] + spread) - comm) / risk_sell

                    trade_exit_bar = exit_idx
                    trades.append(r_val)

        r_arr = np.array(trades)
        n_t = len(r_arr)
        wins = r_arr[r_arr > 0]; losses = r_arr[r_arr < 0]
        wr = len(wins) / n_t * 100.0 if n_t > 0 else 0
        gw = float(np.sum(wins)); gl = float(np.abs(np.sum(losses)))
        pf = gw / gl if gl > 0 else 99.0
        exp = float(np.mean(r_arr)) if n_t > 0 else 0
        cum = np.cumsum(r_arr) if n_t > 0 else [0]
        mdd = float(np.max(np.maximum.accumulate(cum) - cum)) if n_t > 0 else 0
        results[tf_name] = {"trades": n_t, "wr": wr, "pf": pf, "exp": exp, "tot_r": cum[-1], "mdd": mdd}

    return sym, results

def main():
    print("=" * 85)
    print("MASTER CROSS-ASSET PORTFOLIO BACKTEST (POLA N BAKU + EXPIRED RULE / RR 1:1.50)")
    print("=" * 85)
    
    summary = []
    for spec in ASSET_SPECS:
        sym, res = evaluate_symbol(spec)
        summary.append((sym, res))

    print("\n" + "=" * 90)
    print("RINGKASAN KINERJA LINTAS 5 KELAS ASET (TIMEFRAME H1, M30, M15)")
    print("=" * 90)
    print(f"{'Symbol':<8} | {'Timeframe':<5} | {'Trades':<7} | {'Win Rate':<9} | {'Profit Factor':<13} | {'Net Exp (R)':<11} | {'Total Net R':<11} | {'Max DD':<7}")
    print("-" * 90)
    for sym, res in summary:
        for tf in ["H1", "M30", "M15"]:
            r = res[tf]
            print(f"{sym:<8} | {tf:<5} | {r['trades']:<7,} | {r['wr']:6.2f}%   |    {r['pf']:5.3f}      |  {r['exp']:+.4f} R   | {r['tot_r']:+9.1f} R | {r['mdd']:4.1f} R")
        print("-" * 90)

if __name__ == "__main__":
    main()
