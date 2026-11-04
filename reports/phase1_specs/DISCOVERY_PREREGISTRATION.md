# HIGH-FREQUENCY DISCOVERY PRE-REGISTRATION PROTOCOL

**Document ID**: PRE-REG-v1.0  
**Effective Date**: 2026-11-01  
**Auditor / Author**: Hermes Quantitative Research Platform  
**Research Mandate**: Autonomous High-Frequency, High-Win-Rate Strategy Discovery on XAUUSD  

---

## 1. Chronological Dataset Segmentation Invariants

To eliminate data snooping, selection bias, and backtest overfitting, the verified 5-year XAUUSD dataset (2021-08-23 to 2026-08-21 UTC, 1,769,576 candles) is strictly locked into three chronological partitions:

| Partition Role | Start Timestamp (UTC) | End Timestamp (UTC) | Duration | Primary Research Function | Access Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Partition 1: In-Sample (IS)** | `2021-08-23 00:00:00` | `2024-08-21 23:59:59` | **3 Years** | Feature exploration, parameter scanning, signal generation | **OPEN for discovery** |
| **Partition 2: Walk-Forward Validation** | `2024-08-22 00:00:00` | `2025-08-21 23:59:59` | **1 Year** | Out-of-sample confirmation, parameter stability check | **LOCKED (Evaluated once per candidate)** |
| **Partition 3: Blind Final Holdout** | `2025-08-22 00:00:00` | `2026-08-21 20:59:00` | **1 Year** | Final irrevocable acceptance / rejection gate | **STRICTLY SEALED until validation passes** |

---

## 2. Pre-Registered Candidate Acceptance Criteria

A candidate strategy from any of the four discovery families (H1, H2, H3, H4) can only pass to the final evaluation if it satisfies **ALL** of the following quantitative gates on the **Walk-Forward Validation (Partition 2)**:

1. **Win Rate Gate**: Out-of-Sample Win Rate $\ge \mathbf{68.0\%}$.
2. **Expectancy Gate**: Net Expectancy after realistic transaction costs ($\ge \$0.47/\text{oz}$) must be $\ge \mathbf{+0.10\text{ R}}$ per trade.
3. **Profit Factor Gate**: Out-of-Sample Profit Factor $\ge \mathbf{1.30}$.
4. **Trade Frequency Gate**:
   - Minimum trade count on 1-year validation: $\ge \mathbf{500\text{ trades}}$.
   - Target active day pacing: $\ge \mathbf{3\text{ to }5\text{ trades per active trading day}}$.
5. **Regime Robustness Gate**: Must show positive net expectancy across both London and New York sessions independently (no single-window dependency).
6. **Execution Integrity Gate**: Total percentage of ambiguous intra-bar outcomes must be $\le \mathbf{5.0\%}$ of total trades.

---

## 3. Multiple Testing & Data Mining Controls

1. **Every Experiment Recorded**: Every parameter combination, variation, and failed hypothesis will be logged into `CANDIDATE_COMPARISON.csv`. No losing variants will be pruned or hidden.
2. **Statistical Adjustments**:
   - Family-wise error rate (FWER) controlled via **Holm-Bonferroni**.
   - False Discovery Rate (FDR) controlled via **Benjamini-Hochberg**.
   - Resampling confidence intervals evaluated via **Moving Block Bootstrap** (blocks of 10 trades).
3. **Anti-Overfitting Pledge**:
   - If a candidate strategy fails in Partition 2 or Partition 3, it is **PERMANENTLY REJECTED**.
   - No parameters will be adjusted after viewing Partition 2/3 results to re-run on the same data.
