import urllib.request
import json

headers = {'User-Agent': 'QuantResearcher vallencia@hermes-agent.org'}
url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json'
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        facts = data['facts']['us-gaap']
        net_income = facts.get('NetIncomeLoss', {})['units']['USD']
        print('Total Catatan Laporan Keuangan Resmi Apple di SEC EDGAR:', len(net_income))
        # Filter laporan tahunan resmi (10-K)
        annuals = [x for x in net_income if x.get('form') == '10-K']
        print('\n=== CONTOH HISTORICAL FUNDAMENTAL POINT-IN-TIME (APPLE 10-K) ===')
        for item in annuals[-5:]:
            print(f"Tahun Buku {item.get('fy')} (Filed: {item.get('filed')}) | Laba Bersih: ${item.get('val')/1e9:.2f} Miliar USD")
except Exception as e:
    print('SEC Error:', e)
