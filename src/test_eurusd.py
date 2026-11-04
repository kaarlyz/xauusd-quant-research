#!/usr/bin/env python3
"""
Backtest Pola N Baku pada EURUSD menggunakan data yang sudah terkumpul (2003 s/d 2018 / 16 Tahun).
Friksi ECN EURUSD Baku:
- Spread ECN median: 0.3 pip (0.00003).
- Slippage Stop order: 0.2 pip (0.00002).
- Komisi: $7.00 per standard lot round-turn (0.00007 per unit).
Timeframe diuji: H1, M30, M15, M5.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import os
import glob
import polars as pl
import numpy as np

TEMP_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data/multi_m1_temp/EURUSD"

def run_eurusd_test():
    print("=== Loading Available EURUSD M1 Data ===")
    files = sorted(glob.glob(os.path.join(TEMP_DIR, "*.json*")))
    print(f"Total files: {len(files)}")

    dfs = []
    for fp in files:
        try:
            sub = pl.read_json(fp)
            if len(sub) == 0: continue
            dfs.append(sub.select([
                pl.col("timestamp").cast(pl.Int64),
                pl.col("open").cast(pl.Float64),
                pl.col("high").cast(pl.Float64),
                pl.col("low").cast(pl.Float64),
                pl.col("close").cast(pl.Float64),
            ]))
        except: pass

    df = pl.concat(dfs).unique(subset=["timestamp"]).sort("timestamp")
    print(f"Total EURUSD M1 Bars: {len(df):,}")

    df = df.with_columns(
        (pl.col("timestamp") // (5 * 60 * 1000) * (5 * 60 * 1000)).alias("m5_ts"),
        (pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"),
        (pl.col("timestamp") // (30 * 60 * 1000) * (30 * 60 * 1000)).alias("m30_ts"),
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    df_clean = df.filter(~pl.col("hour").is_between(21, 23))

    def evaluate_fx(bars_df, tf_name, min_span_pips, max_span_pips, swing_k=3, target_rr=1.5, max_hold=40,
                    spread_pips=0.3, slippage_pips=0.2, comm_pips=0.7):
        o = bars_df["open"].to_numpy(); h = bars_df["high"].to_numpy()
        l = bars_df["low"].to_numpy(); c = bars_df["close"].to_numpy()
        n = len(o)

        is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
        for i in range(swing_k, n - swing_k):
            if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
            if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

        last_sw_l = []; last_sw_h = []
        trade_exit_bar = 0

        # Convert pips to price
        pip_unit = 0.0001
        min_span = min_span_pips * pip_unit
        max_span = max_span_pips * pip_unit
        spread = spread_pips * pip_unit
        slippage = slippage_pips * pip_unit
        comm = comm_pips * pip_unit
        buffer = 2.0 * pip_unit # 2 pips buffer

        trades = []
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
                    trades.append({"side": order_side, "r": r_val})

        r_all = np.array([t["r"] for t in trades])
        n_t = len(r_all)
        gw = sum(x for x in r_all if x > 0); gl = abs(sum(x for x in r_all if x < 0))
        pf = gw / gl if gl > 0 else 99.0
        wr = sum(1 for x in r_all if x > 0) / n_t * 100.0 if n_t > 0 else 0
        exp = float(np.mean(r_all)) if n_t > 0 else 0
        cum = np.cumsum(r_all) if n_t > 0 else [0]
        mdd = float(np.max(np.maximum.accumulate(cum) - cum)) if n_t > 0 else 0

        longs = [t["r"] for t in trades if t["side"] == "BUY"]
        shorts = [t["r"] for t in trades if t["side"] == "SELL"]
        pf_l = sum(x for x in longs if x > 0) / abs(sum(x for x in longs if x < 0)) if abs(sum(x for x in longs if x < 0)) > 0 else 0
        pf_s = sum(x for x in shorts if x > 0) / abs(sum(x for x in shorts if x < 0)) if abs(sum(x for x in shorts if x < 0)) > 0 else 0

        print(f"\n[EURUSD {tf_name}] Trades={n_t:,} | WR={wr:5.2f}% | PF={pf:5.3f} | Net Exp={exp:+.4f}R | Tot R={cum[-1]:+.1f}R | MDD={mdd:4.1f}R")
        print(f"  BUY : N={len(longs):<5} | WR={sum(1 for x in longs if x>0)/len(longs)*100:.1f}% | PF={pf_l:.2f} | Net R={sum(longs):+.1f}R")
        print(f"  SELL: N={len(shorts):<5} | WR={sum(1 for x in shorts if x>0)/len(shorts)*100:.1f}% | PF={pf_s:.2f} | Net R={sum(shorts):+.1f}R")

    # Timeframe resamplings
    # EURUSD span in pips:
    # H1: 30 - 100 pips
    # M30: 18 - 50 pips
    # M15: 12 - 35 pips
    # M5: 6 - 20 pips

    h1 = df_clean.group_by("h1_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
    ]).sort("h1_ts")
    evaluate_fx(h1, "H1", min_span_pips=30.0, max_span_pips=100.0, swing_k=3, target_rr=1.5, max_hold=40)

    m30 = df_clean.group_by("m30_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
    ]).sort("m30_ts")
    evaluate_fx(m30, "M30", min_span_pips=18.0, max_span_pips=50.0, swing_k=3, target_rr=1.5, max_hold=40)

    m15 = df_clean.group_by("m15_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
    ]).sort("m15_ts")
    evaluate_fx(m15, "M15", min_span_pips=12.0, max_span_pips=35.0, swing_k=3, target_rr=1.5, max_hold=40)

    m5 = df_clean.group_by("m5_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
    ]).sort("m5_ts")
    evaluate_fx(m5, "M5", min_span_pips=6.0, max_span_pips=20.0, swing_k=3, target_rr=1.5, max_hold=40)

if __name__ == "__main__":
    run_eurusd_test()
