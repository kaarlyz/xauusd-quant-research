import urllib.request
import json
import numpy as np
import datetime
import random

# DATABASE REKAMAN HISTORIS TANGGAL & KOIN DI MASA LALU
# Kita siapkan kasus-kasus nyata di masa lalu (Bull run, Crash, Sideways)
SCENARIOS = [
    {
        'id': 'CASE-01',
        'name': 'Kripto A (Misterius)',
        'symbol': 'SOL-USD',
        'date_sim': '2021-01-01',
        'date_name': '01 Januari 2021',
        'fundamental_note': 'Blockchain L1 baru, kecepatan tinggi 50k TPS, pendanaan kuat dari VC tier-1, volume dev aktif naik 300%. Market Cap masih di luar Top 20.',
        'lookback_days': 60,
        'forward_days': 90
    },
    {
        'id': 'CASE-02',
        'name': 'Kripto B (Misterius)',
        'symbol': 'LUNC-USD',
        'date_sim': '2022-04-15',
        'date_name': '15 April 2022',
        'fundamental_note': 'Ekosistem stablecoin algoritma tumbuh agresif, tapi cadangan devisa mulai tipis, yield 20% Anchor dinilai tidak berkelanjutan, inflasi suplai token membengkak.',
        'lookback_days': 60,
        'forward_days': 90
    },
    {
        'id': 'CASE-03',
        'name': 'Kripto C (Misterius)',
        'symbol': 'DOGE-USD',
        'date_sim': '2021-02-01',
        'date_name': '01 Februari 2021',
        'fundamental_note': 'Volume pencarian Google meledak 1000%, viral di Twitter/Reddit, endorsement tokoh publik, rasio NVT rendah karena transaksi ritel melonjak tinggi.',
        'lookback_days': 60,
        'forward_days': 90
    },
    {
        'id': 'CASE-04',
        'name': 'Kripto D (Misterius)',
        'symbol': 'FTT-USD',
        'date_sim': '2022-10-01',
        'date_name': '01 Oktober 2022',
        'fundamental_note': 'Bursa kripto nomor 2 dunia, tapi ada rumor neraca keuangan dipegang oleh entitas afiliasi tertutup, likuiditas aset kolateral token sendiri sangat rapuh.',
        'lookback_days': 60,
        'forward_days': 90
    },
    {
        'id': 'CASE-05',
        'name': 'Kripto E (Misterius)',
        'symbol': 'BTC-USD',
        'date_sim': '2022-11-20',
        'date_name': '20 November 2022',
        'fundamental_note': 'Harga tertekan di dasar bear market ($16.000), rasio MVRV < 0.80 (zona akumulasi historis), dompet holder jangka panjang (> 1 tahun) terus menambah muatan.',
        'lookback_days': 60,
        'forward_days': 90
    }
]

def load_case_blind(case_idx):
    c = SCENARIOS[case_idx]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{c['symbol']}?interval=1d&range=max"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        d = json.loads(resp.read().decode())['chart']['result'][0]
        ts = np.array(d['timestamp'])
        q = d['indicators']['quote'][0]
        close = np.array(q['close'], dtype=float)
        high = np.array(q['high'], dtype=float)
        low = np.array(q['low'], dtype=float)

        valid = ~np.isnan(close)
        ts = ts[valid]; close = close[valid]; high = high[valid]; low = low[valid]

        target_ts = int(datetime.datetime.strptime(c['date_sim'], '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc).timestamp())
        # Temukan index persis di tanggal tersebut
        idx = np.searchsorted(ts, target_ts)
        
        # 60 hari candle masa lalu (yang boleh dilihat saat itu)
        past_closes = close[max(0, idx - c['lookback_days']) : idx + 1]
        cur_price = close[idx]

        # 90 hari masa depan (yang disimpan rahasia untuk buka tirai)
        future_highs = high[idx + 1 : idx + 1 + c['forward_days']]
        future_lows = low[idx + 1 : idx + 1 + c['forward_days']]
        future_closes = close[idx + 1 : idx + 1 + c['forward_days']]

        return {
            'id': c['id'],
            'date_name': c['date_name'],
            'fundamental_note': c['fundamental_note'],
            'current_price': cur_price,
            'past_prices': past_closes.tolist(),
            'future_highs': future_highs.tolist(),
            'future_lows': future_lows.tolist(),
            'future_closes': future_closes.tolist(),
            'symbol': c['symbol'],
            'real_name': c['symbol'].split('-')[0]
        }

if __name__ == "__main__":
    print("Point-in-Time Flash Gym Ready!")
