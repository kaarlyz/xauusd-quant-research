# HYPOTHESIS OPERATIONAL DEFINITIONS & DETERMINISTIC FORMULAS

**Document ID**: HYP-OPDEF-v1.0  
**Audit Phase**: PHASE 1C — INDEPENDENT METHODOLOGY REVIEW  
**Auditor**: Hermes Independent Quantitative Validation Unit  
**Status**: 100% DETERMINISTIC — SUBJECTIVE LANGUAGE ELIMINATED  

---

## 1. Universal Feature Definitions & Calculation Invariants

1. **Timeframe**: Strictly **M1 (1-minute continuous bars)**.
2. **Signal Timing**: All indicators and conditions are evaluated at the **Close of Bar $t$** ($\text{Close}_t$). Orders are routed for execution at the **Open of Bar $t+1$** ($\text{Open}_{t+1}$).
3. **Lookahead Prevention**: Under no circumstances may an indicator at bar $t$ reference bar $t+1$.
4. **Volume Semantics**: In spot gold (CFD/Forex), the volume field represents **Tick Volume** ($V_t = \text{number of quote changes per minute}$).
5. **Volatility Metric ($\text{ATR}_{14}$)**:
   $$\text{TR}_t = \max\Big(\text{High}_t - \text{Low}_t, \; |\text{High}_t - \text{Close}_{t-1}|, \; |\text{Low}_t - \text{Close}_{t-1}|\Big)$$
   $$\text{ATR}_{14, t} = \frac{13 \times \text{ATR}_{14, t-1} + \text{TR}_t}{14}$$

---

## 2. Deterministic Formulation: H1 (Liquidity Sweep & Reclaim)

### A. Operational Definitions:
- **Lookback Window**: $N = 20\text{ M1 bars}$.
- **Prior Resistance**: $H_{\text{pivot}, t-1} = \max_{k=1..20}(\text{High}_{t-k})$.
- **Prior Support**: $L_{\text{pivot}, t-1} = \min_{k=1..20}(\text{Low}_{t-k})$.

### B. Long Entry Conditions (Sweep of Lows):
1. **Sweep Penetration**:
   $$\text{Low}_t \le L_{\text{pivot}, t-1} - (0.50 \times \text{ATR}_{14, t})$$
2. **Reclaim Bar Close**:
   $$\text{Close}_t \ge L_{\text{pivot}, t-1}$$
3. **Rejection Wick Ratio**:
   $$\frac{\min(\text{Open}_t, \text{Close}_t) - \text{Low}_t}{\text{High}_t - \text{Low}_t} \ge 0.40$$
4. **Execution**: Market Buy at $\text{Open}_{t+1}$ (at Ask).
5. **Stop Loss**: $\text{SL} = \text{Low}_t - \$0.30$.
6. **Take Profit**: $\text{TP} = \text{Fill} + (0.70 \times |\text{Fill} - \text{SL}|)$.
7. **Time Exit**: Liquidate at market if position open $> 10\text{ minutes}$.

### C. Short Entry Conditions (Sweep of Highs):
1. **Sweep Penetration**: $\text{High}_t \ge H_{\text{pivot}, t-1} + (0.50 \times \text{ATR}_{14, t})$.
2. **Reclaim Bar Close**: $\text{Close}_t \le H_{\text{pivot}, t-1}$.
3. **Rejection Wick Ratio**: $\frac{\text{High}_t - \max(\text{Open}_t, \text{Close}_t)}{\text{High}_t - \text{Low}_t} \ge 0.40$.
4. **Execution**: Market Sell at $\text{Open}_{t+1}$ (at Bid).
5. **Stop Loss**: $\text{SL} = \text{High}_t + \$0.30$.
6. **Take Profit**: $\text{TP} = \text{Fill} - (0.70 \times |\text{SL} - \text{Fill}|)$.
7. **Time Exit**: Liquidate at market if position open $> 10\text{ minutes}$.

---

## 3. Deterministic Formulation: H2 (Intraday Rolling Mean Reversion)

### A. Mathematical Indicators:
- **Rolling Mean (20)**: $\mu_{20, t} = \frac{1}{20} \sum_{k=0}^{19} \text{Close}_{t-k}$.
- **Rolling Std Dev (20)**: $\sigma_{20, t} = \sqrt{\frac{1}{20} \sum_{k=0}^{19} (\text{Close}_{t-k} - \mu_{20, t})^2}$.
- **Price Z-Score**: $Z_t = \frac{\text{Close}_t - \mu_{20, t}}{\sigma_{20, t}}$.
- **Relative Volume**: $\text{RVol}_t = \frac{V_t}{\frac{1}{20}\sum_{k=0}^{19} V_{t-k}}$.
- **Wilder's RSI(7)**: Computed using standard 7-period smoothing.

### B. Long Entry Conditions:
1. $Z_{t-1} \le -2.20$ AND $\text{RSI}_{7, t-1} \le 20.0$.
2. Relative volume surge: $\text{RVol}_{t-1} \ge 1.80$.
3. Confirmation candle: $\text{Close}_t > \text{Open}_t$ (green candle).
4. **Execution**: Market Buy at $\text{Open}_{t+1}$ (at Ask).
5. **Stop Loss**: $\text{SL} = \min(\text{Low}_t, \text{Low}_{t-1}) - \$0.40$.
6. **Take Profit**: $\text{TP} = \text{Fill} + (0.50 \times |\text{Fill} - \text{SL}|)$.
7. **Time Exit**: Force close at market after **5 minutes**.

