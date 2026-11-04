#!/usr/bin/env python3
"""
Backtest Pola N Baku pada BTCUSD Khusus Timeframe M1 (9.5 Tahun: 2017 - 2026).
Dataset: 4.56M bars BTCUSD_M1.parquet
Friction: Spread $12.00 + Slippage $5.00 + Komisi $5.00.
Target RR: 1:1.0, 1:1.2, 1:1.5.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

BTC_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/BTCUSD_M1.parquet"

def test_btcusd_m1():
    print("=== Loading 9.5 Years BTCUSD M1 Parquet ===")
    df = pl.read_parquet(BTC_PARQUET).sort("timestamp")
    df = df.with_columns(
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    dates = df["date"].to_numpy()
    n = len(o)
    print(f"Total BTCUSD M1 Bars to evaluate: {n:,}")

    swing_k = 5
    is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
    for i in range(swing_k, n - swing_k):
        if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
        if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

    # Span M1 BTC: $40 - $180
    min_span = 40.0
    max_span = 180.0
    spread = 12.0
    comm = 5.0
    slippage = 5.0
    buffer = 5.0
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
                    trades.append(r_val)

        r_all = np.array(trades)
        n_t = len(r_all)
        gw = sum(x for x in r_all if x > 0); gl = abs(sum(x for x in r_all if x < 0))
        pf = gw / gl if gl > 0 else 99.0
        wr = sum(1 for x in r_all if x > 0) / n_t * 100.0 if n_t > 0 else 0
        exp = float(np.mean(r_all)) if n_t > 0 else 0
        cum = np.cumsum(r_all) if n_t > 0 else [0]
        mdd = float(np.max(np.maximum.accumulate(cum) - cum)) if n_t > 0 else 0
        bep = 100.0 / (1.0 + target_rr)

        print(f"\n[BTCUSD M1 | RR 1:{target_rr:.1f}] Trades={n_t:,} | WR={wr:5.2f}% (BEP {bep:.1f}%) | PF={pf:5.3f} | Net Exp={exp:+.4f}R | Total Net={cum[-1]:+9.1f}R | MDD={mdd:4.1f}R")

if __name__ == "__main__":
    test_btcusd_m1()
