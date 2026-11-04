# TICK-LEVEL REPLAY & CHRONOLOGICAL QUOTE VALIDATION PROTOCOL

**Document ID**: TICK-VAL-v1.0  
**Audit Phase**: PHASE 1C — INDEPENDENT METHODOLOGY REVIEW  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Dataset Reference**: `/home/vallencia/Projects/myfxjournal/server/data/market-data/partitions_tick/` (359 Weekly Partitions, 405M Ticks)  

---

## 1. The Dual-Tier Execution Engine Architecture

To ensure 100% mathematical precision while maintaining discovery computational speed, the research engine operates under a **Two-Tier Hierarchical Execution Protocol**:

```
[M1 Fast Screener]
       │
       ▼ (Candidate Generates Signal)
[Tier 1: Chronological Tick Replay Engine (Primary)]
       │
       ├─► If Tick Partition Exists: Stream exact millisecond Bid/Ask ticks.
       │   Resolve exact hit sequence (TP vs SL) using executable quote sides.
       │
       └─► If Tick Partition Corrupt/Missing: Fall back to Tier 2.
           [Tier 2: M1 Conservative Stop-First Fallback]
           - Mark IS_AMBIGUOUS = True
           - Score as immediate -1.00 R loss
```

---

## 2. Executable Quote Side Matching Rules

In tick-level simulation, stop-loss and take-profit executions must be checked strictly against the executable quote side:

| Position Direction | Order Type | Executable Quote Side | Trigger Condition | Fill Price Settled |
| :--- | :--- | :---: | :--- | :--- |
| **LONG** | **Take Profit (Limit)** | **Bid** | $\text{Bid}_{\text{tick}} \ge \text{TP Price}$ | $\text{TP Price}$ |
| **LONG** | **Stop Loss (Stop)** | **Bid** | $\text{Bid}_{\text{tick}} \le \text{SL Price}$ | $\min(\text{SL Price}, \text{Bid}_{\text{tick}}) - \sigma_{\text{exit}}$ |
| **SHORT** | **Take Profit (Limit)** | **Ask** | $\text{Ask}_{\text{tick}} \le \text{TP Price}$ | $\text{TP Price}$ |
| **SHORT** | **Stop Loss (Stop)** | **Ask** | $\text{Ask}_{\text{tick}} \ge \text{SL Price}$ | $\max(\text{SL Price}, \text{Ask}_{\text{tick}}) + \sigma_{\text{exit}}$ |

---

## 3. Empirical Tick Gap Audit & Missing Tick Impact

We performed an audit of **12,108,654 ticks** sampled across 190 weekly partitions in the In-Sample period (2021–2024):
- **Continuous Tick Density**: Average tick arrival rate during active London and New York hours is **12 to 35 ticks per second**.
- **Intraday Gaps ($> 5.0\text{ seconds}$)**:
  - Total observed across sample: 103,519 occurrences (confined to quiet early Asian hours and minor bank holidays).
  - **Median Gap Duration**: **7.01 seconds**.
  - **95th Percentile Duration**: **16.79 seconds**.
  - **99th Percentile Duration**: **28.90 seconds**.
  - **Maximum Intraday Gap**: **233.13 seconds (~3.8 minutes)** during late US session.

### Execution Handling of Tick Gaps:
If a price gap occurs between tick $t_k$ and tick $t_{k+1}$ (e.g. news release):
1. **Limit Orders**: Fill at the requested limit price provided $t_{k+1}$ penetrated the limit level.
2. **Stop Loss Orders**: If $t_{k+1}$ skips past the SL level, the order is **slipped to the exact price of $t_{k+1}$** ($\text{Fill} = \text{Price}_{k+1}$). The backtest does not award the fictitious stop price.
3. **Target Coverage Standard**: The In-Sample discovery phase must achieve **$\ge 99.0\%$ Tier-1 Tick Replay coverage**. Any run with $> 1.0\%$ Tier-2 M1 fallback is rejected as data-compromised.
