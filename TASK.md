TASK.md — LOCKED RESEARCH MANDATE

Project: Hermes Quantitative Research
Primary Instrument: XAUUSD
Research Mode: Autonomous Quantitative Discovery
Mission Status: LOCKED
Execution Permission: Research Only
Mandate Version: 1.0

---

SECTION 1 — IMMUTABLE MISSION

Primary Objective

Discover one or more statistically defensible, reproducible, and economically viable trading methods for XAUUSD through unrestricted quantitative exploration.

The research must not be restricted to conventional trading indicators, technical analysis frameworks, or predefined strategies.

Hermes is explicitly authorized to discover:

- New mathematical features.
- Unconventional price relationships.
- Conditional market behaviors.
- Statistical anomalies.
- Nonlinear relationships.
- Multi-variable interactions.
- Temporal and volatility patterns.
- Market regime-dependent opportunities.
- Previously unexplored combinations of market variables.

The objective is not to reproduce an existing trading strategy.

The objective is to discover whether the historical market data contains exploitable statistical relationships that survive rigorous validation.

Locked Constraints

The following constraints cannot be changed autonomously:

1. The primary research instrument remains XAUUSD.
2. The primary mission remains statistical edge discovery.
3. The research must remain evidence-based.
4. Out-of-sample validation is mandatory.
5. Transaction costs must be considered.
6. Rejected experiments must be preserved.
7. No live trading is permitted.
8. No research result may be represented as guaranteed future profitability.

Changing these constraints requires explicit authorization from the user.

Do not reinterpret silence as permission.

---

SECTION 2 — DATA RESEARCH

Initial Data Sources

Preferred research source:

- Dukascopy historical XAUUSD data.

Additional validation source:

- Actual broker historical data through MT5.

Potential datasets:

- M1 OHLC.
- Bid/Ask prices.
- Historical tick data.
- Tick volume.
- Historical spread.
- Additional external variables where reliable historical timestamps are available.

Do not assume that all datasets are available.

First inspect the existing environment, files, datasets, and research infrastructure.

Never download duplicate datasets without checking existing files.

Data Integrity Requirements

Before research begins, inspect:

- Missing timestamps.
- Duplicate records.
- Invalid OHLC relationships.
- Unexpected gaps.
- Timezone consistency.
- Daylight-saving transitions.
- Spread anomalies.
- Price precision.
- Source inconsistencies.
- Historical symbol specification changes.

Never silently repair data.

Document every transformation and preserve the original raw data.

Separate different data providers rather than blindly merging their price series.

---

SECTION 3 — RESEARCH METHODOLOGY

Phase 0: Environment Reconnaissance

Inspect the available system.

Determine:

- Available datasets.
- Data formats.
- Historical coverage.
- Existing Python libraries.
- CPU and RAM constraints.
- Existing backtesting infrastructure.
- Existing research documentation.
- Available storage.

Produce an infrastructure assessment before starting expensive experiments.

Do not assume that an intended tool is already installed.

Phase 1: Exploratory Data Analysis

Investigate the statistical properties of XAUUSD.

Research:

- Return distributions.
- Volatility distributions.
- Autocorrelation.
- Conditional volatility.
- Price displacement.
- Candle morphology.
- Range expansion and contraction.
- Wick/body relationships.
- Time-of-day behavior.
- Session interactions.
- Trend and mean-reversion characteristics.
- Market regime changes.
- Intraday seasonality.

Do not restrict analysis to these categories.

Discover additional research dimensions when justified by the data.

Phase 2: Feature Discovery

Create and investigate new mathematical features.

Possible approaches:

- OHLC transformations.
- Rolling statistical features.
- Normalized price displacement.
- Volatility-adjusted features.
- Candle sequence features.
- Time-based features.
- Conditional probability features.
- Nonlinear feature combinations.
- Information-theoretic features.
- Unsupervised regime representations.

Every feature must have:

- A mathematical definition.
- An explicit calculation method.
- A defined information timestamp.
- A reproducible implementation.

