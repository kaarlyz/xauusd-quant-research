# MICROSTRUCTURE FRICTION & EXECUTION REALISM AUDIT

**Audit Date**: 2026-11-01  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Target Portfolio**: STRAT-08 (London Fibo M15) + STRAT-07 (Tokyo M1)  
**Mandate**: Granular decomposition of market spread, institutional commission, and execution slippage on real-world edge survival.

---

## 1. Friction Decomposition Architecture

Execution friction in retail and prop-firm trading comprises three independent components:
1. **Quoted Bid-Ask Spread ($S$)**: The instantaneous price difference between buyers and sellers.
2. **Broker Commission ($C$)**: Standard institutional ECN fee, typically $7.00 per standard lot round-trip ($\approx \$0.07$ per ounce of Gold).
3. **Execution Slippage ($\sigma$)**: Adverse execution lag between order transmission and matching engine confirmation:
   - $0.0\text{ ticks} = \$0.00$
   - $0.5\text{ ticks} = \$0.05$
   - $1.0\text{ ticks} = \$0.10$

$$\text{Total Friction per Trade} = S + C + \sigma$$

---

## 2. Comprehensive Friction Stress-Test Matrix

We evaluated STRAT-08 and the combined Portfolio B across 15 discrete friction permutations:

| Base Spread | Slippage | Total Friction ($) | STRAT-08 Win Rate | STRAT-08 Profit Factor | STRAT-08 Net Exp (R) | Portfolio B Profit Factor | Portfolio B Net Exp (R) | Portfolio B Max DD (R) | Operational Verdict |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **$0.25 (Raw ECN)** | **$0.00 (Zero)** | **$0.32** | 48.28% | **1.381** | **+0.1964 R** | **1.374** | **+0.1871 R** | **-18.19 R** | **PRISTINE (Ideal)** |
| $0.25 | $0.05 (0.5 tick) | **$0.37** | 48.28% | **1.382** | **+0.1968 R** | **1.377** | **+0.1883 R** | **-20.71 R** | **EXCELLENT** |
| $0.25 | $0.10 (1 tick) | **$0.42** | 47.45% | **1.343** | **+0.1791 R** | **1.339** | **+0.1719 R** | **-24.73 R** | **EXCELLENT** |
| **$0.35 (Prop ECN)** | **$0.00 (Zero)** | **$0.42** | 47.45% | **1.343** | **+0.1791 R** | **1.339** | **+0.1719 R** | **-24.73 R** | **EXCELLENT** |
| $0.35 | $0.05 (0.5 tick) | **$0.47** | 46.52% | **1.309** | **+0.1633 R** | **1.306** | **+0.1575 R** | **-23.75 R** | **STRONG** |
| $0.35 | $0.10 (1 tick) | **$0.52** | 45.18% | **1.232** | **+0.1259 R** | **1.233** | **+0.1232 R** | **-26.02 R** | **STRONG (Baseline)** |
| **$0.40 (Standard ECN)** | $0.00 (Zero) | **$0.47** | 46.52% | **1.309** | **+0.1633 R** | **1.306** | **+0.1575 R** | **-23.75 R** | **STRONG** |
| $0.40 | $0.05 (0.5 tick) | **$0.52** | 45.18% | **1.232** | **+0.1259 R** | **1.233** | **+0.1232 R** | **-26.02 R** | **STRONG** |
| $0.40 | $0.10 (1 tick) | **$0.57** | 43.62% | **1.164** | **+0.0912 R** | **1.168** | **+0.0912 R** | **-28.64 R** | **ACCEPTABLE** |
| **$0.50 (Elevated)** | $0.00 (Zero) | **$0.57** | 43.62% | **1.164** | **+0.0912 R** | **1.168** | **+0.0912 R** | **-28.64 R** | **ACCEPTABLE** |
| $0.50 | $0.05 (0.5 tick) | **$0.62** | 42.13% | **1.106** | **+0.0602 R** | **1.112** | **+0.0617 R** | **-43.87 R** | **MARGINAL (DD Spikes)** |
| $0.50 | $0.10 (1 tick) | **$0.67** | 40.80% | **1.057** | **+0.0333 R** | **1.065** | **+0.0365 R** | **-56.75 R** | **DANGEROUS (DD > 50R)** |
| **$0.75 (Standard Retail)**| $0.00 (Zero) | **$0.82** | 38.84% | **0.970** | **-0.0181 R** | **0.978** | **-0.0126 R** | **-112.42 R** | **EXTINCTION (Loss)** |
| $0.75 | $0.05 (0.5 tick) | **$0.87** | 38.37% | **0.953** | **-0.0281 R** | **0.961** | **-0.0227 R** | **-127.53 R** | **EXTINCTION (Loss)** |
| $0.75 | $0.10 (1 tick) | **$0.92** | 37.98% | **0.939** | **-0.0372 R** | **0.946** | **-0.0315 R** | **-136.20 R** | **EXTINCTION (Loss)** |

---

## 3. The Edge Extinction Cliff: Critical Findings

### 1. The Critical Friction Ceiling is $0.55 per Trade
- As long as total round-trip friction remains **$\le \$0.52$**, the portfolio generates robust performance:
  $$\text{Profit Factor} \ge 1.23 \quad | \quad \text{Expectancy} \ge +0.12\text{ R} \quad | \quad \text{Max DD} \le -26.0\text{ R}$$
- Once total friction crosses **$\$0.60$**, maximum drawdown doubles to **-43.87 R**.
- Once total friction reaches **$\$0.82$**, the edge completely vanishes ($\text{PF} = 0.97$, Expectancy is negative).

### 2. Microstructure Asymmetry Between STRAT-08 and STRAT-07
- **STRAT-08 (London Fibo M15)**: Because it enters via **Passive Limit Orders**, entry slippage is essentially zero ($\sigma_{\text{entry}} = 0$). However, because its stop loss is relatively tight ($1.50–$3.50), high bid-ask spread directly expands the stop distance, diluting the realized reward-to-risk ratio.
- **STRAT-07 (Tokyo M1)**: Uses a market entry at 08:15 WIB. While it suffers slippage on market fill ($\approx 0.5\text{ ticks}$), its wider stop loss ($2.50–$4.50) gives it superior resistance to spread widening (retains PF > 1.07 even at $1.00 spread).

---

## 4. Mandatory Broker Specification Baseline

Before connecting any account or bot:
1. **Account Type**: **Raw ECN / Zero Spread Only**. Standard spread accounts are strictly prohibited.
2. **Quoted Spread Threshold**: Average London/NY session XAUUSD spread must be **$\le \$0.30$** (3.0 pips on Gold).
3. **Commission Limit**: Commission must not exceed **$7.00 per lot ($0.07/oz)**.
4. **Hard Execution Gate**: If the live spread at order generation time is **$> \$0.45$**, the execution engine must abort the order.
