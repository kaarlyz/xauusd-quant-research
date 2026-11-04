# ATR FILTER OUT-OF-SAMPLE EVALUATION & MULTIPLE TESTING AUDIT

**Audit Date**: 2026-11-01  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Target Rule**: Addition of London Opening Volatility Filter ($\text{ATR}_{20} > \text{Threshold}$) to STRAT-08  
**Mandate**: Formal scientific determination of whether the ATR filter represents a robust economic discovery or data snooping.

---

## 1. Provenance & Methodological Status

### The Origin of the $1.30 Threshold:
During Phase 2 analysis of market regimes, the dataset was split into volatility terciles (low, normal, high). The 33rd percentile boundary landed at $\text{ATR}_{20} \approx \$1.25–\$1.30$. Observing that the lowest tercile was unprofitable, a filter of $\text{ATR}_{20} > \$1.30$ was proposed.

### Scientific Classification:
Because the $\$1.30$ cutoff was observed **after seeing the entire 12-year dataset**, it cannot be claimed as an a priori theoretical parameter. Under scientific research discipline, it must be classified as **EXPLORATORY / CANDIDATE RULE** until strictly evaluated across untouched chronological out-of-sample partitions with multiple-testing penalties.

---

## 2. Threshold Sensitivity Matrix Across Chronological Partitions

We froze the threshold sweep across six explicit levels ($\text{None}, \$1.20, \$1.25, \$1.30, \$1.35, \$1.40$) and evaluated them across the three chronological partitions:
- **In-Sample (IS)**: 2015–2022
- **OOS Validation**: 2023–2024
- **OOS Blind Holdout**: 2025–2026

| Filter Variant | Partition | Trades ($N$) | Win Rate | Profit Factor | Net Expectancy | Max Drawdown | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **No ATR Filter (Baseline)** | Full Sample (12y) | 1,277 | 45.58% | 1.256 | +0.1379 R | -24.58 R | Core Benchmark |
| | In-Sample (2015–2022) | 669 | 42.15% | 1.087 | +0.0494 R | -24.58 R | Positive |
| | OOS Validation (2023–2024) | 309 | 44.01% | 1.186 | +0.1035 R | -19.00 R | Positive |
| | OOS Holdout (2025–2026) | 299 | **54.85%** | **1.828** | **+0.3713 R** | **-7.00 R** | Exceptional |
| **ATR > $1.20** | Full Sample (12y) | 1,149 | 46.39% | 1.301 | +0.1597 R | -24.58 R | Improved |
| | In-Sample (2015–2022) | 554 | 42.42% | 1.103 | +0.0587 R | -24.58 R | Improved |
| | OOS Validation (2023–2024) | 296 | 45.27% | 1.248 | +0.1351 R | -16.00 R | Improved |
| | OOS Holdout (2025–2026) | 299 | **54.85%** | **1.828** | **+0.3713 R** | **-7.00 R** | Identical |
| **ATR > $1.25** | Full Sample (12y) | 1,134 | 46.30% | 1.296 | +0.1574 R | -26.58 R | Higher Drawdown |
| | In-Sample (2015–2022) | 544 | 42.28% | 1.097 | +0.0552 R | -26.58 R | Higher Drawdown |
| | OOS Validation (2023–2024) | 291 | 45.02% | 1.236 | +0.1288 R | -16.50 R | Improved |
| | OOS Holdout (2025–2026) | 299 | **54.85%** | **1.828** | **+0.3713 R** | **-7.00 R** | Identical |
| **ATR > $1.30 (Proposed)** | Full Sample (12y) | 1,112 | 46.40% | 1.301 | +0.1601 R | -25.08 R | Improved |
| | In-Sample (2015–2022) | 526 | 42.21% | 1.093 | +0.0533 R | -25.08 R | Neutral |
| | OOS Validation (2023–2024) | 287 | 45.30% | 1.250 | +0.1358 R | -16.50 R | Improved |
| | OOS Holdout (2025–2026) | 299 | **54.85%** | **1.828** | **+0.3713 R** | **-7.00 R** | Identical |
| **ATR > $1.35** | Full Sample (12y) | 1,090 | 46.79% | 1.322 | +0.1698 R | -23.58 R | Improved |
| | In-Sample (2015–2022) | 509 | 42.83% | 1.122 | +0.0688 R | -23.58 R | Improved |
| | OOS Validation (2023–2024) | 282 | 45.39% | 1.255 | +0.1382 R | -16.50 R | Improved |
| | OOS Holdout (2025–2026) | 299 | **54.85%** | **1.828** | **+0.3713 R** | **-7.00 R** | Identical |
| **ATR > $1.40** | Full Sample (12y) | 1,067 | 46.95% | 1.331 | +0.1739 R | -24.08 R | Improved |
| | In-Sample (2015–2022) | 490 | 42.86% | 1.123 | +0.0694 R | -24.08 R | Improved |
| | OOS Validation (2023–2024) | 278 | 45.68% | 1.270 | +0.1456 R | -15.50 R | Improved |
| | OOS Holdout (2025–2026) | 299 | **54.85%** | **1.828** | **+0.3713 R** | **-7.00 R** | Identical |

---

## 3. Critical Quantitative Discoveries

### Discovery 1: The Blind Holdout (2025–2026) Is Completely Invariant
Across **all six threshold variants**, the results in the 2025–2026 holdout are **100% identical**:
$$\text{Trades} = 299 \quad | \quad \text{Win Rate} = 54.85\% \quad | \quad \text{Profit Factor} = 1.828 \quad | \quad \text{Expectancy} = +0.3713\text{ R}$$
- *Explanation*: In 2025–2026, gold experienced elevated macro volatility where the London opening $\text{ATR}_{20}$ never dropped below $\$1.40$. The filter did not eliminate a single trade in the modern era.

### Discovery 2: The Filter Operates Solely as a 2015–2019 Regime Gate
- During 2015–2019, gold experienced historic multi-year compression ($\text{ATR} \le \$1.20$).
- Applying $\text{ATR}_{20} > \$1.30$ eliminated 165 trades between 2015 and 2024, of which ~60% were small losses, thereby lifting full-sample Profit Factor from **1.256 to 1.301**.
- However, for ATR > $1.25 and ATR > $1.30, maximum drawdown slightly worsened from **-24.58 R to -25.08 R / -26.58 R** because several winning trades in late 2015 were also filtered out.

---

## 4. Final Scientific Verdict on the ATR Filter

> **Should the ATR filter be codified as an active live trading requirement?**

### THE VERDICT: **RETAIN AS AN INFORMATIONAL REGIME MONITOR. DO NOT HARD-CODE AS A LIVE ENTRY GATE.**

1. **The Baseline Unfiltered Strategy Already Has an Authenticated Edge**:
   - The unfiltered strategy has a Bonferroni-adjusted $p$-value of **$0.0055$** and delivers **+176 R** across 12 years. It does not require the ATR filter to be profitable.
2. **Risk of Over-Engineering**:
   - Hard-coding $\$1.30$ introduces a static parameter that was discovered post-hoc. In changing macroeconomic environments, fixed dollar thresholds can cause unintended signal gating.
3. **Operational Protocol**:
   - Execute STRAT-08 according to its **locked baseline rules** ($\text{Span} \in [\$4.00, \$30.00]$, $0.786$ Fibo).
   - If gold volatility drops into extreme historical compression ($\text{ATR}_{20} < \$1.00$), review macro regime manually before deploying fresh risk.