Prevent future information from entering predictive features.

Do not create features merely because they produce attractive backtest results.

Phase 3: Hypothesis Discovery

Generate testable hypotheses.

Each hypothesis must define:

1. The independent variables.
2. The observed market condition.
3. The prediction target.
4. The observation horizon.
5. The expected relationship.
6. The null hypothesis.
7. The statistical test.
8. The potential trading interpretation.

Examples:

- Does normalized Asia session range contain information about London session returns?
- Does extreme wick displacement predict short-term mean reversion?
- Does volatility contraction precede statistically significant range expansion?
- Does a particular sequence of returns contain predictive information about future direction?
- Does a combination of temporal and volatility features outperform individual features?

These are research questions, not established trading rules.

Phase 4: Statistical Discovery

Use appropriate statistical methods.

Potential methods include:

- Pearson correlation.
- Spearman correlation.
- Kendall correlation.
- Mutual information.
- Conditional probability.
- Logistic regression.
- Time-series analysis.
- Hypothesis testing.
- Bootstrap analysis.
- Information-theoretic analysis.
- Clustering.
- Change-point detection.
- Tree-based models.
- Other suitable statistical or machine learning techniques.

Choose methods based on the research question.

Do not apply every statistical method indiscriminately.

Account for:

- Autocorrelation.
- Heteroskedasticity.
- Non-independent observations.
- Multiple hypothesis testing.
- Sample size.
- Statistical uncertainty.

Correlation alone is never sufficient evidence of a trading edge.

Phase 5: Trading Rule Extraction

Convert promising findings into deterministic rules.

A strategy must specify:

- Entry conditions.
- Entry timing.
- Direction.
- Exit conditions.
- Stop-loss.
- Take-profit or alternative exit logic.
- Position sizing assumptions.
- Maximum holding period.
- Trading session restrictions.
- Spread restrictions.
- Conditions for avoiding trades.

The strategy must be implementable without subjective LLM interpretation.

No ambiguous entry conditions are permitted.

Phase 6: Backtesting

Use a reproducible backtesting engine.

Every backtest must account for:

- Bid/Ask execution.
- Spread.
- Commission where applicable.
- Slippage assumptions.
- Realistic entry timing.
- Stop-loss and take-profit execution.
- Intrabar ambiguity.
- Consecutive positions.
- Position sizing.
- Trading session boundaries.

When M1 data cannot establish the order of intrabar events, use tick data where available or adopt a conservative execution assumption.

Never assume the best possible execution when the actual execution sequence is unknown.

Phase 7: Robustness Validation

A promising strategy must undergo:

- Chronological training and validation splits.
- Locked out-of-sample evaluation.
- Walk-forward testing.
- Parameter sensitivity analysis.
- Market regime analysis.
- Transaction cost stress testing.
- Bootstrap or Monte Carlo analysis.
- Independent feed comparison where possible.

Correct for multiple testing and selection bias.

Do not repeatedly optimize against the final holdout dataset.

If the holdout is exposed to iterative strategy selection, it is no longer an untouched final test.

Preserve a final test set or use a new independent evaluation period.

---

SECTION 4 — PERFORMANCE EVALUATION

Do not optimize solely for win rate.

Evaluate every strategy using:

1. Win rate.
2. Average win.
3. Average loss.
4. Average reward-to-risk.
5. Expectancy in R.
6. Profit factor.
7. Maximum drawdown.
8. Recovery factor.
9. Trade frequency.
10. Consecutive losses.
11. Equity curve stability.
12. Net performance after transaction costs.
13. Out-of-sample performance.
14. Parameter stability.
15. Regime robustness.

Primary objective:

Find positive and robust net expectancy with acceptable drawdown and sufficient statistical evidence.

High win rate is desirable when it does not come at the expense of negative expectancy or unacceptable tail risk.

Do not impose an arbitrary win-rate threshold that causes the discovery process to discard stronger strategies.

---

SECTION 5 — DISCOVERY CLASSIFICATION

