import json

with open("/home/vallencia/xauusd_research/data/prelive_gate_results.json") as f:
    d = json.load(f)

print("=== 1. ARITHMETIC RECONCILIATION ===")
ar = d["arithmetic_reconciliation"]
for k, v in ar.items():
    if isinstance(v, dict):
        print(f"[{k}]")
        for sub_k, sub_v in v.items():
            print(f"  {sub_k}: {sub_v}")
    else:
        print(f"[{k}]: {v}")

print("\n=== 2. ATR FILTER OUT-OF-SAMPLE STUDY ===")
atr_s = d["atr_filter_out_of_sample_study"]
for th_k, partitions in atr_s.items():
    print(f"\n[{th_k}]")
    for part_k, metrics in partitions.items():
        print(f"  {part_k:<24}: N={metrics['n']:<4} | WR={metrics['wr']}% | PF={metrics['pf']} | Exp={metrics['exp']:+.4f}R | MDD={metrics['mdd']}R")

print("\n=== 3. UNDERWATER DURATIONS ===")
uw = d["underwater_durations"]
for k, v in uw.items():
    print(f"[{k}]")
    print(f"  Total periods: {v['total_drawdown_periods']} (Unrecovered: {v['unrecovered_periods']})")
    print(f"  Max Underwater: {v['max_underwater_cal_days']} cal days ({v['max_underwater_trading_days']} trading days, {v['max_underwater_trades']} trades)")
    print(f"  Median Underwater: {v['median_underwater_cal_days']} cal days ({v['median_underwater_trading_days']} trading days)")
    print(f"  P90 Underwater: {v['p90_underwater_cal_days']} cal days")

print("\n=== 4. DIVERSIFICATION & DOWNSIDE PROTECTION ===")
div = d["diversification_and_downside_protection"]
for k, v in div.items():
    print(f"  {k}: {v}")

print("\n=== 5. EXECUTION FRICTION MATRIX ===")
ef = d["execution_friction_matrix"]
for sp_k, slips in ef.items():
    print(f"\n[{sp_k}]")
    for slip_k, res in slips.items():
        s8 = res["strat08"]
        pb = res["portfolio_b"]
        print(f"  {slip_k} (Tot ${res['total_friction_dollars']}): STRAT08 PF={s8['pf']}, Exp={s8['exp']:+.4f}R | PortB PF={pb['pf']}, Exp={pb['exp']:+.4f}R, MDD={pb['mdd_r']}R")

print("\n=== 6. EVT DAILY LOSS BREACH RISK ===")
evt = d["extreme_value_daily_loss_tail_risk"]
print("GPD Fit:", evt["gpd_fit_parameters"])
for sz_k, v in evt["daily_loss_breach_probability_by_risk_size"].items():
    print(f"  {sz_k}: Limit {v['daily_limit_r']}R | P(Daily Breach)={v['evt_daily_breach_prob_per_day']} | DaysToBreach={v['expected_trading_days_to_breach']} | AnnualP={v['annualized_breach_prob']}")
