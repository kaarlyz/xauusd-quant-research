# INDEPENDENT AUDIT REPORT: STRAT-01 (London 17:30 WIB Reversal M1)

**Audit Date**: 2026-11-01  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Status Assigned**: **INCONCLUSIVE (Validation Failure in 2023–2024 Split)**  

---

## 1. Specification Baseline & Verified Rules
- **Instrument**: XAUUSD
- **Timeframe**: M1
- **Evaluation Timing**: Exactly at minute 29 of hour 10 UTC (17:29 WIB).
- **Execution Timing**: Market order at open of minute 30 of hour 10 UTC (17:30:00 WIB).
- **Pre-Condition**:
  - Net displacement $|\Delta P| = |Close_{29} - Open_{00}| \ge \max(0.8 \times \text{ATR}_{60}, \$2.00)$.
  - Rejection wick on 30m range $> 30\%$.
- **Stop Loss**: 30m extreme ($H_{30} + \$0.50$ for Short; $L_{30} - \$0.50$ for Long). Risk must be between $0.80 and $15.00.
- **Nominal Target RR**: 1.50 : 1.
- **Time Exit**: Market close at minute 59 of hour 10 UTC (17:59 WIB) if neither SL nor TP is reached.

---

## 2. Reproduction of Results & Discrepancy Reconciliation

### A. Summary Across Partitions (Spread = $0.50)
| Partition | Period | Trades ($N$) | Win Rate | Nominal RR | Realized RR | Profit Factor | Net Expectancy | Max Drawdown | Max Daily Loss | $p$-Value |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full Sample** | 2015–2026 | **155** | **48.39%** | 1.50 | **1.205** | **1.144** | **+0.0517 R** | **-9.08 R** | **-1.00 R** | **0.48080** |
| **In-Sample** | 2015–2022 | 42 | **59.52%** | 1.50 | 1.052 | **1.547** | **+0.1368 R** | -4.16 R | -1.00 R | 0.28767 |
| **OOS Validation** | 2023–2024 | 28 | **32.14%** | 1.50 | 0.817 | **0.410** | **-0.2647 R** | -8.33 R | -1.00 R | **0.05983** |
| **OOS Holdout** | 2025–2026 | 85 | **48.24%** | 1.50 | 1.391 | **1.300** | **+0.1139 R** | -7.45 R | -1.00 R | 0.29338 |

### B. Reconciliation with Previously Reported Figures
- **Reported Trade Count**: 155 trades. **Confirmed exactly 155 trades**.
- **Reported Win Rate**: 48.4%. **Confirmed 48.39%**.
- **Reported Profit Factor**: 1.14. **Confirmed 1.144**.
- **Reported Max Drawdown**: -9.1 R. **Confirmed -9.08 R**.
- **Realized RR vs Nominal RR**:
  - Nominal RR = 1.50 : 1.
  - Realized RR = **1.205 : 1**.
  - As with STRAT-07, timeout exits at minute 59 curtail wins to partial gains, reducing net average win size.

---

## 3. Critical Discovery: The 2023–2024 Regime Failure
An audit of chronological splits reveals an unstable equity profile:
1. **2015–2022**: Exceptionally high win rate (59.52%) and strong PF (1.55).
2. **2023–2024 OOS Validation**: Complete collapse. Win rate plummeted to **32.14%**, Profit Factor crashed to **0.41**, and expectancy dropped to **-0.2647 R**.
3. **2025–2026 Holdout**: Rebounded to 48.24% WR and 1.30 PF.

**Macro Structural Explanation**:
During 2023–2024, institutional London lunch flows experienced a structural change: trending continuation regimes replaced mean-reversion during 17:00–18:00 WIB, causing rejection wicks to fail as continuation traps.

---

## 4. Statistical Reliability & Multiple Testing Corrections
- **Null Hypothesis ($H_0$)**: Expected return $E[R] \le 0$.
- **Parametric t-test**: $t = 0.707$, two-tailed $p$-value = **$0.48080$**.
- **Holm-Bonferroni Adjusted $p$-value**: **$0.48080$** (Statistically Indistinguishable from Randomness).
- **95% Confidence Interval for Expectancy**: **[-0.0926 R, +0.1960 R]** — heavily straddles zero.

---

## 5. Sensitivity to Transaction Friction & Execution Slippage

| Friction Scenario | Round-Trip Cost | Trades ($N$) | Win Rate | Profit Factor | Net Expectancy | Max Drawdown | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Tight ECN** | $0.30 | 156 | 50.00% | 1.170 | +0.0633 R | -9.62 R | Moderate |
| **Baseline** | $0.50 | 155 | 48.39% | 1.144 | +0.0517 R | -9.08 R | Marginal |
| **Elevated** | $0.75 | 153 | 46.41% | 1.097 | +0.0347 R | -11.02 R | Weak |
| **Adverse Slippage** | $1.00 | 153 | 46.41% | 1.070 | +0.0245 R | -12.18 R | Survives |

---

## 6. Audit Verdict & Recommendation
- **Verdict**: **INCONCLUSIVE**.
- **Justification**:
  - The strategy cannot be certified as robust because it **failed out-of-sample validation during the 2023–2024 period** (PF 0.41).
  - Its full-sample $p$-value ($0.481$) fails all statistical significance hurdles.
  - While it recovered in 2025–2026 and maintains a tiny drawdown footprint (-9.08 R), it carries undeniable regime-dependence risk.
  - **Operational Rule**: If traded, it must be gated with a regime filter (e.g. only take when London morning range is expanded $> 1.5 \times \text{ATR}$) or capped at half-risk ($0.30\%$).