Every candidate must receive one of the following statuses.

DISCOVERED

A statistically interesting relationship has been identified.

It is not yet an established trading edge.

PROMISING

The relationship has survived initial testing and warrants further investigation.

VALIDATED

The candidate has passed predefined out-of-sample and robustness criteria.

REJECTED

The hypothesis failed statistical, economic, or robustness requirements.

INCONCLUSIVE

The evidence is insufficient to accept or reject the hypothesis.

Never upgrade a candidate's status without satisfying its criteria.

---

SECTION 6 — RESEARCH RECORDS

Every experiment must receive a unique identifier.

Example:

EXP-2026-000001

Store:

- Experiment ID.
- Research question.
- Hypothesis.
- Dataset fingerprint.
- Data source.
- Date range.
- Feature definitions.
- Parameters.
- Code version.
- Statistical methods.
- Results.
- Validation results.
- Limitations.
- Final classification.

Preserve failed experiments.

Never overwrite historical research records.

Maintain a discovery registry to prevent unnecessary repetition of identical experiments.

---

SECTION 7 — RESEARCH OUTPUT

Produce the following documents:

A. Market Research Report

Summarize market characteristics, statistical distributions, and interesting relationships.

B. Feature Discovery Registry

Document newly discovered mathematical features and their definitions.

C. Experiment Registry

Track all experiments, including rejected hypotheses.

D. Strategy Candidates

Document promising deterministic strategies and their performance.

E. Validation Reports

Provide detailed out-of-sample, walk-forward, and robustness results.

F. Final Research Report

Identify:

- Strongest surviving candidate.
- Statistical evidence.
- Net expectancy.
- Win rate.
- Reward-to-risk.
- Drawdown.
- Sample size.
- Market conditions.
- Known limitations.
- Remaining uncertainties.

If no candidate passes validation, explicitly report that no validated edge has been found.

Do not manufacture a successful result to complete the task.

---

SECTION 8 — RESOURCE AND TOKEN POLICY

Perform numerical processing locally.

Use Python for computation and statistical testing.

Use LLM reasoning for hypothesis design, research decisions, and interpretation.

Never send millions of raw candles into the model context.

Use compact experiment summaries.

Cache expensive computations.

Avoid duplicate experiments.

Use model escalation only when the complexity of the research justifies it.

Preserve research continuity through persistent experiment records rather than relying exclusively on conversation history.

---

SECTION 9 — PERMISSION BOUNDARIES

Authorized:

- Read approved historical datasets.
- Analyze data.
- Generate research scripts.
- Run offline experiments.
- Create reports.
- Maintain research databases.
- Improve local research infrastructure within the approved workspace.

Not authorized:

- Place live orders.
- Connect to live order execution.
- Modify broker accounts.
- Access or transfer funds.
- Deploy autonomous live trading.
- Delete original market datasets.
- Modify locked research objectives.
- Expand filesystem or external account permissions without authorization.

Any proposed change to the mission, safety boundaries, or data-access permissions requires explicit user approval.

---

SECTION 10 — DEFINITION OF SUCCESS

The mission is not successful merely because a profitable backtest exists.

Success means:

1. A reproducible statistical relationship has been discovered.
2. It can be translated into deterministic trading rules.
3. Its economic performance remains positive after realistic transaction costs.
4. It survives independent out-of-sample testing.
5. It demonstrates reasonable robustness across different market conditions.
6. Its risks and limitations are documented.
7. Its findings can be independently reproduced.

If no strategy meets these standards, the correct conclusion is:

NO ROBUST EDGE IDENTIFIED YET.

Continue research without compromising the methodology.

---

FINAL LOCK

This document defines the authorized research mandate.

Hermes may autonomously determine HOW to investigate the market.

Hermes may not autonomously redefine WHAT constitutes success.

Exploration is flexible.
Methodology is accountable.
Validation is mandatory.
Live execution is prohibited.

Find the edge. Prove the edge. Attempt to destroy the edge. Only then report the edge.