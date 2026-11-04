#!/usr/bin/env python3
"""
Pipeline Downloader: BTCUSD M1 Historical Master Dataset (2017 to 2026).
Downloads annual M1 chunks from Dukascopy via dukascopy-node,
validates schema and timestamps, and creates BTCUSD_M1.parquet.
"""

import os
import sys
import glob
import subprocess
import datetime
import polars as pl

BASE_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data"
TEMP_DIR = os.path.join(BASE_DIR, "btcusd_m1_temp")
TARGET_PARQUET = os.path.join(BASE_DIR, "BTCUSD_M1.parquet")
os.makedirs(TEMP_DIR, exist_ok=True)

CHUNKS = [
    ("2017-05-07", "2017-12-31"),
    ("2018-01-01", "2018-12-31"),
    ("2019-01-01", "2019-12-31"),
    ("2020-01-01", "2020-12-31"),
    ("2021-01-01", "2021-12-31"),
    ("2022-01-01", "2022-12-31"),
    ("2023-01-01", "2023-12-31"),
    ("2024-01-01", "2024-12-31"),
    ("2025-01-01", "2025-12-31"),
    ("2026-01-01", "2026-10-31"),
]

def download_btcusd():
    print("=" * 70)
    print("STARTING BTCUSD M1 HISTORICAL PIPELINE (2017 - 2026)")
    print("=" * 70)

    for d_from, d_to in CHUNKS:
        yr = d_from[:4]
        out_fn = f"BTCUSD-m1-{yr}"
        actual_json = os.path.join(TEMP_DIR, f"{out_fn}.json")

        if os.path.exists(actual_json) and os.path.getsize(actual_json) > 100000:
            print(f"[{yr}] Already downloaded ({os.path.getsize(actual_json):,} bytes).")
            continue

        print(f"[{yr}] Downloading BTCUSD M1: {d_from} to {d_to}...")
        cmd = [
            "npx", "-y", "dukascopy-node",
            "-i", "btcusd",
            "-from", d_from,
            "-to", d_to,
            "-t", "m1",
            "-p", "bid",
            "-v",
            "-f", "json",
            "-dir", TEMP_DIR,
            "-fn", out_fn,
            "--silent"
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            produced = glob.glob(os.path.join(TEMP_DIR, f"{out_fn}*.json"))
            if produced:
                sz = os.path.getsize(produced[0])
                print(f"   -> OK: {os.path.basename(produced[0])} ({sz:,} bytes)")
        except Exception as e:
            print(f"   -> Error on {yr}: {e}")

    print("\nConsolidating BTCUSD into Parquet...")
    json_files = sorted(glob.glob(os.path.join(TEMP_DIR, "*.json*")))
    if not json_files:
        print("No JSON files found. Exiting.")
        return

    dfs = []
    for fp in json_files:
        try:
            sub = pl.read_json(fp)
            if len(sub) == 0: continue
            if "volume" not in sub.columns:
                sub = sub.with_columns(pl.lit(1.0).alias("volume"))
            else:
                sub = sub.with_columns(pl.col("volume").cast(pl.Float64))

            sub = sub.select([
                pl.col("timestamp").cast(pl.Int64),
                pl.col("open").cast(pl.Float64),
                pl.col("high").cast(pl.Float64),
                pl.col("low").cast(pl.Float64),
                pl.col("close").cast(pl.Float64),
                pl.col("volume").cast(pl.Float64),
            ])
            dfs.append(sub)
        except Exception as e:
            print(f"Error reading {fp}: {e}")

    if dfs:
        master_df = pl.concat(dfs).unique(subset=["timestamp"]).sort("timestamp")
        master_df.write_parquet(TARGET_PARQUET, compression="zstd")
        sz_pq = os.path.getsize(TARGET_PARQUET)
        t_min = datetime.datetime.fromtimestamp(master_df["timestamp"].min() // 1000, tz=datetime.timezone.utc)
        t_max = datetime.datetime.fromtimestamp(master_df["timestamp"].max() // 1000, tz=datetime.timezone.utc)
        print(f"\nSUCCESS BTCUSD: {len(master_df):,} bars | {t_min.strftime('%Y-%m-%d')} s/d {t_max.strftime('%Y-%m-%d')} | Size: {sz_pq/(1024*1024):.1f} MB")

        # Cleanup JSON files
        for fp in json_files:
            try: os.remove(fp)
            except: pass

if __name__ == "__main__":
    download_btcusd()
