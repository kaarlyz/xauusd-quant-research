#!/usr/bin/env python3
"""
Analisis Fraktal Multi-Timeframe:
Dampak Rezim Tren/Sideways Timeframe Lebih Besar (H4 & H1) terhadap Performa & Drawdown M5.
Target Analisis:
1. Rekonstruksi rezim pasar di H4 dan H1:
   - Strong Trend: EMA20 vs EMA50 slope & directional alignment + ADX/ATR expansion.
   - Squeeze / Sideways Range: ADX rendah / range sempit H4 (inside bar / consolidation).
2. Periksa performa trade M5 saat:
   A. M5 searah dengan Tren H4 (Aligned Trend).
   B. M5 melawan Tren H4 (Counter Trend).
   C. M5 dieksekusi saat H4 sedang Konsolidasi Sempit (H4 Sideways Regime).
3. Evaluasi fase Drawdown Juni 2026: Apakah H4 saat itu sedang sideways sempit?
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

BTC_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/BTCUSD_M1.parquet"

def analyze_trend_regime_impact():
    print("=== Loading Dataset & Resampling Multi-Timeframe (H4, H1, M5) ===")
    df = pl.read_parquet(BTC_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (5 * 60 * 1000) * (5 * 60 * 1000)).alias("m5_ts"),
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        (pl.col("timestamp") // (4 * 60 * 60 * 1000) * (4 * 60 * 60 * 1000)).alias("h4_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    # 1. Bangun H4 Bars & Hitung Trend Regime
    h4 = df.group_by("h4_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
    ]).sort("h4_ts")

    h4_c = h4["close"].to_numpy()
    h4_h = h4["high"].to_numpy()
    h4_l = h4["low"].to_numpy()
    h4_ts = h4["h4_ts"].to_numpy()
    n_h4 = len(h4_c)

    # EMA 20 & EMA 50 on H4
    def calc_ema(arr, span):
        alpha = 2.0 / (span + 1.0)
        out = np.empty_like(arr)
        out[0] = arr[0]
        for t in range(1, len(arr)):
            out[t] = alpha * arr[t] + (1 - alpha) * out[t-1]
        return out

    ema20_h4 = calc_ema(h4_c, 20)
    ema50_h4 = calc_ema(h4_c, 50)

    # ATR 14 on H4
    tr_h4 = np.maximum(h4_h - h4_l, np.maximum(np.abs(h4_h - np.roll(h4_c, 1)), np.abs(h4_l - np.roll(h4_c, 1))))
    atr14_h4 = calc_ema(tr_h4, 14)
    # Volatility Ratio = ATR14 / Rolling Mean ATR14 (50 bars)
    atr50_base = calc_ema(atr14_h4, 50)
    vol_ratio_h4 = atr14_h4 / (atr50_base + 1e-6)

    # H4 Regime:
    # Bullish Trend: EMA20 > EMA50 dan Close > EMA20
    # Bearish Trend: EMA20 < EMA50 dan Close < EMA20
    # Sideways / Choppy: Volatility Ratio < 0.85 ATAU EMA20 & EMA50 berdempetan (|EMA20 - EMA50| / Close < 0.005)
    h4_regimes = np.empty(n_h4, dtype=object)
    for i in range(n_h4):
        ema_diff_pct = abs(ema20_h4[i] - ema50_h4[i]) / h4_c[i]
        if vol_ratio_h4[i] < 0.80 or ema_diff_pct < 0.006:
            h4_regimes[i] = "SIDEWAYS"
        elif ema20_h4[i] > ema50_h4[i] and h4_c[i] >= ema20_h4[i]:
            h4_regimes[i] = "BULL_TREND"
        elif ema20_h4[i] < ema50_h4[i] and h4_c[i] <= ema20_h4[i]:
            h4_regimes[i] = "BEAR_TREND"
        else:
            h4_regimes[i] = "SIDEWAYS"

    h4_dict = {h4_ts[i]: h4_regimes[i] for i in range(n_h4)}

    # 2. Bangun M5 Bars & Jalankan Strategi Pola N
    m5 = df.group_by("m5_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("date").first()
    ]).sort("m5_ts")

    o5 = m5["open"].to_numpy(); h5 = m5["high"].to_numpy()
    l5 = m5["low"].to_numpy(); c5 = m5["close"].to_numpy()
    dates5 = m5["date"].to_numpy(); ts5 = m5["m5_ts"].to_numpy()
    n5 = len(o5)

    swing_k = 3
    is_sw_h = np.zeros(n5, dtype=bool); is_sw_l = np.zeros(n5, dtype=bool)
    for i in range(swing_k, n5 - swing_k):
        if h5[i] == np.max(h5[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
        if l5[i] == np.min(l5[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

    spread = 15.0; slippage = 5.0; comm = 5.0; buffer = 5.0
    min_span = 80.0; max_span = 300.0; target_rr = 1.5; max_hold = 40

    trades = []
    last_sw_l = []; last_sw_h = []
    trade_exit_bar = 0

    for i in range(swing_k, n5 - max_hold - 5):
        if is_sw_l[i]: last_sw_l.append((i, l5[i]))
        if is_sw_h[i]: last_sw_h.append((i, h5[i]))
        if len(last_sw_l) > 10: last_sw_l.pop(0)
        if len(last_sw_h) > 10: last_sw_h.pop(0)

        if i < trade_exit_bar: continue

        if len(last_sw_h) >= 2 and len(last_sw_l) >= 2:
            idx_h, val_h = last_sw_h[-1]; idx_l, val_l = last_sw_l[-1]
            span = val_h - val_l
            if not (min_span <= span <= max_span): continue

            rel_pos = (c5[i] - val_l) / span
            allow_buy = rel_pos >= 0.35; allow_sell = rel_pos <= 0.65

            risk_buy = (val_h + spread + slippage) - (val_l - buffer - slippage) + comm
            tp_buy = (val_h + spread + slippage) + (target_rr * risk_buy)

            risk_sell = (val_h + buffer + spread + slippage) - (val_l - slippage) + comm
            tp_sell = (val_l - slippage) - (target_rr * risk_sell)

            buy_active = allow_buy; sell_active = allow_sell
            triggered = False; order_side = None; fill_bar = -1

            for step in range(1, 16):
                chk = i + step
                if chk >= n5: break
                if (is_sw_h[chk] and chk > idx_h) or (is_sw_l[chk] and chk > idx_l): break
                if buy_active and h5[chk] >= val_h:
                    triggered = True; order_side = "BUY"; fill_bar = chk; break
                if sell_active and l5[chk] <= val_l:
                    triggered = True; order_side = "SELL"; fill_bar = chk; break

            if triggered:
                outcome = 0; r_val = 0.0; exit_idx = fill_bar
                if order_side == "BUY":
                    sl_exec = val_l - buffer - slippage
                    for s in range(fill_bar + 1, min(n5, fill_bar + max_hold)):
                        exit_idx = s
                        if l5[s] <= (val_l - buffer):
                            actual_sl = min(sl_exec, o5[s] - slippage if o5[s] < sl_exec else sl_exec)
                            r_val = - ((val_h + spread + slippage) - actual_sl + comm) / risk_buy
                            outcome = -1; break
                        elif h5[s] >= tp_buy:
                            r_val = target_rr; outcome = 1; break
                    if outcome == 0 and fill_bar + max_hold < n5:
                        r_val = (c5[fill_bar + max_hold] - (val_h + spread + slippage) - comm) / risk_buy
                else:
                    sl_exec = val_h + buffer + spread + slippage
                    for s in range(fill_bar + 1, min(n5, fill_bar + max_hold)):
                        exit_idx = s
                        if h5[s] + spread >= (val_h + buffer + spread):
                            actual_sl = max(sl_exec, (o5[s] + spread + slippage) if (o5[s] + spread) > sl_exec else sl_exec)
                            r_val = - (actual_sl - (val_l - slippage) + comm) / risk_sell
                            outcome = -1; break
                        elif l5[s] + spread <= tp_sell:
                            r_val = target_rr; outcome = 1; break
                    if outcome == 0 and fill_bar + max_hold < n5:
                        r_val = ((val_l - slippage) - (c5[fill_bar + max_hold] + spread) - comm) / risk_sell

                trade_exit_bar = exit_idx

                # Cari H4 timestamp dari bar entry M5
                entry_ts = ts5[fill_bar]
                h4_aligned_ts = (entry_ts // (4 * 3600 * 1000)) * (4 * 3600 * 1000)
                h4_st = h4_dict.get(h4_aligned_ts, "SIDEWAYS")

                # Hubungan Arah M5 vs H4
                if h4_st == "SIDEWAYS":
                    rel_type = "H4_SIDEWAYS"
                elif (order_side == "BUY" and h4_st == "BULL_TREND") or (order_side == "SELL" and h4_st == "BEAR_TREND"):
                    rel_type = "ALIGNED_WITH_H4_TREND"
                else:
                    rel_type = "COUNTER_H4_TREND"

                trades.append({
                    "r": r_val,
                    "date": str(dates5[fill_bar]),
                    "side": order_side,
                    "h4_state": h4_st,
                    "rel_type": rel_type
                })

    print(f"\n{'='*75}\nHASIL KORELASI REZIM H4 TERHADAP EKSEKUSI M5 (17.986 TRADES)\n{'='*75}")
    for cat in ["ALIGNED_WITH_H4_TREND", "COUNTER_H4_TREND", "H4_SIDEWAYS"]:
        sub = [t for t in trades if t["rel_type"] == cat]
        r_sub = np.array([t["r"] for t in sub])
        n_c = len(r_sub)
        if n_c > 0:
            gw = sum(x for x in r_sub if x > 0); gl = abs(sum(x for x in r_sub if x < 0))
            pf = gw / gl if gl > 0 else 99.0
            wr = sum(1 for x in r_sub if x > 0) / n_c * 100.0
            exp = float(np.mean(r_sub))
            cum = np.cumsum(r_sub)
            mdd = float(np.max(np.maximum.accumulate(cum) - cum))
            print(f"Kategori: {cat:<24} | N={n_c:<6,} ({n_c/len(trades)*100:4.1f}%) | WR={wr:5.2f}% | PF={pf:5.3f} | Exp={exp:+.4f}R | Tot R={cum[-1]:+8.1f}R | MDD={mdd:4.1f}R")

    # Analisis Kasus Spesifik Drawdown Juni 2026
    print(f"\n{'='*75}\nBEDAH SPESIFIK: PERIODE DRAWDOWN 16 - 22 JUNI 2026\n{'='*75}")
    dd_trades = [t for t in trades if "2026-06-16" <= t["date"] <= "2026-06-22"]
    print(f"Total Trade di Masa Drawdown: {len(dd_trades)} trade")
    for cat in ["ALIGNED_WITH_H4_TREND", "COUNTER_H4_TREND", "H4_SIDEWAYS"]:
        c_sub = [t for t in dd_trades if t["rel_type"] == cat]
        print(f"  - Muncul saat {cat:<24}: {len(c_sub)} trade ({len(c_sub)/len(dd_trades)*100:.1f}%)")

if __name__ == "__main__":
    analyze_trend_regime_impact()
