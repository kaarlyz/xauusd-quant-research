# MULTIPLE TESTING CONTROLS, EXPERIMENT BUDGET & EMBARGO PROTOCOL

**Document ID**: MULT-TEST-v1.0  
**Audit Phase**: PHASE 1C — INDEPENDENT METHODOLOGY REVIEW  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Scope**: Prevention of p-hacking, selection bias, and temporal leakage across discovery folds.

---

## 1. Fixed Pre-Registration Experiment Budget ($M = 32$)

To prevent unrestricted data mining and asymptotic curve-fitting, the discovery engine operates under a **Hard Experiment Budget**:

$$\text{Total Pre-Registered Parameter Combinations } (M) = \mathbf{32}$$

Across the 4 registered hypotheses (H1, H2, H3, H4), exactly **8 parameter permutations** are permitted per hypothesis:

| Hypothesis ID | Core Mechanism | Permutations Allowed | Parameter Axes Varied |
| :---: | :--- | :---: | :--- |
| **H1** | Liquidity Sweep & Reclaim | **8 Variants** | Lookback ($N=15, 30$) $\times$ Wick Ratio ($0.35, 0.45$) $\times$ Target RR ($0.60\text{R}, 0.80\text{R}$) |
| **H2** | Intraday Mean Reversion | **8 Variants** | Z-Score ($2.0, 2.5$) $\times$ RSI ($15/85, 20/80$) $\times$ Target RR ($0.50\text{R}, 0.60\text{R}$) |
| **H3** | Failed Breakout (Trap) | **8 Variants** | Range Window ($30\text{m}, 45\text{m}$) $\times$ Re-entry Depth ($0.25, 0.40$) $\times$ Target RR ($0.70\text{R}, 0.80\text{R}$) |
| **H4** | Micro-Momentum Push | **8 Variants** | Velocity ($1.2\text{ATR}, 1.8\text{ATR}$) $\times$ Body Ratio ($0.60, 0.70$) $\times$ Target RR ($0.50\text{R}, 0.70\text{R}$) |

### Immutable Anti-Snooping Rule:
- Once all 32 pre-registered variants are executed, **no further parameter tuning or grid expansion is permitted**.
- Every single variant (including all 32 outcomes) will be recorded in `CANDIDATE_COMPARISON.csv`.

---

## 2. Formal Multiple Testing Corrections

With $M = 32$ total tests:

### A. Holm-Bonferroni Family-Wise Error Rate (FWER):
To guarantee a global significance level of $\alpha = 0.05$:
$$p_{(1)} \le \frac{0.05}{32} = \mathbf{0.00156}$$
$$p_{(k)} \le \frac{0.05}{32 - k + 1}$$
Any candidate failing its step-down significance threshold is rejected.

### B. Benjamini-Hochberg False Discovery Rate (FDR):
We enforce an FDR threshold of $q = 0.05$:
$$p_{(k)} \le \frac{k}{32} \times 0.05$$

### C. Moving Block Bootstrap (10,000 Iterations):
Resampling with replacement using blocks of **10 consecutive trades** to preserve temporal dependency, volatility clustering, and serial autocorrelation.

---

## 3. Walk-Forward Fold Structure & Embargo Protocol

### A. Chronological Fold Partitions:
1. **Fold 1**: Train on `2021-08-23 to 2023-08-21` (2 Years) $\rightarrow$ Validate on `2023-08-22 to 2024-08-21` (1 Year).
2. **Fold 2 (Walk-Forward Gate)**: Train on `2021-08-23 to 2024-08-21` (3 Years) $\rightarrow$ Validate on `2024-08-22 to 2025-08-21` (1 Year).
3. **Fold 3 (Blind Holdout)**: `2025-08-22 to 2026-08-21` (1 Year) $\rightarrow$ **SEALED**.

### B. Purge / Embargo & Boundary Rules:
- **Zero Boundary Rollover**: Any trade open at the exact final timestamp of an In-Sample fold is forcibly closed at market.
- **48-Hour Embargo Window**: A 48-hour gap is enforced between the end of Training and the start of Validation to prevent indicator leakage (e.g. rolling moving averages overlapping across the partition seam).
