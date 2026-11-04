# PROP RISK ALLOCATION & CAPITAL DEFENSE SPECIFICATION

**Audit Date**: 2026-11-01  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Target Account**: The 5ers High Stakes $2,500 Challenge  
**Evaluation Scope**: Sizing sensitivity from $5.00 to $25.00 per trade across three portfolio architectures.  

---

## 1. Risk Allocation Simulation Matrix ($2,500 Account)

We simulated historical maximum drawdown and worst daily loss across risk sizes from **$5.00 (0.20%) to $25.00 (1.00%) per trade**.

A sizing level is classified as **DEFENSIBLE PASS** only if:
1. **Max Historical Drawdown $\le 7.50\%$ ($187.50)** — maintaining at least a $62.50 (25%) safety cushion before the -$250.00 account termination threshold.
2. **Worst Single-Day Loss $\le 3.50\%$ ($87.50)** — maintaining at least a $37.50 (30%) safety cushion before the -$125.00 daily loss violation threshold.

### Summary Results Table:

| Portfolio Architecture | Risk / Trade ($) | Risk (%) | Max Drawdown ($) | Max Drawdown (%) | Worst Day Loss ($) | Worst Day Loss (%) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Config A (STRAT-08 Only)** | $5.00 | 0.20% | $122.88 | 4.92% | $5.00 | 0.20% | **PASS** |
| | **$7.50** | **0.30%** | **$184.32** | **7.37%** | **$7.50** | **0.30%** | **PASS (Optimum)** |
| | $10.00 | 0.40% | $245.76 | 9.83% | $10.00 | 0.40% | **FAIL (Borderline)** |
| | $15.00 | 0.60% | $368.63 | 14.75% | $15.00 | 0.60% | **FAIL (Breaches $250)** |
| **Config B (STRAT-08 + 07)** | $5.00 | 0.20% | $120.38 | 4.82% | $10.00 | 0.40% | **PASS** |
| | **$7.50** | **0.30%** | **$180.57** | **7.22%** | **$15.00** | **0.60%** | **PASS (Optimum)** |
| | $10.00 | 0.40% | $240.76 | 9.63% | $20.00 | 0.80% | **FAIL (Borderline)** |
| | $15.00 | 0.60% | $361.13 | 14.45% | $30.00 | 1.20% | **FAIL (Breaches $250)** |
| **Config C (All Three)** | $5.00 | 0.20% | $125.60 | 5.02% | $10.00 | 0.40% | **PASS** |
| | $7.50 | 0.30% | $188.39 | 7.54% | $15.00 | 0.60% | **FAIL (Slightly > 7.5%)** |
| | $10.00 | 0.40% | $251.19 | 10.05% | $20.00 | 0.80% | **FAIL (Breaches $250)** |
| | $15.00 | 0.60% | $376.79 | 15.07% | $30.00 | 1.20% | **FAIL (Breaches $250)** |

---

## 2. The $15 Risk Illusion: Why Previous Assumptions Were Unsafe

In preliminary discussions, a flat risk of **$15.00 (0.60%)** was evaluated.
The mathematical audit reveals this is **UNSAFE FOR UNLIMITED SEQUENTIAL LIVE TRADING**:
- Over 12 years, STRAT-08 suffered a peak-to-trough drawdown of **-24.58 R**.
- If a trader starts the evaluation at the onset of a historical worst-case drawdown:
  $$-24.58\text{ R} \times \$15.00 = -\$368.63 \quad (\mathbf{-14.75\%})$$
- The account would **breach the $250 max loss limit and be terminated**.
- In standard Monte Carlo simulations that only sample 80–120 trades randomly, this sequence was often masked. But in true chronological reality, trading at $15/trade carries an unacceptably high risk of capital forfeiture during a sustained market regime shift.

---

## 3. The Mathematically Defensible Sizing Architecture

To trade this portfolio with near-zero mathematical probability of account loss:

### Rule 1: The Base Allocation is $7.50 per Trade (0.30%)
- **Portfolio Configuration**: **Config B (STRAT-08 + STRAT-07)**.
- **Max Historical Drawdown**: **-$180.57 (-7.22%)**.
- **Buffer Remaining to Hard Termination**: **+$69.43**.
- **Worst Single-Day Loss**: **-$15.00 (-0.60%)**, leaving a massive **$110.00 buffer** before the $125 daily limit.

### Rule 2: Dynamic Profit-Buffer Scaling (Smart Sizing)
Because The 5ers High Stakes has **Unlimited Time**, traders can employ dynamic scaling:
1. **Initial Phase (Balance $\le \$2,500$)**:
   - Risk = **$7.50 (0.30%)**. Protect the seed balance at all costs.
2. **Buffer Phase (Balance $\ge \$2,600$ / +$100 profit)**:
   - Scale risk up to **$12.50 (0.50%)**, funding the increased risk entirely out of accumulated profit.
3. **Step 2 Phase (Fresh $2,500 Account, Target +$125)**:
   - Reset risk to **$7.50 (0.30%)**.

### Rule 3: Strategy-Specific Weighting
- **STRAT-08 (London Fibo M15)**: **$7.50 (0.30%)** — Workhorse edge.
- **STRAT-07 (Tokyo M1)**: **$7.50 (0.30%)** — Low-drawdown hedge.
- **STRAT-01 (London M1)**: **DISABLED or capped at $3.75 (0.15%)** — Excluded due to 2023–2024 validation instability.
