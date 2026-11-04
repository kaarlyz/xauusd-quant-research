#!/usr/bin/env python3
import os
import glob
import datetime
import polars as pl

MASTER_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"
TEMP_DIR = "/home/vallencia/Projects/myfxjournal/server/data/market-data/m1_history_temp"

def merge():
    files = sorted(glob.glob(os.path.join(TEMP_DIR, "*.json*")))
    print(f"Found {len(files)} JSON files in {TEMP_DIR}:")
    for f in files:
        print(f"  {os.path.basename(f)}: {os.path.getsize(f):,} bytes")

    new_dfs = []
    for fp in files:
        print(f"Reading {os.path.basename(fp)}...")
        sub_df = pl.read_json(fp)
        if "volume" not in sub_df.columns:
            sub_df = sub_df.with_columns(pl.lit(1.0).alias("volume"))
        else:
            sub_df = sub_df.with_columns(pl.col("volume").cast(pl.Float64))

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

    consolidated_new = pl.concat(new_dfs).sort("timestamp")
    print(f"\nTotal new historical bars (2003-2014): {len(consolidated_new):,}")

    print(f"Loading existing Master Parquet: {MASTER_PARQUET}...")
    existing_df = pl.read_parquet(MASTER_PARQUET)
    print(f"Existing bars (2015-2026): {len(existing_df):,}")

    combined = pl.concat([consolidated_new, existing_df]).unique(subset=["timestamp"]).sort("timestamp")
    print(f"Combined Master Total: {len(combined):,} M1 bars.")

    t_min = combined["timestamp"].min()
    t_max = combined["timestamp"].max()
    dt_min = datetime.datetime.fromtimestamp(t_min // 1000, tz=datetime.timezone.utc)
    dt_max = datetime.datetime.fromtimestamp(t_max // 1000, tz=datetime.timezone.utc)
    print(f"New Master Coverage: {dt_min.isoformat()} to {dt_max.isoformat()} (~23.5 Years!)")

    backup_path = MASTER_PARQUET + ".bak"
    if not os.path.exists(backup_path):
        print(f"Creating backup: {backup_path}...")
        os.system(f"cp '{MASTER_PARQUET}' '{backup_path}'")

    print(f"Writing updated Master Parquet to {MASTER_PARQUET}...")
    combined.write_parquet(MASTER_PARQUET, compression="zstd")
    print(f"New file size: {os.path.getsize(MASTER_PARQUET):,} bytes")
    print("SUCCESS: 2003-2026 M1 DATASET MERGED!")

if __name__ == "__main__":
    merge()
