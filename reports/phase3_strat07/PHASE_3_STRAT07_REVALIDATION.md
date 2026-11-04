# PHASE 3: STRAT-07 FINAL REVALIDATION & SCIENTIFIC AUDIT REPORT

**Document ID**: P3-REVAL-v1.0  
**Phase**: PHASE 3 — STRAT-07 FINAL REVALIDATION  
**Auditor / Engineer**: Hermes Autonomous Quantitative Trading Research Unit  
**Strategy Target**: STRAT-07 (Tokyo 08:15 WIB / 01:15 UTC M1 Reversal)  
**Status**: REVALIDATION COMPLETED — EMPIRICAL REJECTION CONFIRMED  

---

## 1. Executive Summary & Definitive Decision

In strict accordance with Phase 3 instructions, STRAT-07 was subjected to final revalidation under the frozen execution specification without modifying any parameters, adding filters, or merging partitions:
- **Execution Model**: Market entry with Ask/Bid separation (Long buys at Ask, exits at Bid; Short sells at Bid, exits at Ask; Commission: $0.07/oz; Slippage: $0.05/oz; Tokyo Median Spread: $0.410/oz).
- **In-Sample Period**: 2021-08-23 to 2024-08-21 UTC (3 Years).
- **Validation Period**: 2024-08-22 to 2025-08-21 UTC (1 Year, Untouched).
- **Pre-IS Historical Context**: 2015-01-01 to 2021-08-22 UTC (6.5 Years).
- **Blind Final Holdout (2025–2026)**: **STRICTLY SEALED & UNTOUCHED**.

### Final Verdict:
$$\mathbf{REJECT}$$

### Verdict Justification:
Under the pre-registered decision rules:
> *"Gagal expectancy atau PF pada validation: REJECT."*

On the independent 1-year Validation partition (2024–2025):
- **Win Rate collapsed to 24.00%** (6 wins, 19 losses).
- **Profit Factor collapsed to 0.381** (Rejection threshold: $< 1.00$).
- **Net Expectancy collapsed to -0.3618 R per trade** (95% CI: `[-0.6961 R, -0.0275 R]`).
- **Maximum Drawdown reached -10.42 R** in a single year.

STRAT-07 completely failed out-of-sample validation. It has zero forward statistical advantage.

---

## 2. In-Sample vs Validation vs Historical Partition Results

| Partition | Time Range | Trades ($N$) | Win Rate (%) | Profit Factor (PF) | Net Expectancy (R) | 95% Confidence Interval | Total Net Return (R) | Max Drawdown (R) | Realized RR | Official Decision |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **In-Sample (IS)** | 2021-08-23 to 2024-08-21 | 18 | 55.56% | 1.404 | +0.1556 R | [-0.3175, +0.6287] | +2.80 R | -2.63 R | 1.123 : 1 | Apparent Edge (N=18) |
| **Validation (OOS)** | 2024-08-22 to 2025-08-21 | 25 | **24.00%** | **0.381** | **-0.3618 R** | **[-0.6961, -0.0275]** | **-9.05 R** | **-10.42 R** | 1.205 : 1 | 🔴 **REJECT (Collapsed)** |
| **Pre-IS Historical** | 2015-01-01 to 2021-08-22 | 41 | 43.90% | 0.956 | -0.0132 R | [-0.2454, +0.2190] | -0.54 R | -6.84 R | 1.218 : 1 | Breakeven / Net Loss |
| **Combined 10-Year** | **2015-01-01 to 2025-08-21** | **84** | **40.48%** | **0.799** | **-0.0808 R** | **[-0.2648, +0.1032]** | **-6.79 R** | **-11.52 R** | **1.183 : 1** | 🔴 **OVERALL LOSS** |

---

## 3. Directional Breakdown: The Long Collapse

Analyzing Long and Short performance separately exposes severe structural asymmetry:

### A. Validation Partition (2024–2025):
- **LONG Trades ($N = 13$)**:
  - Win Rate: **7.69% (1 win, 12 losses)**!
  - Profit Factor: **0.059 (Total Destruction)**.
  - Net Expectancy: **-0.7410 R per trade**.
  - Net Return: **-9.63 R**.
- **SHORT Trades ($N = 12$)**:
  - Win Rate: **41.67% (5 wins, 7 losses)**.
  - Profit Factor: **1.136**.
  - Net Expectancy: **+0.0489 R per trade**.
  - Net Return: **+0.59 R**.

### B. In-Sample Partition (2021–2024):
- **LONG Trades ($N = 11$)**: WR = 54.55%, PF = 1.508, Net Exp = +0.1804 R.
- **SHORT Trades ($N = 7$)**: WR = 57.14%, PF = 1.278, Net Exp = +0.1165 R.

