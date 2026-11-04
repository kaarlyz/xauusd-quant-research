#!/usr/bin/env python3
"""
Mencari Tanggal & Jam Persis Periode Drawdown M1 di Era Modern (2021-2026),
serta membedah apa yang terjadi di M15 dan H1 pada saat itu.
Target: Menemukan koordinat tanggal-jam persis agar user bisa buka TradingView langsung.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

BTC_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/BTCUSD_M1.parquet"

def find_m1_drawdown_dates():
    print("=== Analyzing M1 Trades 2021-2026 for Exact Drawdown Windows ===")
    df = pl.read_parquet(BTC_PARQUET).sort("timestamp")
    df = df.filter(pl.col("timestamp") >= 1609459200000) # 2021-2026
    
    o = df["open"].to_numpy(); h = df["high"].to_numpy()
    l = df["low"].to_numpy(); c = df["close"].to_numpy()
    ts = df["timestamp"].to_numpy()
    n = len(o)

    swing_k = 5
    is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
    for i in range(swing_k, n - swing_k):
        if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
        if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

    spread = 15.0; slippage = 5.0; comm = 5.0; buffer = 5.0
    min_span = 40.0; max_span = 180.0; target_rr = 1.0; max_hold = 60

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
                trades.append({
                    "r": r_val,
                    "ts": ts[fill_bar],
                    "side": order_side,
                    "entry_p": val_h if order_side == "BUY" else val_l
                })

    r_all = np.array([t["r"] for t in trades])
    cum = np.cumsum(r_all)
    peaks = np.maximum.accumulate(cum)
    dd = peaks - cum
    max_dd_idx = np.argmax(dd)
    peak_idx = np.argmax(cum[:max_dd_idx+1])
    mdd_val = dd[max_dd_idx]

    import datetime
    t_start = datetime.datetime.fromtimestamp(trades[peak_idx]["ts"] // 1000, tz=datetime.timezone.utc)
    t_end = datetime.datetime.fromtimestamp(trades[max_dd_idx]["ts"] // 1000, tz=datetime.timezone.utc)

    print(f"\n[HASIL KOORDINAT DRAWDOWN TERBESAR M1 (2021-2026)]")
    print(f"Max Drawdown: -{mdd_val:.1f} R")
    print(f"Tanggal Mulai Peak   : {t_start.strftime('%Y-%m-%d %H:%M UTC')} ({t_start + datetime.timedelta(hours=7)} WIB)")
    print(f"Tanggal Akhir Trough : {t_end.strftime('%Y-%m-%d %H:%M UTC')} ({t_end + datetime.timedelta(hours=7)} WIB)")
    print(f"Total Trade di Window Ini: {max_dd_idx - peak_idx + 1} trade")
    print(f"Harga Bitcoin Saat Itu   : ${trades[peak_idx]['entry_p']:,.0f} -> ${trades[max_dd_idx]['entry_p']:,.0f}")

    # Cari juga drawdown terbesar di tahun 2026 berjalan (biar fresh di chart TradingView)
    trades_2026 = [(idx, t) for idx, t in enumerate(trades) if t["ts"] >= 1767225600000]
    if trades_2026:
        r_26 = np.array([t["r"] for _, t in trades_2026])
        cum_26 = np.cumsum(r_26)
        peaks_26 = np.maximum.accumulate(cum_26)
        dd_26 = peaks_26 - cum_26
        mdd_idx_26 = np.argmax(dd_26)
        peak_idx_26 = np.argmax(cum_26[:mdd_idx_26+1])
        mdd_val_26 = dd_26[mdd_idx_26]

        real_p_idx = trades_2026[peak_idx_26][0]
        real_m_idx = trades_2026[mdd_idx_26][0]

        t26_start = datetime.datetime.fromtimestamp(trades[real_p_idx]["ts"] // 1000, tz=datetime.timezone.utc)
        t26_end = datetime.datetime.fromtimestamp(trades[real_m_idx]["ts"] // 1000, tz=datetime.timezone.utc)

        print(f"\n[KOORDINAT DRAWDOWN TERBESAR M1 DI TAHUN 2026 (PALING GAMPANG DICEK DI TRADINGVIEW)]")
        print(f"Max Drawdown 2026   : -{mdd_val_26:.1f} R")
        print(f"Waktu Mulai Drawdown: {t26_start.strftime('%Y-%m-%d %H:%M UTC')} ({t26_start + datetime.timedelta(hours=7)} WIB)")
        print(f"Waktu Dasar Drawdown: {t26_end.strftime('%Y-%m-%d %H:%M UTC')} ({t26_end + datetime.timedelta(hours=7)} WIB)")
        print(f"Rentang Harga       : ${trades[real_p_idx]['entry_p']:,.0f} s/d ${trades[real_m_idx]['entry_p']:,.0f}")


if __name__ == "__main__":
    find_m1_drawdown_dates()

