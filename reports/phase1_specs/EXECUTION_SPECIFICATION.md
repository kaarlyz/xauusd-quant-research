# PHASE 1B: FROZEN EXECUTION SPECIFICATION & COST ACCOUNTING CONTRACT

**Document ID**: EXEC-SPEC-v1.0  
**Effective Date**: 2026-11-01  
**Auditor / Author**: Hermes Quantitative Research Platform  
**Target Asset**: XAUUSD (Gold Spot / US Dollar)  
**Status**: LOCKED FOR STRATEGY DISCOVERY  

---

## 1. Contract Specifications & Fundamental Units

- **Instrument**: XAUUSD Spot Gold.
- **Contract Size**: 1 Standard Lot = **100 Troy Ounces**.
- **Quote Currency**: USD per Troy Ounce.
- **Minimum Price Increment (Tick Size)**: **$0.001** (Dukascopy quote precision: 3 decimals, e.g. 2650.125).
- **Minimum Exchange Fluctuation (Point Size)**: $0.01 (0.1 pips) / $0.10 (1.0 pips).
- **Pip Definition**: 1 pip = **$0.10** per ounce ($10.00 per standard lot).

---

## 2. Definitive Microstructure Cost Accounting Architecture

To eliminate ambiguity across all future discovery experiments, the cost accounting model is formally decomposed into three distinct mathematical components:

### A. Bid-Ask Spread ($S$)
- **Definition**: The instantaneous difference between the lowest price a seller will accept (Ask) and the highest price a buyer will pay (Bid):
  $$S = \text{Ask} - \text{Bid}$$
- **Baseline Quoted Spread**: **$0.35 per ounce** (set as the median institutional ECN spread observed during active London and New York hours).
- **Accounting Semantics**: The spread is **NOT** charged twice. The cost of entering at Ask and exiting at Bid inherently pays the full spread **once per completed round-turn cycle** ($S = \$0.35/\text{oz}$).

### B. Broker Commission ($C$)
- **Standard Institutional ECN Rate**: **$7.00 per standard lot round-turn** ($3.50 per lot per side).
- **Per-Ounce Conversion**:
  $$C_{\text{oz}} = \frac{\$7.00}{100\text{ oz}} = \mathbf{\$0.07\text{ per ounce (Round-Turn)}}$$
  ($\$0.035/\text{oz}$ at entry, $\$0.035/\text{oz}$ at exit).

### C. Execution Slippage ($\sigma$)
- **Definition**: Adverse execution drift between order transmission and matching engine execution.
- **Market Orders**: Modeled as **0.5 tick = $0.05 per ounce per market execution**.
- **Passive Limit Orders**: Modeled as **$0.00 slippage** upon fill, provided the penetration requirement is met.
- **Stop Orders (SL)**: Modeled as **0.5 tick = $0.05 adverse slippage** upon triggering.

### D. Total Round-Trip Friction Baseline Summary:
- **For Market-Entry / Stop-or-Target-Exit Trades**:
  $$\text{Total Friction} = S_{\text{round}} + C_{\text{round}} + \sigma_{\text{entry}} + \sigma_{\text{exit}}$$
  $$\text{Total Friction} = \$0.35 + \$0.07 + \$0.05 + \$0.00 = \mathbf{\$0.47\text{ per ounce (Limit TP)}}$$
  $$\text{Total Friction (Stop Loss Hit)} = \$0.35 + \$0.07 + \$0.05 + \$0.05 = \mathbf{\$0.52\text{ per ounce}}$$

---

## 3. Order Execution Mechanics & Side Conventions

### A. Long Positions (BUY)
1. **Market Entry**:
   - Order executes at the prevailing **Ask price**:
     $$\text{Fill Price}_{\text{Long}} = \text{Bid}_{\text{M1}} + S + \sigma_{\text{entry}}$$
