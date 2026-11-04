# RESEARCH REGISTRY RESET & STRATEGY GOVERNANCE DECREE

**Document ID**: REG-RESET-v1.0  
**Phase**: PHASE 2D — RESEARCH STATUS RESET  
**Auditor / Governance Authority**: Hermes Quantitative Research Governance Board  
**Effective Date**: 2026-11-01  
**Status**: BINDING & PERMANENT  

---

## 1. Master Strategy Registry Status Reset

In accordance with Section 5 of the locked quantitative research mandate (`SOUL.md`: *"Maintain a permanent distinction between exploratory findings, validated findings, and rejected hypotheses"*), all strategy candidates are re-classified:

| Strategy ID | Timeframe | Strategy Architecture | Prior Status | Newly Verified Official Status | Technical Root Cause for Status Reset |
| :---: | :---: | :--- | :---: | :---: | :--- |
| **STRAT-08** | M15 | London Fibo 78.6% Retest | `OUT-OF-SAMPLE VALIDATED` | 🔴 **INVALIDATED HISTORICAL BACKTEST — EXECUTION-MODEL DEFECT** | Backtest evaluated Buy Limit fills on Bid Low instead of Ask Low. Under realistic Ask-penetration, Win Rate collapses to 34.7% and Profit Factor to 0.796 (MDD = -134.5 R). |
| **H1** | M1 | Liquidity Sweep & Reclaim (8 Variants) | `EXPLORATORY` | 🔴 **REJECTED UNDER TESTED CONFIGURATIONS** | High frequency negative-RR scalping produces 36%–41% WR and -0.39 R net expectancy after ECN friction. |
| **H2** | M1 | Intraday Mean Reversion (8 Variants) | `EXPLORATORY` | 🔴 **REJECTED UNDER TESTED CONFIGURATIONS** | Z-score/RSI extremes without time-window filters fail to revert in trending regimes (PF = 0.33–0.41). |
| **H3** | M1 | Failed Breakout / Trap (8 Variants) | `EXPLORATORY` | 🔴 **REJECTED UNDER TESTED CONFIGURATIONS** | Fails under 1-pip penetration rule; corrected retest signals yield 41% WR and -0.38 R expectancy. |
| **H4** | M1 | Micro-Momentum Push (8 Variants) | `EXPLORATORY` | 🔴 **REJECTED UNDER TESTED CONFIGURATIONS** | Post-impulse pullback entry catches exhaustion tops; tight stops amplify friction drag to >70% of risk budget. |
| **STRAT-01** | M1 | London 17:30 WIB Reversal | `INCONCLUSIVE` | 🔴 **REJECTED (REGIME FAILURE)** | Total collapse during 2023–2024 validation split (PF = 0.41). |
| **STRAT-07** | M1 | Tokyo 08:15 WIB Reversal | `PROMISING` | 🟡 **PENDING REVALIDATION** | Market-order entry avoids limit-fill queue defect, but requires independent tick-by-tick revalidation before any deployment. |

---

## 2. Inviolable Governance Constraints

1. **Zero Active Live/Prop Authorizations**:
   - There are currently **ZERO approved strategies** authorized for funded prop-firm evaluations, challenge accounts, or live capital.
   - All previous GO decisions regarding STRAT-08 are **FORMALLY REVOKED**.
2. **The Blind Holdout Invariant**:
   - The 1-year final holdout (`2025-08-22 to 2026-08-21 UTC`, ~340,000 candles) remains **100% SEALED, UNACCESSED, AND UNTAINTED**.
   - No strategy selection or parameter tuning has accessed or will access this partition.
3. **Requirement for Future Discovery**:
   - Any future discovery candidate must use **executable quote sides from day one**:
     - Buy Limits must trigger on $\text{Ask} \le \text{Limit} - \$0.10$.
     - Sell Limits must trigger on $\text{Bid} \ge \text{Limit} + \$0.10$.
     - Market Buys must fill at $\text{Ask} + \sigma$.
     - Market Sells must fill at $\text{Bid} - \sigma$.
   - Any backtest failing to separate Bid and Ask quotes is automatically classified as invalid.

---

## 3. Code Provenance & Cryptographic Traceability

- **Engine Revision ID**: `REV-2D-001`
- **Execution Script**: `/home/vallencia/xauusd_research/src/phase2d_reproduce_strat08.py`
- **Dataset Evaluated**: `/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet`
  - SHA-256 Checksum: `771ae44ae2774e1b067dd9955d00c38e5058185370449c756746f6f65107dfd6`
- **Reproducible Sensitivity Ledger**: `/home/vallencia/xauusd_research/STRAT08_EXECUTION_SENSITIVITY_REPRODUCTION.csv`
- **Reproducible Drawdown Ledger**: `/home/vallencia/xauusd_research/STRAT08_DRAWDOWN_RECONCILIATION.csv`
