import urllib.request
import json
import numpy as np

coins = [
    ('XRP-USD', 'XRP', 0.0004),
    ('BNB-USD', 'BNB', 0.15),
    ('DOGE-USD', 'DOGE', 0.0001),
    ('SOL-USD', 'SOLANA', 0.05),
    ('SHIB-USD', 'SHIBA INU', 0.00000002),
    ('PEPE24478-USD', 'PEPE', 0.00000001)
]

def test_pola_n_crypto(symbol, name, spread_cost, target_rr=1.5):
    # Tarik data M15 60 hari terakhir (~5.700 candle M15 per koin)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=15m&range=60d"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())['chart']['result'][0]
            ts = data['timestamp']
            q = data['indicators']['quote'][0]
            o = np.array(q['open'], dtype=float)
            h = np.array(q['high'], dtype=float)
            l = np.array(q['low'], dtype=float)
            c = np.array(q['close'], dtype=float)

            valid = ~np.isnan(c)
            o = o[valid]; h = h[valid]; l = l[valid]; c = c[valid]
            n = len(o)

            # Deteksi Swing k=3 di M15
            swing_k = 3
            is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
            for i in range(swing_k, n - swing_k):
                if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
                if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

            trades = []
            last_sw_l = []; last_sw_h = []
            trade_exit = 0

            for i in range(swing_k, n - 20):
                if is_sw_l[i]: last_sw_l.append((i, l[i]))
                if is_sw_h[i]: last_sw_h.append((i, h[i]))
                if len(last_sw_l) > 10: last_sw_l.pop(0)
                if len(last_sw_h) > 10: last_sw_h.pop(0)

                # Strict one trade at a time
                if i < trade_exit: continue

                if len(last_sw_h) >= 2 and len(last_sw_l) >= 2:
                    idx_h, val_h = last_sw_h[-1]; idx_l, val_l = last_sw_l[-1]
                    span = val_h - val_l
                    # Filter rentang minimal agar tidak kemakan fee
                    if span > spread_cost * 4 and i == max(idx_h, idx_l) + swing_k:
                        rel = (c[i] - val_l) / span
                        if 0.35 <= rel <= 0.65:
                            # Straddle Pola N
                            for s in range(i + 1, min(i + 12, n)):
                                # Expired rule
                                if is_sw_h[s] or is_sw_l[s]: break

                                if h[s] >= val_h + spread_cost: # Buy Trigger
                                    tp = val_h + target_rr * span
                                    sl = val_l
                                    for ex in range(s + 1, min(s + 40, n)):
                                        if l[ex] <= sl:
                                            trades.append(-1.0); trade_exit = ex; break
                                        elif h[ex] >= tp:
                                            trades.append(target_rr); trade_exit = ex; break
                                    break
                                elif l[s] <= val_l: # Sell Trigger
                                    tp = val_l - target_rr * span
                                    sl = val_h + spread_cost
                                    for ex in range(s + 1, min(s + 40, n)):
                                        if h[ex] + spread_cost >= sl:
                                            trades.append(-1.0); trade_exit = ex; break
                                        elif l[ex] <= tp:
                                            trades.append(target_rr); trade_exit = ex; break
                                    break

            tr = np.array(trades)
            tot = len(tr)
            if tot == 0:
                return {'name': name, 'symbol': symbol, 'trades': 0}
            wins = np.sum(tr > 0)
            wr = wins / tot * 100
            gross_p = np.sum(tr[tr > 0])
            gross_l = np.abs(np.sum(tr[tr < 0]))
            pf = gross_p / gross_l if gross_l > 0 else 0
            net = np.sum(tr)

            # Max drawdown
            eq = np.cumsum(tr)
            dd = eq - np.maximum.accumulate(eq)
            mdd = np.min(dd) if len(dd) > 0 else 0

            return {
                'name': name, 'symbol': symbol, 'bars': n, 'trades': tot,
                'wr': wr, 'pf': pf, 'net_r': net, 'mdd': mdd
            }
    except Exception as e:
        return {'name': name, 'symbol': symbol, 'error': str(e)}

if __name__ == "__main__":
    print("=== BACKTEST FORENSIK POLA N BAKU PADA ALTCOIN & KOIN MEME (M15) ===")
    print(f"{'Koin':<12} | {'Trades':<8} | {'Win Rate':<10} | {'Profit Factor':<14} | {'Net R':<10} | {'Max DD':<8} | Status")
    print("-" * 85)
    for s, n, sp in coins:
        res = test_pola_n_crypto(s, n, sp)
        if 'error' in res:
            print(f"{res['name']:<12} | Error: {res['error']}")
        else:
            status = "🔥 SANGAT BAGUS" if res['pf'] >= 1.8 else ("✅ PROFITABLE" if res['pf'] > 1.2 else "❌ GAGAL")
            print(f"{res['name']:<12} | {res['trades']:<8} | {res['wr']:<9.1f}% | {res['pf']:<14.2f} | {res['net_r']:<+9.1f}R | {res['mdd']:<7.1f}R | {status}")
