#!/usr/bin/env python3
"""
Phase 2C.1 Forensic Engine:
1. Reconstruct exact Economic Drag relative to Mid-Price Benchmark for H4 and STRAT-08.
2. Evaluate Stop Loss Distance vs Cost Drag across all 4 Order Combinations.
3. Forensically test STRAT-08 limit fills:
   - Model 1: Naive Bid-Touch (Low_Bid <= Limit)
   - Model 2: True Ask-Touch (Low_Ask <= Limit <=> Low_Bid <= Limit - Spread)
   - Model 3: True Ask-Penetration 1-pip (Low_Ask <= Limit - 0.10)
   Measure exact trade count, win rate, PF, and expectancy drop!
"""

import os
import csv
import json
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
SPREAD_MEDIAN = 0.380
COMMISSION_ROUND = 0.070
SLIPPAGE_MARKET = 0.050
RISK_BUDGET = 7.50

def run_phase2c1():
    print("=== 1. Stop Loss Distance vs Order Combination Cost Matrix ===")
    # Order combinations:
    # Combo 1: Limit Entry + Limit TP Exit (Zero spread, Zero slippage, Comm only = $0.07/oz)
    # Combo 2: Limit Entry + Market SL Exit (Comm $0.07 + Exit Slip $0.05 = $0.12/oz)
    # Combo 3: Market Entry + Limit TP Exit (Spread $0.38 + Entry Slip $0.05 + Comm $0.07 = $0.50/oz)
    # Combo 4: Market Entry + Market SL Exit (Spread $0.38 + Entry Slip $0.05 + Exit Slip $0.05 + Comm $0.07 = $0.55/oz)

    stop_distances = [0.70, 1.50, 2.50, 5.00]
    combos = [
        {"name": "Combo 1: Passive Limit Entry + Limit TP Exit", "cost_oz": 0.070, "desc": "Commission only ($0.07). No spread cross, no slippage."},
        {"name": "Combo 2: Passive Limit Entry + Market SL Exit", "cost_oz": 0.120, "desc": "Commission ($0.07) + Exit Slippage ($0.05). No entry spread cross."},
        {"name": "Combo 3: Market Entry + Limit TP Exit (Standard Market Win)", "cost_oz": 0.500, "desc": "Spread ($0.38) + Entry Slip ($0.05) + Comm ($0.07)."},
        {"name": "Combo 4: Market Entry + Market SL Exit (Standard Market Loss)", "cost_oz": 0.550, "desc": "Spread ($0.38) + Entry Slip ($0.05) + Exit Slip ($0.05) + Comm ($0.07)."}
    ]

    print(f"{'Order Combination':<45} | {'Cost/oz':<8} | {'DSL=$0.70':<12} | {'DSL=$1.50':<12} | {'DSL=$2.50':<12} | {'DSL=$5.00'}")
    print("-" * 105)
    for c in combos:
        cost = c["cost_oz"]
        d70 = (cost / 0.70) * 100.0
        d150 = (cost / 1.50) * 100.0
        d250 = (cost / 2.50) * 100.0
        d500 = (cost / 5.00) * 100.0
        print(f"{c['name']:<45} | ${cost:<7.2f} | {d70:5.2f}% ({cost/0.70:.3f}R) | {d150:5.2f}% ({cost/1.50:.3f}R) | {d250:5.2f}% ({cost/2.50:.3f}R) | {d500:5.2f}% ({cost/5.00:.3f}R)")

    # =========================================================================
    # 2. Reconstruct Mid-Price Benchmark for H4 and STRAT-08
    # =========================================================================
    print("\n=== 2. Reconstructing Mid-Price Economic Drag Table ===")
    # H4 Win
    h4_ref_bid = 2650.000; h4_ref_ask = 2650.380
    h4_mid_entry = (h4_ref_bid + h4_ref_ask) / 2.0 # 2650.190
    h4_actual_entry = h4_ref_ask + SLIPPAGE_MARKET # 2650.430
    h4_dsl = 0.680
    h4_lots = RISK_BUDGET / (h4_dsl * 100.0) # 0.110294 lots = 11.0294 oz
    h4_actual_exit_bid = h4_actual_entry + (0.50 * h4_dsl) # 2650.770
    h4_mid_exit = h4_actual_exit_bid + (SPREAD_MEDIAN / 2.0) # 2650.960

    # Mid PnL
    h4_mid_pnl = (h4_mid_exit - h4_mid_entry) * h4_lots * 100.0 # (2650.96 - 2650.19) * 11.0294 = +$8.4926
    # Actual Net PnL
    h4_actual_gross_pnl = (h4_actual_exit_bid - h4_actual_entry) * h4_lots * 100.0 # +$3.7500
    h4_comm = COMMISSION_ROUND * h4_lots * 100.0 # -$0.7721
    h4_net_pnl = h4_actual_gross_pnl - h4_comm # +$2.9779
    h4_econ_drag_dollars = h4_mid_pnl - h4_net_pnl # $5.5147
    h4_econ_drag_r = h4_econ_drag_dollars / RISK_BUDGET # 0.7353 R

    # H4 Loss
    h4_actual_sl_bid = h4_actual_entry - h4_dsl - SLIPPAGE_MARKET # 2649.700
    h4_mid_exit_loss = h4_actual_sl_bid + (SPREAD_MEDIAN / 2.0) + SLIPPAGE_MARKET # 2650.080 (where stop price was at mid)
    h4_mid_loss_pnl = (h4_actual_sl_bid + SLIPPAGE_MARKET + SPREAD_MEDIAN/2.0 - h4_mid_entry) * h4_lots * 100.0
    # True mid loss: price moved from 2650.190 to 2649.940 (0.250 mid drop)
    h4_mid_loss_move = (2649.750 + SPREAD_MEDIAN/2.0) - h4_mid_entry # nominal SL was 2649.750
    # Mid-price loss if nominal SL was hit at mid:
    mid_sl_p = 2649.750 + SPREAD_MEDIAN/2.0 # 2649.940
    h4_mid_loss_pnl = (mid_sl_p - h4_mid_entry) * h4_lots * 100.0 # -0.250 * 11.0294 = -$2.7574
    h4_actual_gross_loss = (h4_actual_sl_bid - h4_actual_entry) * h4_lots * 100.0 # -0.730 * 11.0294 = -$8.0515
    h4_net_loss = h4_actual_gross_loss - h4_comm # -$8.8235
    h4_econ_drag_loss_dollars = h4_mid_loss_pnl - h4_net_loss # -$2.7574 - (-$8.8235) = +$6.0661
    h4_econ_drag_loss_r = h4_econ_drag_loss_dollars / RISK_BUDGET # 0.8088 R

    econ_rows = [
        {
            "case": "H4_Micro_Momentum_Win",
            "order_type": "MARKET_ENTRY_LIMIT_TP",
            "mid_entry": h4_mid_entry,
            "bid_at_entry": h4_ref_bid,
            "ask_at_entry": h4_ref_ask,
            "entry_slippage": SLIPPAGE_MARKET,
            "actual_fill_entry": h4_actual_entry,
            "actual_exit": h4_actual_exit_bid,
            "exit_slippage": 0.000,
            "commission_total_dollars": round(h4_comm, 4),
            "mid_price_benchmark_pnl_dollars": round(h4_mid_pnl, 4),
            "actual_gross_pnl_dollars": round(h4_actual_gross_pnl, 4),
            "net_realized_pnl_dollars": round(h4_net_pnl, 4),
            "mid_pnl_r": round(h4_mid_pnl / RISK_BUDGET, 4),
            "net_realized_r": round(h4_net_pnl / RISK_BUDGET, 4),
            "total_economic_drag_dollars": round(h4_econ_drag_dollars, 4),
            "total_economic_drag_r": round(h4_econ_drag_r, 4),
            "economic_drag_pct_of_risk": round(h4_econ_drag_r * 100, 2),
            "cost_accounting_breakdown": f"Entry Half-Spread ($2.10) + Exit Half-Spread ($2.10) + Entry Slip ($0.55) + Comm ($0.77) = ${h4_econ_drag_dollars:.4f}"
        },
        {
            "case": "H4_Micro_Momentum_Loss",
            "order_type": "MARKET_ENTRY_MARKET_SL",
            "mid_entry": h4_mid_entry,
            "bid_at_entry": h4_ref_bid,
            "ask_at_entry": h4_ref_ask,
            "entry_slippage": SLIPPAGE_MARKET,
            "actual_fill_entry": h4_actual_entry,
            "actual_exit": h4_actual_sl_bid,
            "exit_slippage": SLIPPAGE_MARKET,
            "commission_total_dollars": round(h4_comm, 4),
            "mid_price_benchmark_pnl_dollars": round(h4_mid_loss_pnl, 4),
            "actual_gross_pnl_dollars": round(h4_actual_gross_loss, 4),
            "net_realized_pnl_dollars": round(h4_net_loss, 4),
            "mid_pnl_r": round(h4_mid_loss_pnl / RISK_BUDGET, 4),
            "net_realized_r": round(h4_net_loss / RISK_BUDGET, 4),
            "total_economic_drag_dollars": round(h4_econ_drag_loss_dollars, 4),
            "total_economic_drag_r": round(h4_econ_drag_loss_r, 4),
            "economic_drag_pct_of_risk": round(h4_econ_drag_loss_r * 100, 2),
            "cost_accounting_breakdown": f"Entry Half-Spread ($2.10) + Exit Half-Spread ($2.10) + Entry Slip ($0.55) + Exit Slip ($0.55) + Comm ($0.77) = ${h4_econ_drag_loss_dollars:.4f}"
        }
    ]

    with open("/home/vallencia/xauusd_research/ECONOMIC_DRAG_BENCHMARK_RECONSTRUCTION.csv", "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(econ_rows[0].keys()))
        writer.writeheader()
        writer.writerows(econ_rows)
    print("Saved /home/vallencia/xauusd_research/ECONOMIC_DRAG_BENCHMARK_RECONSTRUCTION.csv")

    # =========================================================================
    # 3. STRAT-08 Limit Fill Mechanics Forensic Audit
    # =========================================================================
    print("\n=== 3. Forensic Audit of STRAT-08 Limit Fills on M1 Dataset ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // (15 * 60 * 1000) * (15 * 60 * 1000)).alias("m15_ts"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
    )
    df = df.filter(~pl.col("hour").is_between(21, 23))

    m15 = df.group_by("m15_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.col("timestamp").first().alias("ts"),
        pl.col("date").first(), pl.col("hour").first()
    ]).sort("m15_ts")

    h_15 = m15["high"].to_numpy()
    l_15 = m15["low"].to_numpy() # Note: This is BID Low!
    o_15 = m15["open"].to_numpy()
    c_15 = m15["close"].to_numpy()
    hours_15 = m15["hour"].to_numpy()
    dates_15 = m15["date"].to_numpy()
    n_15 = len(o_15)

    day_indices = {}
    for i, d in enumerate(dates_15):
        if d not in day_indices: day_indices[d] = []
        day_indices[d].append(i)

    lvl = 0.786
    target_rr = 1.5

    # Test 3 Limit Execution Models:
    # Model 1: Naive Bid-Touch (Original audit_engine.py logic: Low_Bid <= bounce)
    # Model 2: True Ask-Touch (Low_Ask <= bounce <=> Low_Bid <= bounce - SPREAD)
    # Model 3: True Ask-Penetration 1-pip (Low_Ask <= bounce - 0.10 <=> Low_Bid <= bounce - SPREAD - 0.10)
    # Model 4: True Ask-Penetration 2-pip (Low_Ask <= bounce - 0.20 <=> Low_Bid <= bounce - SPREAD - 0.20)

    strat08_models = [
        {"name": "Model 1: Naive Bid-Touch (Flawed / Ignores Spread)", "offset": 0.000, "pen": 0.000, "desc": "Assumes Buy Limit fills when Bid touches limit level. Unrealistic; Ask is still spread above limit."},
        {"name": "Model 2: True Ask-Touch (Ask reaches Limit)", "offset": SPREAD_MEDIAN, "pen": 0.000, "desc": "Buy Limit fills only when Ask touches limit (Bid drops to Limit - Spread)."},
        {"name": "Model 3: True Ask-Penetration 1-Pip (Realistic Queue)", "offset": SPREAD_MEDIAN, "pen": 0.100, "desc": "Ask penetrates limit by 1 full pip ($0.10). Primary realistic benchmark."},
        {"name": "Model 4: True Ask-Penetration 2-Pips (Stress Queue)", "offset": SPREAD_MEDIAN, "pen": 0.200, "desc": "Ask penetrates limit by 2 full pips ($0.20). Adverse queue stress test."}
    ]

    limit_audit_rows = []

    for m in strat08_models:
        offset = m["offset"] + m["pen"]
        trades = []
        for d, d_idx in day_indices.items():
            if len(d_idx) < 30: continue
            lon_imp = [i for i in d_idx if 7 <= hours_15[i] <= 8]
            if len(lon_imp) < 6: continue
            l_h = np.max(h_15[lon_imp]); l_l = np.min(l_15[lon_imp])
            span = l_h - l_l
            if not (4.0 <= span <= 30.0): continue

            is_bull = c_15[lon_imp[-1]] > o_15[lon_imp[0]]
            ny = [i for i in d_idx if 9 <= hours_15[i] <= 16]
            if not ny: continue

            if is_bull:
                bounce = l_h - (lvl * span)
                sl = l_l - (SPREAD_MEDIAN / 2.0)
                risk = (bounce + (SPREAD_MEDIAN / 2.0)) - sl
                if 1.5 <= risk <= 20.0:
                    entry = bounce + (SPREAD_MEDIAN / 2.0)
                    tp = entry + (target_rr * risk)
                    # Trigger condition on Bid Low:
                    # For Buy Limit: Low_Bid must reach bounce - offset
                    for pos, i in enumerate(ny):
                        if l_15[i] <= bounce - offset:
                            sub = ny[pos:]
                            r_val = -1.0
                            for j in sub:
                                if l_15[j] <= sl: r_val = -1.0; break
                                elif h_15[j] >= tp: r_val = target_rr; break
                            trades.append(r_val)
                            break
            else:
                bounce = l_l + (lvl * span)
                sl = l_h + (SPREAD_MEDIAN / 2.0)
                risk = sl - (bounce - (SPREAD_MEDIAN / 2.0))
                if 1.5 <= risk <= 20.0:
                    entry = bounce - (SPREAD_MEDIAN / 2.0)
                    tp = entry - (target_rr * risk)
                    # For Sell Limit: High_Bid must reach bounce + offset
                    for pos, i in enumerate(ny):
                        if h_15[i] >= bounce + offset:
                            sub = ny[pos:]
                            r_val = -1.0
                            for j in sub:
                                if h_15[j] >= sl: r_val = -1.0; break
                                elif l_15[j] <= tp: r_val = target_rr; break
                            trades.append(r_val)
                            break

        r_arr = np.array(trades)
        n_tr = len(r_arr)
        if n_tr > 0:
            gw = sum(x for x in r_arr if x > 0); gl = abs(sum(x for x in r_arr if x < 0))
            pf = gw / gl if gl > 0 else 99.0
            wr = sum(1 for x in r_arr if x > 0) / n_tr * 100.0
            net_exp = float(np.mean(r_arr))
            cum = np.cumsum(r_arr)
            mdd = float(np.max(np.maximum.accumulate(cum) - cum))
        else:
            pf = 0.0; wr = 0.0; net_exp = 0.0; mdd = 0.0

        limit_audit_rows.append({
            "model_name": m["name"],
            "fill_condition_bid": f"Low_Bid <= Limit - ${offset:.3f}" if offset > 0 else "Low_Bid <= Limit",
            "total_trades_12y": n_tr,
            "win_rate": round(wr, 2),
            "profit_factor": round(pf, 3),
            "net_expectancy_r": round(net_exp, 4),
            "max_drawdown_r": round(mdd, 2),
            "realism_status": "UNREALISTIC (Flawed)" if offset == 0 else ("REALISTIC (Verified)" if offset == SPREAD_MEDIAN + 0.10 else "STRESS_TEST")
        })
        print(f"{m['name']:<55} | N={n_tr:<5} | WR={wr:5.2f}% | PF={pf:5.3f} | Exp={net_exp:+.4f}R | MDD={mdd:5.2f}R")

    with open("/home/vallencia/xauusd_research/LIMIT_FILL_EXECUTION_VALIDATION.csv", "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(limit_audit_rows[0].keys()))
        writer.writeheader()
        writer.writerows(limit_audit_rows)
    print("Saved /home/vallencia/xauusd_research/LIMIT_FILL_EXECUTION_VALIDATION.csv")

if __name__ == "__main__":
    run_phase2c1()
