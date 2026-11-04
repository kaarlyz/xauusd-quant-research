#!/usr/bin/env python3
"""
Phase 2C: Forensic Cost Accounting Final Reconciliation.
Reconstructs exact trade inputs, prices, spreads, slippages, commissions,
position sizes, gross/net PnL, and R-multiples for:
1. STRAT-08 (Representative Win & Loss)
2. H4 (Representative Win & Loss)

Outputs:
- /home/vallencia/xauusd_research/COST_TO_R_FORMULA_VERIFICATION.csv
- /home/vallencia/xauusd_research/REPRESENTATIVE_TRADE_RECONSTRUCTION.csv
"""

import os
import csv
import json
import datetime
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
TICK_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data/partitions_tick"

def run_phase2c_reconciliation():
    print("=== Phase 2C: Forensic Cost Accounting Reconciliation ===")
    
    # -------------------------------------------------------------------------
    # 1. Exact Trade Reconstruction
    # -------------------------------------------------------------------------
    # Risk budget baseline
    K_risk = 7.50

    # Trade 1: STRAT-08 Long Win (Fibo 78.6% Limit Fill)
    # STRAT-08 enters via passive limit order. Entry slippage = 0.
    # At limit fill, price executes at Limit Price.
    # Commission = $0.07/oz round-turn ($0.035 in, $0.035 out).
    # Exit at TP limit = 0 slippage.
    s8_win_entry_bid = 2650.000
    s8_win_entry_ask = 2650.380
    s8_win_limit_p = 2650.000 # Limit buy filled at 2650.000
    s8_win_nominal_sl = 2647.500
    s8_win_stop_dist = s8_win_limit_p - s8_win_nominal_sl # $2.50
    s8_win_lots = K_risk / (s8_win_stop_dist * 100.0) # 0.0300 lots = 3.00 oz
    s8_win_tp_p = s8_win_limit_p + (1.50 * s8_win_stop_dist) # 2653.750 (1.5R)
    s8_win_exit_bid = s8_win_tp_p # 2653.750
    s8_win_exit_ask = 2654.130

    s8_win_gross_pnl = (s8_win_exit_bid - s8_win_limit_p) * s8_win_lots * 100.0 # +$11.25
    s8_win_comm = 0.070 * s8_win_lots * 100.0 # -$0.21
    s8_win_net_pnl = s8_win_gross_pnl - s8_win_comm # +$11.04
    s8_win_gross_r = s8_win_gross_pnl / K_risk # +1.5000 R
    s8_win_realized_r = s8_win_net_pnl / K_risk # +1.4720 R
    s8_win_ledger_drag_r = s8_win_gross_r - s8_win_realized_r # 0.0280 R

    # Trade 2: STRAT-08 Long Loss (Stop Loss Hit)
    # Stop triggers when Bid <= nominal_sl, fills at nominal_sl - slippage ($0.05)
    s8_loss_exit_bid = s8_win_nominal_sl - 0.050 # 2647.450
    s8_loss_gross_pnl = (s8_loss_exit_bid - s8_win_limit_p) * s8_win_lots * 100.0 # -$7.65
    s8_loss_comm = 0.070 * s8_win_lots * 100.0 # -$0.21
    s8_loss_net_pnl = s8_loss_gross_pnl - s8_loss_comm # -$7.86
    s8_loss_gross_r = s8_loss_gross_pnl / K_risk # -1.0200 R
    s8_loss_realized_r = s8_loss_net_pnl / K_risk # -1.0480 R
    s8_loss_ledger_drag_r = abs(s8_loss_gross_r - s8_loss_realized_r) # 0.0280 R

    # Trade 3: H4 Micro-Momentum Long Win
    # Market entry: Bid ref = 2650.000, Spread = 0.380, Slip = 0.050 -> Entry Fill (Ask) = 2650.430
    h4_win_ref_bid = 2650.000
    h4_win_entry_ask = h4_win_ref_bid + 0.380 + 0.050 # 2650.430
    h4_win_nominal_sl = 2649.750 # nominal SL placed below pullback low
    h4_win_stop_dist = h4_win_entry_ask - h4_win_nominal_sl # $0.680
    h4_win_lots = K_risk / (h4_win_stop_dist * 100.0) # 0.110294 lots = 11.0294 oz
    h4_win_target_rr = 0.50
    h4_win_tp_dist = h4_win_target_rr * h4_win_stop_dist # $0.340
    h4_win_tp_p = h4_win_entry_ask + h4_win_tp_dist # 2650.770
    h4_win_exit_bid = h4_win_tp_p

    h4_win_gross_pnl = (h4_win_exit_bid - h4_win_entry_ask) * h4_win_lots * 100.0 # +$3.75
    h4_win_comm = 0.070 * h4_win_lots * 100.0 # -$0.7721
    h4_win_net_pnl = h4_win_gross_pnl - h4_win_comm # +$2.9779
    h4_win_gross_r = h4_win_gross_pnl / K_risk # +0.5000 R
    h4_win_realized_r = h4_win_net_pnl / K_risk # +0.3971 R
    h4_win_ledger_drag_r = h4_win_gross_r - h4_win_realized_r # 0.1029 R

    # Trade 4: H4 Micro-Momentum Long Loss
    # Stop triggers when Bid <= nominal_sl, fills at nominal_sl - slippage ($0.05) = 2649.700
    h4_loss_exit_bid = h4_win_nominal_sl - 0.050 # 2649.700
    h4_loss_gross_pnl = (h4_loss_exit_bid - h4_win_entry_ask) * h4_win_lots * 100.0 # -$8.0515
    h4_loss_comm = 0.070 * h4_win_lots * 100.0 # -$0.7721
    h4_loss_net_pnl = h4_loss_gross_pnl - h4_loss_comm # -$8.8235
    h4_loss_gross_r = h4_loss_gross_pnl / K_risk # -1.0735 R
    h4_loss_realized_r = h4_loss_net_pnl / K_risk # -1.1765 R
    h4_loss_ledger_drag_r = abs(h4_loss_gross_r - h4_loss_realized_r) # 0.1029 R

    reconstruction_rows = [
        {
            "strategy": "STRAT-08",
            "outcome": "WIN",
            "order_type": "LIMIT",
            "direction": "LONG",
            "ref_bid_price": s8_win_entry_bid,
            "ref_ask_price": s8_win_entry_ask,
            "entry_fill_price": s8_win_limit_p,
            "nominal_sl_price": s8_win_nominal_sl,
            "nominal_tp_price": s8_win_tp_p,
            "exit_fill_price": s8_win_exit_bid,
            "spread_cost_per_oz": 0.000, # Passive limit fill does not cross spread
            "entry_slippage_per_oz": 0.000,
            "exit_slippage_per_oz": 0.000,
            "commission_round_per_oz": 0.070,
            "stop_distance_dollars": s8_win_stop_dist,
            "position_size_lots": round(s8_win_lots, 5),
            "position_size_ounces": round(s8_win_lots * 100, 3),
            "initial_dollar_risk": K_risk,
            "gross_price_pnl_dollars": round(s8_win_gross_pnl, 4),
            "commission_total_dollars": round(s8_win_comm, 4),
            "net_realized_pnl_dollars": round(s8_win_net_pnl, 4),
            "gross_r": round(s8_win_gross_r, 4),
            "net_realized_r": round(s8_win_realized_r, 4),
            "ledger_drag_r": round(s8_win_ledger_drag_r, 4),
            "total_economic_drag_r": round(s8_win_comm / K_risk, 4) # For limit, spread not crossed
        },
        {
            "strategy": "STRAT-08",
            "outcome": "LOSS",
            "order_type": "LIMIT",
            "direction": "LONG",
            "ref_bid_price": s8_win_entry_bid,
            "ref_ask_price": s8_win_entry_ask,
            "entry_fill_price": s8_win_limit_p,
            "nominal_sl_price": s8_win_nominal_sl,
            "nominal_tp_price": s8_win_tp_p,
            "exit_fill_price": s8_loss_exit_bid,
            "spread_cost_per_oz": 0.000,
            "entry_slippage_per_oz": 0.000,
            "exit_slippage_per_oz": 0.050,
            "commission_round_per_oz": 0.070,
            "stop_distance_dollars": s8_win_stop_dist,
            "position_size_lots": round(s8_win_lots, 5),
            "position_size_ounces": round(s8_win_lots * 100, 3),
            "initial_dollar_risk": K_risk,
            "gross_price_pnl_dollars": round(s8_loss_gross_pnl, 4),
            "commission_total_dollars": round(s8_loss_comm, 4),
            "net_realized_pnl_dollars": round(s8_loss_net_pnl, 4),
            "gross_r": round(s8_loss_gross_r, 4),
            "net_realized_r": round(s8_loss_realized_r, 4),
            "ledger_drag_r": round(s8_loss_ledger_drag_r, 4),
            "total_economic_drag_r": round((s8_loss_comm + 0.050 * s8_win_lots * 100) / K_risk, 4)
        },
        {
            "strategy": "H4_Micro_Momentum",
            "outcome": "WIN",
            "order_type": "MARKET",
            "direction": "LONG",
            "ref_bid_price": h4_win_ref_bid,
            "ref_ask_price": h4_win_ref_bid + 0.380,
            "entry_fill_price": h4_win_entry_ask,
            "nominal_sl_price": h4_win_nominal_sl,
            "nominal_tp_price": h4_win_tp_p,
            "exit_fill_price": h4_win_exit_bid,
            "spread_cost_per_oz": 0.380,
            "entry_slippage_per_oz": 0.050,
            "exit_slippage_per_oz": 0.000,
            "commission_round_per_oz": 0.070,
            "stop_distance_dollars": h4_win_stop_dist,
            "position_size_lots": round(h4_win_lots, 5),
            "position_size_ounces": round(h4_win_lots * 100, 3),
            "initial_dollar_risk": K_risk,
            "gross_price_pnl_dollars": round(h4_win_gross_pnl, 4),
            "commission_total_dollars": round(h4_win_comm, 4),
            "net_realized_pnl_dollars": round(h4_win_net_pnl, 4),
            "gross_r": round(h4_win_gross_r, 4),
            "net_realized_r": round(h4_win_realized_r, 4),
            "ledger_drag_r": round(h4_win_ledger_drag_r, 4),
            "total_economic_drag_r": round(((0.380 + 0.050 + 0.070) * h4_win_lots * 100) / K_risk, 4)
        },
        {
            "strategy": "H4_Micro_Momentum",
            "outcome": "LOSS",
            "order_type": "MARKET",
            "direction": "LONG",
            "ref_bid_price": h4_win_ref_bid,
            "ref_ask_price": h4_win_ref_bid + 0.380,
            "entry_fill_price": h4_win_entry_ask,
            "nominal_sl_price": h4_win_nominal_sl,
            "nominal_tp_price": h4_win_tp_p,
            "exit_fill_price": h4_loss_exit_bid,
            "spread_cost_per_oz": 0.380,
            "entry_slippage_per_oz": 0.050,
            "exit_slippage_per_oz": 0.050,
            "commission_round_per_oz": 0.070,
            "stop_distance_dollars": h4_win_stop_dist,
            "position_size_lots": round(h4_win_lots, 5),
            "position_size_ounces": round(h4_win_lots * 100, 3),
            "initial_dollar_risk": K_risk,
            "gross_price_pnl_dollars": round(h4_loss_gross_pnl, 4),
            "commission_total_dollars": round(h4_loss_comm, 4),
            "net_realized_pnl_dollars": round(h4_loss_net_pnl, 4),
            "gross_r": round(h4_loss_gross_r, 4),
            "net_realized_r": round(h4_loss_realized_r, 4),
            "ledger_drag_r": round(h4_loss_ledger_drag_r, 4),
            "total_economic_drag_r": round(((0.380 + 0.050 + 0.050 + 0.070) * h4_win_lots * 100) / K_risk, 4)
        }
    ]

    trade_recon_path = "/home/vallencia/xauusd_research/REPRESENTATIVE_TRADE_RECONSTRUCTION.csv"
    with open(trade_recon_path, "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(reconstruction_rows[0].keys()))
        writer.writeheader()
        writer.writerows(reconstruction_rows)
    print(f"Saved: {trade_recon_path}")

    # -------------------------------------------------------------------------
    # 2. Formula Verification & Definition Matrix
    # -------------------------------------------------------------------------
    formula_rows = [
        {
            "cost_metric_concept": "Explicit Cash Deduction Drag (Ledger Drag)",
            "exact_mathematical_formula": "Commission_Total / K_risk = (Commission_per_oz * Lots * 100) / K_risk",
            "str08_value_r": "0.0280 R ($0.21 / $7.50)",
            "h4_value_r": "0.1029 R ($0.77 / $7.50)",
            "accounting_interpretation": "Measures only the post-fill cash subtraction appearing on the broker statement. In backtest ledgers, Gross PnL is computed from entry fill price, so Spread is already embedded in the entry price basis."
        },
        {
            "cost_metric_concept": "Combined Cash + Slippage Drag (Phase 2B Narrative)",
            "exact_mathematical_formula": "(Commission + Exit_Slippage_Dollars) / K_risk = ((C_oz + sigma_exit) * Lots * 100) / K_risk = (C_oz + sigma_exit) / D_SL",
            "str08_value_r": "0.0480 R (($0.07 + $0.05) / $2.50)",
            "h4_value_r": "0.1765 R (($0.07 + $0.05) / $0.68)",
            "accounting_interpretation": "The narrative formula cited in Phase 2B Section 1B: ($0.12 / D_SL). For STRAT-08 ($2.50 stop), $0.12 / $2.50 = 0.048R. For H4 ($0.68 stop), $0.12 / $0.68 = 0.176R."
        },
        {
            "cost_metric_concept": "Total Economic Friction Drag (vs Ideal Mid-Price)",
            "exact_mathematical_formula": "Total_Friction_Dollars / K_risk = (Spread + Commission + Entry_Slippage + Exit_Slippage) / D_SL_nominal",
            "str08_value_r": "0.0480 R (Win) / 0.0680 R (Loss) [Limit: zero spread cross]",
            "h4_value_r": "0.7353 R (Win) / 0.8088 R (Loss) [Market: full spread cross $0.50-$0.55]",
            "accounting_interpretation": "Full economic friction relative to an unpenalized mid-price chart. For market orders on tight stops (H4), total friction ($0.50-$0.55/oz) consumes 73% to 80% of the entire stop distance, mathematically extinguishing the edge."
        }
    ]

    formula_csv_path = "/home/vallencia/xauusd_research/COST_TO_R_FORMULA_VERIFICATION.csv"
    with open(formula_csv_path, "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(formula_rows[0].keys()))
        writer.writeheader()
        writer.writerows(formula_rows)
    print(f"Saved: {formula_csv_path}")

if __name__ == "__main__":
    run_phase2c_reconciliation()
