#!/usr/bin/env python3
"""
Pipeline Downloader: XAUUSD M1 Historical Extension (2003-05-05 to 2014-12-31).
Downloads annual M1 chunks from Dukascopy via dukascopy-node,
validates schema and timestamps, and appends them to XAUUSD_M1.parquet.
"""

import os
import sys
import json
import subprocess
import datetime
import polars as pl

MASTER_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
TEMP_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data/m1_history_temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# 2003-05-05 to 2014-12-31 chunks
CHUNKS = [
    ("2003-05-05", "2003-12-31"),
    ("2004-01-01", "2004-12-31"),
    ("2005-01-01", "2005-12-31"),
    ("2006-01-01", "2006-12-31"),
    ("2007-01-01", "2007-12-31"),
    ("2008-01-01", "2008-12-31"),
    ("2009-01-01", "2009-12-31"),
    ("2010-01-01", "2010-12-31"),
    ("2011-01-01", "2011-12-31"),
    ("2012-01-01", "2012-12-31"),
    ("2013-01-01", "2013-12-31"),
    ("2014-01-01", "2014-12-31"),
]

def download_and_process():
    print("=" * 70)
    print("STARTING XAUUSD M1 HISTORICAL EXTENSION PIPELINE (2003 - 2014)")
    print("=" * 70)

    downloaded_files = []

    for d_from, d_to in CHUNKS:
        yr = d_from[:4]
        out_name = f"xauusd-m1-{yr}"
        # dukascopy-node automatically appends .json when format is json
        out_path = os.path.join(TEMP_DIR, f"{out_name}.json")

        if os.path.exists(out_path) and os.path.getsize(out_path) > 100000:
            print(f"[{yr}] Already downloaded: {out_path} ({os.path.getsize(out_path):,} bytes)")
            downloaded_files.append(out_path)
            continue

        print(f"\n[{yr}] Downloading M1: {d_from} to {d_to}...")
        cmd = [
            "npx", "-y", "dukascopy-node",
            "-i", "xauusd",
            "-from", d_from,
            "-to", d_to,
            "-t", "m1",
            "-p", "bid",
            "-v",
            "-f", "json",
            "-dir", TEMP_DIR,
            "-fn", out_name,
            "--silent"
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if os.path.exists(out_path):
                sz = os.path.getsize(out_path)
                print(f"[{yr}] Downloaded successfully: {sz:,} bytes")
                downloaded_files.append(out_path)
            else:
                print(f"[{yr}] Warning: File not found after download: {out_path}")
        except Exception as e:
            print(f"[{yr}] Error downloading: {e}")
            if res.stderr:
                print(f"Stderr: {res.stderr}")

    print("\n" + "=" * 70)
    print("ALL CHUNKS DOWNLOADED. PARSING AND CONSOLIDATING...")
    print("=" * 70)

    # Re-scan TEMP_DIR for all completed json files
    completed_files = [os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR) if f.endswith(".json") and not f.endswith(".part")]
    print(f"Found {len(completed_files)} completed JSON files in {TEMP_DIR}.")

    new_dfs = []
    for fp in sorted(completed_files):
        print(f"Reading {os.path.basename(fp)}...")
        try:
            # Read JSON with polars
            # Schema expected: timestamp, open, high, low, close, volume (if present)
            sub_df = pl.read_json(fp)
            if "volume" not in sub_df.columns:
                sub_df = sub_df.with_columns(pl.lit(1.0).alias("volume"))
            else:
                sub_df = sub_df.with_columns(pl.col("volume").cast(pl.Float64))

            # Select exact schema: timestamp, open, high, low, close, volume
            sub_df = sub_df.select([
                pl.col("timestamp").cast(pl.Int64),
                pl.col("open").cast(pl.Float64),
                pl.col("high").cast(pl.Float64),
                pl.col("low").cast(pl.Float64),
                pl.col("close").cast(pl.Float64),
                pl.col("volume").cast(pl.Float64),
            ])
            new_dfs.append(sub_df)
            print(f"  Loaded {len(sub_df):,} bars.")
        except Exception as e:
            print(f"Error parsing {fp}: {e}")

    if not new_dfs:
        print("No new data downloaded. Exiting.")
        return

    consolidated_new = pl.concat(new_dfs).sort("timestamp")
    print(f"\nTotal new historical bars (2003-2014): {len(consolidated_new):,}")

    # Load existing Master Parquet
    print(f"Loading existing Master Parquet: {MASTER_PARQUET}...")
    existing_df = pl.read_parquet(MASTER_PARQUET)
    print(f"Existing bars (2015-2026): {len(existing_df):,}")

    # Combine
    combined = pl.concat([consolidated_new, existing_df]).unique(subset=["timestamp"]).sort("timestamp")
    print(f"Combined Master Total: {len(combined):,} M1 bars.")

    t_min = combined["timestamp"].min()
    t_max = combined["timestamp"].max()
    dt_min = datetime.datetime.fromtimestamp(t_min // 1000, tz=datetime.timezone.utc)
    dt_max = datetime.datetime.fromtimestamp(t_max // 1000, tz=datetime.timezone.utc)
    print(f"New Master Coverage: {dt_min.isoformat()} to {dt_max.isoformat()} (~23.5 Years!)")

    # Backup existing
    backup_path = MASTER_PARQUET + ".bak"
    if not os.path.exists(backup_path):
        print(f"Creating backup: {backup_path}...")
        os.system(f"cp '{MASTER_PARQUET}' '{backup_path}'")

    # Write new master parquet
    print(f"Writing updated Master Parquet to {MASTER_PARQUET}...")
    combined.write_parquet(MASTER_PARQUET, compression="zstd")
    print(f"New file size: {os.path.getsize(MASTER_PARQUET):,} bytes")
    print("M1 PIPELINE COMPLETE SUCCESS!")

if __name__ == "__main__":
    download_and_process()
