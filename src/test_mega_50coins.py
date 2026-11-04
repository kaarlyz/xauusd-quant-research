import urllib.request
import json
import numpy as np
import datetime

# 50 KOIN KRIPTO BERBEDA LINTAS SEKTOR (Top Layer 1/2, DeFi, AI, Gaming, Privacy)
FIFTY_COINS = [
    ('ADA-USD', 'Cardano (ADA)'),
    ('DOT-USD', 'Polkadot (DOT)'),
    ('LINK-USD', 'Chainlink (LINK)'),
    ('LTC-USD', 'Litecoin (LTC)'),
    ('BCH-USD', 'Bitcoin Cash (BCH)'),
    ('XLM-USD', 'Stellar (XLM)'),
    ('ATOM-USD', 'Cosmos (ATOM)'),
    ('FIL-USD', 'Filecoin (FIL)'),
    ('HBAR-USD', 'Hedera (HBAR)'),
    ('ICP-USD', 'Internet Computer (ICP)'),
    ('APT21794-USD', 'Aptos (APT)'),
    ('ARB11841-USD', 'Arbitrum (ARB)'),
    ('OP-USD', 'Optimism (OP)'),
    ('INJ-USD', 'Injective (INJ)'),
    ('RUNE-USD', 'THORChain (RUNE)'),
    ('FTM-USD', 'Fantom (FTM)'),
    ('ALGO-USD', 'Algorand (ALGO)'),
    ('STX4847-USD', 'Stacks (STX)'),
    ('TIA22861-USD', 'Celestia (TIA)'),
    ('MKR-USD', 'Maker (MKR)'),
    ('SNX-USD', 'Synthetix (SNX)'),
    ('CRV-USD', 'Curve DAO (CRV)'),
    ('LDO-USD', 'Lido DAO (LDO)'),
    ('CAKE-USD', 'PancakeSwap (CAKE)'),
    ('COMP5692-USD', 'Compound (COMP)'),
    ('GRT6719-USD', 'The Graph (GRT)'),
    ('1INCH-USD', '1inch Network (1INCH)'),
    ('PENDLE-USD', 'Pendle (PENDLE)'),
    ('ONDO-USD', 'Ondo Finance (ONDO)'),
    ('FET-USD', 'Artificial Superintelligence (FET)'),
    ('RENDER-USD', 'Render (RENDER)'),
    ('TAO22974-USD', 'Bittensor (TAO)'),
    ('AR-USD', 'Arweave (AR)'),
    ('AKT-USD', 'Akash Network (AKT)'),
    ('JASMY-USD', 'JasmyCoin (JASMY)'),
    ('THETA-USD', 'Theta Network (THETA)'),
    ('SAND-USD', 'The Sandbox (SAND)'),
    ('AXS-USD', 'Axie Infinity (AXS)'),
    ('ENJ-USD', 'Enjin Coin (ENJ)'),
    ('CHZ-USD', 'Chiliz (CHZ)'),
    ('FLOW-USD', 'Flow (FLOW)'),
    ('BEAM28298-USD', 'Beam (BEAM)'),
    ('IMX10603-USD', 'Immutable (IMX)'),
    ('XMR-USD', 'Monero (XMR)'),
    ('ZEC-USD', 'Zcash (ZEC)'),
    ('DASH-USD', 'Dash (DASH)'),
    ('QNT-USD', 'Quant (QNT)'),
    ('KAVA-USD', 'Kava (KAVA)'),
    ('EOS-USD', 'EOS (EOS)'),
    ('NEO-USD', 'Neo (NEO)')
]

