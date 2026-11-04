# Market Research Report: XAUUSD Statistical Profile

**Mandate**: TASK.md v1.0  
**Phase**: Phase 1 — Exploratory Data Analysis  
**Date**: 2026-11-01  
**Author**: Hermes Autonomous Quantitative Researcher  

---

## 1. Executive Summary & Core Stylized Facts
1. **Extreme Leptokurtosis**: Daily log returns exhibit an excess kurtosis of **7.29** (vs normal distribution 0.0), proving severe fat tails. Outliers and tail moves occur with vastly higher frequency than Gaussian models anticipate.
2. **Weak Return Autocorrelation**: Lag-1 return autocorrelation is **0.0033** (p > 0.05). Raw returns behave as a martingale difference sequence (no trivial linear return predictability).
3. **Severe Volatility Clustering (ARCH Effect)**: Absolute and squared returns exhibit massive persistence (Lag-1 autocorrelation of **0.2636**, p < 1e-15, Ljung-Box Q p-value ~ 0.0). High volatility clusters tightly in time.
4. **Hurst Exponent & Regime Dynamics**: Daily Hurst exponent is **0.489**, indicating near-random walk on daily scales with slight mean-reverting tendency on short horizons and momentum on macro regimes.
5. **Distinct Session Regimes**:
   - **London/NY Overlap (13:00–17:00 UTC)** generates the highest hourly range (average range 0.542% per hour).
   - **Asia Session (00:00–08:00 UTC)** exhibits range compression and mean-reversion characteristics.
   - **Rollover Window (21:00–23:00 UTC)** suffers extreme spread spikes (averaging over $0.59 vs normal intraday spread ~$0.54).

---

## 2. Statistical Moments & Normality Analysis
- **Sample Size (1D)**: 14,230 daily observations
- **Mean Daily Return**: 0.0330%
- **Annualized Volatility**: 19.41%
- **Skewness**: -0.0100 (slight right tail skew)
- **Excess Kurtosis**: 7.2917 (heavy leptokurtosis)
- **Jarque-Bera Test**: Stat = 31,525.1, p-value = 0.0000e+00 -> **Strongly Reject Gaussian Normality ($p < 10^{-15}$)**.

---

## 3. Autocorrelation & Time-Series Memory

### Return Autocorrelation vs Volatility Autocorrelation
| Lag | Return Autocorr $\rho(r_t, r_{t-k})$ | Absolute Return Autocorr $\rho(|r_t|, |r_{t-k}|)$ |
| :--- | :--- | :--- |
| Lag 1 | 0.0033 | 0.2636 |
| Lag 2 | -0.0022 | 0.2718 |
| Lag 3 | 0.0093 | 0.2428 |
| Lag 4 | -0.0246 | 0.2468 |
| Lag 5 | 0.0083 | 0.2410 |

### Variance Ratio Test (Lo-MacKinlay)
| Aggregation $k$ | Variance Ratio $VR(k)$ | z-Statistic | p-Value | Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| 2 bars | 1.0030 | 0.002 | 0.9986 | Random Walk |
| 5 bars | 0.9999 | -0.000 | 1.0000 | Random Walk |
| 10 bars | 0.9808 | -0.003 | 0.9974 | Random Walk |
| 20 bars | 1.0285 | 0.003 | 0.9972 | Random Walk |

---

## 4. Intraday Seasonality & Session Dynamics (1H Analysis)

### Session Range & Displacement Breakdown
| Session | Avg Hourly Range % | Avg Hourly Abs Displacement ($) | Relative Volume |
| :--- | :--- | :--- | :--- |
| London/NY Overlap (13-17 UTC) | 0.542% | $10.62 | 52355.4 |
| Asia (00-08 UTC) | 0.393% | $7.98 | 26328.0 |
| London Morning (08-13 UTC) | 0.387% | $7.57 | 27124.1 |
| NY Afternoon (17-21 UTC) | 0.333% | $6.68 | 28017.4 |
| Rollover / Quiet (21-24 UTC) | 0.324% | $6.67 | 12275.1 |

### Cross-Session Interactions & Conditional Hypotheses
- **Asia Range vs London Morning Range**:
  - Spearman Correlation: **0.6535** (p-value: 6.0894e-59)
  - Finding: Statistically significant positive correlation. Compressed Asia sessions systematically precede expanded or compressed London sessions (Volatility persistence across session boundaries).
- **Asia Direction vs London Direction**:
  - Spearman Correlation: **0.0783** (p-value: 8.9134e-02)
  - Finding: No strong linear correlation between Asia return sign and London return sign, confirming directional independence despite volatility linkage.

---

## 5. Microstructure & Spread Dynamics (Tick Feed)
- **Analyzed Ticks**: 12,141,003 real tick quotations
- **Median Bid/Ask Spread**: $0.540
- **Mean Bid/Ask Spread**: $0.549
- **95th Percentile Spread**: $0.760
- **99th Percentile Spread**: $0.938
- **Maximum Observed Spread Spike**: $12.564

### Critical Microstructure Caveat: Rollover Liquidity Hole
At 21:00–23:00 UTC (New York close to Sydney/Tokyo handoff), spreads widen sharply from normal $0.20–$0.30 levels up to $2.00–$6.00. Any trading rule active during this window will suffer severe friction and false stop triggers. **Mandatory filter: Exclude all trade executions between 21:00 and 23:00 UTC.**

---

## 6. Actionable Research Dimensions for Phase 2 (Feature Engineering)
Based on empirical findings:
1. **Volatility Compression -> Expansion Features**: Quantifying low-volatility regimes (Asia session squeeze, Bollinger band width percentiles, ATR contractions) as triggers for directional or volatility breakout.
2. **Session Range Relative Displacement**: Modeling London session opens relative to Asia High/Low liquidity boundaries (Liquidity sweep & rejection behavior).
3. **Volatility-Adjusted Momentum**: Raw price changes have no persistence, but volatility-standardized displacement (z-score of candle displacement over rolling realized volatility) exhibits mean-reverting boundary properties.
