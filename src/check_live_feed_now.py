import urllib.request
import json
import datetime
import numpy as np

def check_live_pola_n(symbol, name, min_span, max_span, target_rr=1.5):
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
            
            print(f"=== STATUS LIVE {name} PAGI INI (Total M1: {n} candle) ===")
            cur_time = datetime.datetime.fromtimestamp(ts[-1], tz=datetime.timezone.utc)
            cur_wib = cur_time + datetime.timedelta(hours=7)
            print(f"Waktu Candle Terakhir : {cur_wib.strftime('%Y-%m-%d %H:%M:%S WIB')}")
            print(f"Harga Saat Ini        : ${c[-1]:,.2f}")
            
            swing_k = 5
            is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
            for i in range(swing_k, n - swing_k):
                if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
                if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True
                
            last_sw_h = [(i, h[i]) for i in range(n) if is_sw_h[i]]
            last_sw_l = [(i, l[i]) for i in range(n) if is_sw_l[i]]
            
            if len(last_sw_h) >= 1 and len(last_sw_l) >= 1:
                val_h = last_sw_h[-1][1]
                idx_h = last_sw_h[-1][0]
                val_l = last_sw_l[-1][1]
                idx_l = last_sw_l[-1][0]
                span = val_h - val_l
                
                print(f"Swing High Terakhir   : ${val_h:,.2f} ({n - idx_h} menit lalu)")
                print(f"Swing Low Terakhir    : ${val_l:,.2f} ({n - idx_l} menit lalu)")
                print(f"Rentang Kotak (Span)  : ${span:,.2f}")
                
                rel_pos = (c[-1] - val_l) / span if span > 0 else 0.5
                print(f"Posisi Harga Relatif  : {rel_pos*100:.1f}% di dalam rentang")
                
                if min_span <= span <= max_span:
                    print(">> KONDISI: MEMENUHI SYARAT RENTANG KOTAK POLA N!")
                    if rel_pos >= 0.35 and rel_pos <= 0.65:
                        print(">> ORDER: DOUBLE PENDING ORDER AKTIF (STRADDLE)")
                        print(f"   [BUY STOP]  : ${val_h:,.2f} | SL: ${val_l-1.0:,.2f} | TP: ${val_h + (target_rr*span):,.2f}")
                        print(f"   [SELL STOP] : ${val_l:,.2f} | SL: ${val_h+1.0:,.2f} | TP: ${val_l - (target_rr*span):,.2f}")
                    elif rel_pos > 0.65:
                        print(">> ORDER: SINGLE ORDER BUY STOP!")
                        print(f"   [BUY STOP]  : ${val_h:,.2f} | SL: ${val_l-1.0:,.2f} | TP: ${val_h + (target_rr*span):,.2f}")
                    else:
                        print(">> ORDER: SINGLE ORDER SELL STOP!")
                        print(f"   [SELL STOP] : ${val_l:,.2f} | SL: ${val_h+1.0:,.2f} | TP: ${val_l - (target_rr*span):,.2f}")
                else:
                    print(f">> KONDISI: Span ${span:.2f} di luar batas filter (${min_span} - ${max_span}). Menunggu swing baru.")
            print()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    check_live_pola_n('GC=F', 'XAUUSD (Gold)', min_span=5.0, max_span=25.0)
    check_live_pola_n('BTC-USD', 'BTCUSD (Bitcoin)', min_span=80.0, max_span=500.0)
