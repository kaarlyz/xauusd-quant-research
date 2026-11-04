#!/usr/bin/env python3
"""
Backtest Pola N Baku pada NAS100 Khusus Timeframe M1 (15 Tahun: 2011 - 2026).
Dataset: 4.23M bars NAS100_M1.parquet
Friction: Spread 1.0 poin ($1.00) + Slippage 0.5 poin + Komisi $0.20 per kontrak.
Target RR: 1:1.0, 1:1.2, 1:1.5.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

NAS100_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/NAS100_M1.parquet"

def test_nas100_m1():
    print("=== Loading 15 Years NAS100 M1 Parquet ===")
    df = pl.read_parquet(NAS100_PARQUET).sort("timestamp")
    df = df.with_columns(
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    # Rollover exclusion: 21:00 - 23:00 UTC
    df_clean = df.filter(~pl.col("hour").is_between(21, 23))

    o = df_clean["open"].to_numpy()
    h = df_clean["high"].to_numpy()
    l = df_clean["low"].to_numpy()
    c = df_clean["close"].to_numpy()
    dates = df_clean["date"].to_numpy()
    years = df_clean["year"].to_numpy()
    n = len(o)
    print(f"Total NAS100 M1 Bars to evaluate: {n:,}")

    # Deteksi swing M1: k=5
    swing_k = 5
    is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
    print("Computing swing highs and lows...")
    for i in range(swing_k, n - swing_k):
        if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
        if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

    # Span wajar range M1 Nasdaq: 8 poin s/d 35 poin
    min_span = 8.0
    max_span = 35.0
    spread = 1.0
    comm = 0.20
    slippage = 0.50
    buffer = 1.0
    max_hold = 60 # 60 menit

    for target_rr in [1.0, 1.2, 1.5]:
        trades = []
        last_sw_l = []; last_sw_h = []
        trade_exit_bar = 0

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
                    trades.append({"side": order_side, "r": r_val, "year": int(str(dates[fill_bar])[:4])})

        r_all = np.array([t["r"] for t in trades])
        n_t = len(r_all)
        gw = sum(x for x in r_all if x > 0); gl = abs(sum(x for x in r_all if x < 0))
        pf = gw / gl if gl > 0 else 99.0
        wr = sum(1 for x in r_all if x > 0) / n_t * 100.0 if n_t > 0 else 0
        exp = float(np.mean(r_all)) if n_t > 0 else 0
        cum = np.cumsum(r_all) if n_t > 0 else [0]
        mdd = float(np.max(np.maximum.accumulate(cum) - cum)) if n_t > 0 else 0

        per_month = n_t / (15.1 * 12)
        per_week = n_t / (15.1 * 52)
        per_day = n_t / (15.1 * 250)
        bep = 100.0 / (1.0 + target_rr)

        print(f"\n[NAS100 M1 | Target RR 1:{target_rr:.1f}]")
        print(f"Total Trade 15 Thn : {n_t:,} (~{per_day:.1f}/hari | ~{per_week:.1f}/mgg | ~{per_month:.1f}/bln)")
        print(f"Win Rate (WR)      : {wr:.2f}% (Titik Impas: {bep:.1f}%)")
        print(f"Profit Factor (PF) : {pf:.3f} | Net Exp: {exp:+.4f}R")
        print(f"Total Net PnL (R)  : {cum[-1]:+.1f}R | Max Drawdown: {mdd:.1f}R")

        longs = [t["r"] for t in trades if t["side"] == "BUY"]
        shorts = [t["r"] for t in trades if t["side"] == "SELL"]
        pf_l = sum(x for x in longs if x > 0) / abs(sum(x for x in longs if x < 0)) if abs(sum(x for x in longs if x < 0)) > 0 else 0
        pf_s = sum(x for x in shorts if x > 0) / abs(sum(x for x in shorts if x < 0)) if abs(sum(x for x in shorts if x < 0)) > 0 else 0
        print(f"  BUY : N={len(longs):<5} | WR={sum(1 for x in longs if x>0)/len(longs)*100:.1f}% | PF={pf_l:.2f} | Net R={sum(longs):+.1f}R")
        print(f"  SELL: N={len(shorts):<5} | WR={sum(1 for x in shorts if x>0)/len(shorts)*100:.1f}% | PF={pf_s:.2f} | Net R={sum(shorts):+.1f}R")

if __name__ == "__main__":
    test_nas100_m1()
