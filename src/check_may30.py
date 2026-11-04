import polars as pl
import datetime

df = pl.read_parquet('/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet')

t_s = int(datetime.datetime(2025, 5, 30, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
t_e = int(datetime.datetime(2025, 5, 30, 16, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)

sub = df.filter((pl.col('timestamp') >= t_s) & (pl.col('timestamp') <= t_e)).sort('timestamp')
print('Bars on May 30, 2025 (00:00 - 16:00 UTC):', len(sub))
o_day = sub['open'].to_numpy()
h_day = sub['high'].to_numpy()
l_day = sub['low'].to_numpy()
c_day = sub['close'].to_numpy()

print(f'Open: {o_day[0]:.2f}, High: {h_day.max():.2f}, Low: {l_day.min():.2f}, Close: {c_day[-1]:.2f}')
print(f'Day range: ${h_day.max() - l_day.min():.2f}')
