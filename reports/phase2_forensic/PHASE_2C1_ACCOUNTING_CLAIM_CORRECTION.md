# PHASE 2C.1: ACCOUNTING CLAIM CORRECTION & EXECUTION BENCHMARK AUDIT

**Document ID**: P2C1-AUDIT-v1.0  
**Audit Phase**: PHASE 2C.1 — POST-GATE FORENSIC AUDIT  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Status**: IRREVOCABLE CORRECTION & REALISM AUDIT DECREE  

---

## 1. Formal Retraction & Correction: The "Stop Loss $\ge \$2.50$" Generalization

In Phase 2C, the following broad statement was made:
> *"Pada Stop Loss Lebar / Institusional ($D_{\text{SL}} \ge \$2.50$): Total biaya friksi hanya memakan $< 5\%$ modal risiko."*

### Auditor's Binding Correction:
**THIS STATEMENT IS MATHEMATICALLY AND OPERATIONALLY INVALID AS A GENERAL CLAIM.**

That $< 5\%$ figure applied **exclusively to an idealized passive limit entry that exits at a passive limit take-profit where zero spread and zero slippage are crossed at both ends**. For any strategy that uses market orders or stop-loss market exits, total friction remains substantial even with wide stops:

### Stop Loss Distance vs Order Combination Cost Matrix:

| Order Execution Combination | Cost per Ounce ($/oz) | $D_{\text{SL}} = \$0.70$ (Tight M1) | $D_{\text{SL}} = \$1.50$ (Normal M1) | $D_{\text{SL}} = \$2.50$ (STRAT-08) | $D_{\text{SL}} = \$5.00$ (M15 Swing) | Microstructure Realism |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Combo 1: Passive Limit Entry + Limit TP Exit** | **$0.070** | 10.00% (0.100 R) | 4.67% (0.047 R) | **2.80% (0.028 R)** | 1.40% (0.014 R) | Idealized limit win (Zero spread crossed) |
| **Combo 2: Passive Limit Entry + Market SL Exit** | **$0.120** | 17.14% (0.171 R) | 8.00% (0.080 R) | **4.80% (0.048 R)** | 2.40% (0.024 R) | Limit entry with stop slippage ($0.05) + comm |
| **Combo 3: Market Entry + Limit TP Exit** | **$0.500** | 71.43% (0.714 R) | 33.33% (0.333 R) | **20.00% (0.200 R)** | 10.00% (0.100 R) | Standard market win (Pays spread $0.38 + slip $0.05) |
| **Combo 4: Market Entry + Market SL Exit** | **$0.550** | 78.57% (0.786 R) | 36.67% (0.367 R) | **22.00% (0.220 R)** | 11.00% (0.110 R) | Standard market loss (Pays entry spread + both slips) |

### Key Audit Finding:
- For any market-order strategy (such as H1, H2, H4, or STRAT-01), even with a stop loss of **$2.50**, transaction friction consumes **20.0% to 22.0% of the entire risk budget** ($0.20\text{R}$ to $0.22\text{R}$).
- Generalizing the 0.048 R cost drag of STRAT-08 to other strategies with wide stops was an erroneous conflation of limit-order queue assumptions with market-order reality.

---

## 2. Mid-Price Benchmark Verification for H4 (Zero Omission / Zero Double-Counting)

To verify the economic drag of H4 Micro-Momentum against an unpenalized mid-price world, we reconstructed the trade ledger from first principles:

### A. The H4 Winning Trade Walkthrough:
- **Signal Time Quote**: $\text{Bid} = \$2,650.000$, $\text{Ask} = \$2,650.380$ ($\text{Spread} = \$0.380$).
- **Mid-Price at Entry**:
  $$\text{Mid}_{\text{entry}} = \frac{2,650.000 + 2,650.380}{2} = \mathbf{\$2,650.190}$$
- **Actual Market Buy Fill Price**:
  $$\text{Fill}_{\text{entry}} = \text{Ask} + \sigma_{\text{entry}} = 2,650.380 + 0.050 = \mathbf{\$2,650.430}$$
