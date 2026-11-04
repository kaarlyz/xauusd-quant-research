#!/usr/bin/env python3
"""
Backtest Komprehensif Pola N Baku + Expired Rule pada BTCUSD (Bitcoin / US Dollar).
Dataset: 4.56M bars BTCUSD_M1.parquet (2017 - 2026 / 9.5 Tahun).
Friksi CFD Kripto Baku (ECN):
- Spread median BTC: $12.00 (sekitar 0.02% - 0.05% harga).
- Slippage Stop order: $5.00.
- Komisi: 0.05% nominal round-turn ($0.05 per $100 value).
Timeframe diuji: H4, H1, M30, M15, M5.
Target RR: 1:1.50
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

BTC_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/BTCUSD_M1.parquet"

def run_btcusd_backtest():
    print("=" * 80)
    print("BACKTEST POLA N BAKU PADA BTCUSD (BITCOIN / 2017 - 2026 / 9.5 TAHUN)")
    print("=" * 80)

    df = pl.read_parquet(BTC_PARQUET).sort("timestamp")
    print(f"Total BTCUSD M1 Bars: {len(df):,}")

    df = df.with_columns(
        (pl.col("timestamp") // (5 * 60 * 1000) * (5 * 60 * 1000)).alias("m5_ts"),
        (pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"),
        (pl.col("timestamp") // (30 * 60 * 1000) * (30 * 60 * 1000)).alias("m30_ts"),
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        (pl.col("timestamp") // (4 * 60 * 60 * 1000) * (4 * 60 * 60 * 1000)).alias("h4_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    def evaluate_btc(bars_df, tf_name, min_span, max_span, swing_k=3, target_rr=1.5, max_hold=40,
                     spread=12.0, comm=5.0, slippage=5.0):
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
        trade_exit_bar = 0
        buffer = 5.0 # $5 buffer

        for i in range(swing_k, n - max_hold - 5):
            if is_sw_l[i]: last_sw_l.append((i, l[i]))
            if is_sw_h[i]: last_sw_h.append((i, h[i]))
            if len(last_sw_l) > 10: last_sw_l.pop(0)
            if len(last_sw_h) > 10: last_sw_h.pop(0)

            if i < trade_exit_bar: continue

            if len(last_sw_h) >= 2 and len(last_sw_l) >= 2:
                idx_h, val_h = last_sw_h[-1]
                idx_l, val_l = last_sw_l[-1]
                span = val_h - val_l
                if not (min_span <= span <= max_span): continue

                rel_pos = (c[i] - val_l) / span
                allow_buy = rel_pos >= 0.35
                allow_sell = rel_pos <= 0.65

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
                    else: # SELL
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

        tot_months = 9.5 * 12
        per_month = n_t / tot_months
        per_week = n_t / (9.5 * 52)

        longs = [t["r"] for t in trades if t["side"] == "BUY"]
        shorts = [t["r"] for t in trades if t["side"] == "SELL"]
        pf_l = sum(x for x in longs if x > 0) / abs(sum(x for x in longs if x < 0)) if abs(sum(x for x in longs if x < 0)) > 0 else 0
        pf_s = sum(x for x in shorts if x > 0) / abs(sum(x for x in shorts if x < 0)) if abs(sum(x for x in shorts if x < 0)) > 0 else 0

        print(f"\n[BTCUSD {tf_name}] 9.5 Tahun (2017-2026) | Trades={n_t:,} ({per_month:.1f}/bln | {per_week:.1f}/mgg)")
        print(f"  Win Rate: {wr:.2f}% (BEP: 40.0%) | Profit Factor: {pf:.3f} | Net Exp: {exp:+.4f}R")
        print(f"  Total Net PnL: {cum[-1]:+.1f}R | Max Drawdown: {mdd:.1f}R")
        print(f"  BUY : N={len(longs):<5} | WR={sum(1 for x in longs if x>0)/len(longs)*100:.1f}% | PF={pf_l:.2f} | Net R={sum(longs):+.1f}R")
        print(f"  SELL: N={len(shorts):<5} | WR={sum(1 for x in shorts if x>0)/len(shorts)*100:.1f}% | PF={pf_s:.2f} | Net R={sum(shorts):+.1f}R")

    # Timeframe resamplings
    # Bitcoin span rentang harga:
    # H4: $1,500 - $6,000
    # H1: $600 - $2,500
    # M30: $300 - $1,200
    # M15: $150 - $600
    # M5: $80 - $300

    h4 = df.group_by("h4_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("h4_ts")
    evaluate_btc(h4, "H4", min_span=1500.0, max_span=6000.0, swing_k=2, max_hold=30)

    h1 = df.group_by("h1_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("h1_ts")
    evaluate_btc(h1, "H1", min_span=600.0, max_span=2500.0, swing_k=3, max_hold=40)

    m30 = df.group_by("m30_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("m30_ts")
    evaluate_btc(m30, "M30", min_span=300.0, max_span=1200.0, swing_k=3, max_hold=40)

    m15 = df.group_by("m15_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("m15_ts")
    evaluate_btc(m15, "M15", min_span=150.0, max_span=600.0, swing_k=3, max_hold=40)

    m5 = df.group_by("m5_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("m5_ts")
    evaluate_btc(m5, "M5", min_span=80.0, max_span=300.0, swing_k=3, max_hold=40)

if __name__ == "__main__":
    run_btcusd_backtest()
