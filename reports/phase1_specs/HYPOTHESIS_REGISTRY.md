# HIGH-FREQUENCY STRATEGY DISCOVERY HYPOTHESIS REGISTRY

**Document ID**: HYP-REG-v1.0  
**Effective Date**: 2026-11-01  
**Auditor / Author**: Hermes Quantitative Research Platform  
**Target Timeframe**: M1 Intraday  
**Target Frequency**: 5+ trades per active day  
**Target Reward-to-Risk**: 0.50R to 0.80R (High Win Rate Design)  

---

## 1. HYPOTHESIS 1 (H1): LIQUIDITY SWEEP AND RECLAIM

### A. Economic Rationale
Retail and breakout algorithms cluster stop-loss orders immediately above recent swing highs and below swing lows. Institutional market makers intentionally drive price through these resting stop clusters to absorb volume without moving the average entry price against themselves. Once liquidity is absorbed, buying/selling pressure vanishes and price snaps back inside the prior range.

### B. Mathematical Features
- `rolling_high_N`, `rolling_low_N` ($N = 15, 30\text{ bars}$).
- Sweep Depth: $D_{\text{sweep}} = \text{High} - \text{rolling\_high}_N$ (Long: $\text{rolling\_low}_N - \text{Low}$).
- Reclaim Speed: Number of bars $k \le 3$ for close to re-enter the prior boundary.
- Rejection Wick Ratio: $\text{Wick} / \text{Candle Range} \ge 0.40$.

### C. Execution Specifications
- **Long Side (Sweep of Lows)**:
  - Condition: Bar $t$ pierces below `rolling_low_N` by $\ge 0.5 \times \text{ATR}$, but closes back ABOVE `rolling_low_N` within 1–2 bars with a lower wick $\ge 40\%$.
  - Entry: Market Buy at close of reclaim bar (at Ask).
  - Stop Loss: Extreme low of the sweep wick $- \$0.30$.
  - Take Profit: Asymmetric target at **0.60R, 0.70R, or 0.80R**.
  - Time Exit: Force close after **5, 10, or 15 minutes** if neither SL nor TP is hit.
- **Short Side (Sweep of Highs)**:
  - Condition: Bar $t$ pierces above `rolling_high_N` by $\ge 0.5 \times \text{ATR}$, but closes back BELOW `rolling_high_N` within 1–2 bars with an upper wick $\ge 40\%$.
  - Entry: Market Sell at close of reclaim bar (at Bid).
  - Stop Loss: Extreme high of the sweep wick $+ \$0.30$.
  - Take Profit: Asymmetric target at **0.60R, 0.70R, or 0.80R**.
  - Time Exit: Force close after **5, 10, or 15 minutes**.

### D. Expected Market Regime & Falsification Condition
- **Optimal Regime**: Ranging / Normal Volatility sessions (Tokyo and Mid-Day London).
- **Falsification Condition**: Reject if Out-of-Sample Win Rate $< 68.0\%$ or Net Expectancy after $\$0.47$ friction $< +0.10\text{ R}$.

---

## 2. HYPOTHESIS 2 (H2): INTRADAY ROLLING MEAN REVERSION

### A. Economic Rationale
On ultra-short intraday horizons (M1), aggressive market orders temporarily deplete local order book depth, creating extreme price displacement from short-term VWAP/EMA. As market makers replenish passive quotes, high-frequency price action reverts back toward the rolling equilibrium price.

### B. Mathematical Features
- Normalized Z-Score of Price: $Z = \frac{Close - \text{EMA}_{20}}{\sigma_{20}}$.
- Relative Volume Surge: $\text{Volume} / \text{VolumeSMA}_{20} \ge 2.0$.
- RSI(7) Extreme: $\text{RSI} > 80$ (Overbought) or $\text{RSI} < 20$ (Oversold).

### C. Execution Specifications
- **Long Side**:
  - Condition: Price displacement $Z \le -2.2$ AND $\text{RSI}_7 < 20$ with subsequent candle closing positive.
  - Entry: Market Buy at Ask.
  - Stop Loss: Local swing low $- \$0.40$ (Baseline 1.0R).
  - Take Profit: Quick snap target at **0.50R or 0.60R** (near $\text{EMA}_{20}$).
  - Time Exit: **3 or 5 minutes** (ultra-short holding period).
