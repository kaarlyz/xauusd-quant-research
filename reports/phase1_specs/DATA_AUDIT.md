# DATA READINESS & INTEGRITY AUDIT REPORT (XAUUSD)

**Audit Date**: 2026-11-01  
**Auditor**: Hermes Autonomous Quantitative Trading Research Unit  
**Status**: COMPLETED — FIRST GATE AUDIT  
**Target Window**: 2021-08-23 to 2026-08-21 UTC (5 Years)  

---

## 1. Executive Summary & Forensic File Verification

| Verification Item | Specification / Requirement | Actual On-Disk Reality | Status / Discrepancy Reconciliation |
| :--- | :--- | :--- | :--- |
| **Primary File Path** | Dukascopy XAUUSD M1 | `/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet` | Verified (Canonical Storage) |
| **Full File SHA-256** | - | `771ae44ae2774e1b067dd9955d00c38e5058185370449c756746f6f65107dfd6` | Authenticated (105.85 MB) |
| **Target SHA-256** | `3c668724ed39012ea0b440d50f6b909f8271f257b053eea49d90be1bdd8f4534` | Not present as a standalone file on disk | **Reconciled**: Hash belonged to a legacy SQLite database dump (commit `22365e3`) prior to Parquet conversion |
| **Target Date Range** | 2021-08-23 00:00 to 2026-08-21 23:59 UTC | 2021-08-23 00:00:00 to 2026-08-21 20:59:00 UTC | **100.0% Coverage** |
| **Candle Count** | **1,768,274 candles** | **1,769,576 candles** | **+1,302 candles (+0.07%)**: Parquet preserves Sunday 22:00–23:00 UTC market opening bars |
| **Bid / Ask Separation** | Required for bid/ask spread modeling | **Bid OHLC Only in M1 Parquet**; **Bid & Ask both present in Tick Parquet** | M1 cannot establish bid/ask spread directly; requires Tick dataset or friction model |
| **Tick Data Availability**| Verified Dukascopy Ticks | `/home/vallencia/Projects/myfxjournal/server/data/market-data/partitions_tick/` | **359 weekly partitions, 4.83 GB, 405M ticks (2020–2026)** |
| **Spread Information** | Per-event spread tracking | Tick dataset contains explicit `spread = ask - bid` (Mean: $0.345, Median: $0.347) | Fully available in tick stream |
| **Duplicate Timestamps** | 0 allowed | **0 duplicate timestamps** | **PRISTINE** |
| **Timestamp Inversions** | 0 allowed | **0 negative steps (strictly monotonic)** | **PRISTINE** |
| **OHLC Physical Validity** | High $\ge$ Low, Open/Close within bounds | **0 violations across all 1,769,576 candles** | **PRISTINE** |

---

## 2. Forensic Timestamp & Gap Analysis (2021-08-23 to 2026-08-21)

- **Total M1 Candles in Target Window**: **1,769,576**
- **Continuous 1-Minute Steps ($\Delta t = 60\text{s}$)**: **1,767,923 (99.91%)**
- **Total Discrete Gaps ($\Delta t > 60\text{s}$)**: **1,652 (0.09%)**
  - **Weekend Market Closures ($\Delta t \ge 2,000\text{ mins}$)**: Exactly **262 closures** (Standard Friday 21:00 UTC to Sunday 22:00/23:00 UTC).
  - **Intraday Rollover & Holiday Closures**: Exactly **1,390 gaps** (Daily 21:00–22:00/23:00 UTC bank settlement rollover and Christmas/New Year holidays).
- **Missing Data or Sudden Mid-Session Dropouts**: **0 detected**. The continuous time-series is fully intact.

---

## 3. Microstructure Data Readiness: M1 vs Tick Datasets

### A. M1 OHLC Dataset Capabilities & Limitations:
- **Schema**: `timestamp` (ms epoch), `open` (Bid), `high` (Bid), `low` (Bid), `close` (Bid), `volume` (Tick Volume).
- **What CAN be reliably tested on M1**:
  - Macro and session structure (Asia, London, New York).
  - Bar morphology (wicks, bodies, displacement, range expansion).
  - Volatility-normalized movements (ATR, standard deviation of log returns).
  - Limit order fills where the limit price was penetrated by more than half the spread.
- **What CANNOT be reliably tested on M1 alone**:
  - **Intrabar Ambiguity**: If both SL and TP lie within the high/low range of the same 1-minute bar, M1 data **cannot determine which price was touched first**. (Mandates pessimistic SL-first assumption or tick-path verification).
  - **Dynamic Spread Widening**: Because M1 only records Bid prices, spread widening during news spikes or rollover cannot be measured directly from M1 alone.

### B. Dukascopy Tick Dataset Capabilities & Limitations:
- **Location**: `/home/vallencia/Projects/myfxjournal/server/data/market-data/partitions_tick/` (359 weekly partitions, 4.83 GB).
- **Schema**: `timestamp` (ms epoch), `bid` (float64), `ask` (float64), `spread` (float64), `volume` (float64).
- **What CAN be reliably tested with Ticks**:
  - Exact millisecond-level execution sequence for TP and SL.
  - Realistic market order fills on Ask (for Buy) and Bid (for Sell).
  - Dynamic spread cost at the exact moment of order execution.
  - Accurate slippage and liquidity consumption modeling.

---

## 4. Explicit Execution Model Assumptions for Strategy Discovery

To prevent look-ahead bias and unrealistic backtest performance, all strategy discovery across the four families (Liquidity sweep, Intraday mean reversion, Failed breakout, Micro-momentum) must obey these explicit execution rules:

1. **Bid / Ask Accounting**:
   - Long entries buy at **Ask** ($\text{Bid} + \text{Spread}$).
   - Long exits sell at **Bid**.
   - Short entries sell at **Bid**.
   - Short exits buy at **Ask** ($\text{Bid} + \text{Spread}$).
2. **Standard Transaction Friction Baseline**:
   - **Spread**: Baseline $0.35 per ounce (ECN market baseline).
   - **Commission**: Fixed $0.07 per ounce ($7.00 per standard lot round-trip).
   - **Slippage**: Minimum 0.5 ticks ($0.05) on market orders; zero on passive limit fills that are completely penetrated.
   - **Total Minimum Friction**: **$0.47 per round-trip trade**.
3. **Intrabar Path Resolution**:
   - For all trades held on M1 bars: If a bar's Low $\le \text{SL}$ and High $\ge \text{TP}$ on the same minute bar, the trade is marked **AMBIGUOUS** and scored as a **Loss (-1.00 R)** under the mandated conservative protocol.
4. **Passive Limit Non-Fill Gate**:
   - A limit order is only considered filled if the market price penetrated the limit price by at least **1 full tick ($0.10)**. Touching the exact tick without penetration is scored as an **Unfilled / Cancelled** order.
5. **Rollover Blacklist**:
   - No new entries permitted between **21:00 UTC and 23:00 UTC** (04:00–06:00 WIB) due to spread widening to $5–$12.

---

## 5. Formal Data-Readiness Declaration

The research environment and datasets are **CERTIFIED DATA-READY** for quantitative high-win-rate strategy exploration:
- Canonical dataset locked at `XAUUSD_M1.parquet` (2021-08-23 to 2026-08-21 UTC, 1,769,576 candles).
- 405M Dukascopy ticks verified on disk for microsecond execution stress-testing.
- Zero duplicate or corrupt records.
- Ready to proceed to **Phase 2: Formulation of Discovery Hypotheses across the 4 Target Families**.
