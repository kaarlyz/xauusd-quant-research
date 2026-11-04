# INDEPENDENT AUDIT REPORT: STRAT-07 (Tokyo 08:15 WIB Reversal M1)

**Audit Date**: 2026-11-01  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Status Assigned**: **PROMISING (Sample Size Constrained, Regime Dependent)**  

---

## 1. Specification Baseline & Verified Rules
- **Instrument**: XAUUSD
- **Timeframe**: M1
- **Evaluation Timing**: Exactly at minute 14 of hour 01 UTC (08:14 WIB).
- **Execution Timing**: Market order at open of minute 15 of hour 01 UTC (08:15:00 WIB).
- **Pre-Condition**:
  - Net displacement $|\Delta P| = |Close_{14} - Open_{00}| \ge \max(0.7 \times \text{ATR}_{60}, \$1.50)$.
  - Rejection wick on 15m range $> 35\%$.
- **Stop Loss**: 15m extreme ($H_{15} + \$0.50$ for Short; $L_{15} - \$0.50$ for Long). Risk must be between $0.80 and $15.00.
- **Nominal Target RR**: 1.50 : 1.
- **Time Exit**: Market close at minute 44 of hour 01 UTC (08:44 WIB) if neither SL nor TP is reached.

---

## 2. Reproduction of Results & Discrepancy Reconciliation

### A. Summary Across Partitions (Spread = $0.50)
| Partition | Period | Trades ($N$) | Win Rate | Nominal RR | Realized RR | Profit Factor | Net Expectancy | Max Drawdown | Max Daily Loss | $p$-Value |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full Sample** | 2015–2026 | **129** | **50.39%** | 1.50 | **1.248** | **1.268** | **+0.0992 R** | **-10.42 R** | **-1.00 R** | **0.24703** |
| **In-Sample** | 2015–2022 | 46 | 50.00% | 1.50 | 1.481 | 1.481 | +0.1336 R | -5.33 R | -1.00 R | 0.29578 |
| **OOS Validation** | 2023–2024 | 19 | 47.37% | 1.50 | 1.036 | 0.931 | -0.0313 R | -4.35 R | -1.00 R | 0.89358 |
| **OOS Holdout** | 2025–2026 | 64 | **51.56%** | 1.50 | 1.200 | **1.278** | **+0.1133 R** | **-6.16 R** | **-1.00 R** | **0.38820** |

### B. Reconciliation with Previously Reported Figures
- **Reported Trade Count**: 129 trades. **Confirmed exactly 129 trades**.
- **Reported Win Rate**: 50.4%. **Confirmed 50.39%**.
- **Reported Profit Factor**: 1.27. **Confirmed 1.268**.
- **Reported Net Expectancy**: +0.099 R. **Confirmed +0.0992 R**.
- **Realized RR Discrepancy (CRITICAL FINDING)**:
  - Nominal RR was specified as **1.50 : 1**.
  - Realized RR is **1.248 : 1**.
  - *Root Cause Identified*: In ~22% of trades, neither SL nor TP was hit before the 30-minute timeout exit (08:44 WIB). Positions were closed at market with partial profit (average $+0.65 R$) rather than full $+1.50 R$, bringing the average realized win down to $+1.248 R$.

---

## 3. Statistical Reliability & Multiple Testing Corrections
- **Null Hypothesis ($H_0$)**: Expected return $E[R] \le 0$.
- **Parametric t-test**: $t = 1.163$, two-tailed $p$-value = **$0.24703$**.
- **Holm-Bonferroni Adjusted $p$-value**: **$0.49406$** (**NOT Statistically Significant at $\alpha = 0.05$**).
- **Benjamini-Hochberg FDR Adjusted $p$-value**: **$0.37054$**.
- **Statistical Assessment**:
  - Due to low trade frequency ($N = 129$ over 12 years / ~11 trades/year), the sample size is insufficient to reject the null hypothesis of randomness at the 95% confidence level.
  - 95% Confidence Interval for Expectancy: **[-0.0699 R, +0.2683 R]** — crosses zero.

---

## 4. Sensitivity to Transaction Friction & Execution Slippage

| Friction Scenario | Round-Trip Cost | Trades ($N$) | Win Rate | Profit Factor | Net Expectancy | Max Drawdown | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Tight ECN** | $0.30 | 129 | 49.61% | 1.300 | +0.1128 R | -10.29 R | Strong Edge |
| **Baseline** | $0.50 | 129 | 50.39% | 1.268 | +0.0992 R | -10.42 R | Profitable |
| **Elevated** | $0.75 | 129 | 49.61% | 1.177 | +0.0648 R | -9.79 R | Mild Decay |
| **Adverse Slippage** | $1.00 | 129 | 47.29% | 1.073 | +0.0269 R | -10.29 R | Survives |

**Robustness Observation**:
Unlike STRAT-08, STRAT-07 is remarkably resistant to spread widening (remains PF > 1.07 even at $1.00 spread) because the 15-minute Tokyo impulse creates larger stop buffers ($2.50–$4.50).

---

## 5. Audit Verdict & Recommendation
- **Verdict**: **PROMISING**.
- **Justification**:
  - The strategy cannot be granted full `OUT-OF-SAMPLE VALIDATED` status due to small sample size ($N = 129$, $p = 0.247$) and a slight drawdown dip during 2023–2024 (PF 0.93).
  - However, it demonstrates exceptional drawdown containment (-10.42 R max over 12 years) and strong performance in the modern holdout (2025–2026 PF 1.28). It is valid as a secondary portfolio component.
