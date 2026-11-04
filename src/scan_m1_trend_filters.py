#!/usr/bin/env python3
"""
Analisis Multi-Timeframe Matrix untuk M1 Scalping:
Mencari Pasangan Trend Filter Terbaik untuk Eksekusi M1 (XAUUSD & BTCUSD).
Timeframe yang diuji sebagai filter tren M1:
1. M15 (Rasio 15:1)
2. M30 (Rasio 30:1)
3. H1  (Rasio 60:1)
4. H4  (Rasio 240:1)
Mengukur: Win Rate, Profit Factor, Net Expectancy, dan Pemotongan Max Drawdown di M1.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

BTC_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/BTCUSD_M1.parquet"

def scan_m1_trend_filters():
    print("=== Loading M1 Data & Testing Trend Filters (M15, M30, H1, H4) ===")
    df = pl.read_parquet(BTC_PARQUET).sort("timestamp")
    
    # Ambil era modern 2021-2026 agar representatif
    df = df.filter(pl.col("timestamp") >= 1609459200000)
    df = df.with_columns(
        (pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"),
        (pl.col("timestamp") // (30 * 60 * 1000) * (30 * 60 * 1000)).alias("m30_ts"),
        (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
        (pl.col("timestamp") // (4 * 60 * 60 * 1000) * (4 * 60 * 60 * 1000)).alias("h4_ts"),
    )

    def calc_ema(arr, span):
        alpha = 2.0 / (span + 1.0)
        out = np.empty_like(arr)
        out[0] = arr[0]
        for t in range(1, len(arr)):
            out[t] = alpha * arr[t] + (1 - alpha) * out[t-1]
        return out

    # Hitung tren untuk masing-masing timeframe
    def get_trend_dict(ts_col, span_ema=50):
        b_df = df.group_by(ts_col).agg([
            pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        ]).sort(ts_col)
        c = b_df["close"].to_numpy()
        ts = b_df[ts_col].to_numpy()
        ema = calc_ema(c, span_ema)
        # Trend: 1 if Close > EMA else -1
        t_dict = {ts[i]: (1 if c[i] >= ema[i] else -1) for i in range(len(c))}
        return t_dict

    print("Computing higher timeframe trends...")
    t_m15 = get_trend_dict("m15_ts", 50)
    t_m30 = get_trend_dict("m30_ts", 50)
    t_h1  = get_trend_dict("h1_ts", 50)
    t_h4  = get_trend_dict("h4_ts", 50)

    # Jalankan M1 Strategy
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

    raw_trades = []
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
                cur_t = ts[fill_bar]

                # Cari status tren di masing-masing TF
                ts_15 = (cur_t // (15 * 60 * 1000)) * (15 * 60 * 1000)
                ts_30 = (cur_t // (30 * 60 * 1000)) * (30 * 60 * 1000)
                ts_h1 = (cur_t // (60 * 60 * 1000)) * (60 * 60 * 1000)
                ts_h4 = (cur_t // (4 * 3600 * 1000)) * (4 * 3600 * 1000)

                side_val = 1 if order_side == "BUY" else -1
                raw_trades.append({
                    "r": r_val,
                    "side": side_val,
                    "t15": t_m15.get(ts_15, 0),
                    "t30": t_m30.get(ts_30, 0),
                    "th1": t_h1.get(ts_h1, 0),
                    "th4": t_h4.get(ts_h4, 0),
                })

    print(f"\nTotal Raw Trades M1 (2021-2026): {len(raw_trades):,}")

    def eval_filter(name, cond_fn):
        sub = [t["r"] for t in raw_trades if cond_fn(t)]
        r_sub = np.array(sub)
        n_c = len(r_sub)
        wins = r_sub[r_sub > 0]; losses = r_sub[r_sub < 0]
        wr = len(wins) / n_c * 100.0 if n_c > 0 else 0
        gw = sum(wins); gl = abs(sum(losses))
        pf = gw / gl if gl > 0 else 99.0
        exp = float(np.mean(r_sub)) if n_c > 0 else 0
        cum = np.cumsum(r_sub) if n_c > 0 else [0]
        mdd = float(np.max(np.maximum.accumulate(cum) - cum)) if n_c > 0 else 0
        print(f"{name:<30} | N={n_c:<6,} ({n_c/len(raw_trades)*100:4.1f}%) | WR={wr:5.2f}% | PF={pf:5.3f} | Exp={exp:+.4f}R | Tot R={cum[-1]:+9.1f}R | MDD={mdd:4.1f}R")

    print("\n" + "=" * 95)
    print(f"{'Konfigurasi Filter Tren untuk M1':<30} | {'Trades':<15} | {'Win Rate':<9} | {'PF':<7} | {'Net Exp':<11} | {'Total Net R':<11} | {'Max DD':<7}")
    print("=" * 95)
    eval_filter("M1 Raw (Tanpa Filter Tren)", lambda t: True)
    eval_filter("M1 + Filter M15 Trend", lambda t: t["side"] == t["t15"])
    eval_filter("M1 + Filter M30 Trend", lambda t: t["side"] == t["t30"])
    eval_filter("M1 + Filter H1 Trend", lambda t: t["side"] == t["th1"])
    eval_filter("M1 + Filter H4 Trend", lambda t: t["side"] == t["th4"])
    eval_filter("M1 + Filter Dual (M15 & H1)", lambda t: (t["side"] == t["t15"]) and (t["side"] == t["th1"]))

if __name__ == "__main__":
    scan_m1_trend_filters()
