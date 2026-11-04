# FINAL METRIC RECONCILIATION & MATHEMATICAL IDENTITY AUDIT

**Audit Date**: 2026-11-01  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Mandate**: FINAL GATE — MATHEMATICAL CONSISTENCY & CAPITAL RISK AUDIT  
**Scope**: Exact reconciliation of Trade Count, Win Rate, Average Win/Loss, Realized RR, Gross PnL, Profit Factor, Net Expectancy, and Cumulative R.

---

## 1. Master Metric Reconciliation Table

Every figure below was generated from identical trade populations using uniform $0.50 round-trip spread friction and strict intrabar path validation on 4,182,209 M1 bars (2015–2026).

| Metric | STRAT-08 (London Fibo M15) | STRAT-07 (Tokyo 08:15 M1) | STRAT-01 (London 17:30 M1) | COMBINED PORTFOLIO |
| :--- | :---: | :---: | :---: | :---: |
| **Total Trades ($N$)** | **1,277** | **129** | **155** | **1,561** |
| **Winning Trades ($N_w$)** | 582 | 65 | 75 | 722 |
| **Losing Trades ($N_l$)** | 695 | 64 | 79 | 838 |
| **Zero / Breakeven Trades** | 0 | 0 | 1 | 1 |
| **Win Rate ($\text{WR}$)** | **45.58%** | **50.39%** | **48.39%** | **46.25%** |
| **Loss Rate ($\text{LR}$)** | **54.42%** | **49.61%** | **50.97%** | **53.68%** |
| **Average Win R** | **+1.4843 R** | **+0.9322 R** | **+0.8499 R** | **+1.3687 R** |
| **Average Loss R** | **-0.9896 R** | **-0.7467 R** | **-0.7054 R** | **-0.9443 R** |
| **Nominal Target RR** | 1.50 : 1 | 1.50 : 1 | 1.50 : 1 | 1.50 : 1 |
| **Realized RR ($\text{Avg Win}/\text{Avg Loss}$)** | **1.4999 : 1** | **1.2484 : 1** | **1.2048 : 1** | **1.4494 : 1** |
| **Gross Profit (R)** | **+863.87 R** | **+60.59 R** | **+63.74 R** | **+988.20 R** |
| **Gross Loss (R)** | **-687.80 R** | **-47.79 R** | **-55.73 R** | **-791.31 R** |
| **Profit Factor ($\text{GP}/\text{GL}$)** | **1.2560** | **1.2679** | **1.1438** | **1.2488** |
| **Net Expectancy (Direct Sample Mean)** | **+0.1379 R** | **+0.0992 R** | **+0.0517 R** | **+0.1261 R** |
| **Net Expectancy (Formula Calculated)** | **+0.1379 R** | **+0.0992 R** | **+0.0517 R** | **+0.1261 R** |
| **Mathematical Identity Discrepancy** | **0.00000000** | **0.00000000** | **0.00000000** | **0.00000000** |
| **Total Cumulative Net R** | **+176.07 R** | **+12.80 R** | **+8.02 R** | **+196.89 R** |
| **Max Realized Drawdown** | **-24.58 R** | **-10.42 R** | **-9.08 R** | **-25.12 R** |

---

## 2. Verification of Mathematical Identity

The fundamental identity of trading expectancy states:
$$\text{Expectancy} = (\text{Win Rate} \times \text{Average Win R}) - (\text{Loss Rate} \times \text{Average Loss R})$$

### Empirical Proof:
1. **STRAT-08**:
   $$\text{Expectancy} = (0.45575568 \times 1.484313) - (0.54424432 \times 0.989640) = 0.676483 - 0.538606 = +0.137877 \text{ R}$$
   $$\text{Sample Mean} = \frac{1}{1,277} \sum r_i = +0.137877 \text{ R} \quad \rightarrow \quad \Delta = 0.00000000$$

2. **STRAT-07**:
   $$\text{Expectancy} = (0.50387597 \times 0.932154) - (0.49612403 \times 0.746719) = 0.469689 - 0.370468 = +0.099221 \text{ R}$$
   $$\text{Sample Mean} = \frac{1}{129} \sum r_i = +0.099221 \text{ R} \quad \rightarrow \quad \Delta = 0.00000000$$

3. **STRAT-01**:
   $$\text{Expectancy} = (0.48387097 \times 0.849867) - (0.50967742 \times 0.705443) = 0.411226 - 0.359548 = +0.051677 \text{ R}$$
   $$\text{Sample Mean} = \frac{1}{155} \sum r_i = +0.051677 \text{ R} \quad \rightarrow \quad \Delta = 0.00000000$$

4. **Combined Portfolio**:
   $$\text{Expectancy} = (0.46252402 \times 1.368698) - (0.53683536 \times 0.944284) = 0.633056 - 0.506925 = +0.126131 \text{ R}$$
   $$\text{Sample Mean} = \frac{1}{1,561} \sum r_i = +0.126131 \text{ R} \quad \rightarrow \quad \Delta = 0.00000000$$

**Verdict**: The mathematical identity holds with zero error ($\Delta < 10^{-8}$) across all strategies and the portfolio.

---

## 3. Explanation of Every Discrepancy vs Initial Reports

1. **Discrepancy 1: Nominal RR (1.50) vs Realized RR in STRAT-07 (1.25) and STRAT-01 (1.20)**:
   - *Cause*: In M1 strategies, trades have an enforced 30-minute time-exit rule (STRAT-07 exits at 08:44 WIB; STRAT-01 exits at 17:59 WIB). When positions are closed at market before hitting SL or TP, profitable trades close with partial gains (e.g. $+0.40\text{R}$ to $+1.10\text{R}$) rather than $+1.50\text{R}$. This lowers the average win from $+1.50\text{R}$ to $+0.93\text{R}$ (STRAT-07) and $+0.85\text{R}$ (STRAT-01).
   - *Contrast with STRAT-08*: STRAT-08 holds for up to 7 hours on M15. Nearly 98% of trades resolve directly at the limit TP ($+1.50\text{R}$) or stop loss ($-1.00\text{R}$), preserving a true Realized RR of **1.4999 : 1**.

2. **Discrepancy 2: STRAT-08 Cumulative Return (+155.5 R reported vs +176.07 R reproduced)**:
   - *Cause*: The early exploratory prototype script `fast_fibo_scan.py` recorded trade outcomes conservatively by assigning $-1.00\text{R}$ to trades open at session close. The final audit engine `audit_engine.py` marked open positions to exact market close on the final candle of the day, properly recognizing accumulated open profit.
