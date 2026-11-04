# Phase 0: Infrastructure Assessment

Date: 2026-11-01
Mandate: TASK.md v1.0 (XAUUSD Autonomous Quantitative Discovery)

## 1. Hardware & System
- CPU: AMD Ryzen 7 6800H (8 cores / 16 threads @ 4.7GHz max boost)
- RAM: 14 GiB total, 7.1 GiB available (14 GiB swap)
- Storage: NVMe SSD, 315 GiB free on root mount (`/`)
- OS: Linux 7.3.0-4-cachyos x86_64

## 2. Python & Compute Stack
- Dedicated venv created: `/home/vallencia/xauusd_research/.venv`
- Python version: CPython 3.12.14
- Libraries installed:
  - `polars` 2.1.0 (SIMD/multithreaded vectorized processing)
  - `numpy` 2.5.4
  - `scipy` 1.18.1
  - `statsmodels` 0.15.0
  - `pyarrow` 26.0.0
  - `duckdb` 2.0.0
  - `pandas` 3.1.0

## 3. Discovered Data Assets
- Location: `/home/vallencia/backtest/data/custom/`
  - `XAUUSD_1m.csv`: 6,880 bars (2026-10-25 to 2026-10-30 UTC)
  - `XAUUSD_5m.csv`: 5,520 bars (intraday Oct 2026)
  - `XAUUSD_15m.csv`: 5,970 bars (intraday Oct 2026)
  - `XAUUSD_1h.csv`: 10,844 bars (~2024 to 2026)
  - `XAUUSD_4h.csv`: 5,931 bars (~2022 to 2026)
  - `XAUUSD_1d.csv`: 14,883 bars (1978 to 2026)
  - `XAUUSD_1w.csv`: 3,590 bars (1970s to 2026)
  - `XAUUSD_month.csv`: 1,333 bars
- Tick downloader pipeline:
  - Discovered `/home/vallencia/Projects/myfxjournal/server/src/services/dukascopy_direct_downloader.py`. Direct Dukascopy CDN (.bi5) downloader with direct IP patch to bypass ISP DNS hijacking. Writes PyArrow Parquet tick chunks.
- MT5 infrastructure:
  - Wine MT5 installed at `/home/vallencia/.wine-mt5/drive_c/Program Files/MetaTrader 5`.

## 4. Platform Constraints & Protocol
- Memory limit: 7 GiB working RAM available. Large tick datasets must be streamed in partitions via DuckDB/Polars lazy frames rather than full in-memory loads.
- Execution boundary: Research only. No live trading, no broker execution APIs enabled.
