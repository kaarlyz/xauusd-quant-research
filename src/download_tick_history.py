#!/usr/bin/env python3
"""
Pipeline Downloader: XAUUSD Historical Tick Partitions (2003 to 2019).
Downloads weekly partitions from Dukascopy via dukascopy-node,
formats into Parquet, and saves to /home/vallencia/Projects/myfxjournal/server/data/market-data/partitions_tick/
"""

import os
import sys
import datetime
import subprocess
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

TICK_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data/partitions_tick"
TEMP_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data/tick_history_temp"
os.makedirs(TICK_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Generate weekly intervals from 2003-05-05 to 2020-01-01
def get_weekly_intervals():
    start = datetime.date(2003, 5, 5)
    end = datetime.date(2020, 1, 1)
    cur = start
    intervals = []
    while cur < end:
        next_w = cur + datetime.timedelta(days=7)
        if next_w > end:
            next_w = end
        intervals.append((cur.strftime("%Y-%m-%d"), next_w.strftime("%Y-%m-%d")))
        cur = next_w
    return intervals

def run_tick_pipeline():
    print("=" * 70)
    print("XAUUSD HISTORICAL TICK PIPELINE (2003 - 2019)")
    print("=" * 70)

    intervals = get_weekly_intervals()
    print(f"Total Weekly Partitions to Process: {len(intervals)}")

    for idx, (d_from, d_to) in enumerate(intervals):
        target_name = f"tick_{d_from}_{d_to}.parquet"
        target_path = os.path.join(TICK_DIR, target_name)

        if os.path.exists(target_path) and os.path.getsize(target_path) > 10000:
            continue

        temp_json = os.path.join(TEMP_DIR, f"temp_{d_from}_{d_to}")
        actual_json = temp_json + ".json"
        print(f"[{idx+1}/{len(intervals)}] Downloading Tick: {d_from} to {d_to}...")

        cmd = [
            "npx", "-y", "dukascopy-node",
            "-i", "xauusd",
            "-from", d_from,
            "-to", d_to,
            "-t", "tick",
            "-f", "json",
            "-dir", TEMP_DIR,
            "-fn", os.path.basename(temp_json),
            "--silent"
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if os.path.exists(actual_json) and os.path.getsize(actual_json) > 100:
                df_t = pl.read_json(actual_json)
                if len(df_t) > 0:
                    c_cols = df_t.columns
                    ask_col = "askPrice" if "askPrice" in c_cols else "ask"
                    bid_col = "bidPrice" if "bidPrice" in c_cols else "bid"
                    vol_col = "volume" if "volume" in c_cols else None

                    exprs = [
                        pl.col("timestamp").cast(pl.Int64),
                        pl.col(bid_col).cast(pl.Float64).alias("bid"),
                        pl.col(ask_col).cast(pl.Float64).alias("ask"),
                        (pl.col(ask_col).cast(pl.Float64) - pl.col(bid_col).cast(pl.Float64)).alias("spread"),
                    ]
                    if vol_col and vol_col in c_cols:
                        exprs.append(pl.col(vol_col).cast(pl.Float64).alias("volume"))
                    else:
                        exprs.append(pl.lit(0.001).alias("volume"))

                    df_clean = df_t.select(exprs).sort("timestamp")
                    df_clean.write_parquet(target_path, compression="zstd")
                    print(f"   -> Saved Parquet: {target_name} ({len(df_clean):,} ticks, {os.path.getsize(target_path):,} bytes)")
                
                os.remove(actual_json)
            elif os.path.exists(actual_json):
                os.remove(actual_json)
        except Exception as e:
            print(f"   Error on {d_from}_{d_to}: {e}")

    print("\nTICK PIPELINE FINISHED!")

if __name__ == "__main__":
    run_tick_pipeline()
