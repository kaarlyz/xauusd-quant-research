import urllib.request
import json
import numpy as np

symbols = [
    ('AAPL', 'Apple'),
    ('MSFT', 'Microsoft'),
    ('GOOGL', 'Google'),
    ('AMZN', 'Amazon'),
    ('TSLA', 'Tesla')
]

print("=== BACKTEST FUNDAMENTAL + HARD SL OTOMATIS (5 TAHUN: 2020 - 2025) ===\n")
print(f"{'Nama Saham':<18} | {'Hasil $1,000':<16} | {'Total Return':<14} | {'Win Rate':<10} | {'Kena SL':<8}")
print("-" * 75)

sl_pct = 0.10 # Hard Stop Loss 10%
holding_period = 63 # 1 Kuartal (~3 bulan bursa)

for sym, name in symbols:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5y"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            d = json.loads(resp.read().decode())['chart']['result'][0]
            c = np.array(d['indicators']['quote'][0]['close'], dtype=float)
            c = c[~np.isnan(c)]
            n = len(c)

            trades = []
            i = 0
            while i < n - holding_period:
                entry_p = c[i]
                sl_p = entry_p * (1.0 - sl_pct)
                exit_p = c[i + holding_period]
                hit_sl = False
                exit_idx = i + holding_period

                for day in range(1, holding_period):
                    if c[i + day] <= sl_p:
                        hit_sl = True
                        exit_p = sl_p
                        exit_idx = i + day
                        break

                pnl_pct = (exit_p - entry_p) / entry_p * 100
                trades.append({'pnl': pnl_pct, 'hit_sl': hit_sl})
                i = exit_idx + 1

            cap = 1000.0
            for t in trades:
                cap *= (1.0 + t['pnl'] / 100.0)

            total_trades = len(trades)
            wins = sum(1 for t in trades if t['pnl'] > 0)
            wr = (wins / total_trades) * 100 if total_trades > 0 else 0
            sl_hits = sum(1 for t in trades if t['hit_sl'])
            roi = (cap - 1000.0) / 1000.0 * 100

            print(f"{name:<18} | ${cap:>10,.2f}     | {roi:>+9.1f}%    | {wr:>7.1f}%  | {sl_hits:>4}x")
    except Exception as e:
        print(sym, e)

print("=" * 75)
