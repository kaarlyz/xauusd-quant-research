import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np
from fast_phase2_discovery import load_data_and_features

df = load_data_and_features()
o = df["open"].to_numpy()
h = df["high"].to_numpy()
l = df["low"].to_numpy()
c = df["close"].to_numpy()
v = df["volume"].to_numpy()
dates = df["date"].to_numpy()
hours = df["hour"].to_numpy()
atr14 = df["atr14"].to_numpy()
h_box = df["h_max_30"].to_numpy()
l_box = df["l_min_30"].to_numpy()
v_mean = df["v_mean20"].to_numpy()
rvol = np.where(v_mean > 0, v / v_mean, 1.0)
n = len(o)

# Group trades by date
daily_trades = {}
target_rr = 0.75
last_exit_idx = -1

for i in range(40, n - 20):
    if i <= last_exit_idx: continue
    if not (0 <= hours[i] <= 16): continue
    cur_atr = atr14[i]
    if cur_atr < 0.30: continue
    if rvol[i] < 1.30: continue

    pierce_low = (l[i] <= l_box[i] - 0.30 * cur_atr)
    pierce_high = (h[i] >= h_box[i] + 0.30 * cur_atr)

    if pierce_low and c[i] > l[i] + 0.25 * (h[i] - l[i]):
        exec_bar = i + 1
        entry_fill = o[exec_bar] + 0.380 + 0.050
        nominal_sl = l[i] - 0.50
        stop_dist = entry_fill - nominal_sl
        if not (0.80 <= stop_dist <= 15.0): continue
        tp_price = entry_fill + (target_rr * stop_dist)
        exit_fill = c[exec_bar + 15]; exit_idx = exec_bar + 15
        is_win = False
        for b in range(exec_bar, exec_bar + 16):
            if l[b] <= nominal_sl: is_win = False; exit_idx = b; break
            elif h[b] >= tp_price: is_win = True; exit_idx = b; break
        d_str = str(dates[exec_bar])
        if d_str not in daily_trades: daily_trades[d_str] = []
        daily_trades[d_str].append(1 if is_win else 0)
        last_exit_idx = exit_idx

    elif pierce_high and c[i] < h[i] - 0.25 * (h[i] - l[i]):
        exec_bar = i + 1
        entry_fill = o[exec_bar] - 0.050
        nominal_sl = h[i] + 0.50
        stop_dist = nominal_sl - entry_fill
        if not (0.80 <= stop_dist <= 15.0): continue
        tp_price = entry_fill - (target_rr * stop_dist)
        exit_fill = c[exec_bar + 15]; exit_idx = exec_bar + 15
        is_win = False
        for b in range(exec_bar, exec_bar + 16):
            if h[b] + 0.380 >= nominal_sl: is_win = False; exit_idx = b; break
            elif l[b] + 0.380 <= tp_price: is_win = True; exit_idx = b; break
        d_str = str(dates[exec_bar])
        if d_str not in daily_trades: daily_trades[d_str] = []
        daily_trades[d_str].append(1 if is_win else 0)
        last_exit_idx = exit_idx

# Analyze daily win rates on days with >= 10 trades
day_wrs = []
for d, trs in daily_trades.items():
    if len(trs) >= 8:
        wr = sum(trs) / len(trs) * 100.0
        day_wrs.append((d, len(trs), wr))

print(f"Total days with >= 8 trades: {len(day_wrs)}")
high_wr_days = [d for d in day_wrs if d[2] >= 70.0]
low_wr_days = [d for d in day_wrs if d[2] <= 30.0]
mid_wr_days = [d for d in day_wrs if 30.0 < d[2] < 70.0]
print(f"Days with WR >= 70%: {len(high_wr_days)} ({len(high_wr_days)/len(day_wrs)*100:.1f}%)")
print(f"Days with WR <= 30%: {len(low_wr_days)} ({len(low_wr_days)/len(day_wrs)*100:.1f}%)")
print(f"Days in between   : {len(mid_wr_days)} ({len(mid_wr_days)/len(day_wrs)*100:.1f}%)")

# Check May 30, 2025 specifically if it exists in daily_trades
if "2025-05-30" in daily_trades:
    m30_tr = daily_trades["2025-05-30"]
    print(f"May 30, 2025 exact simulated trades: {len(m30_tr)}, Win Rate: {sum(m30_tr)/len(m30_tr)*100:.1f}%")
