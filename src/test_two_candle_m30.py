#!/usr/bin/env python3
"""
Uji Kuantitatif Independen: Teknik Scalping Dua Candle M30 -> M5
Berdasarkan Video YouTube: JddnO_5Pjxw

Aturan Baku:
1. Timeframe Trend: M30. Timeframe Entry: M5.
2. Setup M30:
   - Candle 1: Impulsif (Body >= 1.0 * ATR14 M30).
   - Candle 2: Searah dengan Candle 1 (Bullish-Bullish atau Bearish-Bearish).
   - Setelah Candle 2 close: Tarik kotak High-Low dari kedua candle tersebut.
3. Entry di M5:
   - Tunggu harga retrace ke Fibo 61.8% dari kotak range tersebut (atau 50%).
   - Stop Loss di luar kotak (di atas High kotak untuk Sell, di bawah Low kotak untuk Buy).
   - Take Profit: RR 1:2 (2 kali jarak risiko).
   - Maksimal menunggu retrace: 1 jam (12 candle M5).
4. Uji pada Master M1 Parquet (resampled to M5 and M30) 12 tahun (2015-2026).
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"

def test_two_candle_strategy():
    print("=== Loading M1 Data & Resampling to M5 and M30 ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (5 * 60 * 1000) * (5 * 60 * 1000)).alias("m5_ts"),
        (pl.col("timestamp") // (30 * 60 * 1000) * (30 * 60 * 1000)).alias("m30_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    df = df.filter(~pl.col("hour").is_between(21, 23))

    # M30
    m30 = df.group_by("m30_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("m30_ts")

    # M5
    m5 = df.group_by("m5_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("m5_ts")

    print(f"Total M30 Bars: {len(m30):,} | Total M5 Bars: {len(m5):,}")

    o30 = m30["open"].to_numpy(); h30 = m30["high"].to_numpy(); l30 = m30["low"].to_numpy(); c30 = m30["close"].to_numpy()
    dates30 = m30["date"].to_numpy(); n30 = len(o30)

    # 14-period ATR on M30
    tr30 = np.maximum(h30 - l30, np.maximum(np.abs(h30 - np.roll(c30, 1)), np.abs(l30 - np.roll(c30, 1))))
    cumsum30 = np.cumsum(np.insert(tr30, 0, 0))
    atr30 = (cumsum30[14:] - cumsum30[:-14]) / 14.0
    atr30 = np.pad(atr30, (14, 0), mode="edge")[:n30]

    o5 = m5["open"].to_numpy(); h5 = m5["high"].to_numpy(); l5 = m5["low"].to_numpy(); c5 = m5["close"].to_numpy()
    n5 = len(o5)

    # Map M30 bar index to M5 bar index (each M30 bar contains 6 M5 bars)
    # Ratio is approx 6 M5 bars per M30 bar
    # Let's test on M30 directly for simplicity and robustness
    # A setup is completed at close of candle 2 (bar i)
    # Box is High = max(h[i-1], h[i]), Low = min(l[i-1], l[i])
    # Entry at 61.8% retrace of box in next 2 bars (1 hour)

    for retrace_lvl, rr_target in [(0.618, 2.0), (0.500, 2.0), (0.618, 1.0), (0.618, 3.0)]:
        trades = []
        for i in range(20, n30 - 25):
            cur_atr = atr30[i]
            if cur_atr < 1.0: continue

            # Candle 1 (i-1) is impulsive: Body >= 1.0 * ATR
            body1 = abs(c30[i-1] - o30[i-1])
            if body1 < 1.0 * cur_atr: continue

            # Check directional alignment
            is_bull1 = c30[i-1] > o30[i-1]
            is_bull2 = c30[i] > o30[i]

            is_bear1 = c30[i-1] < o30[i-1]
            is_bear2 = c30[i] < o30[i]

            box_h = max(h30[i-1], h30[i])
            box_l = min(l30[i-1], l30[i])
            box_span = box_h - box_l
            if not (2.0 <= box_span <= 40.0): continue

            # BULLISH SETUP (Buy on dip to 61.8% from high)
            if is_bull1 and is_bull2:
                # 61.8% retrace = box_h - 0.618 * box_span
                entry_level = box_h - (retrace_lvl * box_span)
                sl_level = box_l - 0.50
                risk = (entry_level + 0.38 + 0.05) - sl_level
                if risk < 1.0 or risk > 30.0: continue
                tp_level = (entry_level + 0.38 + 0.05) + (rr_target * risk)

                # Check if price retraces to entry_level in next 2 M30 bars (1 hour)
                triggered = False
                entry_bar = -1
                for step in range(1, 3):
                    chk = i + step
                    if chk >= n30: break
                    if l30[chk] <= entry_level:
                        triggered = True
                        entry_bar = chk
                        break
                    if h30[chk] >= tp_level: break # missed, already ran

                if triggered:
                    outcome = 0; r_val = 0.0
                    for s in range(1, 20):
                        b = entry_bar + s
                        if b >= n30: break
                        if l30[b] <= sl_level: r_val = -1.0; outcome = -1; break
                        elif h30[b] >= tp_level: r_val = rr_target; outcome = 1; break
                    if outcome == 0 and entry_bar + 20 < n30:
                        r_val = (c30[entry_bar + 20] - entry_level) / risk
                    trades.append({"r": r_val, "year": int(str(dates30[entry_bar])[:4])})

            # BEARISH SETUP (Sell on rally to 61.8% from low)
            elif is_bear1 and is_bear2:
                # 61.8% retrace = box_l + 0.618 * box_span
                entry_level = box_l + (retrace_lvl * box_span)
                sl_level = box_h + 0.50
                risk = sl_level - (entry_level - 0.05)
                if risk < 1.0 or risk > 30.0: continue
                tp_level = (entry_level - 0.05) - (rr_target * risk)

                triggered = False
                entry_bar = -1
                for step in range(1, 3):
                    chk = i + step
                    if chk >= n30: break
                    if h30[chk] >= entry_level:
                        triggered = True
                        entry_bar = chk
                        break
                    if l30[chk] <= tp_level: break

                if triggered:
                    outcome = 0; r_val = 0.0
                    for s in range(1, 20):
                        b = entry_bar + s
                        if b >= n30: break
                        if h30[b] + 0.38 >= sl_level: r_val = -1.0; outcome = -1; break
                        elif l30[b] + 0.38 <= tp_level: r_val = rr_target; outcome = 1; break
                    if outcome == 0 and entry_bar + 20 < n30:
                        r_val = (entry_level - c30[entry_bar + 20]) / risk
                    trades.append({"r": r_val, "year": int(str(dates30[entry_bar])[:4])})

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

        print(f"Retrace={retrace_lvl*100:4.1f}% | RR=1:{rr_target:.0f} | Trades={n_t:<5} | WR={wr:5.2f}% | PF={pf:5.3f} | Net Exp={exp:+.4f}R | Tot R={tot_r:+.1f}R | MDD={mdd:.1f}R")

if __name__ == "__main__":
    test_two_candle_strategy()
