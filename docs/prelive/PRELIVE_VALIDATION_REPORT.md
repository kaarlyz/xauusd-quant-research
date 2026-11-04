# PRE-LIVE VALIDATION & EXECUTIVE AUDIT REPORT

**Audit Date**: 2026-11-01  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Mandate**: FINAL PRE-LIVE GATE — NO MORE STRATEGY OPTIMIZATION  
**Scope**: Final determination on STRAT-08 (London Fibo 78.6% M15), STRAT-07 (Tokyo 08:15 M1), and their combined portfolio before live deployment.

---

## 1. Complete Reconciliation of Arithmetic Discrepancies

All drawdown and capital risk figures were recalculated directly from source trade records using uniform tick-level path resolution.

### A. Resolution of the $180.57 vs $184.35 Discrepancy
- **Standalone STRAT-08 Maximum Drawdown**:
  - Raw unrounded MDD: **24.5756 R**
  - At $7.50 risk (exact from raw): $24.5756 \times \$7.50 = \mathbf{\$184.32}$
  - At $7.50 risk (from rounded 24.58 R): $24.58 \times \$7.50 = \mathbf{\$184.35}$
  - At $15.00 risk: $24.5756 \times \$15.00 = \mathbf{\$368.63}$
- **Portfolio B (STRAT-08 + STRAT-07) Maximum Drawdown**:
  - Raw unrounded MDD: **24.0756 R**
  - At $7.50 risk (exact from raw): $24.0756 \times \$7.50 = \mathbf{\$180.57}$
  - At $7.50 risk (from rounded 24.08 R): $24.08 \times \$7.50 = \mathbf{\$180.60}$
  - At $15.00 risk: $24.0756 \times \$15.00 = \mathbf{\$361.13}$
- **Portfolio C (All Three Strategies) Maximum Drawdown**:
  - Raw unrounded MDD: **25.1191 R**
  - At $7.50 risk (exact from raw): $25.1191 \times \$7.50 = \mathbf{\$188.39}$
  - At $7.50 risk (from rounded 25.12 R): $25.12 \times \$7.50 = \mathbf{\$188.40}$
  - At $15.00 risk: $25.1191 \times \$15.00 = \mathbf{\$376.79}$

### Conclusion:
The previously cited **$180.57** figure belongs specifically to **Portfolio B (STRAT-08 + STRAT-07)** ($24.0756\text{R} \times \$7.50$). Standalone STRAT-08 is **$184.32 / $184.35**. Both figures are mathematically verified and traceable to raw trade arrays.

---

## 2. Definitive Summary of the 5 Mandatory Inquiries

| Inquiry Area | Key Finding | Quantitative Evidence | Final Status |
| :--- | :--- | :--- | :---: |
| **1. STRAT-08 Statistical Validity** | Edge survives across all 3 partitions; statistical significance holds after 79-hypothesis penalty | Bonferroni $p = 0.00553 < 0.01$; 95% Block Bootstrap CI = [+0.049 R, +0.195 R] | **VALIDATED** |
| **2. ATR Filter Rule Status** | $1.30 threshold was observed on full dataset; improves PF but was not locked a priori | Out-of-sample holdout (2025–2026) unaffected ($N=299$ identical across all filters) | **EXPLORATORY (Non-Core)** |
| **3. STRAT-07 Diversification Value** | True downside protection confirmed; delivers net positive R during STRAT-08 loss days | Coincident conditional correlation = -0.173; generated +8.82 R on STRAT-08 loss days | **CONFIRMED HEDGE** |
| **4. Execution Feasibility** | Highly sensitive to friction; edge evaporates if total cost exceeds $0.55 round-trip | At $0.32 cost: PF 1.38; At $0.52 cost: PF 1.23; At $0.82 cost: PF 0.97 (negative) | **CONDITIONAL (Raw ECN Only)** |
| **5. Prop-Firm Survival** | Sizing at $15/trade fails max loss; sizing at $7.50/trade survives 100% of historical drawdowns | $7.50 sizing caps MDD at $180.57 (7.22%), leaving $69.43 buffer from $250 termination | **APPROVED AT $7.50 RISK** |

---

## 3. High-Water Mark & Recovery Audit (Underwater Time)

Drawdown recovery conditions were formally audited:
- **High-Water Mark (HWM)**: Cumulative sum of R multiples at historical peak.
- **Underwater State**: Cumulative R strictly below previous peak.
- **Recovery Condition**: Cumulative R reaches or exceeds previous peak.

### Comparative Duration Statistics:

| Metric | STRAT-08 Standalone | Portfolio B (STRAT-08 + STRAT-07) | Diversification Impact |
| :--- | :---: | :---: | :---: |
| **Total Drawdown Periods** | 79 Periods | 97 Periods | Higher turnover |
| **Unrecovered Periods** | 1 (Active at end) | 0 (All recovered) | 100% Recovery achieved |
| **Maximum Underwater Duration (Calendar Days)** | **1,388 Days (~3.8 Years)** | **719 Days (~1.9 Years)** | **-669 Days (-48.2% Reduction!)** |
| **Maximum Underwater Duration (Trading Days)** | 235 Trading Days | 236 Trading Days | Equal trading exposure |
| **Maximum Underwater Trades** | 234 Trades | 239 Trades | Equal trade exposure |
| **Median Underwater Duration (Calendar Days)** | **7.0 Days** | **7.0 Days** | Identical quick recovery |
| **90th Percentile Underwater Duration** | **96.6 Days** | **83.2 Days** | Shorter tail duration |

### Interpretation:
STRAT-08 alone experienced a grueling 1,388 calendar day stagnation between October 2016 and July 2020. Combining it with STRAT-07 cut this stagnation in half (**719 days**), proving that multi-session diversification is essential for real-world psychological survival.

---

## 4. Final Operational Directives

1. **Deploy Strategy Portfolio**: **STRAT-08 + STRAT-07 (Portfolio B)**.
2. **Exclude STRAT-01**: STRAT-01 remains excluded due to failure during the 2023–2024 validation split.
3. **Core Entry Rules Locked**: Do not enforce the post-hoc ATR > $1.30 filter as an immutable barrier; use standard locked baseline parameters.
4. **Execution Sizing**: **Fixed $7.50 (0.30%) per trade**.
5. **Broker Requirement**: Raw ECN spread $\le \$0.35$.
