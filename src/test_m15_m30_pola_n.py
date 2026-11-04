#!/usr/bin/env python3
"""
Pengujian Pola N Hosoda pada Timeframe M15 dan M30 (2015 - 2026).
Dataset: 4.18M bars XAUUSD_M1.parquet
Friction: Spread ECN riil ($0.38) + Komisi ($0.07/oz round-turn) + Slippage stop ($0.05).
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"

def run_m15_m30_test():
    print("=== Loading M1 Data & Resampling to M15 and M30 ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"),
        (pl.col("timestamp") // (30 * 60 * 1000) * (30 * 60 * 1000)).alias("m30_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    # 1. Resample M15
    m15 = df.group_by("m15_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("m15_ts")

    # 2. Resample M30
    m30 = df.group_by("m30_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("m30_ts")

    print(f"Total M15 Bars: {len(m15):,} | Total M30 Bars: {len(m30):,}")

    def evaluate_n_pattern(bars_df, tf_name, swing_k=3):
        o = bars_df["open"].to_numpy()
        h = bars_df["high"].to_numpy()
        l = bars_df["low"].to_numpy()
        c = bars_df["close"].to_numpy()
        years = bars_df["year"].to_numpy()
        dates = bars_df["date"].to_numpy()
        n = len(o)

        is_sw_h = np.zeros(n, dtype=bool)
        is_sw_l = np.zeros(n, dtype=bool)
        for i in range(swing_k, n - swing_k):
            if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
            if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

        trades = []
        last_sw_l = []; last_sw_h = []

        # Forward holding limit: 40 bars (for M15 = 10 jam, for M30 = 20 jam)
        max_hold = 40

        for i in range(swing_k, n - max_hold - 5):
            if is_sw_l[i]: last_sw_l.append((i, l[i]))
            if is_sw_h[i]: last_sw_h.append((i, h[i]))

            if len(last_sw_l) > 10: last_sw_l.pop(0)
            if len(last_sw_h) > 10: last_sw_h.pop(0)

            # Bullish N pattern
            if len(last_sw_l) >= 2 and len(last_sw_h) >= 1:
                idx_a, price_a = last_sw_l[-2]
                idx_b, price_b = last_sw_h[-1]
                idx_c, price_c = last_sw_l[-1]

                if idx_a < idx_b < idx_c:
                    if price_c > price_a and price_b > price_a and price_b > price_c:
                        if i == idx_c + swing_k:
                            sl_p = price_c - 0.50
                            tp_p = price_c + (price_b - price_a)
                            risk = (price_b + 0.38 + 0.05) - sl_p
                            reward = tp_p - (price_b + 0.38 + 0.05)

                            if risk > 0.80 and reward > 0.40:
                                triggered = False
                                for step in range(1, 25):
                                    chk = i + step
                                    if chk >= n: break
                                    if l[chk] <= sl_p: break
                                    if h[chk] >= price_b:
                                        triggered = True
                                        entry_bar = chk
                                        break
                                if triggered:
                                    outcome = 0; r_val = 0.0
                                    for s in range(1, max_hold):
                                        bar_idx = entry_bar + s
                                        if bar_idx >= n: break
                                        if l[bar_idx] <= sl_p: r_val = -1.0; outcome = -1; break
                                        elif h[bar_idx] >= tp_p: r_val = (reward / risk); outcome = 1; break
                                    if outcome == 0 and entry_bar + max_hold < n:
                                        r_val = (c[entry_bar + max_hold] - price_b) / risk
                                    trades.append({"dir": "LONG", "r": r_val, "risk": risk, "reward": reward, "rr": reward/risk, "year": int(str(dates[entry_bar])[:4])})

            # Bearish N pattern
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

                            if risk > 0.80 and reward > 0.40:
                                triggered = False
                                for step in range(1, 25):
                                    chk = i + step
                                    if chk >= n: break
                                    if h[chk] >= sl_p: break
                                    if l[chk] <= price_b:
                                        triggered = True
                                        entry_bar = chk
                                        break
                                if triggered:
                                    outcome = 0; r_val = 0.0
                                    for s in range(1, max_hold):
                                        bar_idx = entry_bar + s
                                        if bar_idx >= n: break
                                        if h[bar_idx] + 0.38 >= sl_p: r_val = -1.0; outcome = -1; break
                                        elif l[bar_idx] + 0.38 <= tp_p: r_val = (reward / risk); outcome = 1; break
                                    if outcome == 0 and entry_bar + max_hold < n:
                                        r_val = (price_b - c[entry_bar + max_hold]) / risk
                                    trades.append({"dir": "SHORT", "r": r_val, "risk": risk, "reward": reward, "rr": reward/risk, "year": int(str(dates[entry_bar])[:4])})

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
            avg_rr = float(np.mean([t["rr"] for t in trades]))
        else:
            pf = wr = exp = mdd = tot_r = avg_rr = 0.0

        per_week = n_t / (12 * 52)
        print(f"\n[{tf_name} RAW] Swing Strength={swing_k}")
        print(f"Total Trade : {n_t:,} (Rata-rata {per_week:.1f} trade/minggu | {n_t/144:.1f} trade/bulan)")
        print(f"Win Rate    : {wr:.2f}% | Rata-rata RR: {avg_rr:.2f}:1")
        print(f"Profit Factor: {pf:.3f} | Net Exp: {exp:+.4f}R")
        print(f"Total Net R : {tot_r:+.1f}R | Max Drawdown: {mdd:.1f}R")

        # Long vs Short
        longs = [t["r"] for t in trades if t["dir"] == "LONG"]
        shorts = [t["r"] for t in trades if t["dir"] == "SHORT"]
        pf_l = sum(x for x in longs if x > 0) / abs(sum(x for x in longs if x < 0)) if abs(sum(x for x in longs if x < 0)) > 0 else 0
        pf_s = sum(x for x in shorts if x > 0) / abs(sum(x for x in shorts if x < 0)) if abs(sum(x for x in shorts if x < 0)) > 0 else 0
        print(f"Sisi LONG   : N={len(longs):<4} | WR={sum(1 for x in longs if x>0)/len(longs)*100:.1f}% | PF={pf_l:.2f} | Net R={sum(longs):+.1f}R")
        print(f"Sisi SHORT  : N={len(shorts):<4} | WR={sum(1 for x in shorts if x>0)/len(shorts)*100:.1f}% | PF={pf_s:.2f} | Net R={sum(shorts):+.1f}R")

        # Filter RR >= 0.80
        sub_80 = [t for t in trades if t["rr"] >= 0.80]
        r_80 = np.array([t["r"] for t in sub_80])
        if len(r_80) > 0:
            gw8 = sum(x for x in r_80 if x > 0); gl8 = abs(sum(x for x in r_80 if x < 0))
            pf8 = gw8 / gl8 if gl8 > 0 else 99.0
            wr8 = sum(1 for x in r_80 if x > 0) / len(r_80) * 100.0
            exp8 = float(np.mean(r_80))
            cum8 = np.cumsum(r_80)
            mdd8 = float(np.max(np.maximum.accumulate(cum8) - cum8))
            print(f"[{tf_name} FILTER RR >= 0.80]: N={len(r_80):,} ({len(r_80)/(12*52):.1f}/mgg) | WR={wr8:.1f}% | PF={pf8:.2f} | Exp={exp8:+.4f}R | Tot R={cum8[-1]:+.1f}R | MDD={mdd8:.1f}R")

    print("\n" + "=" * 80)
    print("HASIL PENGUJIAN POLA N HOSODA: M15 & M30 (2015 - 2026)")
    print("=" * 80)
    evaluate_n_pattern(m30, "M30", swing_k=3)
    evaluate_n_pattern(m15, "M15", swing_k=3)

if __name__ == "__main__":
    run_m15_m30_test()
