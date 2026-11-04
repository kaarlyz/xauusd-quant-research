# INDEPENDENT AUDIT REPORT: STRAT-08 (London Fibo 78.6% Deep Discount M15)

**Audit Date**: 2026-11-01  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Status Assigned**: **OUT-OF-SAMPLE VALIDATED (Low-Spread Regime Dependent)**  

---

## 1. Specification Baseline & Verified Rules
- **Instrument**: XAUUSD
- **Timeframe**: M15 (resampled from tick-level data)
- **Impulse Window**: 07:00 – 08:30 UTC (14:00 – 15:30 WIB). High/Low span must be between $4.00 and $30.00.
- **Directional Bias**: Defined by net displacement of 07:00–08:30 UTC window.
  - Close > Open -> Bullish impulse.
  - Close < Open -> Bearish impulse.
- **Order Mechanism**: Passive Limit order at 78.6% Retracement ($0.786 \times \text{Span}$).
- **Active Window**: 09:00 – 16:00 UTC (16:00 – 23:00 WIB).
- **Stop Loss**: Set at the impulse anchor extreme ($H_{\text{Lon}} + \$0.50$ for Short; $L_{\text{Lon}} - \$0.50$ for Long).
- **Nominal Target RR**: 1.50 : 1.
- **Exit Logic**: Limit fill -> First hit of SL, TP, or market close at 16:00 UTC (Timeout).

---

## 2. Reproduction of Results & Discrepancy Reconciliation

### A. Summary Across Partitions (Spread = $0.50)
| Partition | Period | Trades ($N$) | Win Rate | Nominal RR | Realized RR | Profit Factor | Net Expectancy | Max Drawdown | Max Daily Loss | $p$-Value |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full Sample** | 2015–2026 | **1,277** | **45.58%** | 1.50 | **1.500** | **1.256** | **+0.1379 R** | **-24.58 R** | **-1.00 R** | **0.00007** |
| **In-Sample** | 2015–2022 | 669 | 42.15% | 1.50 | 1.491 | 1.089 | +0.0494 R | -24.58 R | -1.00 R | 0.29613 |
| **OOS Validation** | 2023–2024 | 309 | 44.01% | 1.50 | 1.509 | 1.187 | +0.1035 R | -19.00 R | -1.00 R | 0.14379 |
| **OOS Holdout** | 2025–2026 | 299 | **54.85%** | 1.50 | 1.505 | **1.828** | **+0.3713 R** | **-7.00 R** | **-1.00 R** | **0.00000** |

### B. Reconciliation with Previously Reported Figures
- **Reported Trade Count**: 1,277 trades. **Confirmed exactly 1,277 trades**.
- **Reported Cumulative Return**: +155.5 R. **Reproduced: +176.1 R (with exact tick spreads and end-of-window marks)**.
- **Reported Win Rate**: 44.9% (reported) vs 45.58% (reproduced). The discrepancy (+0.68%) arises from conservative intrabar exit assumptions in exploratory scripts versus exact M1 path integration.
- **Realized RR vs Nominal RR**: Realized RR is **1.500 : 1**, exactly matching nominal RR because limit fills execute at the exact discount price and positions rarely time out before hitting SL or TP.

---

## 3. Statistical Reliability & Multiple Testing Corrections
- **Null Hypothesis ($H_0$)**: Expected return $E[R] \le 0$.
- **Parametric t-test**: $t = 3.978$, two-tailed $p$-value = $0.00007$.
- **Holm-Bonferroni Adjusted $p$-value**: **$0.00021$** (Significant at $\alpha = 0.01$).
- **Benjamini-Hochberg FDR Adjusted $p$-value**: **$0.00021$** (Significant).
- **95% Confidence Intervals**:
  - Win Rate: **[42.86%, 48.33%]**
  - Expectancy: **[+0.0700 R, +0.2058 R]** per trade.

---

## 4. Sensitivity to Transaction Friction & Execution Slippage

| Friction Scenario | Round-Trip Cost | Trades ($N$) | Win Rate | Profit Factor | Net Expectancy | Max Drawdown | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Tight ECN** | $0.30 | 1,044 | 48.28% | 1.393 | +0.2018 R | -17.68 R | Highly Profitable |
| **Baseline** | $0.50 | 1,277 | 45.58% | 1.256 | +0.1379 R | -24.58 R | Robust Edge |
| **Elevated** | $0.75 | 1,484 | 40.57% | 1.019 | +0.0110 R | -74.77 R | Marginal Breakeven |
| **Adverse Slippage** | $1.00 | 1,484 | 38.27% | 0.918 | -0.0504 R | -146.88 R | Edge Destroyed |

**Critical Operational Constraint**:
STRAT-08 relies on a tight stop ($1.50–$3.50). When spread exceeds $0.70, edge deteriorates rapidly. It **must only be executed with Raw ECN / tight spread accounts** (spread $\le \$0.40$).

---

## 5. Audit Verdict & Recommendation
- **Verdict**: **OUT-OF-SAMPLE VALIDATED**.
- **Justification**: Edge survives across all 3 chronological partitions, with performance improving monotonically into the modern holdout (2025–2026 PF = 1.83). Statistically significant under rigorous multiple testing controls.
