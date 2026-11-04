import json

with open("/home/vallencia/xauusd_research/data/final_discrepancy_results.json") as f:
    d = json.load(f)

print("=== 1. FRICTION CONFIGURATION TABLE ===")
for r in d["friction_mdd_mapping"]:
    print(f"{r['config_name']:<55} | Tot: ${r['total_friction']:.2f} | PF: {r['profit_factor']} | NetR: {r['net_r']}R | MDD: {r['mdd_r']}R (${r['mdd_dollars_at_750']} / {r['mdd_pct_at_750']}%) | MaxSafeRisk: ${r['max_defensible_risk_for_7_5pct_dd']}")

print("\n=== 2. UNDERWATER TIMESTAMPS ===")
for k, v in d["underwater_exact_timestamps"].items():
    print(f"[{k}]")
    print(f"  Peak: {v['peak_time']} (Date: {v['peak_date']})")
    print(f"  Trough: {v['trough_time']} (Depth: -{v['depth_r']}R)")
    print(f"  Recovery: {v['recovery_time']} (Date: {v['recovery_date']})")
    print(f"  Calendar Days: {v['calendar_days']} | Market Trading Days: {v['market_trading_days']} | Active Trading Days: {v['active_trading_days']} | Trades: {v['trades_count']}")

print("\n=== 3. STRAT-07 HEDGING BY PARTITION ===")
for k, v in d["strat07_hedging_by_partition"].items():
    print(f"[{k}]")
    print(f"  S08 Loss Days: {v['strat08_loss_days']} | Coincident Active: {v['both_active_days']} | Co-Loss: {v['simultaneous_loss_days']}")
    print(f"  Co-Loss Freq on Coincident: {v['cond_loss_freq_on_coincident_pct']}% | Unconditional on S08 Loss: {v['uncond_loss_freq_on_s08_loss_pct']}%")
    print(f"  S07 Wins on S08 Loss: {v['strat07_wins_on_s08_loss']} | S07 Losses: {v['strat07_losses_on_s08_loss']} | S07 Inactive: {v['strat07_inactive_on_s08_loss']}")
    print(f"  S07 Win Ratio when Active: {v['strat07_win_ratio_when_active_on_s08_loss']}% | Net R Delivered: {v['strat07_net_r_on_s08_loss']}R | Cond Corr: {v['conditional_correlation_coincident']}")

print("\n=== 4. THE5ERS EXACT SIMULATION ===")
for k, v in d["the5ers_exact_simulation"].items():
    print(f"  {k}: {v}")
