# COST ACCOUNTING WORKED EXAMPLES: LONG & SHORT TRADES

**Document ID**: COST-ACC-v1.0  
**Effective Date**: 2026-11-01  
**Auditor / Author**: Hermes Quantitative Research Platform  
**Purpose**: Complete arithmetic walkthrough of transaction cost deduction, position sizing, and net R realization for Long and Short trades on XAUUSD.

---

## Example 1: LONG Trade (Target Win Scenario at 0.70 R)

### 1. Setup Parameters:
- **Account Balance**: $2,500.00
- **Risk Budget ($K_{\text{risk}}$)**: **$7.50 (0.30%)**
- **Strategy Signal**: Long Mean Reversion at 14:15 UTC.
- **Reference Bid Price at Signal**: $2,650.00
- **Target RR Ratio**: **0.70 : 1**
- **Nominal Stop Distance**: $2.00 ($20.00 pips)
- **Nominal Stop Loss Level**: $2,648.00

### 2. Execution Friction Inputs:
- **Quoted Bid-Ask Spread ($S$)**: $0.35 per ounce
- **Broker Commission ($C$)**: $7.00 per standard lot round-turn ($0.07 per ounce)
- **Market Entry Slippage ($\sigma_{\text{entry}}$)**: $0.05 (0.5 tick)
- **Exit Slippage on Limit TP**: $0.00 (Passive limit fill)

### 3. Step-by-Step Accounting Walkthrough:

#### A. Entry Execution:
Buyer must cross the spread and buy at the prevailing Ask plus entry slippage:
$$\text{Entry Price} = \text{Bid}_{\text{ref}} + S + \sigma_{\text{entry}} = 2,650.00 + 0.35 + 0.05 = \mathbf{\$2,650.40}$$

#### B. Stop Loss & Risk Distance:
Nominal Stop Loss rests at $2,648.00:
$$D_{\text{SL}} = \text{Entry Price} - \text{SL Price} = 2,650.40 - 2,648.00 = \mathbf{\$2.40\text{ per ounce}}$$

#### C. Position Sizing:
$$\text{Lot Size } (V) = \frac{K_{\text{risk}}}{D_{\text{SL}} \times 100} = \frac{\$7.50}{\$2.40 \times 100} = \frac{7.50}{240} = \mathbf{0.03125\text{ Lots (0.03 Standard Lots / 3.125 oz)}}$$

#### D. Take Profit Price Calculation:
Nominal Target = $0.70\text{ R}$ based on risk distance ($D_{\text{SL}} = \$2.40$):
$$\text{Target Distance} = 0.70 \times D_{\text{SL}} = 0.70 \times \$2.40 = \mathbf{\$1.68}$$
$$\text{Take Profit Price (Bid)} = \text{Entry Price} + \text{Target Distance} = 2,650.40 + 1.68 = \mathbf{\$2,652.08}$$

#### E. Outcome & Settlement at TP Hit:
Price moves up and reaches $2,652.08:
- **Gross Price Move**: $\$2,652.08 - \$2,650.40 = +\$1.68\text{ per ounce}$
- **Gross PnL**:
  $$\text{Gross PnL} = +\$1.68 \times 3.125\text{ oz} = \mathbf{+\$5.2500}$$
- **Broker Commission (Round-Turn)**:
  $$\text{Commission} = \$0.07 \times 3.125\text{ oz} = \mathbf{-\$0.21875}$$
- **Net Dollar PnL**:
  $$\text{Net PnL} = +\$5.2500 - \$0.21875 = \mathbf{+\$5.03125}$$
- **Realized R Multiple**:
  $$\text{Realized R} = \frac{+\$5.03125}{\$7.50} = \mathbf{+0.6708\text{ R}}$$

*(Note: Net realized R is +0.6708 R vs nominal 0.7000 R; the difference of -0.0292 R represents commission and slippage drag).*

---

## Example 2: SHORT Trade (Stop Loss Hit Scenario)

### 1. Setup Parameters:
- **Account Balance**: $2,500.00
- **Risk Budget ($K_{\text{risk}}$)**: **$7.50 (0.30%)**
- **Strategy Signal**: Short Liquidity Sweep at 15:30 UTC.
- **Reference Bid Price at Signal**: $2,655.00
- **Nominal Stop Distance**: $1.50 ($15.00 pips)
- **Nominal Stop Loss Level**: $2,656.50

### 2. Execution Friction Inputs:
- **Quoted Bid-Ask Spread ($S$)**: $0.35 per ounce
- **Broker Commission ($C$)**: $7.00 per standard lot ($0.07 per ounce)
- **Market Entry Slippage ($\sigma_{\text{entry}}$)**: $0.05 (0.5 tick)
- **Stop Execution Slippage ($\sigma_{\text{exit}}$)**: $0.05 (0.5 tick adverse gap fill)

### 3. Step-by-Step Accounting Walkthrough:

#### A. Entry Execution:
Seller sells at prevailing Bid minus entry slippage:
$$\text{Entry Price} = \text{Bid}_{\text{ref}} - \sigma_{\text{entry}} = 2,655.00 - 0.05 = \mathbf{\$2,654.95}$$

#### B. Stop Loss & Risk Distance:
Nominal Stop Loss is set at $2,656.50:
$$D_{\text{SL}} = \text{SL Price} - \text{Entry Price} = 2,656.50 - 2,654.95 = \mathbf{\$1.55\text{ per ounce}}$$

#### C. Position Sizing:
$$\text{Lot Size } (V) = \frac{K_{\text{risk}}}{D_{\text{SL}} \times 100} = \frac{\$7.50}{\$1.55 \times 100} = \frac{7.50}{155} = \mathbf{0.048387\text{ Lots (4.8387 oz)}}$$

#### D. Outcome & Settlement at Stop Loss Hit:
Market drives upward. The Ask price touches the Stop Loss level ($2,656.50$) and triggers a market buy order to cover, suffering $0.05 adverse slippage:
$$\text{Actual Exit Fill Price (Ask)} = \text{SL Price} + \sigma_{\text{exit}} = 2,656.50 + 0.05 = \mathbf{\$2,656.55}$$

- **Gross Price Move**:
  $$\Delta P = \text{Entry} - \text{Exit} = 2,654.95 - 2,656.55 = \mathbf{-\$1.60\text{ per ounce}}$$
- **Gross Loss**:
  $$\text{Gross Loss} = -\$1.60 \times 4.8387\text{ oz} = \mathbf{-\$7.7419}$$
- **Broker Commission (Round-Turn)**:
  $$\text{Commission} = \$0.07 \times 4.8387\text{ oz} = \mathbf{-\$0.3387}$$
- **Total Net Loss**:
  $$\text{Total Net Loss} = -\$7.7419 - \$0.3387 = \mathbf{-\$8.0806}$$
- **Realized R Multiple**:
  $$\text{Realized R} = \frac{-\$8.0806}{\$7.50} = \mathbf{-1.0774\text{ R}}$$

*(Note: Realized loss is -1.0774 R rather than -1.0000 R due to adverse stop-fill slippage and broker commission. This proves why nominal 1R losses are modeled conservatively as -1.05R to -1.08R in our stress simulator).*
