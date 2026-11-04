import json

with open("/home/vallencia/xauusd_research/data/final_gate_results.json") as f:
    d = json.load(f)

print("=== 1. METRIC RECONCILIATION ===")
for k, v in d["metric_reconciliation"].items():
    print(f"[{k}] N={v['n_trades']} (W:{v['n_wins']}, L:{v['n_losses']}) | WR={v['win_rate_pct']}% | RealRR={v['realized_rr']} | GP={v['gross_profit_r']} | GL={v['gross_loss_r']} | PF={v['profit_factor']} | ExpDirect={v['net_expectancy_direct']} | ExpFormula={v['net_expectancy_formula']} | Discrepancy={v['formula_discrepancy']} | Verified={v['identity_verified']} | NetR={v['total_net_r']}")

print("\n=== 2. STRAT-08 DEEP ROBUSTNESS ===")
s8 = d["strat08_deep_robustness"]
print("Regimes:", s8["regime_analysis"])
print(f"Max Underwater: {s8['max_underwater_trades']} trades, {s8['max_underwater_calendar_days']} calendar days")
print("Search Space adjustment:", s8["search_space_adjustment"])
print("Block Bootstrap CI 95%:", s8["block_bootstrap_ci_95"])

print("\n=== 3. SYNCHRONIZED PORTFOLIO ===")
sp = d["synchronized_portfolio"]
print("Unconditional daily corr:", sp["unconditional_daily_correlation"])
print("Conditional corr (coincident active days):", sp["conditional_correlation_active_days"])
print("Tail dependence:", sp["tail_dependence_co_loss_pct"])
print("Drawdowns comparison:", sp["drawdown_comparison_r"])

print("\n=== 4. MONTE CARLO 4 ENGINES ===")
for k, v in d["monte_carlo_4_engines"].items():
    print(f"[{k}]: {v}")

print("\n=== 5. RISK ALLOCATION MATRIX ===")
ra = d["risk_allocation_matrix"]
for p, p_res in ra.items():
    print(f"[{p}]")
    for sz_k, v in p_res.items():
        pass_str = "PASS" if v["defensible_pass"] else "FAIL"
        print(f"  {sz_k}: Risk {v['risk_pct']}% | MaxDD ${v['max_drawdown_dollars']} ({v['max_drawdown_pct']}%) | WorstDay ${v['worst_daily_loss_dollars']} ({v['worst_daily_loss_pct']}%) -> {pass_str}")
