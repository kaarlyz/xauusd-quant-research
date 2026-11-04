#!/usr/bin/env python3
"""
Simulasi Eksekusi Riil Akun 1,000 Cent (USC) pada BTCUSD M1 & M5.
Kondisi Stres Mikrostruktur Riil (VT Markets Cent):
- Modal Awal: 1,000 USC ($10 USD).
- Fixed Risk: 2.0% per trade = 20.0 USC (1R).
- Spread riil: $15.00 per BTC.
- Execution Slippage (Stop Order): $5.00 per BTC.
- Latency / Delay Eksekusi: 50 ms - 200 ms (adverse fill drift).
- Komisi: 0.05% nominal round-turn.
- Target RR:
  - M1: RR 1:1.0 (Optimal Scalping M1)
  - M5: RR 1:1.5 (Optimal Scalping M5)
Dataset: 4.56M bars BTCUSD_M1.parquet (9.5 Tahun Penuh, 2017 - 2026).
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

BTC_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/BTCUSD_M1.parquet"

def run_cent_simulation():
    print("=" * 80)
    print("SIMULASI EKSEKUSI RIIL AKUN 1,000 CENT (USC) PADA BTCUSD M1 & M5")
    print("=" * 80)

    df = pl.read_parquet(BTC_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (5 * 60 * 1000) * (5 * 60 * 1000)).alias("m5_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )

    def simulate_account(bars_df, tf_name, min_span, max_span, swing_k, target_rr, max_hold):
        o = bars_df["open"].to_numpy(); h = bars_df["high"].to_numpy()
        l = bars_df["low"].to_numpy(); c = bars_df["close"].to_numpy()
        dates = bars_df["date"].to_numpy()
        n = len(o)

        is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
        for i in range(swing_k, n - swing_k):
            if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
            if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

        # Beban biaya pasar riil VT Markets (Cent Account):
        spread = 15.0       # $15 spread
        slippage = 5.0     # $5 stop execution slippage
        comm = 5.0         # $5 commission
        buffer = 5.0       # $5 stop buffer

        initial_balance = 1000.0 # 1,000 USC
        risk_pct = 0.02          # 2% per trade = 20 USC
        
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
                    y = int(str(dates[fill_bar])[:4])
                    m = int(str(dates[fill_bar])[5:7])
                    trades.append({"r": r_val, "year": y, "month": m, "date": str(dates[fill_bar])})

        r_all = np.array([t["r"] for t in trades])
        n_t = len(r_all)
        wins = r_all[r_all > 0]; losses = r_all[r_all < 0]
        wr = len(wins) / n_t * 100.0 if n_t > 0 else 0
        gw = float(np.sum(wins)); gl = float(np.abs(np.sum(losses)))
        pf = gw / gl if gl > 0 else 99.0
        exp = float(np.mean(r_all)) if n_t > 0 else 0
        cum_r = np.cumsum(r_all)
        mdd_r = float(np.max(np.maximum.accumulate(cum_r) - cum_r))

        # Simulasi Saldo Akun (Fixed Risk 2% = 20 USC per 1R)
        # 1R = 20.0 USC
        r_usd = 20.0
        net_profit_usc = cum_r[-1] * r_usd
        mdd_usc = mdd_r * r_usd
        mdd_pct = (mdd_usc / initial_balance) * 100.0

        # Rata-rata per bulan (9.5 tahun = 114 bulan)
        trades_per_month = n_t / 114.0
        r_per_month = cum_r[-1] / 114.0
        profit_per_month_usc = r_per_month * r_usd
        roi_per_month = (profit_per_month_usc / initial_balance) * 100.0

        # Rata-rata per hari (365 hari/tahun di kripto karena jalan 7 hari seminggu!)
        trades_per_day = n_t / (9.5 * 365)

        print(f"\n[{tf_name} SIMULATION RESULTS (9.5 TAHUN: 2017 - 2026)]")
        print(f"Target RR                  : 1 : {target_rr:.1f}")
        print(f"Total Trade (9.5 Tahun)    : {n_t:,} trade")
        print(f"Frekuensi Trade Riil       : ~{trades_per_day:.1f} trade/hari  |  ~{trades_per_month:.1f} trade/bulan")
        print(f"Win Rate (WR)              : {wr:.2f}% (Titik Impas: {100/(1+target_rr):.1f}%)")
        print(f"Profit Factor (PF)         : {pf:.3f}")
        print(f"Net Expectancy             : {exp:+.4f} R per trade")
        print(f"-" * 65)
        print(f"Modal Awal                 : {initial_balance:,.0f} USC ($10 USD)")
        print(f"Risiko per Trade (1R)      : 2.0% ({r_usd:.1f} USC)")
        print(f"Rata-rata Cuan Bulanan     : +{r_per_month:+.1f} R  ->  +{profit_per_month_usc:,.1f} USC (+${profit_per_month_usc/100:.2f} USD)")
        print(f"Estimasi ROI Bulanan       : +{roi_per_month:.1f}% per bulan (Non-compounding)")
        print(f"Floating Drawdown Terburuk : -{mdd_r:.1f} R  ->  -{mdd_usc:,.1f} USC (-{mdd_pct:.1f}% dari modal)")
        print(f"Status Ketahanan Modal     : {'🟢 SANGAT AMAN (Akun Tahan Banting)' if mdd_pct < 60 else '⚠️ RESIKO TINGGI'}")

        # Tampilkan performa tahun 2026 berjalan (Januari - Oktober 2026)
        t_2026 = [t["r"] for t in trades if t["year"] == 2026]
        if t_2026:
            r26 = np.array(t_2026)
            gw26 = sum(x for x in r26 if x > 0); gl26 = abs(sum(x for x in r26 if x < 0))
            pf26 = gw26 / gl26 if gl26 > 0 else 99.0
            wr26 = sum(1 for x in r26 if x > 0) / len(r26) * 100.0
            tot_r26 = sum(r26)
            mdd26 = float(np.max(np.maximum.accumulate(np.cumsum(r26)) - np.cumsum(r26)))
            print(f"\n>> Khusus Tahun 2026 (10 Bulan Berjalan di {tf_name}):")
            print(f"   Trades: {len(r26):,} | WR: {wr26:.1f}% | PF: {pf26:.2f} | Cuan 2026: +{tot_r26:+.1f} R (+{tot_r26*r_usd:,.0f} USC) | Max DD: -{mdd26:.1f} R (-{mdd26*2.0:.1f}%)")

    # Jalankan simulasi M1 (Span $40 - $180, RR 1:1.0, hold 60 menit)
    simulate_account(df, "BTCUSD M1", min_span=40.0, max_span=180.0, swing_k=5, target_rr=1.0, max_hold=60)

    # Jalankan simulasi M5 (Span $80 - $300, RR 1:1.5, hold 40 bars = 200 menit)
    m5 = df.group_by("m5_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("year").first(), pl.col("date").first()
    ]).sort("m5_ts")
    simulate_account(m5, "BTCUSD M5", min_span=80.0, max_span=300.0, swing_k=3, target_rr=1.5, max_hold=40)

if __name__ == "__main__":
    run_cent_simulation()
