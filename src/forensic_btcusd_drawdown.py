#!/usr/bin/env python3
"""
Forensic Breakdown Penyebab Max Drawdown BTCUSD di M1 (-102.3 R) dan M5 (-18.6 R).
Target Analisis:
1. Menemukan tanggal persis dimulainya dan berakhirnya fase Max Drawdown.
2. Memeriksa kondisi makro/volatilitas pada periode tersebut (ATR, spread relative, market regime).
3. Mengidentifikasi apakah kekalahan disebabkan oleh:
   - False breakout berulang (choppy/sideways sempit).
   - Flash crash / gap eksekusi.
   - Pergeseran volatilitas nominal Bitcoin.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

BTC_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/BTCUSD_M1.parquet"

def analyze_drawdown_causes():
    print("=== Loading BTCUSD M1 Master Dataset for Drawdown Forensic ===")
    df = pl.read_parquet(BTC_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (5 * 60 * 1000) * (5 * 60 * 1000)).alias("m5_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
    )

    def diagnose_tf(bars_df, tf_name, min_span, max_span, swing_k, target_rr, max_hold):
        o = bars_df["open"].to_numpy(); h = bars_df["high"].to_numpy()
        l = bars_df["low"].to_numpy(); c = bars_df["close"].to_numpy()
        dates = bars_df["date"].to_numpy()
        n = len(o)

        is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
        for i in range(swing_k, n - swing_k):
            if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
            if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

        spread = 15.0; slippage = 5.0; comm = 5.0; buffer = 5.0
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
                        "date": str(dates[fill_bar]),
                        "price": (val_h + val_l) / 2.0,
                        "span": span,
                        "side": order_side
                    })

        r_all = np.array([t["r"] for t in trades])
        cum = np.cumsum(r_all)
        peaks = np.maximum.accumulate(cum)
        dd = peaks - cum
        max_dd_idx = np.argmax(dd)
        peak_idx = np.argmax(cum[:max_dd_idx+1])
        mdd_val = dd[max_dd_idx]

        t_start = trades[peak_idx]["date"]
        t_end = trades[max_dd_idx]["date"]
        p_avg = np.mean([trades[k]["price"] for k in range(peak_idx, max_dd_idx+1)])
        loss_streak_trades = trades[peak_idx:max_dd_idx+1]
        n_loss_period = len(loss_streak_trades)
        wr_in_dd = sum(1 for x in loss_streak_trades if x["r"] > 0) / n_loss_period * 100.0

        print(f"\n{'='*75}\nDIAGNOSIS FORENSIK DRAWDOWN: {tf_name}\n{'='*75}")
        print(f"Max Drawdown Terbesar        : -{mdd_val:.1f} R")
        print(f"Periode Terjadinya Drawdown  : {t_start} s/d {t_end}")
        print(f"Jumlah Trade Selama Drawdown : {n_loss_period:,} trade")
        print(f"Win Rate di Periode Tersebut : {wr_in_dd:.1f}%")
        print(f"Rata-rata Harga Bitcoin Saat Itu: ${p_avg:,.1f}")

        # Breakdown per tahun untuk melihat pola konsistensi
        years = sorted(list(set([t["date"][:4] for t in trades])))
        print(f"\nPerforma Tahunan {tf_name}:")
        for yr in years:
            sub = [t["r"] for t in trades if t["date"][:4] == yr]
            s_arr = np.array(sub)
            gw = sum(x for x in s_arr if x > 0); gl = abs(sum(x for x in s_arr if x < 0))
            pf_yr = gw / gl if gl > 0 else 99.0
            wr_yr = sum(1 for x in s_arr if x > 0) / len(s_arr) * 100.0
            tot_yr = sum(s_arr)
            c_yr = np.cumsum(s_arr)
            dd_yr = np.max(np.maximum.accumulate(c_yr) - c_yr)
            print(f"Tahun {yr}: N={len(s_arr):<5} | WR={wr_yr:5.1f}% | PF={pf_yr:5.2f} | Cuan={tot_yr:+7.1f}R | MDD={dd_yr:4.1f}R")

    # Diagnosa M1
    diagnose_tf(df, "BTCUSD M1", min_span=40.0, max_span=180.0, swing_k=5, target_rr=1.0, max_hold=60)

    # Diagnosa M5
    m5 = df.group_by("m5_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("date").first()
    ]).sort("m5_ts")
    diagnose_tf(m5, "BTCUSD M5", min_span=80.0, max_span=300.0, swing_k=3, target_rr=1.5, max_hold=40)

if __name__ == "__main__":
    analyze_drawdown_causes()