- **Effective Stop Distance**: $D_{\text{SL}} = 2,650.430 - 2,649.750 = \mathbf{\$0.680}$ $\implies V = \mathbf{0.110294\text{ Lots (11.0294 oz)}}$.
- **Actual Exit Fill (Bid)**: Price rises to hit target at **$2,650.770**.
- **Mid-Price at Exit**:
  $$\text{Mid}_{\text{exit}} = 2,650.770 + 0.190 = \mathbf{\$2,650.960}$$

### B. Mathematical PnL Comparison:
1. **Mid-Price Benchmark World**:
   $$\Delta P_{\text{mid}} = 2,650.960 - 2,650.190 = \mathbf{+\$0.770 / oz}$$
   $$\text{PnL}_{\text{mid}} = +\$0.770 \times 11.0294\text{ oz} = \mathbf{+\$8.4926} \quad (\mathbf{+1.1324\text{ R}})$$
2. **Actual Realized Ledger World**:
   $$\Delta P_{\text{actual}} = 2,650.770 - 2,650.430 = \mathbf{+\$0.340 / oz}$$
   $$\text{Gross PnL}_{\text{actual}} = +\$0.340 \times 11.0294\text{ oz} = \mathbf{+\$3.7500} \quad (\mathbf{+0.5000\text{ R}})$$
   $$\text{Commission} = -\$0.070 \times 11.0294\text{ oz} = \mathbf{-\$0.7721} \quad (\mathbf{-0.1029\text{ R}})$$
   $$\text{Net Realized PnL} = +\$3.7500 - \$0.7721 = \mathbf{+\$2.9779} \quad (\mathbf{+0.3971\text{ R}})$$
3. **Total Economic Friction Drag**:
   $$\text{Drag (\$) } = \text{PnL}_{\text{mid}} - \text{Net Realized PnL} = \$8.4926 - \$2.9779 = \mathbf{\$5.5147}$$
   $$\text{Drag (in R) } = \frac{\$5.5147}{\$7.50} = \mathbf{0.7353\text{ R}} \quad (\mathbf{73.53\%\text{ of Risk Budget}})$$

### C. Exact Component Reconciliation (Zero Discrepancy):
$$\text{Entry Half-Spread}: \$0.190 \times 11.0294\text{ oz} = \$2.0956 \quad (0.2794\text{ R})$$
$$\text{Exit Half-Spread}: \$0.190 \times 11.0294\text{ oz} = \$2.0956 \quad (0.2794\text{ R})$$
$$\text{Entry Slippage}: \$0.050 \times 11.0294\text{ oz} = \$0.5515 \quad (0.0735\text{ R})$$
$$\text{Broker Commission}: \$0.070 \times 11.0294\text{ oz} = \$0.7721 \quad (0.1029\text{ R})$$
$$\mathbf{\text{Sum Total}} = \$2.0956 + \$2.0956 + \$0.5515 + \$0.7721 = \mathbf{\$5.5148} \quad (\mathbf{0.7353\text{ R}})$$

Every penny is accounted for with zero double-counting and zero omissions. Data recorded in `ECONOMIC_DRAG_BENCHMARK_RECONSTRUCTION.csv`.

---

## 3. Forensic Audit of STRAT-08: The Limit-Fill Flaw Exposed

The core assumption supporting STRAT-08 was that passive limit entry avoids the spread and entry slippage. We audited the actual trigger logic in `audit_engine.py` (lines 385–400):

### A. The Flaw Discovered in `audit_engine.py`:
- In `audit_engine.py`, the limit buy fill condition was evaluated as:
  ```python
  if l_15[i] <= bounce: # l_15 is the M15 BID Low!
  ```
- **The Physical Impossibility**:
  - `l_15` is the **Bid price** of the candlestick.
  - A **Buy Limit order can ONLY fill when the ASK price drops to the limit price**!
  - At the moment Bid touches `bounce`, Ask is resting at $\text{bounce} + \text{Spread}$ ($\approx \text{bounce} + \$0.380$).
  - Evaluating `Low_Bid <= bounce` means `audit_engine.py` filled a Buy Limit when **Ask had NOT even reached the limit price**.
  - **In plain English**: The original backtest assumed you could buy at the Bid price without paying the spread!

