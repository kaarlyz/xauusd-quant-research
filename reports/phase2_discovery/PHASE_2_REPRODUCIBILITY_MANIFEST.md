# PHASE 2: REPRODUCIBILITY MANIFEST & EXECUTION PROVENANCE

**Document ID**: P2-REPRO-v1.0  
**Phase**: STAGE D — REPRODUCIBILITY PROTOCOL  
**Auditor / Engineer**: Hermes Autonomous Quantitative Trading Research Unit  
**Status**: 100% REPRODUCIBLE ARTIFACTS CERTIFIED  

---

## 1. System & Computational Toolchain

- **Host Platform**: Linux 7.3.0-4-cachyos (x86_64)
- **CPU**: AMD Ryzen 7 6800H (16 vCPU)
- **Python Environment**: `/home/vallencia/xauusd_research/.venv` (Python 3.12.14)
- **Core Library Toolchain**:
  - `polars`: 2.1.0 (Vectorized SIMD feature precomputation)
  - `numpy`: 2.5.4
  - `scipy`: 1.18.1
  - `pyarrow`: 26.0.0
- **Random Seed**: `42` (Fixed for all sampling and bootstrap routines)

---

## 2. Immutable Data Artifacts & Cryptographic Hashes

| Data Asset | Path on Disk | SHA-256 Checksum | Dimensions / Scope |
| :--- | :--- | :--- | :--- |
| **Master M1 Parquet** | `/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet` | `771ae44ae2774e1b067dd9955d00c38e5058185370449c756746f6f65107dfd6` | 4,182,209 M1 bars (105.85 MB) |
| **Canonical Tick Archives** | `/home/vallencia/Projects/myfxjournal/server/data/market-data/partitions_tick/` | 359 weekly partitions verified (0 corrupt) | 405,106,965 ticks (4.83 GB) |
| **Experiment Log CSV** | `/home/vallencia/xauusd_research/PHASE_2_EXPERIMENT_LOG.csv` | Dynamically logged | All 32 experiments with IS and Validation metrics |
| **JSON Results Store** | `/home/vallencia/xauusd_research/data/phase2_discovery_results.json` | Dynamically logged | Full machine-readable metrics |

---

## 3. Exact Reproduction Instructions

To reproduce all 32 experiments, metrics, p-values, and tables from scratch:

```bash
# 1. Activate verified virtual environment
source /home/vallencia/xauusd_research/.venv/bin/activate

# 2. Run the synthetic implementation verification test
python /home/vallencia/xauusd_research/src/test_engine_implementation.py

# 3. Run the complete 32-experiment discovery engine
python /home/vallencia/xauusd_research/src/fast_phase2_discovery.py

# 4. Inspect generated CSV experiment log
cat /home/vallencia/xauusd_research/PHASE_2_EXPERIMENT_LOG.csv | column -t -s, | head -n 35
```

Execution runtime: **~22.5 seconds** on the AMD Ryzen 7 6800H platform.
