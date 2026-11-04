#!/usr/bin/env python3
"""
Uji Kuantitatif Pola N Dua Arah (Double Pending Order Buy Stop & Sell Stop).
Berdasarkan Diskusi Video Tito / Mata Trader: HhaNJxbXfeA

Pendekatan di Video:
1. "Semua order saya akan selalu dua. Buy Stop di atas, Sell Stop di bawah."
2. "Begitu satu tersentuh dan kena TP, order pasangannya dicancel."
3. "Ada kalanya dua-duanya kena Stop Loss (Whipsaw double loss)."
4. Timeframe yang dipakai di panggung: H4 (dan H1).
5. Target: Proyeksi N (C + AB).

Mari kita uji variasi "Dua Arah Sekaligus" ini di Master M1 Parquet (2015-2026)!
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"

def test_dual_n_order():
    print("=== Loading M1 Data & Resampling to H4 and H1 ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        (pl.col("timestamp") // (4 * 60 * 60 * 1000) * (4 * 60 * 60 * 1000)).alias("h4_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    h4 = df.group_by("h4_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("h4_ts")

    h1 = df.group_by("h1_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("h1_ts")

    def run_dual_orders(bars_df, tf_name, swing_k=2):
        o = bars_df["open"].to_numpy()
        h = bars_df["high"].to_numpy()
        l = bars_df["low"].to_numpy()
        c = bars_df["close"].to_numpy()
        dates = bars_df["date"].to_numpy()
        n = len(o)

        is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
        for i in range(swing_k, n - swing_k):
            if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
            if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

        trades = []
        last_sw_l = []; last_sw_h = []

        for i in range(swing_k, n - 40):
            if is_sw_l[i]: last_sw_l.append((i, l[i]))
            if is_sw_h[i]: last_sw_h.append((i, h[i]))
            if len(last_sw_l) > 10: last_sw_l.pop(0)
            if len(last_sw_h) > 10: last_sw_h.pop(0)

            # Check if we have recent High and Low range to straddle (Dua Arah)
            if len(last_sw_h) >= 2 and len(last_sw_l) >= 2:
                # Top swing High B and bottom swing Low C
                h_b = last_sw_h[-1][1]
                l_c = last_sw_l[-1][1]
                box_span = h_b - l_c
                if not (5.0 <= box_span <= 60.0): continue

                # Dual Order Setup:
                # Buy Stop at h_b (SL at l_c, TP = h_b + box_span)
                # Sell Stop at l_c (SL at h_b, TP = l_c - box_span)
                if i == max(last_sw_h[-1][0], last_sw_l[-1][0]) + swing_k:
                    # Forward test next 20 bars
                    buy_triggered = False; sell_triggered = False
                    buy_r = 0.0; sell_r = 0.0

                    risk = box_span + 0.38
                    for step in range(1, 25):
                        chk = i + step
                        if chk >= n: break

                        # Check triggers
                        if not buy_triggered and h[chk] >= h_b:
                            buy_triggered = True
                            # Forward test buy
                            for s in range(chk + 1, min(n, chk + 30)):
                                if l[s] <= l_c - 0.50: buy_r = -1.0; break
                                elif h[s] >= h_b + box_span: buy_r = 1.0; break

                        if not sell_triggered and l[chk] <= l_c:
                            sell_triggered = True
                            for s in range(chk + 1, min(n, chk + 30)):
                                if h[s] >= h_b + 0.50: sell_r = -1.0; break
                                elif l[s] <= l_c - box_span: sell_r = 1.0; break

                        if buy_triggered or sell_triggered:
                            break

                    if buy_triggered:
                        trades.append({"r": buy_r, "type": "BUY_STOP", "year": int(str(dates[i])[:4])})
                    if sell_triggered:
                        trades.append({"r": sell_r, "type": "SELL_STOP", "year": int(str(dates[i])[:4])})

        r_all = np.array([t["r"] for t in trades])
        n_t = len(r_all)
        gw = sum(x for x in r_all if x > 0); gl = abs(sum(x for x in r_all if x < 0))
        pf = gw / gl if gl > 0 else 99.0
        wr = sum(1 for x in r_all if x > 0) / n_t * 100.0 if n_t > 0 else 0
        exp = float(np.mean(r_all)) if n_t > 0 else 0
        cum = np.cumsum(r_all) if n_t > 0 else [0]
        mdd = float(np.max(np.maximum.accumulate(cum) - cum)) if n_t > 0 else 0

        print(f"[{tf_name} DUAL ORDER STRADDLE] Trades={n_t:,} | WR={wr:5.2f}% | PF={pf:5.3f} | Net Exp={exp:+.4f}R | Tot R={cum[-1]:+.1f}R | MDD={mdd:.1f}R")

    print("\n--- Testing Dual Order (Straddle) on H4 ---")
    run_dual_orders(h4, "H4", swing_k=2)

    print("\n--- Testing Dual Order (Straddle) on H1 ---")
    run_dual_orders(h1, "H1", swing_k=3)

if __name__ == "__main__":
    test_dual_n_order()