- **Short Side**:
  - Condition: Price displacement $Z \ge +2.2$ AND $\text{RSI}_7 > 80$ with subsequent candle closing negative.
  - Entry: Market Sell at Bid.
  - Stop Loss: Local swing high $+ \$0.40$ (Baseline 1.0R).
  - Take Profit: Quick snap target at **0.50R or 0.60R**.
  - Time Exit: **3 or 5 minutes**.

### D. Expected Market Regime & Falsification Condition
- **Optimal Regime**: Low-to-moderate directional trend; high tick-volume consolidation.
- **Falsification Condition**: Reject if OOS Win Rate $< 70.0\%$ (required to overcome negative RR asymmetry) or Net Expectancy $< +0.10\text{ R}$.

---

## 3. HYPOTHESIS 3 (H3): FAILED BREAKOUT (TRAP REVERSAL)

### A. Economic Rationale
Momentum breakout strategies trigger entry when price breaks a multi-session consolidation or opening range. When institutional volume fails to support the breakout, aggressive trap sellers/buyers reverse the position, initiating a fast liquidation cascade in the opposite direction.

### B. Mathematical Features
- Range High / Low of preceding 30–60 minutes.
- Breakout Volume vs Retest Volume: Breakout bar has high volume, but subsequent bar immediately records negative delta / rejection.
- Displacement failure: Candle breaks level, but fails to hold and closes $> 50\%$ back inside range.

### C. Execution Specifications
- **Long Side (Bear Trap Reversal)**:
  - Condition: A downward breakout below the 30-minute support closes outside the range, but is immediately followed by a bull engulfing candle that re-enters the range.
  - Entry: Retest Limit Buy at the broken support level $+ \$0.10$.
  - Stop Loss: Low of the fakeout bar $- \$0.30$.
  - Take Profit: **0.70R or 0.80R**.
  - Time Exit: **10 or 15 minutes**.
- **Short Side (Bull Trap Reversal)**:
  - Condition: An upward breakout above 30-minute resistance closes outside, but is immediately followed by a bear candle that re-enters the range.
  - Entry: Retest Limit Sell at the broken resistance level $- \$0.10$.
  - Stop Loss: High of the fakeout bar $+ \$0.30$.
  - Take Profit: **0.70R or 0.80R**.
  - Time Exit: **10 or 15 minutes**.

### D. Expected Market Regime & Falsification Condition
- **Optimal Regime**: London Lunch (11:00–13:00 UTC) and New York Afternoon (17:00–19:00 UTC).
- **Falsification Condition**: Reject if OOS Win Rate $< 68.0\%$ or Profit Factor $< 1.30$.

---

## 4. HYPOTHESIS 4 (H4): MICRO-MOMENTUM CONTINUATION

### A. Economic Rationale
During institutional momentum expansion (e.g. London open, US economic data), large algorithmic execution algorithms (TWAP/VWAP) break order books in a single direction. Shallow pullbacks of 1–2 minutes represent brief liquidity breathers before the next wave of institutional buying/selling drives price forward.

### B. Mathematical Features
- 3 consecutive directional bars with $\text{Body} / \text{Range} > 0.65$.
- Normalized Velocity: $\Delta P_{3\text{m}} \ge 1.5 \times \text{ATR}_{15}$.
- Shallow Retracement: Retracement candle does not exceed 38.2% of the impulse body.

### C. Execution Specifications
- **Long Side**:
  - Condition: Strong 3-bar bullish expansion, followed by 1 shallow consolidation bar that holds above EMA9.
  - Entry: Buy Stop or immediate Market Buy upon high break.
  - Stop Loss: Low of the shallow consolidation bar $- \$0.30$.
  - Take Profit: **0.50R, 0.60R, or 0.70R** (rapid capture of the secondary push).
  - Time Exit: **3 or 5 minutes** (abort if momentum stalls).
- **Short Side**:
  - Condition: Strong 3-bar bearish expansion, followed by 1 shallow consolidation bar that holds below EMA9.
  - Entry: Sell Stop or immediate Market Sell upon low break.
  - Stop Loss: High of the shallow consolidation bar $+ \$0.30$.
  - Take Profit: **0.50R, 0.60R, or 0.70R**.
  - Time Exit: **3 or 5 minutes**.

### D. Expected Market Regime & Falsification Condition
- **Optimal Regime**: London Open (07:00–09:00 UTC) and US Morning Open (13:30–15:30 UTC).
- **Falsification Condition**: Reject if OOS Win Rate $< 68.0\%$ or if average loss exceeds $1.08\text{ R}$ after slippage.
