#!/usr/bin/env python3
"""
Bedah Kuantitatif Pola N Hosoda (Ichimoku N-Wave) pada XAUUSD.
Berdasarkan Video YouTube: fcySBFFsm04

Aturan Baku Video:
1. Gelombang N: Titik A -> Titik B -> Titik C.
   - Bullish N: A (Low) -> B (High) -> C (Higher Low, C > A).
   - Bearish N: A (High) -> B (Low) -> C (Lower High, C < B).
2. Entry Order:
   - Buy Stop dipasang tepat di titik B.
   - Stop Loss diletakkan di titik C.
   - Target N (Rumus Asli Hosoda): Target = C + (B - A) [jarak AB diproyeksikan dari C].
   - Jarak Target dari B = C + B - A - B = C - A (sama dengan jarak C ke A).
   - Jarak Stop Loss dari B = B - C.
3. Timeframe: H1 dan H4.
4. Uji pada Master M1 Parquet (resampled to H1 dan H4) dengan spread ECN riil ($0.38) + komisi ($0.07).
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"

def run_n_pattern_test():
    print("=== Loading M1 Data & Resampling to H1 and H4 ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        (pl.col("timestamp") // (4 * 60 * 60 * 1000) * (4 * 60 * 60 * 1000)).alias("h4_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    # 1. Resample H1
    h1 = df.group_by("h1_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("h1_ts")

    # 2. Resample H4
    h4 = df.group_by("h4_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("h4_ts")

    print(f"Total H1 Bars: {len(h1):,} | Total H4 Bars: {len(h4):,}")

    def test_tf_n_pattern(bars_df, tf_name, swing_k=3):
        o = bars_df["open"].to_numpy()
        h = bars_df["high"].to_numpy()
        l = bars_df["low"].to_numpy()
        c = bars_df["close"].to_numpy()
        years = bars_df["year"].to_numpy()
        dates = bars_df["date"].to_numpy()
        n = len(o)

        # Detect swings with strength swing_k
        # Swing High at i: h[i] is max of i-k..i+k
        # Swing Low at i: l[i] is min of i-k..i+k
        is_sw_h = np.zeros(n, dtype=bool)
        is_sw_l = np.zeros(n, dtype=bool)
        for i in range(swing_k, n - swing_k):
            if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
            if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

        trades = []

        # Find N-waves:
        # Bullish: Swing Low A (at idx_a) -> Swing High B (at idx_b > idx_a) -> Swing Low C (at idx_c > idx_b)
        # Conditions: C > A. Order placed: Buy Stop at B. SL at C. TP at C + (B - A).
        # Order active until B is broken or cancelled if new swing forms.
        last_sw_l = [] # list of (idx, price)
        last_sw_h = [] # list of (idx, price)

        for i in range(swing_k, n - 20):
            if is_sw_l[i]: last_sw_l.append((i, l[i]))
            if is_sw_h[i]: last_sw_h.append((i, h[i]))

            # Keep only last 10 swings
            if len(last_sw_l) > 10: last_sw_l.pop(0)
            if len(last_sw_h) > 10: last_sw_h.pop(0)

            # Check if we have formed A -> B -> C recently
            # Bullish N pattern:
            if len(last_sw_l) >= 2 and len(last_sw_h) >= 1:
                idx_a, price_a = last_sw_l[-2]
                idx_b, price_b = last_sw_h[-1]
                idx_c, price_c = last_sw_l[-1]

                if idx_a < idx_b < idx_c:
                    if price_c > price_a and price_b > price_a and price_b > price_c:
                        # Setup is valid at confirmation bar i = idx_c + swing_k
                        if i == idx_c + swing_k:
                            # Forward test Buy Stop at price_b
                            sl_p = price_c - 0.50
                            tp_p = price_c + (price_b - price_a)
                            risk = (price_b + 0.38 + 0.05) - sl_p
                            reward = tp_p - (price_b + 0.38 + 0.05)

                            if risk > 1.0 and reward > 0.5:
                                # Watch forward up to 30 bars for buy stop trigger
                                triggered = False
                                for step in range(1, 31):
                                    chk = i + step
                                    if chk >= n: break
                                    # If price breaks below C before B, setup cancelled
                                    if l[chk] <= sl_p: break
                                    if h[chk] >= price_b: # Triggered
                                        triggered = True
                                        entry_bar = chk
                                        break
                                if triggered:
                                    outcome = 0; r_val = 0.0
                                    for s in range(1, 50):
                                        bar_idx = entry_bar + s
                                        if bar_idx >= n: break
                                        if l[bar_idx] <= sl_p: r_val = -1.0; outcome = -1; break
                                        elif h[bar_idx] >= tp_p: r_val = (reward / risk); outcome = 1; break
                                    if outcome == 0 and entry_bar + 50 < n:
                                        r_val = (c[entry_bar + 50] - price_b) / risk
                                    trades.append({"tf": tf_name, "dir": "LONG", "r": r_val, "year": int(str(dates[entry_bar])[:4])})

            # Bearish N pattern:
            if len(last_sw_h) >= 2 and len(last_sw_l) >= 1:
                idx_a, price_a = last_sw_h[-2]
                idx_b, price_b = last_sw_l[-1]
                idx_c, price_c = last_sw_h[-1]

                if idx_a < idx_b < idx_c:
                    if price_c < price_a and price_b < price_a and price_c > price_b:
                        if i == idx_c + swing_k:
                            sl_p = price_c + 0.50
                            tp_p = price_c - (price_a - price_b)
                            risk = sl_p - (price_b - 0.05)
                            reward = (price_b - 0.05) - (tp_p + 0.38)

                            if risk > 1.0 and reward > 0.5:
                                triggered = False
                                for step in range(1, 31):
                                    chk = i + step
                                    if chk >= n: break
                                    if h[chk] >= sl_p: break
                                    if l[chk] <= price_b:
                                        triggered = True
                                        entry_bar = chk
                                        break
                                if triggered:
                                    outcome = 0; r_val = 0.0
                                    for s in range(1, 50):
                                        bar_idx = entry_bar + s
                                        if bar_idx >= n: break
                                        if h[bar_idx] + 0.38 >= sl_p: r_val = -1.0; outcome = -1; break
                                        elif l[bar_idx] + 0.38 <= tp_p: r_val = (reward / risk); outcome = 1; break
                                    if outcome == 0 and entry_bar + 50 < n:
                                        r_val = (price_b - c[entry_bar + 50]) / risk
                                    trades.append({"tf": tf_name, "dir": "SHORT", "r": r_val, "year": int(str(dates[entry_bar])[:4])})

        r_all = np.array([t["r"] for t in trades])
        n_t = len(r_all)
        if n_t > 0:
            gw = sum(x for x in r_all if x > 0); gl = abs(sum(x for x in r_all if x < 0))
            pf = gw / gl if gl > 0 else 99.0
            wr = sum(1 for x in r_all if x > 0) / n_t * 100.0
            exp = float(np.mean(r_all))
            cum = np.cumsum(r_all)
            mdd = float(np.max(np.maximum.accumulate(cum) - cum))
            tot_r = float(cum[-1])
        else:
            pf = wr = exp = mdd = tot_r = 0.0

        print(f"[{tf_name}] Swing Strength={swing_k} | Trades={n_t:<4} | WR={wr:5.2f}% | PF={pf:5.3f} | Net Exp={exp:+.4f}R | Tot R={tot_r:+.1f}R | MDD={mdd:.1f}R")

        # Annual breakdown
        for y in sorted(list(set(t["year"] for t in trades))):
            sub_y = [t["r"] for t in trades if t["year"] == y]
            if sub_y:
                gw_y = sum(x for x in sub_y if x > 0); gl_y = abs(sum(x for x in sub_y if x < 0))
                pf_y = gw_y / gl_y if gl_y > 0 else 99.0
                wr_y = sum(1 for x in sub_y if x > 0) / len(sub_y) * 100.0
                print(f"   Year {y}: N={len(sub_y):<3} | WR={wr_y:4.1f}% | PF={pf_y:4.2f} | Net R={sum(sub_y):+.2f}R")

    print("\n--- Testing H4 Pola N Asli Hosoda ---")
    test_tf_n_pattern(h4, "H4", swing_k=2)

    print("\n--- Testing H1 Pola N Asli Hosoda ---")
    test_tf_n_pattern(h1, "H1", swing_k=3)

if __name__ == "__main__":
    run_n_pattern_test()
