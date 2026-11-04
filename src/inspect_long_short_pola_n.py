import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import polars as pl
import numpy as np

df = pl.read_parquet('/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet').sort('timestamp')
df = df.with_columns(
    (pl.col("timestamp") // (60 * 60 * 1000) * (60 * 60 * 1000)).alias("h1_ts"),
    pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.year().alias("year"),
    pl.from_epoch(pl.col("timestamp") // 1000, time_unit="s").dt.date().alias("date"),
)
h1 = df.group_by("h1_ts").agg([
    pl.col("open").first(), pl.col("high").max(), pl.col("low").min(), pl.col("close").last(),
    pl.col("year").first(), pl.col("date").first()
]).sort("h1_ts")

o = h1["open"].to_numpy(); h = h1["high"].to_numpy(); l = h1["low"].to_numpy(); c = h1["close"].to_numpy()
dates = h1["date"].to_numpy(); n = len(o)
swing_k = 3

is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
for i in range(swing_k, n - swing_k):
    if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
    if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

trades = []
last_sw_l = []; last_sw_h = []

for i in range(swing_k, n - 20):
    if is_sw_l[i]: last_sw_l.append((i, l[i]))
    if is_sw_h[i]: last_sw_h.append((i, h[i]))
    if len(last_sw_l) > 10: last_sw_l.pop(0)
    if len(last_sw_h) > 10: last_sw_h.pop(0)

    # Bullish
    if len(last_sw_l) >= 2 and len(last_sw_h) >= 1:
        idx_a, price_a = last_sw_l[-2]
        idx_b, price_b = last_sw_h[-1]
        idx_c, price_c = last_sw_l[-1]
        if idx_a < idx_b < idx_c and price_c > price_a and price_b > price_a and price_b > price_c:
            if i == idx_c + swing_k:
                sl_p = price_c - 0.50
                tp_p = price_c + (price_b - price_a)
                risk = (price_b + 0.38 + 0.05) - sl_p
                reward = tp_p - (price_b + 0.38 + 0.05)
                if risk > 1.0 and reward > 0.5:
                    triggered = False
                    for step in range(1, 31):
                        chk = i + step
                        if chk >= n: break
                        if l[chk] <= sl_p: break
                        if h[chk] >= price_b: triggered = True; entry_bar = chk; break
                    if triggered:
                        outcome = 0; r_val = 0.0
                        for s in range(1, 50):
                            bar_idx = entry_bar + s
                            if bar_idx >= n: break
                            if l[bar_idx] <= sl_p: r_val = -1.0; outcome = -1; break
                            elif h[bar_idx] >= tp_p: r_val = (reward / risk); outcome = 1; break
                        if outcome == 0 and entry_bar + 50 < n:
                            r_val = (c[entry_bar + 50] - price_b) / risk
                        trades.append({"dir": "LONG", "r": r_val, "risk": risk, "reward": reward, "rr": reward/risk, "year": int(str(dates[entry_bar])[:4])})

    # Bearish
    if len(last_sw_h) >= 2 and len(last_sw_l) >= 1:
        idx_a, price_a = last_sw_h[-2]
        idx_b, price_b = last_sw_l[-1]
        idx_c, price_c = last_sw_h[-1]
        if idx_a < idx_b < idx_c and price_c < price_a and price_b < price_a and price_c > price_b:
            if i == idx_c + swing_k:
                sl_p = price_c + 0.50
                tp_p = price_c - (price_a - price_b)
                risk = sl_p - (price_b - 0.05)
                reward = (price_b - 0.05) - (tp_p + 0.38)
                if risk > 1.0 and reward > 0.5:
                    triggered = False
                    for step in range(1, 31):
                        chk = i + step
                        if chk >= n: break
                        if h[chk] >= sl_p: break
                        if l[chk] <= price_b: triggered = True; entry_bar = chk; break
                    if triggered:
                        outcome = 0; r_val = 0.0
                        for s in range(1, 50):
                            bar_idx = entry_bar + s
                            if bar_idx >= n: break
                            if h[bar_idx] + 0.38 >= sl_p: r_val = -1.0; outcome = -1; break
                            elif l[bar_idx] + 0.38 <= tp_p: r_val = (reward / risk); outcome = 1; break
                        if outcome == 0 and entry_bar + 50 < n:
                            r_val = (price_b - c[entry_bar + 50]) / risk
                        trades.append({"dir": "SHORT", "r": r_val, "risk": risk, "reward": reward, "rr": reward/risk, "year": int(str(dates[entry_bar])[:4])})

longs = [t for t in trades if t["dir"] == "LONG"]
shorts = [t for t in trades if t["dir"] == "SHORT"]

def print_stat(sub, name):
    r_arr = np.array([t["r"] for t in sub])
    n_t = len(r_arr)
    gw = sum(x for x in r_arr if x > 0); gl = abs(sum(x for x in r_arr if x < 0))
    pf = gw / gl if gl > 0 else 99.0
    wr = sum(1 for x in r_arr if x > 0) / n_t * 100.0
    exp = float(np.mean(r_arr))
    avg_rr = float(np.mean([t["rr"] for t in sub]))
    print(f"[{name}] Trades={n_t:,} | WR={wr:5.2f}% | PF={pf:5.3f} | Net Exp={exp:+.4f}R | Avg Nominal RR={avg_rr:.2f}:1 | Total R={sum(r_arr):+.1f}R")

print_stat(trades, "TOTAL H1")
print_stat(longs, "LONG ONLY")
print_stat(shorts, "SHORT ONLY")
