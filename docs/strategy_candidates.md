# Strategy Candidates Registry: Systematic Minute-30 Timing Playbook

**Mandate**: TASK.md v1.0  
**Asset**: XAUUSD (Spot Gold)  
**Timeframe**: M1  
**Dataset Tested**: 648,677 Continuous M1 Candles (2025 In-Sample vs 2026 Out-of-Sample)  
**Transaction Cost Applied**: $0.50 institutional spread per round-trip trade + intrabar pessimistic SL sequence  

---

## 1. Hourly Timing Matrix (:30 Across the 24-Hour Cycle)

| Timing (UTC) | Timing (WIB) | Session Context | Optimal Mode | Win Rate (IS / OOS) | Expectancy | Profit Factor | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **01:30** | **08:30** | Tokyo Open Exhaustion | **Lawan Trend** | 45.5% / 50.9% | +0.05 R | 1.11 | **VALID** |
| **02:30** | **09:30** | Tokyo Trend Acceleration | **Ikut Trend** | 54.9% / 53.6% | **+0.11 R** | **1.29** | **VALID (Best Asia)** |
| 03:30 | 10:30 | Mid-Asia Drift | Lawan Trend | 38.5% / 46.2% | +0.03 R | 1.07 | Inconclusive |
| 04:30 | 11:30 | Asia Lunch | - | - | - | 0.69 | **REJECTED (No Edge)** |
| 05:30 | 12:30 | Late Asia | - | - | - | 1.03 | **REJECTED (No Edge)** |
| 06:30 | 13:30 | Pre-Europe | - | - | - | 1.02 | **REJECTED (No Edge)** |
| 07:30 | 14:30 | Frankfurt Open Trap | - | - | - | 0.96 | **REJECTED (Whipsaw)** |
| 08:30 | 15:30 | London Open Trap | - | - | - | 0.91 | **REJECTED (Whipsaw)** |
| 09:30 | 16:30 | London Initial Push Trap | - | - | - | 0.72 | **REJECTED (False Breakouts)** |
| **10:30** | **17:30** | London Morning Exhaustion | **Lawan Trend** | 45.2% / 51.2% | **+0.14 R** | **1.30** | **VALID (Best London)** |
| **11:30** | **18:30** | London Pre-NY Squeeze | **Lawan Trend** | 54.8% / 49.0% | **+0.12 R** | **1.25** | **VALID (Strong)** |
| 12:30 | 19:30 | Pre-US Data Ambiguity | Lawan Trend | 32.4% / 52.5% | +0.15 R | 1.33 | Inconclusive |
| 13:30 | 20:30 | US Pre-Open Trap | - | - | - | 0.97 | **REJECTED (High Friction)** |
| **14:30** | **21:30** | US Equity Open Momentum | **Ikut Trend** | 48.0% / 45.5% | **+0.06 R** | **1.14** | **VALID (High Volume)** |
| 15:30 | 22:30 | US Post-Open Chop | - | - | - | 0.98 | **REJECTED (No Edge)** |
| **16:30** | **23:30** | London Fix Rebalancing | **Lawan Trend** | 45.2% / 45.1% | **+0.10 R** | **1.19** | **VALID (Institutional)** |
| 17:30 | 00:30 | Post-London Fix Drift | - | - | - | 1.03 | **REJECTED (No Edge)** |
| 18:30 | 01:30 | US Afternoon Chop | - | - | - | 0.96 | **REJECTED (No Edge)** |
| 19:30 | 02:30 | Pre-Close Dead Zone | - | - | - | 0.85 | **REJECTED (No Edge)** |
| **20:30** | **03:30** | NY Final Push into Close | **Ikut Trend** | 46.3% / 44.7% | **+0.07 R** | **1.23** | **VALID** |
| 21:00–23:00 | 04:00–06:00 | Rollover Liquidity Hole | - | - | - | - | **STRICT BLACKLIST (Spread Spikes)** |

---

## 2. Deterministic Execution Rules ("Bersifat Baku")

### Model 1: The "Ikut Trend" (Continuation) Playbook
**Active Windows**: 02:30 UTC (09:30 WIB), 14:30 UTC (21:30 WIB), 20:30 UTC (03:30 WIB).
1. **Pre-Condition**:
   - Measure 30-minute displacement $\Delta P = Close_{29} - Open_{00}$.
   - Minimum displacement requirement: $|\Delta P| \ge \max(0.8 \times \text{ATR}_{60}, \$2.00)$.
2. **Candle Trigger at Minute 29 (1 minute before :30 close)**:
   - For LONG: $Close_{29}$ must finish in the upper 25% of the 30-minute range ($High_{30} - Close_{29} < 0.25 \times (High_{30} - Low_{30})$). Strong bull candle, small upper wick.
   - For SHORT: $Close_{29}$ must finish in the lower 25% of the 30-minute range ($Close_{29} - Low_{30} < 0.25 \times (High_{30} - Low_{30})$). Strong bear candle, small lower wick.
3. **Execution**:
   - Entry: Market order executed at open of minute 30 ($Close_{29}$).
   - Stop Loss: Set at $Open_{00}$ of the current hour ($\pm \$0.50$ spread buffer).
   - Take Profit: Exactly **1.5 : 1 Reward-to-Risk** ($TP = \text{Entry} \pm 1.5 \times \text{Risk}$).
   - Time-Stop: If neither SL nor TP is triggered by minute 59, market exit at close of minute 59.

### Model 2: The "Lawan Trend" (Reversal) Playbook
**Active Windows**: 01:30 UTC (08:30 WIB), 10:30 UTC (17:30 WIB), 11:30 UTC (18:30 WIB), 16:30 UTC (23:30 WIB).
1. **Pre-Condition**:
   - Measure 30-minute displacement $|\Delta P| \ge \max(0.8 \times \text{ATR}_{60}, \$2.00)$.
2. **Candle Trigger at Minute 29**:
   - For SHORT (Fade Bullish Push): The bar at minute 29 must show an upper rejection wick $> 30\%$ of the 30-minute range ($High_{30} - Close_{29} > 0.30 \times (High_{30} - Low_{30})$).
   - For LONG (Fade Bearish Push): The bar at minute 29 must show a lower rejection wick $> 30\%$ of the 30-minute range ($Close_{29} - Low_{30} > 0.30 \times (High_{30} - Low_{30})$).
3. **Execution**:
   - Entry: Market order executed at open of minute 30.
   - Stop Loss: Set at the 30-minute extreme ($High_{30} + \$0.50$ for Short; $Low_{30} - \$0.50$ for Long).
   - Take Profit: Exactly **1.5 : 1 Reward-to-Risk**.
   - Time-Stop: If neither SL nor TP is triggered by minute 59, market exit at close of minute 59.
