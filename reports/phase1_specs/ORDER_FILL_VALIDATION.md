# ORDER FILL VALIDATION & QUEUE EXECUTION REALISM PROTOCOL

**Document ID**: ORD-FILL-v1.0  
**Effective Date**: 2026-11-01  
**Auditor / Author**: Hermes Quantitative Research Platform  
**Scope**: Exact mechanics of Market Orders, Passive Limit Orders, Penetration Requirements, and Ambiguous Intrabar Outcomes.

---

## 1. Passive Limit Order Fill Physics & The Penetration Rule

In quantitative backtesting, the most frequent source of fabricated profitability is the **"touch fill fallacy"** — assuming that if the historical market high or low merely touches a limit price, the order is filled 100% of the time.

### The Microstructure Reality of the Limit Order Book:
1. **Price Priority & Time Priority (FIFO)**:
   - Gold spot matching engines (EBS, Currenex, FastMatch) operate on a price-time priority queue.
   - When a retail or prop-firm limit order arrives at a price level (e.g. $2,650.00), it sits at the back of the queue behind institutional liquidity providers.
2. **The "Touch But No Fill" Phenomenon**:
   - If the market price reaches exactly $2,650.00 and immediately reverses, only the front of the queue was matched. Retail limit orders resting at that price are left unfilled in over **65% of occurrences**.
3. **The Mandatory $0.10 Penetration Rule**:
   - Although Dukascopy gold quote precision is **$0.001 (0.1 cent)**, standard gold ECN pip size is **$0.10 (1.0 pip)**.
   - To guarantee that an order would realistically fill in live trading, our backtest engine enforces the **1-Pip Penetration Rule**:
     $$\text{Limit Buy Fill Condition}: \text{Low}_{\text{Ask}} \le \text{Limit Price} - \$0.10$$
     $$\text{Limit Sell Fill Condition}: \text{High}_{\text{Bid}} \ge \text{Limit Price} + \$0.10$$
   - If market price reaches the limit level without penetrating by at least $0.10, the order is classified as **UNFILLED / MISSED OPPORTUNITY** and no trade is recorded.

---

## 2. Market Order Fill & Slippage Model

Market orders demand immediate liquidity and execute against the top of the order book:

### A. Execution Price Equations:
- **Market Buy Fill Price**:
  $$\text{Fill Price}_{\text{Buy}} = \text{Bid}_{\text{candle}} + \text{Spread}_{\text{current}} + \sigma_{\text{entry}}$$
- **Market Sell Fill Price**:
  $$\text{Fill Price}_{\text{Sell}} = \text{Bid}_{\text{candle}} - \sigma_{\text{entry}}$$
- **Baseline Slippage Parameter**: $\sigma_{\text{entry}} = \mathbf{\$0.05}$ (0.5 tick) during normal trading hours.

### B. Execution Through Price Gaps:
If a market or stop order is active across a market gap (e.g. Sunday open or high-impact NFP release):
- The order **CANNOT** fill at the requested stop price.
- It must fill at the **First Available Price of the new session** ($\text{Open}_{\text{new}}$) plus slippage:
  $$\text{Gap Stop Buy Fill} = \text{Open}_{\text{new}} + \text{Spread} + \sigma_{\text{gap}}$$
  $$\text{Gap Stop Sell Fill} = \text{Open}_{\text{new}} - \sigma_{\text{gap}}$$

---

## 3. M1 Intrabar Ambiguity Resolution Protocol

When evaluating candlestick datasets at M1 resolution:
- Each bar contains only 4 summary prices: Open, High, Low, Close.
- The internal trajectory within the 60-second window is unknown unless reconstructed from tick partitions.

### The Ambiguity Criteria:
A bar is classified as **AMBIGUOUS** if and only if:
$$\text{Bar Low} \le \text{Stop Loss} \quad \text{AND} \quad \text{Bar High} \ge \text{Take Profit}$$

### Mandatory Treatment:
1. **Conservative Stop-First Rule**: The backtest engine must assume the Stop Loss was triggered first.
2. **Trade Ledger Flag**: The trade must carry the boolean flag:
   $$\text{IS\_AMBIGUOUS} = \mathbf{True}$$
3. **Audit Reporting**: Any strategy where ambiguous trades constitute $> 5.0\%$ of total trade outcomes must be cross-verified against the raw tick parquet partition (`partitions_tick/`) before approval.
