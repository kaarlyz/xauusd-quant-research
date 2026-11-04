#!/usr/bin/env python3
"""
Phase 3: STRAT-07 Final Revalidation Engine.
Evaluates STRAT-07 (Tokyo 08:15 WIB M1 Reversal) under the fully corrected execution model:
- Long buys at Ask (Bid + Spread + Slippage $0.05), exits at Bid.
- Short sells at Bid (Bid - Slippage $0.05), exits at Ask (Bid + Spread + Slippage $0.05).
- Commission: $0.07/oz round-turn.
- Evaluates strictly across:
  - In-Sample (2021-08-23 to 2024-08-21, 3 Years)
  - Validation (2024-08-22 to 2025-08-21, 1 Year)
  - Pre-IS Historical Context (2015-2021)
  - Blind Holdout (2025-08-22 to 2026-08-21) remains STRICTLY SEALED.

Outputs:
- /home/vallencia/xauusd_research/STRAT07_IS_RESULTS.csv
- /home/vallencia/xauusd_research/STRAT07_VALIDATION_RESULTS.csv
- /home/vallencia/xauusd_research/STRAT07_TRADE_LEDGER.csv
- /home/vallencia/xauusd_research/data/strat07_revalidation_summary.json
"""

import os
import csv
import json
import datetime
import numpy as np
import polars as pl
from scipy import stats

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
TICK_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data/partitions_tick"

# Invariants
SPREAD_TOKYO = 0.410 # Empirical median Tokyo spread from Phase 1B/1C audit
COMMISSION_ROUND = 0.070 # $7.00/lot
SLIPPAGE_MARKET = 0.050 # 0.5 tick
RISK_BUDGET = 7.50