### C. Short Entry Conditions:
1. $Z_{t-1} \ge +2.20$ AND $\text{RSI}_{7, t-1} \ge 80.0$.
2. Relative volume surge: $\text{RVol}_{t-1} \ge 1.80$.
3. Confirmation candle: $\text{Close}_t < \text{Open}_t$ (red candle).
4. **Execution**: Market Sell at $\text{Open}_{t+1}$ (at Bid).
5. **Stop Loss**: $\text{SL} = \max(\text{High}_t, \text{High}_{t-1}) + \$0.40$.
6. **Take Profit**: $\text{TP} = \text{Fill} - (0.50 \times |\text{SL} - \text{Fill}|)$.
7. **Time Exit**: Force close at market after **5 minutes**.

---

## 4. Deterministic Formulation: H3 (Failed Breakout / Trap)

### A. Mathematical Indicators:
- **Consolidation Range (30 Bars)**:
  $$H_{\text{box}, t-1} = \max_{k=2..31}(\text{High}_{t-k}), \quad L_{\text{box}, t-1} = \min_{k=2..31}(\text{Low}_{t-k})$$
- Range Width Constraint: $\$3.00 \le (H_{\text{box}} - L_{\text{box}}) \le \$12.00$.

### B. Long Entry Conditions (Bear Trap):
1. **Breakout Bar ($t-1$)**: $\text{Close}_{t-1} < L_{\text{box}, t-1}$.
2. **Failure Re-Entry Bar ($t$)**: $\text{Close}_t \ge L_{\text{box}, t-1} + (0.30 \times \text{ATR}_{14, t})$.
3. **Bullish Engulfing**: $(\text{Close}_t - \text{Open}_t) > (\text{Open}_{t-1} - \text{Close}_{t-1})$.
4. **Execution**: Passive Limit Buy placed at $L_{\text{box}, t-1} + \$0.10$ for bar $t+1$. (Expires if unfilled in 3 bars).
5. **Stop Loss**: $\text{SL} = \text{Low}_{t-1} - \$0.30$.
6. **Take Profit**: $\text{TP} = \text{Limit Fill} + (0.75 \times |\text{Limit Fill} - \text{SL}|)$.
7. **Time Exit**: Force close after **15 minutes**.

### C. Short Entry Conditions (Bull Trap):
1. **Breakout Bar ($t-1$)**: $\text{Close}_{t-1} > H_{\text{box}, t-1}$.
2. **Failure Re-Entry Bar ($t$)**: $\text{Close}_t \le H_{\text{box}, t-1} - (0.30 \times \text{ATR}_{14, t})$.
3. **Bearish Engulfing**: $(\text{Open}_t - \text{Close}_t) > (\text{Close}_{t-1} - \text{Open}_{t-1})$.
4. **Execution**: Passive Limit Sell placed at $H_{\text{box}, t-1} - \$0.10$ for bar $t+1$.
5. **Stop Loss**: $\text{SL} = \text{High}_{t-1} + \$0.30$.
6. **Take Profit**: $\text{TP} = \text{Limit Fill} - (0.75 \times |\text{SL} - \text{Limit Fill}|)$.
7. **Time Exit**: Force close after **15 minutes**.

---

## 5. Deterministic Formulation: H4 (Micro-Momentum Continuation)

### A. Mathematical Indicators:
- $\text{EMA}_9$: 9-period exponential moving average on M1.
- Velocity ($V_3$): $V_{3, t} = \text{Close}_t - \text{Open}_{t-2}$.

### B. Long Entry Conditions:
1. **Impulse Wave**:
   $$V_{3, t-1} \ge 1.50 \times \text{ATR}_{14, t-1}$$
   $$\text{Body Ratio}: \min_{k=1..3}\Big(\frac{\text{Close}_{t-k} - \text{Open}_{t-k}}{\text{High}_{t-k} - \text{Low}_{t-k}}\Big) \ge 0.60$$
2. **Pullback Bar ($t$)**:
   $$\text{Range}_t \le 0.60 \times \text{ATR}_{14, t} \quad \text{AND} \quad \text{Low}_t \ge \text{EMA}_{9, t}$$
3. **Execution**: Stop Buy order at $\text{High}_t + \$0.10$.
4. **Stop Loss**: $\text{SL} = \text{Low}_t - \$0.30$.
5. **Take Profit**: $\text{TP} = \text{Fill} + (0.60 \times |\text{Fill} - \text{SL}|)$.
6. **Time Exit**: Force close after **5 minutes**.

### C. Short Entry Conditions:
1. **Impulse Wave**:
   $$V_{3, t-1} \le -1.50 \times \text{ATR}_{14, t-1}$$
   $$\text{Body Ratio}: \min_{k=1..3}\Big(\frac{\text{Open}_{t-k} - \text{Close}_{t-k}}{\text{High}_{t-k} - \text{Low}_{t-k}}\Big) \ge 0.60$$
2. **Pullback Bar ($t$)**:
   $$\text{Range}_t \le 0.60 \times \text{ATR}_{14, t} \quad \text{AND} \quad \text{High}_t \le \text{EMA}_{9, t}$$
3. **Execution**: Stop Sell order at $\text{Low}_t - \$0.10$.
4. **Stop Loss**: $\text{SL} = \text{High}_t + \$0.30$.
5. **Take Profit**: $\text{TP} = \text{Fill} - (0.60 \times |\text{SL} - \text{Fill}|)$.
6. **Time Exit**: Force close after **5 minutes**.
