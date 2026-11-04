#!/usr/bin/env python3
"""
Multi-Asset Historical M1 Pipeline Downloader & Parquet Consolidator.
Assets to download:
1. USATECHIDXUSD (NAS100): 2011 to 2026 (~15 years)
2. EURUSD: 2003 to 2026 (~23.5 years)
3. GBPUSD: 2003 to 2026 (~23.5 years)
4. GBPJPY: 2003 to 2026 (~23.5 years)

Saves into /home/vallencia/Projects/myfxjournal/server/data/market-data/<PAIR>_M1.parquet
"""

import os
import sys
import glob
import subprocess
import datetime
import polars as pl

BASE_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data"
TEMP_BASE = "/home/vallencia/Projects/myfxjournal/server/data/market-data/multi_m1_temp"
os.makedirs(TEMP_BASE, exist_ok=True)

ASSET_CONFIGS = [
    {
        "id": "usatechidxusd",
        "name": "NAS100",
        "start_year": 2011,
        "end_year": 2026,
        "start_date": "2011-09-19",
    },
    {
        "id": "eurusd",
        "name": "EURUSD",
        "start_year": 2003,
        "end_year": 2026,
        "start_date": "2003-05-05",
    },
    {
        "id": "gbpusd",
        "name": "GBPUSD",
        "start_year": 2003,
        "end_year": 2026,
        "start_date": "2003-05-05",
    },
    {
        "id": "gbpjpy",
        "name": "GBPJPY",
        "start_year": 2003,
        "end_year": 2026,
        "start_date": "2003-08-04",
    },
]

def download_pair(cfg):
    pair_id = cfg["id"]
    pair_name = cfg["name"]
    target_parquet = os.path.join(BASE_DIR, f"{pair_name}_M1.parquet")
    pair_temp = os.path.join(TEMP_BASE, pair_name)
    os.makedirs(pair_temp, exist_ok=True)

    print("\n" + "=" * 70)
    print(f"PROCESSING {pair_name} ({pair_id.upper()}) M1 HISTORICAL DATA")
    print(f"Coverage: {cfg['start_year']} to {cfg['end_year']}")
    print("=" * 70)

    # Generate annual intervals
    years = range(cfg["start_year"], cfg["end_year"] + 1)
    for yr in years:
        out_fn = f"{pair_name}-m1-{yr}"
        actual_json = os.path.join(pair_temp, f"{out_fn}.json")

        if os.path.exists(actual_json) and os.path.getsize(actual_json) > 100000:
            print(f"[{pair_name} {yr}] Already downloaded ({os.path.getsize(actual_json):,} bytes).")
            continue

        d_from = f"{yr}-01-01"
        if yr == cfg["start_year"]:
            d_from = cfg["start_date"]
        d_to = f"{yr}-12-31" if yr < 2026 else "2026-10-31"

        print(f"[{pair_name} {yr}] Downloading: {d_from} to {d_to}...")
        cmd = [
            "npx", "-y", "dukascopy-node",
            "-i", pair_id,
            "-from", d_from,
            "-to", d_to,
            "-t", "m1",
            "-p", "bid",
            "-v",
            "-f", "json",
            "-dir", pair_temp,
            "-fn", out_fn,
            "--silent"
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Find produced file
            produced = glob.glob(os.path.join(pair_temp, f"{out_fn}*.json"))
            if produced:
                sz = os.path.getsize(produced[0])
                print(f"   -> OK: {os.path.basename(produced[0])} ({sz:,} bytes)")
        except Exception as e:
            print(f"   -> Error on {pair_name} {yr}: {e}")

    # Consolidate into Master Parquet
    print(f"\nConsolidating {pair_name} into {target_parquet}...")
    json_files = sorted(glob.glob(os.path.join(pair_temp, "*.json*")))
    if not json_files:
        print(f"No JSON files found for {pair_name}. Skipping.")
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
        master_df.write_parquet(target_parquet, compression="zstd")
        sz_pq = os.path.getsize(target_parquet)
        t_min = datetime.datetime.fromtimestamp(master_df["timestamp"].min() // 1000, tz=datetime.timezone.utc)
        t_max = datetime.datetime.fromtimestamp(master_df["timestamp"].max() // 1000, tz=datetime.timezone.utc)
        print(f"SUCCESS {pair_name}: {len(master_df):,} bars | {t_min.strftime('%Y-%m-%d')} s/d {t_max.strftime('%Y-%m-%d')} | Size: {sz_pq/(1024*1024):.1f} MB")
        
        # Clean up JSON files to save storage
        for fp in json_files:
            try: os.remove(fp)
            except: pass

def run_all():
    print("STARTING BATCH DOWNLOAD FOR MULTI-ASSET M1 MASTER DATASETS")
    for cfg in ASSET_CONFIGS:
        download_pair(cfg)
    print("\nALL ASSETS SUCCESSFULLY DOWNLOADED AND CONVERTED TO PARQUET!")

if __name__ == "__main__":
    run_all()
