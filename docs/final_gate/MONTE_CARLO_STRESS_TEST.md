# MONTE CARLO STRESS TEST & CAPITAL RECOVERY AUDIT

**Audit Date**: 2026-11-01  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Evaluation Target**: The 5ers High Stakes $2,500 Challenge ($19 Entry)  
**Execution Baseline**: 10,000 Iterations per Simulation Engine  
**Account Rules**: Step 1 +$250 (+10%), Step 2 +$125 (+5%), Max Loss -$250 (-10%), Daily Loss -$125 (-5%), Min 3 Profitable Days  

---

## 1. Multi-Engine Monte Carlo Results Matrix

We subjected the combined portfolio (1,561 trades) to four distinct stress engines:

| Monte Carlo Engine | Description / Stress Condition | Step 1 Pass % | Step 2 Pass % | Overall Complete % | Daily Loss Breach % | Max Loss Breach % | Completion Time (Median) | Completion Time (P90) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Engine 1: Independent IID** | Uncorrelated random sampling from trade pool | 77.76% | 82.72% | **64.32%** | 32.28% | **0.00%** | 199 Days (~6.6 mos) | 346 Days (~11.5 mos) |
| **Engine 2: Block Bootstrap** | Resampling in blocks of 10 trades (preserves losing streaks) | 75.91% | 81.81% | **62.10%** | 34.35% | **0.00%** | 196 Days (~6.5 mos) | 343 Days (~11.4 mos) |
| **Engine 3: Regime-Conditioned** | 50% weight placed on adverse 2023–2024 regime | 70.25% | 78.31% | **55.01%** | 39.57% | **0.00%** | 211 Days (~7.0 mos) | 367 Days (~12.2 mos) |
| **Engine 4: Friction Stress** | Elevated spread ($0.75 round-trip) + execution slippage | 35.24% | 53.92% | **19.00%** | 71.01% | **0.00%** | 240 Days (~8.0 mos) | 405 Days (~13.5 mos) |

---

## 2. Key Insights Across Simulation Engines

### A. Total Drawdown Resilience (Zero Max Loss Breaches)
Across **all 40,000 total simulated trials**, the Max Total Loss violation rate was strictly **0.00%**. Not a single account hit the -$250.00 total loss cutoff when trading at the baseline risk of $15.00 per trade. The strategy edge is robust enough to prevent deep capital insolvency.

### B. Block Clustering vs Independent Sampling
Comparing Engine 1 (IID) to Engine 2 (Block Bootstrap):
- The overall completion rate dropped only slightly from **64.32%** to **62.10%**.
- Daily loss breach increased from **32.28%** to **34.35%**.
- This proves that temporal clustering (consecutive losing streaks) has a minor impact on long-term survival, but reinforces the necessity of intra-day circuit breakers.

### C. The Devastating Impact of Spread Expansion (Engine 4)
When spread widens to $0.75:
- Overall completion rate collapses from **64.32% down to 19.00%**.
- Daily loss breach spikes to **71.01%**.
- **Crucial Rule**: The strategy **must never be run on standard or marked-up spread accounts**. It is strictly an ECN / raw-spread strategy.

---

## 3. Modeling of Intrabar Floating Losses & Open Positions

### Execution Realism Audit:
1. **Pessimistic Intrabar Resolution**:
   - In all simulations, if a trade's Stop Loss and Take Profit were both touched during the same bar or session, the algorithm assumed the Stop Loss was hit first (-1.00 R loss).
2. **Equity vs Balance High-Water Mark**:
   - The5ers calculates Daily Loss based on **Equity at Midnight Broker Time (00:00 server time)**.
   - If an open position is carried overnight with floating unrealized loss, that loss counts toward the next day's daily loss budget.
   - In our portfolio, **zero positions are held overnight**. All trades either resolve intra-day or are forcibly liquidated before 21:00 UTC rollover. Consequently, balance equals equity at midnight, eliminating overnight floating drawdown rollover surprises.
