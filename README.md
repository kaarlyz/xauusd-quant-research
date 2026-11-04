# XAUUSD QUANTITATIVE RESEARCH PLATFORM — MASTER REPOSITORY & INDEX

**Repository Root**: `/home/vallencia/xauusd_research/`  
**Last Updated**: 2026-11-01  
**Lead System**: Hermes Autonomous Quantitative Trading Researcher  

---

## 1. Directory Structure & Organization

Seluruh laporan riset, spesifikasi eksekusi, log eksperimen, dan ledger transaksi telah dipindahkan dan dikelompokkan ke dalam folder khusus yang terstruktur rapi:

```
/home/vallencia/xauusd_research/
├── TASK.md                                    # Mandat riset terkunci v1.0
├── README.md                                  # Master index & panduan navigasi repository ini
├── reports/                                   # Seluruh dokumen laporan ilmiah (.md)
│   ├── phase1_specs/                          # Dokumen spesifikasi eksekusi, DST, & pra-registrasi
│   ├── phase2_discovery/                      # Laporan discovery 32 varian H1-H4 & evaluasi statistik
│   ├── phase2_forensic/                       # Audit forensik biaya, rekonsiliasi limit fill, & reset registri
│   ├── phase3_strat07/                        # Laporan revalidasi independen final STRAT-07
│   └── legacy_audits/                         # Arsip audit awal STRAT-08, STRAT-01, final gate, & prelive
├── ledgers/                                   # Seluruh dataset hasil kalkulasi & ledger (.csv)
│   ├── STRAT07_TRADE_LEDGER.csv               # Ledger transaksi trade-by-trade STRAT-07 (84 trades)
│   ├── STRAT07_IS_RESULTS.csv                 # Metrik In-Sample STRAT-07
│   ├── STRAT07_VALIDATION_RESULTS.csv         # Metrik Validation STRAT-07
│   ├── STRAT08_EXECUTION_SENSITIVITY_REPRODUCTION.csv  # Uji 4 model eksekusi STRAT-08
│   ├── STRAT08_DRAWDOWN_RECONCILIATION.csv    # Rekonsiliasi ledakan drawdown STRAT-08
│   ├── PHASE_2_EXPERIMENT_LOG.csv             # Log lengkap 32 eksperimen Phase 2
│   ├── H3_SIGNAL_TO_FILL_FUNNEL.csv           # Corong sinyal H3 (breakout -> re-entry -> fill)
│   ├── HOLM_PVALUE_RECALCULATION.csv          # Audit p-value Holm-Bonferroni & block bootstrap
│   ├── COST_TO_R_RECONCILIATION.csv           # Perbandingan biaya riil vs R per famili strategi
│   ├── COST_TO_R_FORMULA_VERIFICATION.csv     # Pemetaan formula ledger vs economic drag
│   ├── ECONOMIC_DRAG_BENCHMARK_RECONSTRUCTION.csv # Rekonstruksi benchmark harga tengah (Mid-Price)
│   ├── LIMIT_FILL_EXECUTION_VALIDATION.csv    # Uji penetrasi limit order M15
│   ├── REPRESENTATIVE_TRADE_RECONSTRUCTION.csv# Input trade riil STRAT-08 vs H4
│   └── DATA_COVERAGE_RECONCILIATION.csv       # Audit rekonsiliasi 359 partisi tick vs M1
├── data/                                      # File JSON data cache & metadata analitik
└── src/                                       # Seluruh kode engine komputasi Python
```

---

## 2. Status Registri Strategi Resmi (Current State)

| ID Strategi | Timeframe | Arsitektur Logika | Status Resmi Terkunci | Rangkuman Ilmiah Penolakan |
| :---: | :---: | :--- | :---: | :--- |
| **STRAT-08** | M15 | London Fibo 78.6% Retest | 🔴 **INVALIDATED (DEFECT)** | Backtest lama mengevaluasi Buy Limit pada Bid Low (beli di Bid tanpa bayar spread). Di bawah model Ask riil, Win Rate anjlok ke 34,7% dan PF 0,796 (MDD -134,5 R). |
| **H1–H4** | M1 | Scalping Frekuensi Tinggi (32 Varian) | 🔴 **REJECTED** | Seluruh 32 varian gagal total pada validasi out-of-sample (WR 21%–44%, Exp -0,28R s/d -0,74R) akibat tercekik friksi spread ECN. |
| **STRAT-01** | M1 | London 17:30 WIB Reversal | 🔴 **REJECTED** | Hancur pada partisi validasi 2023–2024 (PF 0,41). |
| **STRAT-07** | M1 | Tokyo 08:15 WIB Reversal | 🔴 **REJECTED** | Hancur pada partisi validasi independen 2024–2025 (WR 24,0%, PF 0,381, Net Exp -0,3618 R). |
| **Holdout** | M1 | Partisi Buta (2025-08-22 s/d 2026-08-21) | 🟢 **SEALED** | **100% Tersegel rapat tanpa akses atau kebocoran data.** |