### B. Empirical Re-Testing Across True Quote Fill Models:
We re-tested the entire 12-year dataset (2015–2026, 4.18M bars) using realistic quote mechanics:

| Limit Fill Execution Model | Exact Fill Condition on Bid | Total Trades (12y) | Win Rate (%) | Profit Factor | Net Expectancy (R) | Max Drawdown (R) | Realism Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Model 1: Naive Bid-Touch (Flawed)** | $\text{Low}_{\text{Bid}} \le \text{Limit}$ | 1,132 | **47.17%** | **1.339** | **+0.1793 R** | -21.00 R | **UNREALISTIC (Fictitious Spread Evasion)** |
| **Model 2: True Ask-Touch** | $\text{Low}_{\text{Bid}} \le \text{Limit} - \$0.380$ | 1,102 | **39.66%** | **0.986** | **-0.0086 R** | -95.00 R | **NET LOSS (Marginal Touch)** |
| **Model 3: True Ask-Penetration 1-Pip** | $\text{Low}_{\text{Bid}} \le \text{Limit} - \$0.480$ | 1,090 | **37.52%** | **0.901** | **-0.0619 R** | **-144.50 R** | **REALISTIC ECN QUEUE (Severe Loss)** |
| **Model 4: True Ask-Penetration 2-Pips**| $\text{Low}_{\text{Bid}} \le \text{Limit} - \$0.580$ | 1,077 | **35.47%** | **0.824** | **-0.1133 R** | **-191.00 R** | **ADVERSE QUEUE STRESS (Severe Loss)** |

### C. The Devastating Finding:
- When a Buy Limit is required to actually touch on the **Ask price** (Model 2), Win Rate plunges from **47.17% down to 39.66%**, and Profit Factor collapses to **0.986** (Net Loss).
- When realistic 1-pip queue penetration is required (Model 3), Win Rate drops to **37.52%**, Profit Factor collapses to **0.901**, and Maximum Drawdown explodes to **-144.50 R**.
- **The Truth**: **STRAT-08 HAS NO EDGE UNDER REALISTIC LIMIT FILL PHYSICS.** Its reported profitability was entirely a phantom artifact of filling Buy Limits at the Bid price without crossing the spread.

---

## 4. Multi-Dimensional Audit Decision Matrix

| Dimension Audited | Standard Evaluated | Finding / Proof | Verdict |
| :--- | :--- | :--- | :---: |
| **1. Arithmetic Correctness** | Exact formula equality ($\Delta = 0$) | Reconstructed with zero rounding error across all ledgers | **PASS** |
| **2. Ledger Accounting Correctness**| Internal consistency of ledger subtraction | Price-basis ledger PnL properly tracks cash balances | **PASS** |
| **3. Mid-Price Economic Cost** | Full friction decomposition vs mid-price | Reconciled to $5.5148 ($0.7353R) with zero omission | **PASS** |
| **4. Execution-Model Realism** | Quotes, spreads, and limit order fill physics | **STRAT-08 limit fills evaluated Bid instead of Ask**; edge collapses to PF 0.901 under realistic fill physics | 🔴 **FAIL** |

---

## 5. Final Audit Verdict

$$\mathbf{FAIL \; — \; MATERIAL \; COST \; ACCOUNTING \; \& \; EXECUTION-MODEL \; ERROR \; DISCOVERED}$$

### Direct Conclusion & Injunction:
1. **The apparent edge of STRAT-08 was an illusion caused by flawed limit-order fill simulation** (evaluating Bid Low instead of Ask Low for Buy Limits).
2. Under realistic ECN quote mechanics where Buy Limits fill on Ask penetration, **STRAT-08 is a losing strategy (PF 0.901, Net Expectancy -0.0619 R, MDD -144.5 R)**.
3. **NEITHER STRAT-08 NOR H1–H4 SURVIVES REALISTIC EXECUTION FRICTION.**
4. **IMMEDIATE DIRECTIVE**: All deployment plans for STRAT-08 (whether demo, prop-firm, or live) must be **IMMEDIATELY HALTED**.
5. No strategy may be approved for live capital without verifying that limit orders are triggered strictly on the executable quote side (Ask for Buys, Bid for Sells) with documented queue penetration.
