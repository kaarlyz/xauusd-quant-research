# PHASE 2: RESEARCH CLOSURE & DIRECTIONAL INTERPRETATION

**Document ID**: P2-CLOSURE-v1.0  
**Phase**: PHASE 2B — FORENSIC RESULTS AUDIT & RESEARCH CLOSURE  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Status**: FORMAL RESEARCH CLOSURE DECREE  

---

## 1. Precise Scientific Boundaries & Distinctions

To ensure intellectual honesty, the research unit explicitly delineates what was proven, what was disproven, and what remains open:

### A. What Was DEFINITIVELY DISPROVEN:
1. **The 4 Registered Scalping Hypotheses (H1, H2, H3, H4) are Falsified**:
   - Continuous intraday scalping on M1 with asymmetric negative reward-to-risk ($0.50\text{R}–0.80\text{R}$ TP vs $1.00\text{R}$ SL) and high frequency ($5+$ trades/day) **CANNOT produce a positive net expectancy** after realistic ECN transaction costs ($S = \$0.380$, $C = \$0.070/\text{oz}$, $\sigma = \$0.050/\text{side}$).
   - All 32 pre-registered variants produced deeply negative expectancies ($-0.28\text{ R}$ to $-0.74\text{ R}$) and failed every validation gate.
2. **The "High Win Rate from Tight TP" Retail Fallacy**:
   - The belief that shortening TP to $0.50\text{R}$ will automatically lift Win Rate above $70\%$ is mathematically and empirically false on XAUUSD. The observed Win Rates across 3.4M bars peaked at **$44.5\%$**, far below the breakeven threshold of **$65.6\%$**.

### B. What Was NOT Proven or Disproven:
1. **Universal M1 Trading**:
   - The failure of H1–H4 does **NOT** mean that all trading on M1 is impossible.
   - It proves that **continuous, un-gated scalping across arbitrary hours fails**.
2. **Session & Reward-to-Risk Effects**:
   - When trades are restricted to discrete institutional liquidity events (e.g. STRAT-07 at 08:15 WIB) and target positive asymmetry ($\ge 1.50 : 1\text{ RR}$), the mathematical penalty of transaction friction drops from $17\%$ of risk down to $< 5\%$, allowing statistical edges to survive.

---

## 2. Re-Affirmation of Validated Strategies (STRAT-08 & STRAT-07)

The failure of the Phase 2 high-frequency experiments strongly reinforces the validity and uniqueness of our prior Phase 1 discoveries:

| Strategy ID | Timeframe | Strategy Architecture | Target RR | Win Rate | Profit Factor | Status |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: |
| **STRAT-08** | M15 | London Opening Drive Fibo 78.6% Retest | **1.50 : 1** | **45.6% – 54.9%** | **1.26 – 1.83** | **OUT-OF-SAMPLE VALIDATED** |
| **STRAT-07** | M1 | Tokyo 08:15 WIB Institutional Reversal | **1.50 : 1** | **50.4% – 51.6%** | **1.27 – 1.28** | **PROMISING (Portfolio Hedge)** |
| **Phase 2 H1–H4**| M1 | Continuous High-Frequency Scalping (32 Variants) | **0.50R – 0.80R** | **21.0% – 44.8%** | **0.11 – 0.45** | **PERMANENTLY REJECTED** |

---

## 3. Final Auditor Verdict

$$\mathbf{CONDITIONAL \; PASS \; — \; LIMITATIONS \; DOCUMENTED}$$

### Findings Summary:
1. **Results Internally Consistent**: The negative outcomes of H1–H4 reflect authentic market realities and cannot be attributed to data corruption or missing records.
2. **Implementation Defect Resolved**: The H3 indexing bug (`shift(1)` vs `shift(2)`) was identified and corrected; empirical re-testing proved H3 is equally unprofitable.
3. **Sealed Holdout Intact**: The 2025–2026 blind holdout remains **100% sealed and untouched**.
4. **Mandate for Future Research**: Any future strategy discovery must abandon negative-RR scalping ($< 1.0\text{R}$) and focus exclusively on **institutional liquidity timing, regime-conditioned triggers, and positive reward-to-risk ratios ($\ge 1.50\text{R}$)**.
