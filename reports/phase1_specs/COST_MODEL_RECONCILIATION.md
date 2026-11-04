# COST MODEL RECONCILIATION & SPREAD EMPIRICAL AUDIT

**Document ID**: COST-RECON-v1.0  
**Audit Phase**: PHASE 1C — INDEPENDENT METHODOLOGY REVIEW  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Status**: FORMALLY RECONCILED  

---

## 1. Reconciling the $0.35 Fixed Spread Assumption

In Phase 1B, a baseline fixed spread of **$0.35 per ounce** was proposed. However, our empirical audit of **405,106,965 ticks** across 2020–2026 revealed that observed median spreads across trading sessions are systematically higher:

| Market Session | Local Business Hours | Empirical Median Spread | Empirical Mean Spread | 95th Percentile Spread | Phase 1B Assumed Spread | Understatement / Gap |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tokyo (Asia)** | 00:00 – 07:00 UTC | **$0.3920 – $0.4130** | $0.4542 – $0.4899 | $0.8100 – $0.8800 | $0.3500 | -$0.042 to -$0.063 |
| **London Morning** | 07:00 – 11:00 UTC | **$0.3740 – $0.3840** | $0.4260 – $0.4372 | $0.7100 – $0.7200 | $0.3500 | -$0.024 to -$0.034 |
| **London/NY Overlap** | 12:00 – 15:00 UTC | **$0.3770 – $0.3840** | $0.4348 – $0.4405 | $0.7400 – $0.7640 | $0.3500 | -$0.027 to -$0.034 |
| **New York Afternoon**| 16:00 – 20:00 UTC | **$0.3670 – $0.3970** | $0.4233 – $0.4644 | $0.7200 – $0.7900 | $0.3500 | -$0.017 to -$0.047 |

### Auditor's Binding Determination:
1. **$0.35 CANNOT be treated as a universal spread**: It represents an idealized best-case quote seen only during optimal liquidity pulses.
2. **Primary Execution Model Definition**:
   - The primary backtest execution model **must extract the actual historical Ask and Bid prices** from the tick dataset at the precise millisecond of order execution.
   - If tick replay is active:
     $$\text{Spread}_{\text{actual}} = \text{Ask}_{\text{tick}} - \text{Bid}_{\text{tick}}$$
   - If M1 fallback is utilized: A session-weighted conservative spread must be enforced:
     - **London / NY Overlap**: **$0.380 / oz**
     - **London Morning / NY Afternoon**: **$0.385 / oz**
     - **Tokyo Session**: **$0.405 / oz**
   - The $0.35 fixed figure is relegated to a **comparative benchmark only**.

---

## 2. Commission Schedule Verification

- **Contract Unit**: 1 Standard Lot = 100 Troy Ounces.
- **Broker Schedule (The 5ers & Institutional Raw ECN)**:
  - The 5ers institutional bridge charges **$3.00 to $3.50 per standard lot per side** ($6.00 to $7.00 round-turn).
  - Converting to per-ounce terms:
    $$C_{\text{oz}} = \frac{\$7.00}{100\text{ oz}} = \mathbf{\$0.07\text{ per ounce (Round-Turn)}}$$
  - Sided accounting: **$0.035 / oz on entry**, **$0.035 / oz on exit**.
  - **Verdict**: Verified accurate against institutional broker specifications.

---

## 3. Raw Trade Recalculation: Nominal vs Realized R

To prevent conflation between raw chart price distance and true equity realization, we recalculate the worked examples using observed London/NY median spread ($0.380 / oz):

### Long Trade Worked Recalculation:
- **Balance**: $2,500.00 | **Risk ($K_{\text{risk}}$)**: **$7.50 (0.30%)**
- **Signal**: Long at Bid = $2,650.00 | Nominal SL = $2,648.00 | Target RR = **0.70 : 1**
- **Observed Spread**: $0.380 | **Entry Slippage**: $0.05
- **Actual Entry Fill (Ask)**:
  $$\text{Fill}_{\text{Buy}} = 2,650.00 + 0.380 + 0.05 = \mathbf{\$2,650.430}$$
- **Actual Stop Distance ($D_{\text{SL}}$)**:
  $$D_{\text{SL}} = 2,650.430 - 2,648.00 = \mathbf{\$2.430}$$
- **Position Sizing ($V$)**:
  $$V = \frac{\$7.50}{\$2.430 \times 100} = \mathbf{0.030864\text{ Lots (3.0864 oz)}}$$
- **Nominal Price Target (0.70 R distance = $1.701)**:
  $$\text{TP Price (Bid)} = 2,650.430 + 1.701 = \mathbf{\$2,652.131}$$
- **Settlement at TP Hit**:
  - Gross PnL: $+\$1.701 \times 3.0864\text{ oz} = +\$5.24997$
  - Commission: $-\$0.07 \times 3.0864\text{ oz} = -\$0.21605$
  - Net Dollar PnL: $+\$5.03392$
  - **Net Realized R**: $\frac{+\$5.03392}{\$7.50} = \mathbf{+0.6712\text{ R}}$ (Nominal price move = 0.7000 R; Cost drag = -0.0288 R).

### Short Trade Worked Recalculation:
- **Signal**: Short at Bid = $2,655.00 | Nominal SL = $2,656.50
- **Entry Slippage**: $0.05 | **Observed Spread at SL**: $0.380 | **Exit Slippage**: $0.05
- **Actual Entry Fill (Bid)**:
  $$\text{Fill}_{\text{Sell}} = 2,655.00 - 0.05 = \mathbf{\$2,654.950}$$
- **Actual Stop Distance ($D_{\text{SL}}$)**:
  $$D_{\text{SL}} = 2,656.50 - 2,654.950 = \mathbf{\$1.550}$$
- **Position Sizing ($V$)**:
  $$V = \frac{\$7.50}{\$1.550 \times 100} = \mathbf{0.048387\text{ Lots (4.8387 oz)}}$$
- **Settlement at SL Hit**:
  - Ask touches SL and fills with $0.05 slippage at **$2,656.550**:
  - Gross Price Move: $2,654.950 - 2,656.550 = -\$1.600$
  - Gross Loss: $-\$1.600 \times 4.8387\text{ oz} = -\$7.7419$
  - Commission: $-\$0.07 \times 4.8387\text{ oz} = -\$0.3387$
  - Net Loss: $-\$8.0806$
  - **Net Realized R**: $\frac{-\$8.0806}{\$7.50} = \mathbf{-1.0774\text{ R}}$ (Nominal stop = -1.0000 R; Friction drag = -0.0774 R).
