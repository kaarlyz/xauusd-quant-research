import urllib.request
import json
import datetime
import numpy as np

def inspect_signal(symbol, name, min_span, max_span, target_rr=1.5, buff=0.50):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
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
            n = len(o)

            swing_k = 5
            is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
            for i in range(swing_k, n - swing_k):
                if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
                if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True

            last_sw_h = [(i, h[i]) for i in range(n) if is_sw_h[i]]
            last_sw_l = [(i, l[i]) for i in range(n) if is_sw_l[i]]

            cur_p = c[-1]
            t_now = datetime.datetime.fromtimestamp(ts[-1], tz=datetime.timezone.utc) + datetime.timedelta(hours=7)
            print(f"=== {name} ({t_now:%H:%M:%S WIB}) ===")
            print(f"Harga Sekarang  : ${cur_p:,.2f}")

            if len(last_sw_h) >= 1 and len(last_sw_l) >= 1:
                idx_h, val_h = last_sw_h[-1]
                idx_l, val_l = last_sw_l[-1]
                span = val_h - val_l
                rel = (cur_p - val_l) / span if span > 0 else 0.5
                print(f"Swing High (hb) : ${val_h:,.2f} ({n - idx_h} menit lalu)")
                print(f"Swing Low (lc)  : ${val_l:,.2f} ({n - idx_l} menit lalu)")
                print(f"Rentang Span    : ${span:,.2f}")
                print(f"Posisi Harga    : {rel*100:.1f}% di dalam rentang")

                if min_span <= span <= max_span:
                    if 0.35 <= rel <= 0.65:
                        print(">> ARAH / SINYAL: DOUBLE ORDER / STRADDLE (NETRAL)")
                        print(f"   [BUY STOP]  di ${val_h:,.2f} | SL: ${val_l-buff:,.2f} | TP: ${val_h + target_rr*span:,.2f}")
                        print(f"   [SELL STOP] di ${val_l:,.2f} | SL: ${val_h+buff:,.2f} | TP: ${val_l - target_rr*span:,.2f}")
                        print("   *Kesimpulan: Belum boleh Buy/Sell sekarang. Tunggu harga tembus salah satu pintu!")
                    elif rel > 0.65:
                        print(">> ARAH / SINYAL: BIAS BUY (MENUNGGU BREAKOUT ATAS)")
                        print(f"   [BUY STOP]  di ${val_h:,.2f} | SL: ${val_l-buff:,.2f} | TP: ${val_h + target_rr*span:,.2f}")
                        print("   *Kesimpulan: Cenderung BUY, tapi HANYA masuk jika tembus atap Swing High.")
                    else:
                        print(">> ARAH / SINYAL: BIAS SELL (MENUNGGU BREAKDOWN BAWAH)")
                        print(f"   [SELL STOP] di ${val_l:,.2f} | SL: ${val_h+buff:,.2f} | TP: ${val_l - target_rr*span:,.2f}")
                        print("   *Kesimpulan: Cenderung SELL, tapi HANYA masuk jika tembus lantai Swing Low.")
                else:
                    print(f">> STATUS: Span ${span:.2f} di luar filter (${min_span}-${max_span}). STANDBY.")
            print()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    inspect_signal('GC=F', 'XAUUSD (GOLD)', min_span=5.0, max_span=25.0, buff=0.50)
    inspect_signal('BTC-USD', 'BTCUSD (BITCOIN)', min_span=80.0, max_span=500.0, buff=5.0)
    inspect_signal('NQ=F', 'NAS100 (NASDAQ)', min_span=15.0, max_span=80.0, buff=1.0)
