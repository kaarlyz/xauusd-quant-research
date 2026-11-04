#!/usr/bin/env python3
"""
Uji Kuantitatif Pola N Versi Breakout-Retest Support/Resistance (Andre Rizky Investasi).
Aturan Baku:
1. Timeframe H1 untuk struktur Support/Resistance / Ranging.
2. Penembusan level (Breakout) Resistance (Bullish) atau Support (Bearish).
3. Validasi Retracement (M15 / M30) kembali ke level yang ditembus (Role Reversal SBR / RBS).
4. Entry Limit / Reversal saat harga retest level tersebut dan mantul.
5. SL di luar swing pullback, TP di proyeksi swing high/low sebelumnya.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"

def test_andre_rizky_breakout_retest():
    print("=== Loading M1 Data & Resampling to H1 ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    h1 = df.group_by("h1_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("h1_ts")

    o = h1["open"].to_numpy()
    h = h1["high"].to_numpy()
    l = h1["low"].to_numpy()
    c = h1["close"].to_numpy()
    dates = h1["date"].to_numpy()
    n = len(o)

    # Rolling 24-bar (1 hari) Support and Resistance
    cumsum_c = np.cumsum(np.insert(c, 0, 0))
    # 24-period high and low
    lookback = 24
    trades = []

    for i in range(lookback + 5, n - 35):
        h_res = np.max(h[i - lookback : i - 1])
        l_sup = np.min(l[i - lookback : i - 1])
        range_span = h_res - l_sup
        if not (10.0 <= range_span <= 80.0): continue

        # Bullish Breakout & Retest:
        # Bar i-1 tembus resistance (Close > h_res)
        # Bar i retest kembali ke area h_res (Low <= h_res + 1.0 dan Close > h_res) -> Mantul!
        if c[i-1] > h_res and l[i] <= h_res + 1.5 and c[i] > h_res:
            entry_p = c[i] + 0.38 + 0.05
            sl_p = l[i] - 1.0 # di bawah ekor retest
            risk = entry_p - sl_p
            if 2.0 <= risk <= 30.0:
                tp_p = entry_p + (1.5 * risk) # RR 1.5:1
                outcome = 0; r_val = 0.0
                for s in range(1, 35):
                    chk = i + s
                    if chk >= n: break
                    if l[chk] <= sl_p: r_val = -1.0; outcome = -1; break
                    elif h[chk] >= tp_p: r_val = 1.5; outcome = 1; break
                if outcome == 0 and i + 35 < n:
                    r_val = (c[i+35] - entry_p) / risk
                trades.append({"dir": "LONG", "r": r_val, "year": int(str(dates[i])[:4])})

        # Bearish Breakout & Retest:
        # Bar i-1 tembus support (Close < l_sup)
        # Bar i retest kembali ke area l_sup (High >= l_sup - 1.5 dan Close < l_sup) -> Mantul ke bawah!
        elif c[i-1] < l_sup and h[i] >= l_sup - 1.5 and c[i] < l_sup:
            entry_p = c[i] - 0.05
            sl_p = h[i] + 1.0 + 0.38
            risk = sl_p - entry_p
            if 2.0 <= risk <= 30.0:
                tp_p = entry_p - (1.5 * risk)
                outcome = 0; r_val = 0.0
                for s in range(1, 35):
                    chk = i + s
                    if chk >= n: break
                    if h[chk] + 0.38 >= sl_p: r_val = -1.0; outcome = -1; break
                    elif l[chk] + 0.38 <= tp_p: r_val = 1.5; outcome = 1; break
                if outcome == 0 and i + 35 < n:
                    r_val = (entry_p - c[i+35]) / risk
                trades.append({"dir": "SHORT", "r": r_val, "year": int(str(dates[i])[:4])})

    r_all = np.array([t["r"] for t in trades])
    n_t = len(r_all)
    gw = sum(x for x in r_all if x > 0); gl = abs(sum(x for x in r_all if x < 0))
    pf = gw / gl if gl > 0 else 99.0
    wr = sum(1 for x in r_all if x > 0) / n_t * 100.0 if n_t > 0 else 0
    exp = float(np.mean(r_all)) if n_t > 0 else 0
    cum = np.cumsum(r_all) if n_t > 0 else [0]
    mdd = float(np.max(np.maximum.accumulate(cum) - cum)) if n_t > 0 else 0

    print(f"\n[Breakout-Retest Pola N (H1/M30)] Trades={n_t:,} | WR={wr:5.2f}% | PF={pf:5.3f} | Net Exp={exp:+.4f}R | Tot R={cum[-1]:+.1f}R | MDD={mdd:.1f}R")

    longs = [t["r"] for t in trades if t["dir"] == "LONG"]
    shorts = [t["r"] for t in trades if t["dir"] == "SHORT"]
    pf_l = sum(x for x in longs if x > 0) / abs(sum(x for x in longs if x < 0)) if abs(sum(x for x in longs if x < 0)) > 0 else 0
    pf_s = sum(x for x in shorts if x > 0) / abs(sum(x for x in shorts if x < 0)) if abs(sum(x for x in shorts if x < 0)) > 0 else 0
    print(f"Sisi LONG  : N={len(longs):<4} | WR={sum(1 for x in longs if x>0)/len(longs)*100:.1f}% | PF={pf_l:.2f} | Net R={sum(longs):+.1f}R")
    print(f"Sisi SHORT : N={len(shorts):<4} | WR={sum(1 for x in shorts if x>0)/len(shorts)*100:.1f}% | PF={pf_s:.2f} | Net R={sum(shorts):+.1f}R")

if __name__ == "__main__":
    test_andre_rizky_breakout_retest()
