#!/usr/bin/env python3
"""
Full RR Frontier Scan for NAS100 across H4, H1, M30, M15, M5.
Target RR to test: 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0.
Dataset: 15 Years NAS100_M1.parquet (2011 - 2026).
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

NAS100_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/NAS100_M1.parquet"

def scan_nas100_rr_frontier():
    print("=== Loading 15 Years NAS100 Dataset ===")
    df = pl.read_parquet(NAS100_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (5 * 60 * 1000) * (5 * 60 * 1000)).alias("m5_ts"),
        (pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"),
        (pl.col("timestamp") // (30 * 60 * 1000) * (30 * 60 * 1000)).alias("m30_ts"),
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        (pl.col("timestamp") // (4 * 60 * 60 * 1000) * (4 * 60 * 60 * 1000)).alias("h4_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    df_clean = df.filter(~pl.col("hour").is_between(21, 23))

    def evaluate_rr_nas(bars_df, tf_name, min_span, max_span, swing_k=3, max_hold=40):
        o = bars_df["open"].to_numpy(); h = bars_df["high"].to_numpy()
        l = bars_df["low"].to_numpy(); c = bars_df["close"].to_numpy()
        n = len(o)

        is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
        for i in range(swing_k, n - swing_k):
            if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
            if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

        last_sw_l = []; last_sw_h = []
        rr_levels = [1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0]
        results_by_rr = {rr: [] for rr in rr_levels}
        trade_exit_bars = {rr: 0 for rr in rr_levels}

        buffer = 1.0
        spread = 1.0
        comm = 0.20
        slippage = 0.50

        for i in range(swing_k, n - max_hold - 5):
            if is_sw_l[i]: last_sw_l.append((i, l[i]))
            if is_sw_h[i]: last_sw_h.append((i, h[i]))
            if len(last_sw_l) > 10: last_sw_l.pop(0)
            if len(last_sw_h) > 10: last_sw_h.pop(0)

            if len(last_sw_h) >= 2 and len(last_sw_l) >= 2:
                idx_h, val_h = last_sw_h[-1]; idx_l, val_l = last_sw_l[-1]
                span = val_h - val_l
                if not (min_span <= span <= max_span): continue

                rel_pos = (c[i] - val_l) / span
                allow_buy = rel_pos >= 0.35; allow_sell = rel_pos <= 0.65

                risk_buy = (val_h + spread + slippage) - (val_l - buffer - slippage) + comm
                risk_sell = (val_h + buffer + spread + slippage) - (val_l - slippage) + comm

                for target_rr in rr_levels:
                    if i < trade_exit_bars[target_rr]: continue

                    tp_buy = (val_h + spread + slippage) + (target_rr * risk_buy)
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

                        trade_exit_bars[target_rr] = exit_idx
                        results_by_rr[target_rr].append(r_val)

        print(f"\n{'='*78}\nKURVA EKSPANSI RR MAKSIMAL: TIMEFRAME {tf_name} (NAS100: 2011 - 2026)\n{'='*78}")
        print(f"Target RR | Trades | Win Rate | Titik Impas | Profit Factor | Net Exp (R) | Total Net R | Max DD")
        print("-" * 78)
        for rr in rr_levels:
            r_arr = np.array(results_by_rr[rr])
            n_t = len(r_arr)
            if n_t > 0:
                wins = r_arr[r_arr > 0]; losses = r_arr[r_arr < 0]
                wr = len(wins) / n_t * 100.0
                gw = float(np.sum(wins)); gl = float(np.abs(np.sum(losses)))
                pf = gw / gl if gl > 0 else 99.0
                exp = float(np.mean(r_arr))
                cum = np.cumsum(r_arr)
                mdd = float(np.max(np.maximum.accumulate(cum) - cum))
                bep = 100.0 / (1.0 + rr)
                print(f"1 : {rr:<3.1f}   | {n_t:<6} | {wr:5.2f}%   |   {bep:4.1f}%    |    {pf:5.3f}    |  {exp:+.4f} R   | {cum[-1]:+9.1f} R | {mdd:4.1f} R")

    # Group by
    h4 = df_clean.group_by("h4_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
    ]).sort("h4_ts")

    h1 = df_clean.group_by("h1_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
    ]).sort("h1_ts")

    m30 = df_clean.group_by("m30_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
    ]).sort("m30_ts")

    m15 = df_clean.group_by("m15_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
    ]).sort("m15_ts")

    m5 = df_clean.group_by("m5_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
    ]).sort("m5_ts")

    evaluate_rr_nas(h4, "H4", min_span=150.0, max_span=600.0, swing_k=2, max_hold=30)
    evaluate_rr_nas(h1, "H1", min_span=80.0, max_span=250.0, swing_k=3, max_hold=40)
    evaluate_rr_nas(m30, "M30", min_span=40.0, max_span=150.0, swing_k=3, max_hold=40)
    evaluate_rr_nas(m15, "M15", min_span=25.0, max_span=80.0, swing_k=3, max_hold=40)
    evaluate_rr_nas(m5, "M5", min_span=15.0, max_span=50.0, swing_k=3, max_hold=40)

if __name__ == "__main__":
    scan_nas100_rr_frontier()
