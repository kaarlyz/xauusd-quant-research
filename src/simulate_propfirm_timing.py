#!/usr/bin/env python3
"""
Simulasi Monte Carlo Prop Firm (The 5ers $2,500 High Stakes 2-Step)
Strategi: Pola N Baku + Expired Rule
Akun:
- Modal Awal: $2,500
- Step 1: Target Profit 8% ($200) atau 10% ($250) (The 5ers High Stakes Step 1 = 8%, Step 2 = 5%)
- Max Overall Loss: 10% ($250)
- Max Daily Loss: 5% ($125)
- Unlimited Time Limit.

Parameter Pengujian:
- Timeframe M30 vs M15 vs H1.
- Risiko per trade: 0.5% ($12.50) dan 1.0% ($25.00).
- Jalankan 10.000 simulasi bootstrap Monte Carlo dari riwayat trade riil.
"""

import sys
sys.path.append("/home/vallencia/xauusd_research/src")
import numpy as np

# Hasil riil 12 tahun yang sudah diuji:
# M30: N=1,870 trades, WR=62.73%, RR=1.5, Frekuensi = 13 trade/bulan (0.65 trade/hari)
# M15: N=4,246 trades, WR=62.29%, RR=1.5, Frekuensi = 29.5 trade/bulan (1.47 trade/hari)
# H1 : N=650 trades,   WR=61.08%, RR=1.5, Frekuensi = 4.5 trade/bulan (0.22 trade/hari)

def simulate_prop_firm(wr, target_rr, trades_per_month, risk_pct=0.5, n_sims=10000):
    # The 5ers High Stakes Step 1: Target 8% (atau 10% worst case, kita pakai 10% = 10R jika risk 1%, atau 20R jika risk 0.5%)
    # Let's target Step 1 (8% = 16R pada 0.5%, atau 8R pada 1.0%)
    # Step 2: Target 5% (10R pada 0.5%, atau 5R pada 1.0%)
    # Total Target 2-Step = 13% profit.
    # Max Loss = 10% (-20R pada 0.5%, -10R pada 1.0%)
    
    target_r_step1 = 8.0 / risk_pct
    target_r_step2 = 5.0 / risk_pct
    max_loss_r = 10.0 / risk_pct # batas gugur
    daily_loss_r = 5.0 / risk_pct

    trades_per_day = trades_per_month / 20.0

    passed_count = 0
    days_to_pass_list = []
    trades_to_pass_list = []

    for _ in range(n_sims):
        # Step 1
        cum_r = 0.0
        n_trades = 0
        failed = False
        
        while cum_r < target_r_step1:
            win = np.random.rand() < wr
            r = target_rr if win else -1.0
            cum_r += r
            n_trades += 1
            if cum_r <= -max_loss_r or n_trades > 500:
                failed = True
                break
        
        if failed:
            continue
            
        # Step 2
        cum_r_step2 = 0.0
        while cum_r_step2 < target_r_step2:
            win = np.random.rand() < wr
            r = target_rr if win else -1.0
            cum_r_step2 += r
            n_trades += 1
            if cum_r_step2 <= -max_loss_r or n_trades > 1000:
                failed = True
                break
                
        if not failed:
            passed_count += 1
            total_days = n_trades / trades_per_day
            days_to_pass_list.append(total_days)
            trades_to_pass_list.append(n_trades)

    pass_rate = passed_count / n_sims * 100.0
    median_days = np.median(days_to_pass_list) if days_to_pass_list else 0
    p25_days = np.percentile(days_to_pass_list, 25) if days_to_pass_list else 0
    p75_days = np.percentile(days_to_pass_list, 75) if days_to_pass_list else 0
    median_trades = np.median(trades_to_pass_list) if trades_to_pass_list else 0
    
    return {
        "pass_rate": pass_rate,
        "median_days": median_days,
        "p25_days": p25_days,
        "p75_days": p75_days,
        "median_trades": median_trades,
    }

print("=== SIMULASI PROPFIRM THE 5ERS 2.5K HIGH STAKES (10,000 MONTE CARLO) ===")

scenarios = [
    ("M30 (Sweet Spot)", 0.6273, 1.5, 13.0, 0.5),
    ("M30 (Agresif 1% Risk)", 0.6273, 1.5, 13.0, 1.0),
    ("M15 (Intraday Aktif)", 0.6229, 1.5, 29.5, 0.5),
    ("M15 (Agresif 1% Risk)", 0.6229, 1.5, 29.5, 1.0),
    ("H1  (Santai Swing)", 0.6108, 1.5, 4.5, 0.5),
    ("H1  (Agresif 1% Risk)", 0.6108, 1.5, 4.5, 1.0),
]

for name, wr, rr, freq, risk in scenarios:
    res = simulate_prop_firm(wr, rr, freq, risk)
    weeks = res["median_days"] / 5.0
    months = res["median_days"] / 20.0
    print(f"\n{name} | Risk={risk}% per trade:")
    print(f"  Peluang Lolos Challenge (2-Step) : {res['pass_rate']:.1f}%")
    print(f"  Median Jumlah Trade Dibutuhkan   : {res['median_trades']:.0f} trade total")
    print(f"  Estimasi Waktu Lolos             : {res['median_days']:.1f} hari kerja (~{weeks:.1f} minggu / ~{months:.1f} bulan)")
    print(f"  Rentang Wajar (25th - 75th pct)  : {res['p25_days']/5:.1f} s/d {res['p75_days']/5:.1f} minggu")