def run_test(symbol, name, target_rr=1.5):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1h&range=730d"
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
            o = o[valid]; h = h[valid]; l = l[valid]; c = c[valid]; ts = np.array(ts)[valid]
            tot_bars = len(o)

            # Hitung estimasi spread rata-rata (0.1% dari harga median)
            spread_cost = np.median(c) * 0.001

            swing_k = 3
            is_sw_h = np.zeros(tot_bars, dtype=bool); is_sw_l = np.zeros(tot_bars, dtype=bool)
            for i in range(swing_k, tot_bars - swing_k):
                if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
                if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

            trades = []
            last_sw_l = []; last_sw_h = []
            trade_exit = 0

            for i in range(swing_k, tot_bars - 20):
                if is_sw_l[i]: last_sw_l.append((i, l[i]))
                if is_sw_h[i]: last_sw_h.append((i, h[i]))
                if len(last_sw_l) > 10: last_sw_l.pop(0)
                if len(last_sw_h) > 10: last_sw_h.pop(0)

                if i < trade_exit: continue

                if len(last_sw_h) >= 2 and len(last_sw_l) >= 2:
                    idx_h, val_h = last_sw_h[-1]; idx_l, val_l = last_sw_l[-1]
                    span = val_h - val_l
                    if span > spread_cost * 4 and i == max(idx_h, idx_l) + swing_k:
                        rel = (c[i] - val_l) / span
                        if 0.35 <= rel <= 0.65:
                            for st in range(i + 1, min(i + 12, tot_bars)):
                                if is_sw_h[st] or is_sw_l[st]: break
                                if h[st] >= val_h + spread_cost:
                                    tp = val_h + target_rr * span
                                    sl = val_l
                                    for ex in range(st + 1, min(st + 60, tot_bars)):
                                        if l[ex] <= sl:
                                            trades.append(-1.0); trade_exit = ex; break
                                        elif h[ex] >= tp:
                                            trades.append(target_rr); trade_exit = ex; break
                                    break
                                elif l[st] <= val_l:
                                    tp = val_l - target_rr * span
                                    sl = val_h + spread_cost
                                    for ex in range(st + 1, min(st + 60, tot_bars)):
                                        if h[ex] + spread_cost >= sl:
                                            trades.append(-1.0); trade_exit = ex; break
                                        elif l[ex] <= tp:
                                            trades.append(target_rr); trade_exit = ex; break
                                    break

            tr = np.array(trades)
            tot_tr = len(tr)
            if tot_tr == 0:
                return {'name': name, 'symbol': symbol, 'trades': 0, 'wr': 0.0, 'pf': 0.0, 'net_r': 0.0, 'mdd': 0.0}

            wins = np.sum(tr > 0)
            wr = wins / tot_tr * 100
            gp = np.sum(tr[tr > 0]); gl = np.abs(np.sum(tr[tr < 0]))
            pf = gp / gl if gl > 0 else 0
            net = np.sum(tr)
            eq = np.cumsum(tr); dd = eq - np.maximum.accumulate(eq); mdd = np.min(dd)
            return {
                'name': name, 'symbol': symbol, 'trades': tot_tr,
                'wr': wr, 'pf': pf, 'net_r': net, 'mdd': mdd
            }
    except Exception as e:
        return {'name': name, 'symbol': symbol, 'error': str(e)}

if __name__ == "__main__":
    print("=== MEGA VALIDATION: UJI 50 KOIN KRIPTO BERBEDA SEKALIGUS (H1, 2 TAHUN) ===\n")
    print(f"{'No':<3} | {'Nama Token / Koin':<32} | {'Trades':<7} | {'Win Rate':<9} | {'PF':<7} | {'Net R':<9} | {'Max DD':<7} | Status")
    print("-" * 105)

    all_net = 0.0
    all_trades = 0
    all_wins = 0

    results = []
    for idx, (s, n) in enumerate(FIFTY_COINS, 1):
        res = run_test(s, n)
        results.append(res)
        if 'error' in res:
            print(f"{idx:<3} | {n:<32} | Error: {res['error']}")
        else:
            all_net += res['net_r']
            all_trades += res['trades']
            all_wins += int(res['trades'] * res['wr'] / 100)
            status = "🔥 SUPER ALPHA" if res['pf'] >= 1.8 else ("✅ PROFITABLE" if res['pf'] > 1.2 else "❌ GAGAL")
            print(f"{idx:<3} | {res['name']:<32} | {res['trades']:<7} | {res['wr']:<7.1f}% | {res['pf']:<7.2f} | {res['net_r']:<+7.1f}R | {res['mdd']:<6.1f}R | {status}")

    tot_wr = (all_wins / all_trades) * 100 if all_trades > 0 else 0
    print("-" * 105)
    print(f"GRAND TOTAL 50 KOIN KRIPTO : {all_trades:,} Trades | Rata-rata Win Rate: {tot_wr:.2f}% | Total Net: {all_net:+,.1f} R")
    print("=" * 105)
