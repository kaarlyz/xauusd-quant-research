import urllib.request
import json
import numpy as np

# DAFTAR 50 KOIN KRIPTO BERBEDA (BATCH 6 - 100% UNIK DARI RISET SEBELUMNYA)
# Mencakup: DeFi OG, Web3 Gaming, Oracles, Layer-1/Layer-2, Storage, Metaverse
FIFTY_NEW_COINS = [
    ('SUSHI-USD', 'SushiSwap (SUSHI)'),
    ('YFI-USD', 'Yearn Finance (YFI)'),
    ('BAL-USD', 'Balancer (BAL)'),
    ('ZRX-USD', '0x Protocol (ZRX)'),
    ('CVX-USD', 'Convex Finance (CVX)'),
    ('GMX11857-USD', 'GMX Protocol (GMX)'),
    ('JOE-USD', 'Trader Joe (JOE)'),
    ('OSMO-USD', 'Osmosis (OSMO)'),
    ('RPL-USD', 'Rocket Pool (RPL)'),
    ('SSV-USD', 'SSV Network (SSV)'),
    ('ANKR-USD', 'Ankr Network (ANKR)'),
    ('GLM-USD', 'Golem (GLM)'),
    ('CELO-USD', 'Celo (CELO)'),
    ('ONE2634-USD', 'Harmony (ONE)'),
    ('HOT2682-USD', 'Holo (HOT)'),
    ('RVN-USD', 'Ravencoin (RVN)'),
    ('CKB-USD', 'Nervos Network (CKB)'),
    ('SC-USD', 'Siacoin (SC)'),
    ('WAXP-USD', 'WAX (WAXP)'),
    ('ICX-USD', 'ICON (ICX)'),
    ('AUDIO-USD', 'Audius (AUDIO)'),
    ('MASK8536-USD', 'Mask Network (MASK)'),
    ('ENS-USD', 'Ethereum Name Service (ENS)'),
    ('BAND-USD', 'Band Protocol (BAND)'),
    ('RLC-USD', 'iExec RLC (RLC)'),
    ('SKL-USD', 'SKALE Network (SKL)'),
    ('CTSI-USD', 'Cartesi (CTSI)'),
    ('API3-USD', 'API3 Oracle (API3)'),
    ('METIS-USD', 'Metis L2 (METIS)'),
    ('ILV-USD', 'Illuvium (ILV)'),
    ('MAGIC14783-USD', 'Treasure Magic (MAGIC)'),
    ('SUPER-USD', 'SuperVerse (SUPER)'),
    ('ALICE-USD', 'My Neighbor Alice (ALICE)'),
    ('YGG-USD', 'Yield Guild Games (YGG)'),
    ('HIGH-USD', 'Highstreet (HIGH)'),
    ('ACH-USD', 'Alchemy Pay (ACH)'),
    ('COTI-USD', 'COTI Network (COTI)'),
    ('DENT-USD', 'Dent (DENT)'),
    ('SYS-USD', 'Syscoin (SYS)'),
    ('SFP-USD', 'SafePal (SFP)'),
    ('LRC-USD', 'Loopring (LRC)'),
    ('KNC-USD', 'Kyber Network (KNC)'),
    ('BICO-USD', 'Biconomy (BICO)'),
    ('BNT-USD', 'Bancor (BNT)'),
    ('C98-USD', 'Coin98 (C98)'),
    ('BADGER-USD', 'Badger DAO (BADGER)'),
    ('PERP-USD', 'Perpetual Protocol (PERP)'),
    ('RAD-USD', 'Radicle (RAD)'),
    ('STG-USD', 'Stargate Finance (STG)'),
    ('FXS-USD', 'Frax Share (FXS)')
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
    print("=== MEGA VALIDATION BATCH 6: UJI 50 KOIN KRIPTO BARU SEKALIGUS (H1, 2 TAHUN) ===\n")
    print(f"{'No':<3} | {'Nama Token / Koin':<32} | {'Trades':<7} | {'Win Rate':<9} | {'PF':<7} | {'Net R':<9} | {'Max DD':<7} | Status")
    print("-" * 105)

    all_net = 0.0
    all_trades = 0
    all_wins = 0

    for idx, (s, n) in enumerate(FIFTY_NEW_COINS, 1):
        res = run_test(s, n)
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
    print(f"GRAND TOTAL BATCH 6 (50 KOIN) : {all_trades:,} Trades | Rata-rata Win Rate: {tot_wr:.2f}% | Total Net: {all_net:+,.1f} R")
    print("=" * 105)
