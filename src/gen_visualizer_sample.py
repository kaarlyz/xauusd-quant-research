#!/usr/bin/env python3
"""
Generator Visualisasi TradingView / Matplotlib untuk Pola N Baku.
Mencetak HTML interaktif (Plotly) atau script chart Python yang menampilkan:
1. Candlestick XAUUSD
2. Swing High (Resistance Box) & Swing Low (Support Box)
3. Level Entry Pending Stop Order
4. Level Stop Loss & Take Profit (RR 1:1.5)
5. Anotasi Sinyal 'Triggered' dan 'Expired'
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

M1_PARQUET = "/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet"

def generate_sample_trade_data():
    df = pl.read_parquet(M1_PARQUET).sort("timestamp")
    # Ambil sampel M30 di 2026 yang bersih
    df = df.filter(pl.col("timestamp") >= 1767225600000) # awal 2026
    df = df.with_columns(
        (pl.col("timestamp") // (30 * 60 * 1000) * (30 * 60 * 1000)).alias("m30_ts")
    )
    m30 = df.group_by("m30_ts").agg([
        pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
        pl.from_epoch(pl.col("m30_ts") // 1000, time_unit="s").dt.to_string("%Y-%m-%d %H:%M").first().alias("time")
    ]).sort("m30_ts").head(150)
    
    print("Contoh data 150 candle M30 2026 berhasil disiapkan.")

if __name__ == "__main__":
    generate_sample_trade_data()
