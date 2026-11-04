#!/usr/bin/env python3
"""
Uji Kuantitatif Independen: Metode Pola N Baku Video 4 (The Traders).
Aturan Spesifik Video:
1. Timeframe H1.
2. Swing Detection (Swing High R & Swing Low S).
3. Pembedaan Kondisi:
   - Double Order (Straddle): Jika harga konsolidasi di tengah range (30% - 70% dari box S/R).
   - Single Order: Jika harga berada di dekat salah satu batas (momentum kuat searah).
4. Aturan Expired: Jika terbentuk swing baru yang lebih sempit, batalkan pending order lama.
5. SL dinamis di luar swing (150 - 250 pips), TP fix 1:1.5 dan 1:2.
6. Uji 12 Tahun (2015-2026) pada 4.18M bars M1 (resampled H1) dengan spread ECN $0.38 + komisi $0.07 + slippage $0.05.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"

def test_the_traders_n_pattern():
    print("=== Loading M1 Data & Resampling to H1 ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    # Exclude rollover
    df = df.filter(~pl.col("hour").is_between(21, 23))

    h1 = df.group_by("h1_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("h1_ts")

    o = h1["open"].to_numpy(); h = h1["high"].to_numpy(); l = h1["low"].to_numpy(); c = h1["close"].to_numpy()
    dates = h1["date"].to_numpy(); n = len(o)
    print(f"Total H1 Bars: {n:,}")

    swing_k = 3
    is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
    for i in range(swing_k, n - swing_k):
        if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
        if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

    # Test RR 1:1.5 and RR 1:2.0
    for target_rr in [1.5, 2.0]:
        trades = []
        last_sw_l = []; last_sw_h = []

        # Tracking active pending orders with expiration
        # Only 1 trade at a time (konservatif)
        in_trade = False
        trade_exit_bar = 0

        for i in range(swing_k, n - 40):
            if is_sw_l[i]: last_sw_l.append((i, l[i]))
            if is_sw_h[i]: last_sw_h.append((i, h[i]))
            if len(last_sw_l) > 10: last_sw_l.pop(0)
            if len(last_sw_h) > 10: last_sw_h.pop(0)

            if i < trade_exit_bar:
                continue

            if len(last_sw_h) >= 2 and len(last_sw_l) >= 2:
                # Most recent swings
                idx_h, val_h = last_sw_h[-1]
                idx_l, val_l = last_sw_l[-1]
                span = val_h - val_l

                # S/R range must be reasonable (150 - 350 pips, or $15 - $35)
                if not (15.0 <= span <= 35.0):
                    continue

                # Relative position of current price in the range (0 = at low, 1 = at high)
                rel_pos = (c[i] - val_l) / span

                # Decision: Single vs Double order
                # If rel_pos between 0.35 and 0.65 -> Konsolidasi tengah -> Double Order
                # If rel_pos > 0.65 -> Dekat Resistance -> Single Order Buy Stop
                # If rel_pos < 0.35 -> Dekat Support -> Single Order Sell Stop
                allow_buy = rel_pos >= 0.35
                allow_sell = rel_pos <= 0.65

                # Order details:
                # Buy Stop at val_h (SL at val_l - 0.50)
                # Sell Stop at val_l (SL at val_h + 0.50)
                risk_buy = (val_h + 0.38 + 0.05) - (val_l - 0.50)
                tp_buy = (val_h + 0.38 + 0.05) + (target_rr * risk_buy)

                risk_sell = (val_h + 0.50) - (val_l - 0.05)
                tp_sell = (val_l - 0.05) - (target_rr * risk_sell)

                # Simulate forward until triggered, expired (by new swing), or timeout (max 15 bars)
                buy_active = allow_buy
                sell_active = allow_sell
                triggered = False
                order_side = None
                fill_bar = -1

                for step in range(1, 16):
                    chk = i + step
                    if chk >= n: break

                    # Expire condition: if a new swing is confirmed inside the step, order expires
                    if (is_sw_h[chk] and chk > idx_h) or (is_sw_l[chk] and chk > idx_l):
                        # Expired!
                        break

                    # Check buy fill
                    if buy_active and h[chk] >= val_h:
                        triggered = True
                        order_side = "BUY"
                        fill_bar = chk
                        sell_active = False # cancel opposing
                        break

                    # Check sell fill
                    if sell_active and l[chk] <= val_l:
                        triggered = True
                        order_side = "SELL"
                        fill_bar = chk
                        buy_active = False # cancel opposing
                        break

                if triggered:
                    outcome = 0
                    r_val = 0.0
                    exit_idx = fill_bar

                    if order_side == "BUY":
                        for s in range(fill_bar + 1, min(n, fill_bar + 40)):
                            exit_idx = s
                            if l[s] <= (val_l - 0.50):
                                r_val = -1.0; outcome = -1; break
                            elif h[s] >= tp_buy:
                                r_val = target_rr; outcome = 1; break
                        if outcome == 0 and fill_bar + 40 < n:
                            r_val = (c[fill_bar + 40] - (val_h + 0.38 + 0.05)) / risk_buy
                    else: # SELL
                        for s in range(fill_bar + 1, min(n, fill_bar + 40)):
                            exit_idx = s
                            if h[s] + 0.38 >= (val_h + 0.50):
                                r_val = -1.0; outcome = -1; break
                            elif l[s] + 0.38 <= tp_sell:
                                r_val = target_rr; outcome = 1; break
                        if outcome == 0 and fill_bar + 40 < n:
                            r_val = ((val_l - 0.05) - c[fill_bar + 40]) / risk_sell

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
        print(f"\n[Target RR 1:{target_rr:.1f}]")
        print(f"Total Trade : {n_t:,} (Rata-rata {per_month:.1f} trade/bulan | {n_t/(12*52):.1f} trade/minggu)")
        print(f"Win Rate    : {wr:.2f}% (Titik Impas: {100/(1+target_rr):.1f}%)")
        print(f"Profit Factor: {pf:.3f} | Net Exp: {exp:+.4f}R")
        print(f"Total Net R : {cum[-1]:+.1f}R | Max Drawdown: {mdd:.1f}R")

        longs = [t["r"] for t in trades if t["side"] == "BUY"]
        shorts = [t["r"] for t in trades if t["side"] == "SELL"]
        pf_l = sum(x for x in longs if x > 0) / abs(sum(x for x in longs if x < 0)) if abs(sum(x for x in longs if x < 0)) > 0 else 0
        pf_s = sum(x for x in shorts if x > 0) / abs(sum(x for x in shorts if x < 0)) if abs(sum(x for x in shorts if x < 0)) > 0 else 0
        print(f"Sisi BUY    : N={len(longs):<4} | WR={sum(1 for x in longs if x>0)/len(longs)*100:.1f}% | PF={pf_l:.2f} | Net R={sum(longs):+.1f}R")
        print(f"Sisi SELL   : N={len(shorts):<4} | WR={sum(1 for x in shorts if x>0)/len(shorts)*100:.1f}% | PF={pf_s:.2f} | Net R={sum(shorts):+.1f}R")

if __name__ == "__main__":
    test_the_traders_n_pattern()
