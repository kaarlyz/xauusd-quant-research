# LIMIT ORDER FILL SENSITIVITY & QUEUE SIMULATION SPECIFICATION

**Document ID**: LIMIT-SPEC-v1.0  
**Audit Phase**: PHASE 1C — INDEPENDENT METHODOLOGY REVIEW  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Status**: FORMALLY SPECIFIED  

---

## 1. De-Mythologizing the FIFO Assumption

In Phase 1B, the $0.10 penetration requirement was informally described as "guaranteeing FIFO queue execution".
**Auditor Correction**:
- Neither M1 OHLC nor top-of-book (Level 1) tick data contains Level 3 Market-by-Order (MBO) queue depth.
- In the absence of queue position data, **no backtester can prove exact FIFO fill order**.
- Therefore, the $0.10 penetration rule is **NOT** a verified FIFO simulation. It is a **deterministic heuristic proxy** designed to filter out marginal, unexecutable fills where price merely brushes a limit price before reversing.

---

## 2. Microstructure Dimensions: Precision vs Pips vs Penetration

To prevent confusion across pricing scales on XAUUSD:
- **Quote Precision ($0.001)**: Dukascopy data feeds broadcast gold prices to 3 decimal places (e.g. $2,650.125).
- **Instrument Minimum Tick Increment ($0.001 – $0.01)**: The minimum possible change in quoted price.
- **Pip Convention ($0.10)**: By international Forex/CFD market convention, 1 pip on Gold equals **$0.10 per ounce** ($10.00 per standard lot).
- **Penetration Depth**:
  - $0.00 = Touch (Price hits limit price exactly).
  - $0.10 = 1 full pip penetration through the limit price.
  - $0.20 = 2 full pips penetration through the limit price.

---

## 3. Mandatory 3-Scenario Limit Order Sensitivity Matrix

To prevent selection bias and ensure candidates survive real queue dynamics, any strategy utilizing Limit Orders (H1 or H3 retests) must be evaluated across three mandatory fill regimes:

| Fill Scenario Name | Penetration Threshold | Long Fill Condition | Short Fill Condition | Queue Modeling Rationale | Operational Role / Purpose |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Scenario A: Touch Fill** | **$0.00** | $\text{Low}_{\text{Ask}} \le \text{Limit}$ | $\text{High}_{\text{Bid}} \ge \text{Limit}$ | Assumes infinite liquidity / front-of-queue priority. | **Optimistic Upper Bound** (Theoretical ceiling). |
| **Scenario B: 1-Pip Penetration** | **$0.10** | $\text{Low}_{\text{Ask}} \le \text{Limit} - \$0.10$ | $\text{High}_{\text{Bid}} \ge \text{Limit} + \$0.10$ | Requires price to trade 100 ticks through the limit level, confirming substantial liquidity matching. | **Baseline Gate** (Primary research selection standard). |
| **Scenario C: 2-Pip Penetration** | **$0.20** | $\text{Low}_{\text{Ask}} \le \text{Limit} - \$0.20$ | $\text{High}_{\text{Bid}} \ge \text{Limit} + \$0.20$ | Requires market to violently blow through the limit level, modeling adverse queue positioning during fast market conditions. | **Stress-Test Floor** (Verifies candidate does not collapse under extreme fill slippage). |

### Mandatory Discovery Acceptance Rule:
A limit-order candidate strategy cannot be accepted into the validated registry unless:
1. It passes all performance gates under **Scenario B (1-Pip Penetration)**.
2. It remains net profitable (Expectancy $> 0.00\text{ R}$) under **Scenario C (2-Pip Penetration)**.
