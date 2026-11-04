import urllib.request
import json
import datetime
import numpy as np

def replay_today_session(symbol, name, min_span, max_span, target_rr=1.5, spread=0.38, comm=0.07, slippage=0.05, buffer=0.50, risk_usc=10.0):
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
            
            t_first = datetime.datetime.fromtimestamp(ts[0], tz=datetime.timezone.utc) + datetime.timedelta(hours=7)
            t_last = datetime.datetime.fromtimestamp(ts[-1], tz=datetime.timezone.utc) + datetime.timedelta(hours=7)
            
            print(f"=== SIMULASI EKSEKUSI EA HARI INI: {name} ===")
            print(f"Rentang Sesi: {t_first.strftime('%H:%M WIB')} s/d {t_last.strftime('%H:%M WIB')} (Total {n} Candle M1)")
            
            swing_k = 5
            is_sw_h = np.zeros(n, dtype=bool); is_sw_l = np.zeros(n, dtype=bool)
            for i in range(swing_k, n - swing_k):
                if h[i] == np.max(h[i - swing_k : i + swing_k + 1]): is_sw_h[i] = True
                if l[i] == np.min(l[i - swing_k : i + swing_k + 1]): is_sw_l[i] = True
                
            trades = []
            active_orders = []
            trade_exit_bar = 0
            last_sw_l = []; last_sw_h = []
            
            for i in range(swing_k, n):
                if is_sw_l[i]: last_sw_l.append((i, l[i]))
                if is_sw_h[i]: last_sw_h.append((i, h[i]))
                if len(last_sw_l) > 10: last_sw_l.pop(0)
                if len(last_sw_h) > 10: last_sw_h.pop(0)
                
                # Cek active pending orders
                new_active = []
                for order in active_orders:
                    # Cek expired (if new swing confirmed)
                    if (is_sw_h[i] and i > order['idx_h']) or (is_sw_l[i] and i > order['idx_l']):
                        print(f"[{datetime.datetime.fromtimestamp(ts[i], tz=datetime.timezone.utc)+datetime.timedelta(hours=7):%H:%M WIB}] Order {order['side']} CANCELLED (EXPIRED RULE - New Swing Formed)")
                        continue
                    
                    # Cek trigger
                    triggered = False
                    fill_p = 0.0
                    if order['side'] == "BUY" and h[i] >= order['trigger_p']:
                        triggered = True
                        fill_p = order['trigger_p'] + spread + slippage
                    elif order['side'] == "SELL" and l[i] <= order['trigger_p']:
                        triggered = True
                        fill_p = order['trigger_p'] - slippage
                        
                    if triggered:
                        print(f"[{datetime.datetime.fromtimestamp(ts[i], tz=datetime.timezone.utc)+datetime.timedelta(hours=7):%H:%M WIB}] FILLED {order['side']} @ ${fill_p:,.2f} | SL: ${order['sl']:,.2f} | TP: ${order['tp']:,.2f}")
                        # Simulasikan forward
                        in_pos = True
                        out_r = 0.0
                        exit_time = ""
                        for s in range(i + 1, n):
                            if order['side'] == "BUY":
                                if l[s] <= order['sl']:
                                    out_r = -1.0
                                    in_pos = False
                                    exit_time = f"{datetime.datetime.fromtimestamp(ts[s], tz=datetime.timezone.utc)+datetime.timedelta(hours=7):%H:%M WIB} (SL HIT)"
                                    break
                                elif h[s] >= order['tp']:
                                    out_r = target_rr
                                    in_pos = False
                                    exit_time = f"{datetime.datetime.fromtimestamp(ts[s], tz=datetime.timezone.utc)+datetime.timedelta(hours=7):%H:%M WIB} (TP HIT)"
                                    break
                            else:
                                if h[s] + spread >= order['sl']:
                                    out_r = -1.0
                                    in_pos = False
                                    exit_time = f"{datetime.datetime.fromtimestamp(ts[s], tz=datetime.timezone.utc)+datetime.timedelta(hours=7):%H:%M WIB} (SL HIT)"
                                    break
                                elif l[s] + spread <= order['tp']:
                                    out_r = target_rr
                                    in_pos = False
                                    exit_time = f"{datetime.datetime.fromtimestamp(ts[s], tz=datetime.timezone.utc)+datetime.timedelta(hours=7):%H:%M WIB} (TP HIT)"
                                    break
                        if not in_pos:
                            print(f"   -> Closed at {exit_time} | Result: {out_r:+.1f} R")
                            trades.append(out_r)
                        else:
                            # Still running
                            cur_p = c[-1]
                            floating_r = ((cur_p - fill_p)/order['risk']) if order['side']=="BUY" else ((fill_p - cur_p)/order['risk'])
                            print(f"   -> STILL OPEN (RUNNING FLOATING): {floating_r:+.2f} R @ ${cur_p:,.2f}")
                            trades.append(floating_r)
                    else:
                        new_active.append(order)
                active_orders = new_active
                
                # Deteksi setup baru
                if len(last_sw_h) >= 2 and len(last_sw_l) >= 2:
                    idx_h, val_h = last_sw_h[-1]; idx_l, val_l = last_sw_l[-1]
                    span = val_h - val_l
                    if min_span <= span <= max_span and i == max(idx_h, idx_l) + swing_k:
                        rel_pos = (c[i] - val_l) / span
                        if rel_pos >= 0.35 and rel_pos <= 0.65:
                            # Double order
                            risk_b = (val_h + spread + slippage) - (val_l - buffer - slippage) + comm
                            risk_s = (val_h + buffer + spread + slippage) - (val_l - slippage) + comm
                            active_orders.append({"side": "BUY", "trigger_p": val_h, "sl": val_l - buffer, "tp": val_h + target_rr * risk_b, "risk": risk_b, "idx_h": idx_h, "idx_l": idx_l})
                            active_orders.append({"side": "SELL", "trigger_p": val_l, "sl": val_h + buffer, "tp": val_l - target_rr * risk_s, "risk": risk_s, "idx_h": idx_h, "idx_l": idx_l})
                            print(f"[{datetime.datetime.fromtimestamp(ts[i], tz=datetime.timezone.utc)+datetime.timedelta(hours=7):%H:%M WIB}] Setup New Double Order: BuyStop ${val_h:,.2f} | SellStop ${val_l:,.2f}")
                        elif rel_pos > 0.65:
                            risk_b = (val_h + spread + slippage) - (val_l - buffer - slippage) + comm
                            active_orders.append({"side": "BUY", "trigger_p": val_h, "sl": val_l - buffer, "tp": val_h + target_rr * risk_b, "risk": risk_b, "idx_h": idx_h, "idx_l": idx_l})
                            print(f"[{datetime.datetime.fromtimestamp(ts[i], tz=datetime.timezone.utc)+datetime.timedelta(hours=7):%H:%M WIB}] Setup New Buy Stop @ ${val_h:,.2f}")
                        else:
                            risk_s = (val_h + buffer + spread + slippage) - (val_l - slippage) + comm
                            active_orders.append({"side": "SELL", "trigger_p": val_l, "sl": val_h + buffer, "tp": val_l - target_rr * risk_s, "risk": risk_s, "idx_h": idx_h, "idx_l": idx_l})
                            print(f"[{datetime.datetime.fromtimestamp(ts[i], tz=datetime.timezone.utc)+datetime.timedelta(hours=7):%H:%M WIB}] Setup New Sell Stop @ ${val_l:,.2f}")

            # Rekapitulasi saldo
            tot_r = sum(trades)
            cuan_usc = tot_r * risk_usc
            bal_usc = 1000.0 + cuan_usc
            print("-" * 65)
            print(f"Total Trade Tereksekusi Hari Ini : {len(trades)} trade")
            print(f"Akumulasi Hasil Hari Ini         : {tot_r:+.2f} R")
            print(f"Saldo Awal                       : 1,000.00 USC ($10 USD)")
            print(f"Saldo Saat Ini                   : {bal_usc:,.2f} USC (Profit {cuan_usc:+,.2f} USC / +${cuan_usc/100:+.2f} USD)")
            print("=" * 65 + "\n")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    replay_today_session('GC=F', 'XAUUSD (Gold)', min_span=5.0, max_span=25.0, spread=0.38, comm=0.07, slippage=0.05, buffer=0.50, risk_usc=10.0)
    replay_today_session('BTC-USD', 'BTCUSD (Bitcoin)', min_span=80.0, max_span=500.0, spread=15.0, comm=5.0, slippage=5.0, buffer=5.0, risk_usc=20.0)
