#!/usr/bin/env python3
"""
Cross-Check Strategi Juara (#1 Pola N Baku + Expired Rule) di M5, M15, M30.
Dataset: 4.18M bars XAUUSD_M1.parquet (2015-2026).
Friction: Spread $0.38 + Komisi $0.07 + Slippage $0.05.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"

def cross_check_lower_timeframes():
    print("=== Loading M1 Data & Resampling to M5, M15, M30, and H1 ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (5 * 60 * 1000) * (5 * 60 * 1000)).alias("m5_ts"),
        (pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"),
        (pl.col("timestamp") // (30 * 60 * 1000) * (30 * 60 * 1000)).alias("m30_ts"),
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
    )
    df = df.filter(~pl.col("hour").is_between(21, 23))

    def evaluate_tf(ts_col, tf_name, min_span, max_span, swing_k=3, target_rr=1.5):
        bars_df = df.group_by(ts_col).agg([
            pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
            pl.col("year").first(), pl.col("date").first()
        ]).sort(ts_col)

        o = bars_df["open"].to_numpy(); h = bars_df["high"].to_numpy(); l = bars_df["low"].to_numpy(); c = bars_df["close"].to_numpy()
        dates = bars_df["date"].to_numpy(); n = len(o)

        is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
        for i in range(swing_k, n - swing_k):
            if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
            if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

        trades = []
        last_sw_l = []; last_sw_h = []
        trade_exit_bar = 0

        # Holding max in bars (for H1 = 40h, for M30 = 40 bars = 20h, for M15 = 40 bars = 10h, for M5 = 40 bars = 3.3h)
        max_hold = 40

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

                # Span filter scaled by timeframe
                if not (min_span <= span <= max_span):
                    continue

                rel_pos = (c[i] - val_l) / span
                allow_buy = rel_pos >= 0.35
                allow_sell = rel_pos <= 0.65

                risk_buy = (val_h + 0.38 + 0.05) - (val_l - 0.50)
                tp_buy = (val_h + 0.38 + 0.05) + (target_rr * risk_buy)

                risk_sell = (val_h + 0.50) - (val_l - 0.05)
                tp_sell = (val_l - 0.05) - (target_rr * risk_sell)

                buy_active = allow_buy
                sell_active = allow_sell
                triggered = False
                order_side = None
                fill_bar = -1

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
                            if l[s] <= (val_l - 0.50):
                                r_val = -1.0; outcome = -1; break
                            elif h[s] >= tp_buy:
                                r_val = target_rr; outcome = 1; break
                        if outcome == 0 and fill_bar + max_hold < n:
                            r_val = (c[fill_bar + max_hold] - (val_h + 0.38 + 0.05)) / risk_buy
                    else: # SELL
                        for s in range(fill_bar + 1, min(n, fill_bar + max_hold)):
                            exit_idx = s
                            if h[s] + 0.38 >= (val_h + 0.50):
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
        print(f"\n[{tf_name}] Bars={n:,} | Trades={n_t:,} ({per_month:.1f}/bln, {per_week:.1f}/mgg)")
        print(f"WR: {wr:.2f}% | PF: {pf:.3f} | Net Exp: {exp:+.4f}R | Total Net: {cum[-1]:+.1f}R | MDD: {mdd:.1f}R")

        longs = [t["r"] for t in trades if t["side"] == "BUY"]
        shorts = [t["r"] for t in trades if t["side"] == "SELL"]
        pf_l = sum(x for x in longs if x > 0) / abs(sum(x for x in longs if x < 0)) if abs(sum(x for x in longs if x < 0)) > 0 else 0
        pf_s = sum(x for x in shorts if x > 0) / abs(sum(x for x in shorts if x < 0)) if abs(sum(x for x in shorts if x < 0)) > 0 else 0
        print(f"  BUY : N={len(longs):<4} | WR={sum(1 for x in longs if x>0)/len(longs)*100:.1f}% | PF={pf_l:.2f} | Net R={sum(longs):+.1f}R")
        print(f"  SELL: N={len(shorts):<4} | WR={sum(1 for x in shorts if x>0)/len(shorts)*100:.1f}% | PF={pf_s:.2f} | Net R={sum(shorts):+.1f}R")

    print("\n" + "=" * 75)
    print("HASIL CROSS-CHECK LINTAS TIMEFRAME: M5, M15, M30, H1 (RR 1:1.5)")
    print("=" * 75)
    # H1: Range span $15 - $35
    evaluate_tf("h1_ts", "H1 (Baseline)", min_span=15.0, max_span=35.0, target_rr=1.5)
    # M30: Range span $8 - $20
    evaluate_tf("m30_ts", "M30", min_span=8.0, max_span=20.0, target_rr=1.5)
    # M15: Range span $5 - $15
    evaluate_tf("m15_ts", "M15", min_span=5.0, max_span=15.0, target_rr=1.5)
    # M5: Range span $3 - $10
    evaluate_tf("m5_ts", "M5", min_span=3.0, max_span=10.0, target_rr=1.5)

if __name__ == "__main__":
    cross_check_lower_timeframes()
