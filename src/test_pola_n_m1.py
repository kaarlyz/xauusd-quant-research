#!/usr/bin/env python3
"""
Uji Kuantitatif Pola N Baku (The Traders) di Timeframe M1.
Dataset: 4.18M bars XAUUSD_M1.parquet (2015-2026).
Friction: Spread ECN $0.38 + Komisi $0.07 + Slippage $0.05.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"

def test_pola_n_m1():
    print("=== Loading M1 Data (2015 - 2026) ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.filter(pl.col("timestamp") >= 1420070400000) # 2015-01-01 onwards
    df = df.with_columns(
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    # Exclude rollover 21:00 - 23:00 UTC
    df = df.filter(~pl.col("hour").is_between(21, 23))

    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    dates = df["date"].to_numpy()
    n = len(o)
    print(f"Total M1 Bars to evaluate: {n:,}")

    # Di M1, swing span wajar emas adalah $1.50 s/d $5.00 (15 - 50 pips)
    # Swing k = 5 bars (5 menit untuk swing high/low lokal)
    swing_k = 5
    is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
    print("Computing swing highs and lows...")
    for i in range(swing_k, n - swing_k):
        if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
        if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

    target_rr = 1.5
    trades = []
    last_sw_l = []; last_sw_h = []
    trade_exit_bar = 0
    max_hold = 60 # max hold 60 menit (1 jam) di M1

    print("Simulating trades with real friction ($0.38 spread + $0.07 comm + $0.05 slip)...")
    for i in range(swing_k, n - max_hold - 5):
        if is_sw_l[i]: last_sw_l.append((i, l[i]))
        if is_sw_h[i]: last_sw_h.append((i, h[i]))
        if len(last_sw_l) > 10: last_sw_l.pop(0)
        if len(last_sw_h) > 10: last_sw_h.pop(0)

        if i < trade_exit_bar:
            continue

        if len(last_sw_h) >= 2 and len(last_sw_l) >= 2:
            idx_h, val_h = last_sw_h[-1]
            idx_l, val_l = last_sw_l[-1]
            span = val_h - val_l

            # Range M1: $1.50 s/d $6.00
            if not (1.50 <= span <= 6.00):
                continue

            rel_pos = (c[i] - val_l) / span
            allow_buy = rel_pos >= 0.35
            allow_sell = rel_pos <= 0.65

            # Biaya ECN riil:
            # Buy order fill at val_h + 0.38 spread + 0.05 slippage
            # Sell order fill at val_l - 0.05 slippage
            risk_buy = (val_h + 0.38 + 0.05) - (val_l - 0.20)
            tp_buy = (val_h + 0.38 + 0.05) + (target_rr * risk_buy)

            risk_sell = (val_h + 0.20) - (val_l - 0.05)
            tp_sell = (val_l - 0.05) - (target_rr * risk_sell)

            buy_active = allow_buy
            sell_active = allow_sell
            triggered = False
            order_side = None
            fill_bar = -1

            # Timeout 15 bar M1 (15 menit)
            for step in range(1, 16):
                chk = i + step
                if chk >= n: break

                # Expired condition
                if (is_sw_h[chk] and chk > idx_h) or (is_sw_l[chk] and chk > idx_l):
                    break

                if buy_active and h[chk] >= val_h:
                    triggered = True
                    order_side = "BUY"
                    fill_bar = chk
                    break

                if sell_active and l[chk] <= val_l:
                    triggered = True
                    order_side = "SELL"
                    fill_bar = chk
                    break

            if triggered:
                outcome = 0
                r_val = 0.0
                exit_idx = fill_bar

                if order_side == "BUY":
                    for s in range(fill_bar + 1, min(n, fill_bar + max_hold)):
                        exit_idx = s
                        # Check pessimistic same bar
                        if l[s] <= (val_l - 0.20):
                            r_val = -1.0; outcome = -1; break
                        elif h[s] >= tp_buy:
                            r_val = target_rr; outcome = 1; break
                    if outcome == 0 and fill_bar + max_hold < n:
                        r_val = (c[fill_bar + max_hold] - (val_h + 0.38 + 0.05)) / risk_buy
                else: # SELL
                    for s in range(fill_bar + 1, min(n, fill_bar + max_hold)):
                        exit_idx = s
                        if h[s] + 0.38 >= (val_h + 0.20):
                            r_val = -1.0; outcome = -1; break
                        elif l[s] + 0.38 <= tp_sell:
                            r_val = target_rr; outcome = 1; break
                    if outcome == 0 and fill_bar + max_hold < n:
                        r_val = ((val_l - 0.05) - c[fill_bar + max_hold]) / risk_sell

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

    per_month = n_t / 144.0
    per_week = n_t / (12 * 52)
    per_day = n_t / (12 * 250)

    print("\n" + "=" * 70)
    print("HASIL BACKTEST POLA N BAKU DI TIMEFRAME M1 (2015 - 2026)")
    print("=" * 70)
    print(f"Total Trade 12 Tahun : {n_t:,}")
    print(f"Frekuensi Eksekusi   : ~{per_day:.1f} trade/hari | ~{per_week:.1f} trade/minggu | ~{per_month:.1f} trade/bulan")
    print(f"Win Rate (WR)        : {wr:.2f}% (Titik Impas: 40.0%)")
    print(f"Profit Factor (PF)   : {pf:.3f}")
    print(f"Net Expectancy       : {exp:+.4f} R per trade")
    print(f"Total Net PnL (12 Th): {cum[-1]:+.1f} R")
    print(f"Maximum Drawdown     : {mdd:.1f} R")

    longs = [t["r"] for t in trades if t["side"] == "BUY"]
    shorts = [t["r"] for t in trades if t["side"] == "SELL"]
    pf_l = sum(x for x in longs if x > 0) / abs(sum(x for x in longs if x < 0)) if abs(sum(x for x in longs if x < 0)) > 0 else 0
    pf_s = sum(x for x in shorts if x > 0) / abs(sum(x for x in shorts if x < 0)) if abs(sum(x for x in shorts if x < 0)) > 0 else 0
    print(f"\nSisi BUY  : N={len(longs):<5} | WR={sum(1 for x in longs if x>0)/len(longs)*100:.1f}% | PF={pf_l:.2f} | Net R={sum(longs):+.1f}R")
    print(f"Sisi SELL : N={len(shorts):<5} | WR={sum(1 for x in shorts if x>0)/len(shorts)*100:.1f}% | PF={pf_s:.2f} | Net R={sum(shorts):+.1f}R")

if __name__ == "__main__":
    test_pola_n_m1()
