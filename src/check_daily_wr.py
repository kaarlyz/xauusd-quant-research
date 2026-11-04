import polars as pl
import numpy as np

# Load the exact script logic we used
from test_yt_mean_reversion import test_youtube_strategy

df = pl.read_parquet('/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet')
df = df.with_columns(
    pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
    pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.hour().alias("hour"),
)

# Filter May 30, 2025 specifically
sub = df.filter(pl.col("date") == pl.date(2025, 5, 30))
print("May 30, 2025 total bars:", len(sub))

# Inspect daily win rates across all days in 2024-2025 to see how often a single day gets 70%+
# Run a quick check on daily WR distribution of this strategy
