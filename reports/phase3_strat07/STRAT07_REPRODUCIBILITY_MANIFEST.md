# PHASE 3: STRAT-07 REPRODUCIBILITY MANIFEST & CODE PROVENANCE

**Document ID**: P3-MANIFEST-v1.0  
**Phase**: PHASE 3 — STRAT-07 FINAL REVALIDATION  
**Auditor**: Hermes Autonomous Quantitative Trading Research Unit  
**Status**: 100% REPRODUCIBLE ARTIFACTS CERTIFIED  

---

## 1. Computational Environment & Software Toolchain

- **Operating System**: Linux 7.3.0-4-cachyos (x86_64)
- **CPU Architecture**: AMD Ryzen 7 6800H (16 vCPU)
- **Python Virtualenv**: `/home/vallencia/xauusd_research/.venv` (Python 3.12.14)
- **Primary Libraries**:
  - `polars`: 2.1.0
  - `numpy`: 2.5.4
  - `scipy`: 1.18.1
  - `pyarrow`: 26.0.0
- **Random Seed**: `42`

---

## 2. Master Data Invariants & Checksums

| Asset Description | Filesystem Location | SHA-256 Checksum | Dimensions / Scope |
| :--- | :--- | :--- | :--- |
| **Master M1 Parquet** | `/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet` | `771ae44ae2774e1b067dd9955d00c38e5058185370449c756746f6f65107dfd6` | 4,182,209 M1 bars (105.85 MB) |
| **Weekly Tick Partitions** | `/home/vallencia/Projects/myfxjournal/server/data/market-data/partitions_tick/` | 359 weekly partitions verified | 405,106,965 ticks (4.83 GB) |
| **In-Sample Period** | Evaluated via script | 2021-08-23 00:00 to 2024-08-21 23:59 UTC | 3 Years (Strictly isolated) |
| **Validation Period** | Evaluated via script | 2024-08-22 00:00 to 2025-08-21 23:59 UTC | 1 Year (Strictly isolated) |
| **Final Blind Holdout** | `timestamp > 1755820799000` | 2025-08-22 to 2026-08-21 UTC | **SEALED & UNTOUCHED** |

---

## 3. Generated Artifacts & Manifest

| Output Artifact | Filesystem Path | Records Contained |
| :--- | :--- | :---: |
| **Full Trade Ledger** | `/home/vallencia/xauusd_research/STRAT07_TRADE_LEDGER.csv` | 84 Trades (2015–2025) with exact timestamps, prices, and realized R |
| **In-Sample Results** | `/home/vallencia/xauusd_research/STRAT07_IS_RESULTS.csv` | Overall, Long, and Short performance on In-Sample (N=18) |
| **Validation Results** | `/home/vallencia/xauusd_research/STRAT07_VALIDATION_RESULTS.csv` | Overall, Long, and Short performance on Validation (N=25) |
| **JSON Summary Cache** | `/home/vallencia/xauusd_research/data/strat07_revalidation_summary.json` | Complete machine-readable metrics, annual stats, cost sensitivity |
| **Master Audit Report** | `/home/vallencia/xauusd_research/PHASE_3_STRAT07_REVALIDATION.md` | Formal rejection decree and root-cause analysis |

---

## 4. Exact Reproduction Command

To reproduce all tables, trade ledgers, annual breakdowns, and the final rejection outcome:

```bash
# 1. Activate virtual environment
source /home/vallencia/xauusd_research/.venv/bin/activate

# 2. Execute revalidation engine
python /home/vallencia/xauusd_research/src/phase3_revalidate_strat07.py

# 3. Verify trade ledger integrity
cat /home/vallencia/xauusd_research/STRAT07_VALIDATION_RESULTS.csv
```

Execution runtime: **~1.8 seconds** on the AMD Ryzen 7 6800H platform.
