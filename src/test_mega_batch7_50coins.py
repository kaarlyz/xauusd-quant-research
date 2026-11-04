import urllib.request
import json
import numpy as np

# BATCH 7: 50 KOIN KRIPTO BERBEDA BERIKUTNYA (100% UNIK, BELUM PERNAH DIUJI)
# Total koleksi riset bertambah menjadi 220 Koin Kripto!
BATCH_7_COINS = [
    ('TON11419-USD', 'Toncoin (TON)'),
    ('ZIL-USD', 'Zilliqa (ZIL)'),
    ('GNO-USD', 'Gnosis (GNO)'),
    ('BAT-USD', 'Basic Attention Token (BAT)'),
    ('QTUM-USD', 'Qtum (QTUM)'),
    ('OMG-USD', 'OMG Network (OMG)'),
    ('WAVES-USD', 'Waves (WAVES)'),
    ('ZEN-USD', 'Horizen (ZEN)'),
    ('DGB-USD', 'DigiByte (DGB)'),
    ('XVG-USD', 'Verge (XVG)'),
    ('KMD-USD', 'Komodo (KMD)'),
    ('LSK-USD', 'Lisk (LSK)'),
    ('STEEM-USD', 'Steem (STEEM)'),
    ('ARDR-USD', 'Ardor (ARDR)'),
    ('SNT-USD', 'Status (SNT)'),
    ('STORJ-USD', 'Storj (STORJ)'),
    ('POLY-USD', 'Polymath (POLY)'),
    ('POWR-USD', 'Powerledger (POWR)'),
    ('REQ-USD', 'Request (REQ)'),
    ('LOOM-USD', 'Loom Network (LOOM)'),
    ('MTL-USD', 'Metal DAO (MTL)'),
    ('NKN-USD', 'NKN (NKN)'),
    ('OGN-USD', 'Origin Protocol (OGN)'),
    ('WRX-USD', 'WazirX (WRX)'),
    ('DUSK-USD', 'Dusk Network (DUSK)'),
    ('VITE-USD', 'Vite (VITE)'),
    ('TROY-USD', 'Troy (TROY)'),
    ('HARD-USD', 'Kava Lend (HARD)'),
    ('BEL-USD', 'Bella Protocol (BEL)'),
    ('WING-USD', 'Wing Finance (WING)'),
    ('UNFI-USD', 'Unifi Protocol (UNFI)'),
    ('LIT-USD', 'Litentry (LIT)'),
    ('TRU-USD', 'TrueFi (TRU)'),
    ('POND-USD', 'Marlin (POND)'),
    ('DEGO-USD', 'Dego Finance (DEGO)'),
    ('LINA-USD', 'Linear Finance (LINA)'),
    ('CFX-USD', 'Conflux (CFX)'),
    ('ERN-USD', 'Ethernity Chain (ERN)'),
    ('ATA-USD', 'Automata Network (ATA)'),
    ('GTC-USD', 'Gitcoin (GTC)'),
    ('MLN-USD', 'Enzyme Finance (MLN)'),
    ('QUICK-USD', 'QuickSwap (QUICK)'),
    ('FIDA-USD', 'Bonfida (FIDA)'),
    ('AGLD-USD', 'Adventure Gold (AGLD)'),
    ('RARE-USD', 'SuperRare (RARE)'),
    ('CHESS-USD', 'Tranchess (CHESS)'),
    ('DAR-USD', 'Mines of Dalarnia (DAR)'),
    ('BNX-USD', 'BinaryX (BNX)'),
    ('SPELL-USD', 'Spell Token (SPELL)'),
    ('OXT-USD', 'Orchid Protocol (OXT)')
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
    print("=== MEGA VALIDATION BATCH 7: UJI 50 KOIN KRIPTO BARU SEKALIGUS (H1, 2 TAHUN) ===\n")
    print(f"{'No':<3} | {'Nama Token / Koin':<30} | {'Trades':<7} | {'Win Rate':<9} | {'PF':<7} | {'Net R':<9} | {'Max DD':<7} | Status")
    print("-" * 103)

    all_net = 0.0
    all_trades = 0
    all_wins = 0

    for idx, (s, n) in enumerate(BATCH_7_COINS, 1):
        res = run_test(s, n)
        if 'error' in res:
            print(f"{idx:<3} | {n:<30} | Error: {res['error']}")
        else:
            all_net += res['net_r']
            all_trades += res['trades']
            all_wins += int(res['trades'] * res['wr'] / 100)
            status = "🔥 SUPER ALPHA" if res['pf'] >= 1.8 else ("✅ PROFITABLE" if res['pf'] > 1.2 else "❌ GAGAL")
            print(f"{idx:<3} | {res['name']:<30} | {res['trades']:<7} | {res['wr']:<7.1f}% | {res['pf']:<7.2f} | {res['net_r']:<+7.1f}R | {res['mdd']:<6.1f}R | {status}")

    tot_wr = (all_wins / all_trades) * 100 if all_trades > 0 else 0
    print("-" * 103)
    print(f"GRAND TOTAL BATCH 7 (50 KOIN) : {all_trades:,} Trades | Rata-rata Win Rate: {tot_wr:.2f}% | Total Net: {all_net:+,.1f} R")
    print("=" * 103)
