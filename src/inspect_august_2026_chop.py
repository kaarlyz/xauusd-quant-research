#!/usr/bin/env python3
"""
Bedah Visualisasi Periode Drawdown 2026 di M1 vs M15 & H1 (5 - 9 Agustus 2026).
Memeriksa pergerakan harga, span kotak, dan status EMA di M15 & H1.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

BTC_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/BTCUSD_M1.parquet"

def inspect_august_2026_chop():
    df = pl.read_parquet(BTC_PARQUET).sort("timestamp")
    # Window: 2026-08-04 to 2026-08-11
    df = df.filter(pl.col("timestamp").is_between(1785888000000, 1786579200000))
    
    # Range High dan Low selama 4 hari tersebut
    h_max = df["high"].max()
    l_min = df["low"].min()
    span_total = h_max - l_min
    
    print(f"=== ANATOMI SIDEWAYS PASAR (5 - 9 AGUSTUS 2026) ===")
    print(f"Highest Price : ${h_max:,.2f}")
    print(f"Lowest Price  : ${l_min:,.2f}")
    print(f"Total Range   : ${span_total:,.2f} (Cuma {span_total/l_min*100:.2f}% dari harga Bitcoin!)")
    print(f"Total Candle M1: {len(df):,} bar")

inspect_august_2026_chop()
