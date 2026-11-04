import urllib.request
import json

memes = [
    ('DOGE-USD', 'Dogecoin (DOGE)', 'Dogecoin L1', 11.5),
    ('SHIB-USD', 'Shiba Inu (SHIB)', 'Ethereum', 2.7),
    ('PEPE24478-USD', 'Pepe (PEPE)', 'Ethereum', 2.0),
    ('WIF-USD', 'Dogwifhat (WIF)', 'Solana', 0.17),
    ('BONK-USD', 'Bonk (BONK)', 'Solana', 0.25),
    ('FLOKI-USD', 'Floki (FLOKI)', 'BNB / ETH', 0.22),
    ('BOME-USD', 'Book of Meme (BOME)', 'Solana', 0.04),
    ('TURBO-USD', 'Turbo (TURBO)', 'Ethereum AI', 0.05),
    ('NOT-USD', 'Notcoin (NOT)', 'TON Telegram', 0.035),
    ('FARTCOIN-USD', 'Fartcoin (FARTCOIN)', 'Solana AI', 0.12)
]

print("=== TOP 10 MEMECOIN TERBESAR DUNIA (DATA RESMI LIVE) ===\n")
print(f"{'No':<3} | {'Nama Koin':<22} | {'Harga USD':<16} | {'Market Cap':<14} | Ekosistem")
print("-" * 75)

idx = 1
for s, n, chain, mcap in memes:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval=1h&range=1d"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            d = json.loads(resp.read().decode())['chart']['result'][0]
            c = [x for x in d['indicators']['quote'][0]['close'] if x is not None][-1]
            if c < 0.0001:
                p_str = f"USD {c:.8f}"
            else:
                p_str = f"USD {c:.4f}"
            mcap_str = f"USD {mcap:.2f} B" if mcap >= 1.0 else f"USD {mcap*1000:.0f} M"
            print(f"{idx:<3} | {n:<22} | {p_str:<16} | {mcap_str:<14} | {chain}")
    except Exception as e:
        print(f"{idx:<3} | {n:<22} | Error")
    idx += 1
print("=" * 75)
