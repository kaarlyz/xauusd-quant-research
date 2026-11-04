#!/usr/bin/env python3
"""
Phase 1B: Data Coverage Reconciliation, Tick Integrity, and Spread Distribution Audit.
"""

import os
import csv
import json
import datetime
import numpy as np
import polars as pl

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
TICK_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data/partitions_tick"
OUTPUT_CSV = "/home/vallencia/xauusd_research/DATA_COVERAGE_RECONCILIATION.csv"

def run_phase1b_analysis():
    print("=== 1. Reconciling All Tick Partitions & Checking Integrity ===")
    tick_files = sorted([f for f in os.listdir(TICK_DIR) if f.endswith(".parquet")])
    print(f"Total Tick Partitions found: {len(tick_files)}")

    reconciliation_rows = []
    total_ticks_count = 0
    corrupt_files = 0
    all_spreads_by_hour = {h: [] for h in range(24)}

    # Sample partitions across years for detailed spread distribution
    # We will sample 1 partition per month (~70 partitions) to get a massive, representative sample
    sample_partitions = tick_files[::5] # every 5th partition (~72 partitions across 2020-2026)

    min_tick_ts = 1e15
    max_tick_ts = 0

    tick_sizes = []

    for idx, f in enumerate(tick_files):
        p = os.path.join(TICK_DIR, f)
        try:
            # Read metadata / scan
            df_t = pl.read_parquet(p)
            n_ticks = len(df_t)
            total_ticks_count += n_ticks

            t_start = df_t["timestamp"].min()
            t_end = df_t["timestamp"].max()
            if t_start < min_tick_ts: min_tick_ts = t_start
            if t_end > max_tick_ts: max_tick_ts = t_end

            dt_s = datetime.datetime.fromtimestamp(t_start // 1000, tz=datetime.timezone.utc)
            dt_e = datetime.datetime.fromtimestamp(t_end // 1000, tz=datetime.timezone.utc)

            # Sample spreads
            if f in sample_partitions:
                hours = (df_t["timestamp"] // 1000 // 3600 % 24).to_numpy()
                spreads = df_t["spread"].to_numpy()
                for h_val in range(24):
                    mask = (hours == h_val)
                    if np.any(mask):
                        # Take random 500 spreads per hour per partition
                        sub_sp = spreads[mask]
                        if len(sub_sp) > 500:
                            sub_sp = np.random.choice(sub_sp, size=500, replace=False)
                        all_spreads_by_hour[h_val].extend(sub_sp)

                # Check tick size (difference between consecutive unique bid prices)
                bids = df_t["bid"].head(10000).to_numpy()
                diffs = np.abs(np.diff(bids))
                diffs = diffs[diffs > 0]
                if len(diffs) > 0:
                    tick_sizes.append(float(np.min(diffs)))

            reconciliation_rows.append({
                "partition_file": f,
                "ticks_count": n_ticks,
                "start_utc": dt_s.isoformat(),
                "end_utc": dt_e.isoformat(),
                "mean_spread": round(float(df_t["spread"].mean()), 4),
                "median_spread": round(float(df_t["spread"].median()), 4),
                "status": "VALID"
            })
        except Exception as e:
            corrupt_files += 1
            reconciliation_rows.append({
                "partition_file": f,
                "ticks_count": 0,
                "start_utc": "CORRUPT",
                "end_utc": "CORRUPT",
                "mean_spread": 0,
                "median_spread": 0,
                "status": f"ERROR: {str(e)}"
            })

    print(f"Total Ticks across all partitions: {total_ticks_count:,}")
    print(f"Corrupt Partitions: {corrupt_files}")
    dt_min_tick = datetime.datetime.fromtimestamp(min_tick_ts // 1000, tz=datetime.timezone.utc)
    dt_max_tick = datetime.datetime.fromtimestamp(max_tick_ts // 1000, tz=datetime.timezone.utc)
    print(f"Global Tick Coverage: {dt_min_tick.isoformat()} to {dt_max_tick.isoformat()}")

    # Save DATA_COVERAGE_RECONCILIATION.csv
    print(f"Writing reconciliation to {OUTPUT_CSV}...")
    with open(OUTPUT_CSV, "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=["partition_file", "ticks_count", "start_utc", "end_utc", "mean_spread", "median_spread", "status"])
        writer.writeheader()
        writer.writerows(reconciliation_rows)
    print("Reconciliation CSV saved.")

    # 2. Hourly Spread Distribution Table
    print("\n=== 2. Empirical Hourly Spread Distribution (UTC) ===")
    spread_stats_by_hour = {}
    print(f"{'Hour (UTC)':<12} | {'Session':<18} | {'Median Spread':<15} | {'Mean Spread':<15} | {'P95 Spread':<15} | {'Max Spread'}")
    print("-" * 90)
    for h in range(24):
        sp_arr = np.array(all_spreads_by_hour[h])
        if len(sp_arr) > 0:
            med = float(np.median(sp_arr))
            mean = float(np.mean(sp_arr))
            p95 = float(np.percentile(sp_arr, 95))
            max_sp = float(np.max(sp_arr))
        else:
            med = mean = p95 = max_sp = 0.0

        session = "Tokyo" if 0 <= h < 7 else ("London" if 7 <= h < 12 else ("London/NY Overlap" if 12 <= h < 16 else ("NY Afternoon" if 16 <= h < 21 else "ROLLOVER (Blacklist)")))
        spread_stats_by_hour[h] = {
            "session": session,
            "median": round(med, 4),
            "mean": round(mean, 4),
            "p95": round(p95, 4),
            "max": round(max_sp, 4)
        }
        print(f"Hour {h:02d}:00 UTC  | {session:<18} | ${med:<14.4f} | ${mean:<14.4f} | ${p95:<14.4f} | ${max_sp:.4f}")

    # 3. Minimum Tick Size Verification
    min_tick = float(min(tick_sizes)) if tick_sizes else 0.001
    print(f"\nMinimum Observed Price Increment (Tick Size): ${min_tick:.4f}")

    # 4. Save results to JSON
    with open("/home/vallencia/xauusd_research/data/phase1b_analysis.json", "w") as fp:
        json.dump({
            "total_ticks": total_ticks_count,
            "min_tick_size": min_tick,
            "tick_coverage_start": dt_min_tick.isoformat(),
            "tick_coverage_end": dt_max_tick.isoformat(),
            "hourly_spread_stats": spread_stats_by_hour
        }, fp, indent=2)

if __name__ == "__main__":
    run_phase1b_analysis()