2. **Limit Entry**:
   - Limit Buy order rests at or below the market.
   - **Fill Condition**: The prevailing **Ask price** must penetrate the Limit Buy price by at least **$0.10 (1 pip)**:
     $$\text{Low}_{\text{Ask}} \le \text{Limit Price} - \$0.10 \iff \text{Low}_{\text{Bid}} + S \le \text{Limit Price} - \$0.10$$
3. **Stop Loss (SL)**:
   - Evaluated against the **Bid price**.
   - If $\text{Low}_{\text{Bid}} \le \text{SL Price}$, order triggers and fills at:
     $$\text{Fill}_{\text{SL}} = \min(\text{SL Price}, \text{Open}_{\text{Bid}}) - \sigma_{\text{exit}}$$
4. **Take Profit (TP)**:
   - Evaluated against the **Bid price**.
   - If $\text{High}_{\text{Bid}} \ge \text{TP Price}$, limit order fills at **$\text{TP Price}$** exactly.

### B. Short Positions (SELL)
1. **Market Entry**:
   - Order executes at the prevailing **Bid price**:
     $$\text{Fill Price}_{\text{Short}} = \text{Bid}_{\text{M1}} - \sigma_{\text{entry}}$$
2. **Limit Entry**:
   - Limit Sell order rests at or above the market.
   - **Fill Condition**: The prevailing **Bid price** must penetrate the Limit Sell price by at least **$0.10 (1 pip)**:
     $$\text{High}_{\text{Bid}} \ge \text{Limit Price} + \$0.10$$
3. **Stop Loss (SL)**:
   - Evaluated against the **Ask price** ($\text{Bid} + S$).
   - If $\text{High}_{\text{Ask}} \ge \text{SL Price} \iff \text{High}_{\text{Bid}} + S \ge \text{SL Price}$, order triggers and fills at:
     $$\text{Fill}_{\text{SL}} = \max(\text{SL Price}, \text{Open}_{\text{Bid}} + S) + \sigma_{\text{exit}}$$
4. **Take Profit (TP)**:
   - Evaluated against the **Ask price** ($\text{Bid} + S$).
   - If $\text{Low}_{\text{Ask}} \le \text{TP Price} \iff \text{Low}_{\text{Bid}} + S \le \text{TP Price}$, limit order fills at **$\text{TP Price}$** exactly.

---

## 4. Position Sizing & Conversion into R Multiples

To maintain mathematical rigor across variable stop loss distances ($D_{\text{SL}}$):
1. **Dollar Risk Budget**: Defined as a fixed amount $K_{\text{risk}}$ (e.g. $\$7.50$ on a $\$2,500$ account).
2. **Stop Distance ($D_{\text{SL}}$)**:
   $$D_{\text{SL}} = |\text{Entry Fill} - \text{Nominal SL}|$$
3. **Position Size in Standard Lots ($V$)**:
   $$V = \frac{K_{\text{risk}}}{D_{\text{SL}} \times 100}$$
4. **Realized R Multiple Calculation**:
   $$\text{Gross PnL (\$) } = (\text{Exit Price} - \text{Entry Price}) \times \text{Direction} \times V \times 100$$
   $$\text{Commission (\$) } = C_{\text{round}} \times V \times 100$$
   $$\text{Net PnL (\$) } = \text{Gross PnL} - \text{Commission}$$
   $$\text{Realized R Multiple } = \frac{\text{Net PnL (\$) }}{K_{\text{risk}}}$$

---

## 5. M1 Intrabar Path Ambiguity Resolution Protocol

When backtesting on M1 bars where internal tick sequence is not loaded:
1. **Ambiguity Condition**: If in a single 1-minute bar, $\text{Low} \le \text{SL}$ AND $\text{High} \ge \text{TP}$:
   - **Mandatory Ruling**: The observation is formally tagged as `IS_AMBIGUOUS = True`.
   - **Pessimistic Stop-First Enforcement**: The trade is scored as an immediate **Loss ($-1.00\text{ R}$)**.
   - Under no circumstances will a backtest award a win to an ambiguous intra-bar bar without tick-level millisecond validation.