---

## 3. Indeks Dokumen Laporan Kunci

### A. Laporan Revalidasi STRAT-07 (Phase 3)
- `reports/phase3_strat07/PHASE_3_STRAT07_REVALIDATION.md` — Laporan utama penolakan STRAT-07 (Dekomposisi Long/Short & autopsi sampel kecil).
- `reports/phase3_strat07/STRAT07_REPRODUCIBILITY_MANIFEST.md` — Manifest reproduktibilitas skrip dan checksum data STRAT-07.

### B. Laporan Forensik & Rekonstruksi Eksekusi (Phase 2B, 2C, 2C.1, 2D)
- `reports/phase2_forensic/PHASE_2D_INDEPENDENT_REPRODUCTION.md` — Pembuktian independen runtuhnya STRAT-08 di bawah kuotasi Ask riil.
- `reports/phase2_forensic/RESEARCH_REGISTRY_RESET.md` — Dekrit resmi reset registri dan pembatalan seluruh izin live/prop.
- `reports/phase2_forensic/PHASE_2C1_ACCOUNTING_CLAIM_CORRECTION.md` — Koreksi klaim stop-loss lebar dan pembongkaran defek limit fill Bid vs Ask.
- `reports/phase2_forensic/PHASE_2C_COST_ACCOUNTING_AUDIT.md` — Rekonsiliasi formula biaya kas vs drag ekonomi harga tengah.
- `reports/phase2_forensic/PHASE_2B_FORENSIC_AUDIT.md` — Audit forensik awal Phase 2 (P-value 1.0000, drag inversi stop loss, dan koreksi H3).
- `reports/phase2_forensic/DRAWDOWN_RECONSTRUCTION.md` — Rekonstruksi equity curve dan verifikasi non-concurrency posisi.
- `reports/phase2_forensic/PHASE_2_RESEARCH_CLOSURE.md` — Dekrit penutupan riset scalping frekuensi tinggi.

### C. Laporan Penemuan & Evaluasi Statistik (Phase 2)
- `reports/phase2_discovery/PHASE_2_DISCOVERY_REPORT.md` — Laporan penemuan awal 32 eksperimen H1–H4.
- `reports/phase2_discovery/PHASE_2_STATISTICAL_EVALUATION.md` — Matriks statistik lengkap 32 eksperimen (CI, MDD, t-stat, p-value).
- `reports/phase2_discovery/PHASE_2_CANDIDATE_SHORTLIST.md` — Audit gerbang seleksi (0 kandidat lolos).
- `reports/phase2_discovery/PHASE_2_IMPLEMENTATION_VERIFICATION.md` — Verifikasi 7 kasus uji sintetis implementasi mesin.

### D. Spesifikasi Eksekusi & Metodologi (Phase 1, 1B, 1C)
- `reports/phase1_specs/EXECUTION_SPECIFICATION.md` — Spesifikasi resmi biaya transaksi, slippage, dan semantik Bid/Ask.
- `reports/phase1_specs/COST_MODEL_RECONCILIATION.md` — Rekonsiliasi spread empiris pasar vs baseline ideal.
- `reports/phase1_specs/LIMIT_FILL_SENSITIVITY_SPEC.md` — Spesifikasi 3 skenario penetrasi limit order (Touch, 1-Pip, 2-Pip).
- `reports/phase1_specs/SESSION_DST_SPECIFICATION.md` — Jam pasar UTC, kalender DST US/UK, dan bukti empiris blacklist rollover 21:00–23:00 UTC.
- `reports/phase1_specs/HYPOTHESIS_OPERATIONAL_DEFINITIONS.md` — Formula deterministik 100% untuk H1, H2, H3, H4.
- `reports/phase1_specs/MULTIPLE_TESTING_CONTROL.md` — Batas anggaran eksperimen $M=32$, Holm-Bonferroni, dan protokol embargo.
- `reports/phase1_specs/DATA_AUDIT.md` — Audit forensik 4,18 juta bar M1 dan 405 juta tick Dukascopy.
