# PHASE 2: CANDIDATE SHORTLIST & SELECTION AUDIT

**Document ID**: P2-SHORTLIST-v1.0  
**Phase**: STAGE D — CANDIDATE SELECTION GATE  
**Auditor / Engineer**: Hermes Autonomous Quantitative Trading Research Unit  
**Status**: ZERO CANDIDATES QUALIFIED FOR PROMOTION  

---

## 1. Candidate Promotion Gate Audit

To advance to the locked, blind Out-of-Sample Holdout (Partition 3: 2025-08-22 to 2026-08-21), a candidate strategy was required to satisfy all five pre-registered gates on Partition 2 (Walk-Forward Validation):

| Pre-Registered Gate Criteria | Required Threshold | Best Candidate Observed | Best Candidate ID | Gate Status |
| :--- | :---: | :---: | :---: | :---: |
| **Gate 1: Win Rate** | $\ge \mathbf{68.0\%}$ | **44.5%** | `H2_Z25_RSI20_80_RR50` | **FAILED** |
| **Gate 2: Profit Factor** | $\ge \mathbf{1.30}$ | **0.41** | `H1_LB30_W35_RR80` / `H2` | **FAILED** |
| **Gate 3: Net Expectancy** | $\ge \mathbf{+0.10\text{ R}}$ | **-0.2870 R** | `H2_Z25_RSI15_85_RR50` | **FAILED** |
| **Gate 4: Minimum Volume** | $\ge \mathbf{500\text{ Trades}}$ | 4,748 Trades | `H1_LB15_W35_RR60` | **PASSED (Volume Only)** |
| **Gate 5: Ambiguity Ceiling** | $\le \mathbf{5.0\%}$ | 0.8% Ambiguous | All Active Variants | **PASSED** |

---

## 2. Definitive Classification of All 32 Variants

### Category 1: Rejected Due to Negative Asymmetric Expectancy (24 Variants)
- **H1 (Liquidity Sweep & Reclaim)**: 8 Variants (All rejected; WR = 36.4%–41.9%, PF = 0.35–0.41, Exp = -0.38R to -0.39R).
- **H2 (Intraday Mean Reversion)**: 8 Variants (All rejected; WR = 37.8%–44.5%, PF = 0.33–0.41, Exp = -0.28R to -0.35R).
- **H4 (Micro-Momentum Push)**: 8 Variants (All rejected; WR = 21.0%–31.5%, PF = 0.11–0.23, Exp = -0.57R to -0.74R).

### Category 2: Rejected Due to Execution Non-Fill Infeasibility (8 Variants)
- **H3 (Failed Breakout / Trap Reversal)**: 8 Variants (All rejected; 0 trades filled under mandatory 1-pip penetration rule).

---

## 3. Official Shortlist Determination

$$\mathbf{TOTAL \; CANDIDATES \; SHORTLISTED: \; ZERO \; (0)}$$

### Anti-Overfitting Safeguard Enforcement:
1. In accordance with Rule 2 and Rule 4 of `DISCOVERY_PREREGISTRATION.md`, **NO strategy will be promoted to the sealed final holdout**.
2. The sealed holdout (2025-08-22 to 2026-08-21 UTC) remains **100% UNTOUCHED**.
3. We strictly refuse to lower thresholds, weaken entry criteria, or engage in post-hoc parameter tweaking to manufacture an artificial winner.
