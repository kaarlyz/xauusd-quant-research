import urllib.request
import json
import datetime
import numpy as np

url = 'https://query1.finance.yahoo.com/v8/finance/chart/BOME-USD?interval=1d&range=max'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    d = json.loads(resp.read().decode())['chart']['result'][0]
    ts = np.array(d['timestamp'])
    q = d['indicators']['quote'][0]
    c = np.array(q['close'], dtype=float)
    h = np.array(q['high'], dtype=float)
    l = np.array(q['low'], dtype=float)

    valid = ~np.isnan(c)
    ts = ts[valid]; c = c[valid]; h = h[valid]; l = l[valid]
    
    t0 = datetime.datetime.fromtimestamp(ts[0], tz=datetime.timezone.utc)
    t1 = datetime.datetime.fromtimestamp(ts[-1], tz=datetime.timezone.utc)
    
    print(f"BOME Data Harian: {t0:%d %B %Y} s/d {t1:%d %B %Y} (Total {len(c)} hari)")
    print(f"Harga All-Time High: USD {np.max(h):.6f}")
    print(f"Harga All-Time Low : USD {np.min(l):.6f}")
    print(f"Harga Terkini      : USD {c[-1]:.6f}")
