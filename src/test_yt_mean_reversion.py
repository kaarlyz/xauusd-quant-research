#!/usr/bin/env python3
"""
Bedah Kuantitatif Video YouTube: wsXu2Xr1nQc
"70% Win Rate Gold Trading Strategy (Mean Reversion to 50% Equilibrium)"

Aturan Baku Video yang Diterjemahkan:
1. Timeframe Operasi: M1 / M5 (Video memakai replay bar M1/M5 sesi Asia - London).
2. Range & High-Volume Extension:
   - Identifikasi konsolidasi/range lokal (lookback 30-60 menit).
   - Terjadi "Volume Extension": dorongan cepat menembus range high/low tanpa koreksi.
3. Entry Rule:
   - Short: Saat harga menembus High range dengan volume tinggi, pasang SL di atas pucuk ekstrem, target TP di 50% dari pergerakan dorongan (Mean Reversion).
   - Long: Saat harga menembus Low range dengan volume tinggi, pasang SL di bawah dasar ekstrem, target TP di 50% dari pergerakan dorongan.
4. Rasio Target RR:
   - Sering kali 0.5R s/d 1.0R (karena menargetkan 50% retrace, sementara SL dipasang lebar "memberi ruang napas").
5. Uji pada Master M1 Parquet (2015-2024 / 2021-2024 In-Sample) dengan potongan friksi ECN riil ($0.38 spread + $0.07 komisi + slippage).
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import numpy as np
import polars as pl
from fast_phase2_discovery import load_data_and_features, calculate_detailed_metrics

def test_youtube_strategy():
    print("=== Loading Data and Testing YouTube Strategy (wsXu2Xr1nQc) ===")
    df = load_data_and_features()
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    v = df["volume"].to_numpy()
    dates = df["date"].to_numpy()
    ts = df["timestamp"].to_numpy()
    hours = df["hour"].to_numpy()
    atr14 = df["atr14"].to_numpy()
    n = len(o)

    # Precompute range boundaries for 30 and 60 minutes
    # High volume extension: volume >= 1.5x rolling mean, displacement >= 1.0 ATR
    v_mean = df["v_mean20"].to_numpy()
    rvol = np.where(v_mean > 0, v / v_mean, 1.0)

    # Test 3 variations of his rules:
    # Var A: RR = 0.50 : 1 (Target 50% retrace with wide SL)
    # Var B: RR = 0.75 : 1 (Moderate retrace)
    # Var C: RR = 1.00 : 1 (1:1 as he mentioned on trade #4)

    results = []

    for target_rr in [0.50, 0.75, 1.00]:
        for win_bars in [30, 60]:
            h_box = df[f"h_max_30"].to_numpy() if win_bars == 30 else df[f"h_max_45"].to_numpy()
            l_box = df[f"l_min_30"].to_numpy() if win_bars == 30 else df[f"l_min_45"].to_numpy()

            trades = []
            last_exit_idx = -1

            for i in range(win_bars + 10, n - 35):
                if i <= last_exit_idx: continue
                # Sesi Asia & London: jam 00:00 s/d 16:00 UTC (sesuai pengakuan kreator di video)
                if not (0 <= hours[i] <= 16): continue

                cur_atr = atr14[i]
                if cur_atr < 0.30: continue

                # Condition 1: Penetration of range extreme with high volume
                # Long: Low pierces below l_box, closes back above or shows lower wick
                pierce_low = (l[i] <= l_box[i] - 0.30 * cur_atr)
                pierce_high = (h[i] >= h_box[i] + 0.30 * cur_atr)
                vol_high = (rvol[i] >= 1.30)

                if not vol_high: continue

                # Case Long Reversal (Beli di batas bawah)
                if pierce_low and c[i] > l[i] + 0.25 * (h[i] - l[i]):
                    exec_bar = i + 1
                    entry_fill = o[exec_bar] + 0.380 + 0.050 # Buy at Ask + Slip
                    # Stop loss: "diberi ruang napas" di bawah low ekstrem
                    nominal_sl = l[i] - 0.50
                    stop_dist = entry_fill - nominal_sl
                    if not (0.80 <= stop_dist <= 15.0): continue

                    tp_price = entry_fill + (target_rr * stop_dist)
                    exit_fill = c[exec_bar + 15] # max holding 15 mins
                    exit_reason = "TIMEOUT"
                    exit_idx = exec_bar + 15

                    for b in range(exec_bar, exec_bar + 16):
                        if l[b] <= nominal_sl:
                            exit_fill = nominal_sl - 0.050; exit_reason = "SL"; exit_idx = b; break
                        elif h[b] >= tp_price:
                            exit_fill = tp_price; exit_reason = "TP"; exit_idx = b; break

                    gross_pnl = (exit_fill - entry_fill) * (7.50 / (stop_dist * 100)) * 100
                    comm = 0.070 * (7.50 / (stop_dist * 100)) * 100
                    net_pnl = gross_pnl - comm
                    realized_r = net_pnl / 7.50
                    last_exit_idx = exit_idx
                    trades.append({"r": realized_r, "year": int(str(dates[exec_bar])[:4])})

                # Case Short Reversal (Jual di batas atas)
                elif pierce_high and c[i] < h[i] - 0.25 * (h[i] - l[i]):
                    exec_bar = i + 1
                    entry_fill = o[exec_bar] - 0.050 # Sell at Bid - Slip
                    nominal_sl = h[i] + 0.50
                    stop_dist = nominal_sl - entry_fill
                    if not (0.80 <= stop_dist <= 15.0): continue

                    tp_price = entry_fill - (target_rr * stop_dist)
                    exit_fill = c[exec_bar + 15] + 0.380
                    exit_reason = "TIMEOUT"
                    exit_idx = exec_bar + 15

                    for b in range(exec_bar, exec_bar + 16):
                        if h[b] + 0.380 >= nominal_sl:
                            exit_fill = nominal_sl + 0.050; exit_reason = "SL"; exit_idx = b; break
                        elif l[b] + 0.380 <= tp_price:
                            exit_fill = tp_price; exit_reason = "TP"; exit_idx = b; break

                    gross_pnl = (entry_fill - exit_fill) * (7.50 / (stop_dist * 100)) * 100
                    comm = 0.070 * (7.50 / (stop_dist * 100)) * 100
                    net_pnl = gross_pnl - comm
                    realized_r = net_pnl / 7.50
                    last_exit_idx = exit_idx
                    trades.append({"r": realized_r, "year": int(str(dates[exec_bar])[:4])})

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
                pf = 0; wr = 0; exp = 0; mdd = 0; tot_r = 0

            # Filter validation era (2024-2025)
            val_tr = [t["r"] for t in trades if t["year"] == 2024]
            r_val = np.array(val_tr)
            if len(r_val) > 0:
                gw_v = sum(x for x in r_val if x > 0); gl_v = abs(sum(x for x in r_val if x < 0))
                pf_v = gw_v / gl_v if gl_v > 0 else 99.0
                wr_v = sum(1 for x in r_val if x > 0) / len(r_val) * 100.0
                exp_v = float(np.mean(r_val))
            else:
                pf_v = 0; wr_v = 0; exp_v = 0

            print(f"Window={win_bars}m | Target RR={target_rr:.2f} | 10y Trades={n_t:<5} | 10y WR={wr:4.1f}% | 10y PF={pf:4.2f} | 10y Exp={exp:+.4f}R | 2024 Val WR={wr_v:4.1f}% | 2024 PF={pf_v:4.2f}")

if __name__ == "__main__":
    test_youtube_strategy()