### Auditor Finding:
During 2024–2025, buying Tokyo morning dips (Long reversals) suffered a catastrophic 92.3% failure rate. Bullish momentum expansions during the Asian session continued driving price lower, turning 15-minute lower rejection wicks into continuation bull traps.

---

## 4. Annual Performance Ledger (2015–2025)

| Year | Trades ($N$) | Wins | Losses | Win Rate (%) | Profit Factor | Annual Net Return (R) | Running Drawdown (R) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2015** | 7 | 4 | 3 | 57.14% | 1.745 | +1.64 R | -0.03 R |
| **2016** | 8 | 4 | 4 | 50.00% | 1.157 | +0.48 R | -1.16 R |
| **2017** | 4 | 2 | 2 | 50.00% | 1.189 | +0.33 R | -1.05 R |
| **2018** | 5 | 2 | 3 | 40.00% | 0.812 | -0.42 R | -1.47 R |
| **2019** | 5 | 2 | 3 | 40.00% | 0.724 | -0.66 R | -2.13 R |
| **2020** | 9 | 3 | 6 | 33.33% | 0.712 | -1.39 R | -3.52 R |
| **2021** | 6 | 3 | 3 | 50.00% | 1.108 | +0.26 R | -3.26 R |
| **2022** | 6 | 4 | 2 | 66.67% | 2.145 | +1.78 R | -1.48 R |
| **2023** | 6 | 3 | 3 | 50.00% | 1.092 | +0.18 R | -1.30 R |
| **2024** | 12 | 3 | 9 | **25.00%** | **0.412** | **-4.38 R** | **-5.68 R** |
| **2025 (to Aug)** | 16 | 4 | 12 | **25.00%** | **0.374** | **-4.57 R** | **-10.42 R** |

---

## 5. Transaction Cost Sensitivity Analysis

Evaluating STRAT-07 performance across variable spread levels ($0.30 to $1.00):

| Quoted Tokyo Spread | Total Round-Trip Friction | Win Rate (%) | Profit Factor | Net Expectancy (R) | Viability Status |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **$0.30 (Tight ECN)** | $0.42 / oz | 41.67% | **0.880** | **-0.0457 R** | **UNPROFITABLE** |
| **$0.41 (Baseline)** | $0.53 / oz | 40.48% | **0.799** | **-0.0808 R** | **UNPROFITABLE** |
| **$0.50 (Elevated)** | $0.62 / oz | 39.29% | **0.738** | **-0.1095 R** | **UNPROFITABLE** |
| **$0.75 (Wide)** | $0.87 / oz | 35.71% | **0.594** | **-0.1893 R** | **UNPROFITABLE** |
| **$1.00 (Adverse)** | $1.12 / oz | 32.14% | **0.481** | **-0.2691 R** | **UNPROFITABLE** |

Even under an artificially tight spread assumption of $0.30, STRAT-07 remains net negative (PF 0.880). The strategy has no edge regardless of spread tier.

---

## 6. Root Cause Autopsy: The Small-Sample Mirage

Why did STRAT-07 appear viable in early exploratory sweeps?

1. **The Small Sample Anomaly ($N = 6\text{ trades/year}$)**:
   - In the In-Sample period (2021–2024), STRAT-07 only generated **18 trades across 3 years** (~0.5 trades per month).
   - In an 18-trade sample, random binomial variance easily produces 10 wins out of 18 trades (55.6% WR), creating the statistical illusion of a 1.40 Profit Factor.
2. **Out-of-Sample Reality Reversion**:
   - In 2024–2025, trade frequency increased to 25 trades.
   - As sample size grew, the strategy reverted to its true long-term population mean: **Win Rate 24.0%**, **Profit Factor 0.381**, **Expectancy -0.36 R**.
3. **Pre-IS History Confirms the Rejection**:
   - From 2015 to 2021 (41 trades), the strategy had already operated at a loss (PF 0.956, Net R -0.54 R).
   - The brief positive stretch in 2021–2023 was purely a small-sample statistical fluke.

---

## 7. Final Governance Decree

$$\mathbf{STRAT-07 \; IS \; PERMANENTLY \; REJECTED.}$$

- **No live trading, demo trading, or prop-firm deployment is permitted.**
- **No parameter retuning will be performed.**
- All three historical strategies (**STRAT-08, STRAT-01, STRAT-07**) and all four Phase 2 scalping families (**H1, H2, H3, H4**) are officially **FALSIFIED AND REJECTED**.
- The sealed blind holdout (2025–2026) remains **100% UNTOUCHED**.
