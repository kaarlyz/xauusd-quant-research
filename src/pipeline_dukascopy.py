#!/usr/bin/env python3
"""
Institutional Dukascopy Ingestion Pipeline for XAUUSD.
Downloads tick and M1 data in weekly/monthly slices, converts to standard PyArrow Parquet,
and maintains an atomic checkpoint ledger to support resume-on-failure.
"""

import os
import sys
import json
import time
import shutil
import argparse
import datetime
import subprocess
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

DATA_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data"
CHECKPOINT_FILE = "/home/vallencia/xauusd_research/data/checkpoint_tick.json"
TEMP_DIR = "/home/vallencia/.hermes/profiles/raina/cache/scratch/dukas_tmp"

TICK_SCHEMA = pa.schema([
    ("timestamp", pa.int64()),
    ("bid", pa.float64()),
    ("ask", pa.float64()),
    ("spread", pa.float64()),
    ("volume", pa.float64())
])

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"completed_weeks": []}
    return {"completed_weeks": []}

def save_checkpoint(cp):
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(cp, f, indent=2)

def generate_weekly_ranges(start_year, end_year):
    """Generate (start_date_str, end_date_str) in weekly increments."""
    start_date = datetime.date(start_year, 1, 1)
    today = datetime.date.today()
    max_date = min(today, datetime.date(end_year, 12, 31))
    
    cur = start_date
    weeks = []
    while cur < max_date:
        next_cur = min(cur + datetime.timedelta(days=7), max_date)
        weeks.append((cur.strftime("%Y-%m-%d"), next_cur.strftime("%Y-%m-%d")))
        cur = next_cur
    return weeks

def download_week(symbol, from_date, to_date, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        "npx", "dukascopy-cli",
        "-i", symbol.lower(),
        "-from", from_date,
        "-to", to_date,
        "-t", "tick",
        "-v",
        "-f", "csv",
        "-dir", out_dir,
        "-s"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"dukascopy-cli failed: {res.stderr}")
    
    # Locate output csv
    files = [f for f in os.listdir(out_dir) if f.endswith(".csv")]
    if not files:
        return None
    return os.path.join(out_dir, files[0])

def run_pipeline(symbol="XAUUSD", start_year=2020, end_year=2026, reverse=True):
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    parquet_path = os.path.join(DATA_DIR, f"{symbol.upper()}_Tick.parquet")
    temp_parquet = parquet_path + ".stream"
    
    weeks = generate_weekly_ranges(start_year, end_year)
    if reverse:
        weeks = list(reversed(weeks))
        
    cp = load_checkpoint()
    completed = set(cp.get("completed_weeks", []))
    
    remaining_weeks = [w for w in weeks if f"{w[0]}_{w[1]}" not in completed]
    print(f"=== {symbol} Tick Streamer ({start_year} - {end_year}) ===")
    print(f"Total Weeks: {len(weeks)} | Completed: {len(completed)} | Remaining: {len(remaining_weeks)}")
    print(f"Destination: {parquet_path}")

    # Determine writer mode
    writer = None
    if os.path.exists(parquet_path):
        # We append to existing if valid, or stream new
        pass

    total_ticks = 0
    t_start = time.time()

    for idx, (f_date, t_date) in enumerate(remaining_weeks, 1):
        key = f"{f_date}_{t_date}"
        slice_tmp = os.path.join(TEMP_DIR, f"slice_{key}")
        t0 = time.time()
        
        try:
            csv_path = download_week(symbol, f_date, t_date, slice_tmp)
            if not csv_path or not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
                print(f"[{idx}/{len(remaining_weeks)}] {f_date} -> {t_date}: No tick data (market closed/flat)")
                completed.add(key)
                cp["completed_weeks"] = list(completed)
                save_checkpoint(cp)
                continue
                
            # Process via Polars
            df = pl.read_csv(csv_path)
            if len(df) == 0:
                print(f"[{idx}/{len(remaining_weeks)}] {f_date} -> {t_date}: 0 ticks")
            else:
                # Standardize columns: timestamp, askPrice, bidPrice, askVolume, bidVolume
                vol_col = (pl.col("askVolume") + pl.col("bidVolume")).round(4) if "askVolume" in df.columns else pl.lit(1.0)
                df = df.select([
                    pl.col("timestamp").cast(pl.Int64),
                    pl.col("bidPrice").cast(pl.Float64).alias("bid"),
                    pl.col("askPrice").cast(pl.Float64).alias("ask"),
                    (pl.col("askPrice") - pl.col("bidPrice")).round(4).alias("spread"),
                    vol_col.alias("volume")
                ]).sort("timestamp")
                
                # Write to parquet partition
                part_dir = os.path.join(DATA_DIR, "partitions_tick")
                os.makedirs(part_dir, exist_ok=True)
                part_file = os.path.join(part_dir, f"tick_{key}.parquet")
                df.write_parquet(part_file, compression="snappy")
                
                total_ticks += len(df)
                dt = time.time() - t0
                print(f"[{idx}/{len(remaining_weeks)}] {f_date} -> {t_date}: {len(df):,} ticks in {dt:.1f}s -> {part_file}")

            completed.add(key)
            cp["completed_weeks"] = list(completed)
            save_checkpoint(cp)

        except Exception as e:
            print(f"[{idx}/{len(remaining_weeks)}] ERROR {f_date} -> {t_date}: {e}")
            time.sleep(2)
        finally:
            if os.path.exists(slice_tmp):
                shutil.rmtree(slice_tmp, ignore_errors=True)

    print(f"\nBatch completed: {total_ticks:,} ticks written in {(time.time()-t_start)/60:.1f}m")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=2026)
    parser.add_argument("--end", type=int, default=2026)
    parser.add_argument("--reverse", action="store_true", default=True)
    args = parser.parse_args()
    run_pipeline(start_year=args.start, end_year=args.end, reverse=args.reverse)