# Partition timestamps (ms)
T_IS_START = int(datetime.datetime(2021, 8, 23, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_IS_END = int(datetime.datetime(2024, 8, 21, 23, 59, 59, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_VAL_START = int(datetime.datetime(2024, 8, 22, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
T_VAL_END = int(datetime.datetime(2025, 8, 21, 23, 59, 59, tzinfo=datetime.timezone.utc).timestamp() * 1000)

def run_revalidation():
    print("=== Loading M1 Dataset for STRAT-07 Evaluation ===")
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    df = df.with_columns(
        (pl.col("timestamp") // 1000).alias("ts_sec"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.month().alias("month"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.day().alias("day"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.minute().alias("minute"),
        pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    )
    # Exclude 21-23 UTC
    df = df.filter(~pl.col("hour").is_between(21, 23))
    # Exclude sealed holdout (keep holdout completely unaccessed)
    df = df.filter(pl.col("timestamp") <= T_VAL_END)

    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    hours = df["hour"].to_numpy()
    minutes = df["minute"].to_numpy()
    dates = df["date"].to_numpy()
    years = df["year"].to_numpy()
    months = df["month"].to_numpy()
    ts = df["timestamp"].to_numpy()
    ts_sec = df["ts_sec"].to_numpy()
    n = len(o)

    # 60-bar ATR
    ranges = h - l
    cumsum = np.cumsum(np.insert(ranges, 0, 0))
    atr60 = (cumsum[60:] - cumsum[:-60]) / 60.0
    atr60 = np.pad(atr60, (60, 0), mode="edge")[:n]

    trades = []
    trade_id = 0

    print(f"Scanning {n:,} candles up to 2025-08-21...")

    for i in range(65, n - 35):
        # STRAT-07 triggers at minute 14 of hour 1 UTC (08:14 WIB)
        if hours[i] != 1 or minutes[i] != 14:
            continue
        if minutes[i - 14] != 0 or hours[i - 14] != 1:
            continue

        o_00 = o[i - 14]
        c_14 = c[i]
        h_15 = np.max(h[i - 14 : i + 1])
        l_15 = np.min(l[i - 14 : i + 1])
        disp = c_14 - o_00
        cur_atr = atr60[i]
        if abs(disp) < max(cur_atr * 0.70, 1.50):
            continue

        exec_bar = i + 1 # open of minute 15 (08:15:00 WIB)
        exec_ts = ts[exec_bar]
        date_str = str(dates[exec_bar])
        yr = int(years[exec_bar])
        mo = int(months[exec_bar])

        # Partition assignment
        if exec_ts < T_IS_START:
            partition = "PRE_IS_HISTORICAL"
        elif exec_ts <= T_IS_END:
            partition = "IN_SAMPLE"
        elif exec_ts <= T_VAL_END:
            partition = "VALIDATION"
        else:
            continue # Sealed holdout

        trade_id += 1

        # SHORT SETUP: Bullish impulse rejected at high
        if disp > 0 and (h_15 - c_14) >= 0.35 * (h_15 - l_15):
            # Sell Market at Bid minus slippage
            entry_fill = o[exec_bar] - SLIPPAGE_MARKET
            nominal_sl = h_15 + 0.50
            stop_dist = nominal_sl - entry_fill
            if stop_dist < 0.80 or stop_dist > 15.0:
                continue

            lots = RISK_BUDGET / (stop_dist * 100.0)
            target_dist = 1.50 * stop_dist
            tp_price = entry_fill - target_dist # Short TP is on Ask

            exit_fill = c[exec_bar + 30] + SPREAD_TOKYO
            exit_reason = "TIMEOUT"
            is_ambiguous = False
            exit_bar = exec_bar + 30

            for s in range(0, 30):
                b = exec_bar + s
                # Short exits at Ask = Bid + Spread
                hit_sl = (h[b] + SPREAD_TOKYO >= nominal_sl)
                hit_tp = (l[b] + SPREAD_TOKYO <= tp_price)

                if hit_sl and hit_tp:
                    is_ambiguous = True
                    exit_fill = nominal_sl + SLIPPAGE_MARKET
                    exit_reason = "AMBIGUOUS"
                    exit_bar = b
                    break
                elif hit_sl:
                    exit_fill = nominal_sl + SLIPPAGE_MARKET
                    exit_reason = "SL"
                    exit_bar = b
                    break
                elif hit_tp:
                    exit_fill = tp_price
                    exit_reason = "TP"
                    exit_bar = b
                    break

            gross_pnl = (entry_fill - exit_fill) * lots * 100.0
            comm = COMMISSION_ROUND * lots * 100.0
            net_pnl = gross_pnl - comm
            realized_r = net_pnl / RISK_BUDGET

            trades.append({
                "trade_id": trade_id,
                "partition": partition,
                "entry_time": datetime.datetime.fromtimestamp(ts_sec[exec_bar], tz=datetime.timezone.utc).isoformat(),
                "exit_time": datetime.datetime.fromtimestamp(ts_sec[exit_bar], tz=datetime.timezone.utc).isoformat(),
                "date": date_str,
                "year": yr,
                "month": mo,
                "direction": "SHORT",
                "entry_price": round(entry_fill, 3),
                "sl_price": round(nominal_sl, 3),
                "tp_price": round(tp_price, 3),
                "stop_dist": round(stop_dist, 3),
                "lots": round(lots, 5),
                "exit_price": round(exit_fill, 3),
                "exit_reason": exit_reason,
                "is_ambiguous": is_ambiguous,
                "gross_pnl": round(gross_pnl, 4),
                "commission": round(comm, 4),
                "net_pnl": round(net_pnl, 4),
                "realized_r": round(realized_r, 4),
                "is_win": bool(realized_r > 0),
                "holding_mins": exit_bar - exec_bar + 1
            })

        # LONG SETUP: Bearish impulse rejected at low
        elif disp < 0 and (c_14 - l_15) >= 0.35 * (h_15 - l_15):
            # Buy Market at Ask plus slippage
            entry_fill = o[exec_bar] + SPREAD_TOKYO + SLIPPAGE_MARKET
            nominal_sl = l_15 - 0.50
            stop_dist = entry_fill - nominal_sl
            if stop_dist < 0.80 or stop_dist > 15.0:
                continue

            lots = RISK_BUDGET / (stop_dist * 100.0)
            target_dist = 1.50 * stop_dist
            tp_price = entry_fill + target_dist # Long TP is on Bid

            exit_fill = c[exec_bar + 30]
            exit_reason = "TIMEOUT"
            is_ambiguous = False
            exit_bar = exec_bar + 30

            for s in range(0, 30):
                b = exec_bar + s
                # Long exits at Bid
                hit_sl = (l[b] <= nominal_sl)
                hit_tp = (h[b] >= tp_price)

                if hit_sl and hit_tp:
                    is_ambiguous = True
                    exit_fill = nominal_sl - SLIPPAGE_MARKET
                    exit_reason = "AMBIGUOUS"
                    exit_bar = b
                    break
                elif hit_sl:
                    exit_fill = nominal_sl - SLIPPAGE_MARKET
                    exit_reason = "SL"
                    exit_bar = b
                    break
                elif hit_tp:
                    exit_fill = tp_price
                    exit_reason = "TP"
                    exit_bar = b
                    break

            gross_pnl = (exit_fill - entry_fill) * lots * 100.0
            comm = COMMISSION_ROUND * lots * 100.0
            net_pnl = gross_pnl - comm
            realized_r = net_pnl / RISK_BUDGET

            trades.append({
                "trade_id": trade_id,
                "partition": partition,
                "entry_time": datetime.datetime.fromtimestamp(ts_sec[exec_bar], tz=datetime.timezone.utc).isoformat(),
                "exit_time": datetime.datetime.fromtimestamp(ts_sec[exit_bar], tz=datetime.timezone.utc).isoformat(),
                "date": date_str,
                "year": yr,
                "month": mo,
                "direction": "LONG",
                "entry_price": round(entry_fill, 3),
                "sl_price": round(nominal_sl, 3),
                "tp_price": round(tp_price, 3),
                "stop_dist": round(stop_dist, 3),
                "lots": round(lots, 5),
                "exit_price": round(exit_fill, 3),
                "exit_reason": exit_reason,
                "is_ambiguous": is_ambiguous,
                "gross_pnl": round(gross_pnl, 4),
                "commission": round(comm, 4),
                "net_pnl": round(net_pnl, 4),
                "realized_r": round(realized_r, 4),
                "is_win": bool(realized_r > 0),
                "holding_mins": exit_bar - exec_bar + 1
            })

    print(f"Total STRAT-07 Trades Triggered (2015-2025): {len(trades)}")

    # Save full Trade Ledger CSV
    ledger_csv_path = "/home/vallencia/xauusd_research/STRAT07_TRADE_LEDGER.csv"
    with open(ledger_csv_path, "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(trades[0].keys()))
        writer.writeheader()
        writer.writerows(trades)
    print(f"Trade Ledger written to {ledger_csv_path}")

    # Helper function for metrics
    def evaluate_trades(tr_list, label):
        if not tr_list:
            return {"label": label, "n": 0, "wr": 0.0, "pf": 0.0, "net_exp": 0.0, "tot_r": 0.0, "mdd": 0.0, "avg_win": 0.0, "avg_loss": 0.0}
        r_vals = np.array([t["realized_r"] for t in tr_list])
        n_t = len(r_vals)
        wins = r_vals[r_vals > 0]
        losses = r_vals[r_vals < 0]
        wr = (len(wins) / n_t) * 100.0 if n_t > 0 else 0.0
        gw = float(np.sum(wins)); gl = float(abs(np.sum(losses)))
        pf = (gw / gl) if gl > 0 else 99.0
        net_exp = float(np.mean(r_vals))
        tot_r = float(np.sum(r_vals))
        cum = np.cumsum(r_vals)
        mdd = float(np.max(np.maximum.accumulate(cum) - cum))
        avg_w = float(np.mean(wins)) if len(wins) > 0 else 0.0
        avg_l = float(abs(np.mean(losses))) if len(losses) > 0 else 0.0
        
        # 95% Confidence Interval for Expectancy
        std_r = float(np.std(r_vals, ddof=1)) if n_t > 1 else 1.0
        se = std_r / np.sqrt(n_t) if n_t > 1 else 1.0
        ci_low = net_exp - (1.96 * se)
        ci_high = net_exp + (1.96 * se)

        return {
            "label": label, "n": n_t, "wr": round(wr, 2), "pf": round(pf, 3),
            "net_exp": round(net_exp, 4), "ci_95": f"[{ci_low:.4f}, {ci_high:.4f}]",
            "tot_r": round(tot_r, 2), "mdd": round(mdd, 2),
            "avg_win_r": round(avg_w, 4), "avg_loss_r": round(avg_l, 4),
            "realized_rr": round(avg_w / avg_l, 3) if avg_l > 0 else 0.0
        }

    is_trades = [t for t in trades if t["partition"] == "IN_SAMPLE"]
    val_trades = [t for t in trades if t["partition"] == "VALIDATION"]
    pre_is_trades = [t for t in trades if t["partition"] == "PRE_IS_HISTORICAL"]

    res_is = evaluate_trades(is_trades, "In-Sample (2021-08-23 to 2024-08-21)")
    res_val = evaluate_trades(val_trades, "Validation (2024-08-22 to 2025-08-21)")
    res_pre = evaluate_trades(pre_is_trades, "Pre-IS Historical (2015-01-01 to 2021-08-22)")
    res_all = evaluate_trades(trades, "Combined Complete (2015-2025)")

    print("\n" + "=" * 80)
    print("STRAT-07 REVALIDATION RESULTS")
    print("=" * 80)
    for res in [res_pre, res_is, res_val, res_all]:
        print(f"{res['label']:<40} | N={res['n']:<3} | WR={res['wr']:5.2f}% | PF={res['pf']:5.3f} | Exp={res['net_exp']:+.4f}R ({res['ci_95']}) | MDD={res['mdd']}R | NetR={res['tot_r']:+.2f}R")

    # Long vs Short
    val_long = [t for t in val_trades if t["direction"] == "LONG"]
    val_short = [t for t in val_trades if t["direction"] == "SHORT"]
    res_val_l = evaluate_trades(val_long, "Validation LONG")
    res_val_s = evaluate_trades(val_short, "Validation SHORT")

    is_long = [t for t in is_trades if t["direction"] == "LONG"]
    is_short = [t for t in is_trades if t["direction"] == "SHORT"]
    res_is_l = evaluate_trades(is_long, "In-Sample LONG")
    res_is_s = evaluate_trades(is_short, "In-Sample SHORT")

    # Export STRAT07_IS_RESULTS.csv
    with open("/home/vallencia/xauusd_research/STRAT07_IS_RESULTS.csv", "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(res_is.keys()))
        writer.writeheader()
        writer.writerow(res_is)
        writer.writerow(res_is_l)
        writer.writerow(res_is_s)
    print("Saved STRAT07_IS_RESULTS.csv")

    # Export STRAT07_VALIDATION_RESULTS.csv
    with open("/home/vallencia/xauusd_research/STRAT07_VALIDATION_RESULTS.csv", "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(res_val.keys()))
        writer.writeheader()
        writer.writerow(res_val)
        writer.writerow(res_val_l)
        writer.writerow(res_val_s)
    print("Saved STRAT07_VALIDATION_RESULTS.csv")

    # Annual breakdown
    annual_stats = []
    for yr in range(2015, 2026):
        yr_tr = [t for t in trades if t["year"] == yr]
        if yr_tr:
            e = evaluate_trades(yr_tr, f"Year {yr}")
            annual_stats.append(e)

    # Cost Sensitivity for STRAT-07
    # Test spread variations: $0.30, $0.41 (baseline), $0.50, $0.75, $1.00
    print("\nRunning Cost Sensitivity Test on STRAT-07...")
    cost_sens = []
    for sp_test in [0.30, 0.41, 0.50, 0.75, 1.00]:
        # Simple re-evaluation of trades with new spread
        r_sens = []
        for t in trades:
            sp_diff = sp_test - SPREAD_TOKYO
            # For each trade, additional cost is sp_diff * lots * 100 / RISK_BUDGET
            lots = t["lots"]
            added_drag = (sp_diff * lots * 100.0) / RISK_BUDGET
            r_sens.append(t["realized_r"] - added_drag)
        r_arr = np.array(r_sens)
        gw = sum(x for x in r_arr if x > 0); gl = abs(sum(x for x in r_arr if x < 0))
        pf_sens = gw / gl if gl > 0 else 99.0
        exp_sens = float(np.mean(r_arr))
        wr_sens = sum(1 for x in r_arr if x > 0) / len(r_arr) * 100.0
        cost_sens.append({
            "spread_tested": sp_test,
            "win_rate": round(wr_sens, 2),
            "profit_factor": round(pf_sens, 3),
            "net_expectancy_r": round(exp_sens, 4),
            "status": "PASS" if pf_sens > 1.0 else "FAIL"
        })
        print(f"Spread ${sp_test:.2f} | WR={wr_sens:5.2f}% | PF={pf_sens:5.3f} | Exp={exp_sens:+.4f}R -> {'PROFITABLE' if pf_sens > 1.0 else 'UNPROFITABLE'}")

    summary_payload = {
        "metadata": {
            "strategy": "STRAT-07",
            "timeframe": "M1",
            "session": "Tokyo 08:15 WIB (01:15 UTC)",
            "execution_model": "Market Order with Ask/Bid separation",
            "spread_used": SPREAD_TOKYO,
            "commission_round": COMMISSION_ROUND,
            "slippage": SLIPPAGE_MARKET,
            "target_rr": 1.50
        },
        "in_sample_results": res_is,
        "validation_results": res_val,
        "pre_is_results": res_pre,
        "combined_results": res_all,
        "annual_breakdown": annual_stats,
        "cost_sensitivity": cost_sens
    }

    with open("/home/vallencia/xauusd_research/data/strat07_revalidation_summary.json", "w") as fp:
        json.dump(summary_payload, fp, indent=2)
    print("Saved summary JSON.")

if __name__ == "__main__":
    run_revalidation()
