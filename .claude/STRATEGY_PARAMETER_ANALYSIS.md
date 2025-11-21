# Strategy Parameter Analysis - Multi-Timeframe Breakout

**Date**: 2025-11-20
**Status**: Pre-backtest analysis to avoid redundant metrics
**Issue**: Zero trades found with beta > 1.2, still zero with beta > 1.0

---

## Current Strategy Parameters

### 🚫 Hard Filters (MUST pass or rejected)

1. **Beta > 1.0** (relaxed from 1.2)
   - What it measures: Volatility vs market
   - Rejection rate: ~78% @ beta 1.2, ~60-65% @ beta 1.0

2. **S/R Quality Score >= 60**
   - What it measures: Support/resistance level quality
   - Unknown rejection rate (new feature)

### ✅ Confluence Factors (need minimum 3 of 10)

1. **Weekly uptrend intact** (weekly_strength >= 50)
2. **Daily breakout above resistance**
3. **Volume expansion** (>1.5x average)
4. **Strong weekly trend** (strength >= 75)
5. **Exceptional volume** (>2.0x average)
6. **Very high beta** (>= 1.5)
7. **S/R confluence zone** (2+ levels align)
8. **Outperforming market** (RS > 1.0) ← NEW
9. **RS trend improving/strengthening** ← NEW
10. **Strong sustained outperformance** (RS 90d & 30d > 1.2) ← NEW

---

## 🔴 REDUNDANCY ANALYSIS

### Issue 1: Beta vs Relative Strength - MEASURING SAME THING?

**Beta** = Covariance(stock, market) / Variance(market)
- Measures: **How much stock moves when market moves**
- High beta = stock amplifies market moves (more volatile than market)
- Example: Beta 1.5 = stock moves 50% more than market

**Relative Strength (RS)** = (Stock % change) / (Market % change)
- Measures: **Stock's return performance vs market**
- RS > 1.0 = stock outperforming market (higher returns)
- Example: RS 1.5 = stock returned 50% more than market

**ARE THEY REDUNDANT?**

❌ **NO** - They measure different things:
- **Beta**: Correlation + volatility (can be high beta but negative returns)
- **RS**: Pure performance (can outperform with low beta)

Example:
- Stock A: Beta 1.8, RS 0.7 → Volatile but underperforming
- Stock B: Beta 1.2, RS 1.4 → Moderate volatility but strong outperformance

**VERDICT**: ✅ **KEEP BOTH** - They are complementary, not redundant

---

### Issue 2: ADX vs Beta vs RS - TOO MANY STRENGTH METRICS?

**ADX** (Average Directional Index)
- Measures: **Trend strength** (not direction, not returns)
- ADX > 25 = strong trend (up or down)
- ADX < 20 = weak/sideways trend
- **Does NOT measure volatility or returns**

**Beta**
- Measures: **Volatility vs market** (correlation-based)
- High beta = amplifies market moves

**RS**
- Measures: **Return performance vs market**
- RS > 1.0 = beating market

**ARE THEY REDUNDANT?**

❌ **NO** - All three measure DIFFERENT things:

| Metric | Measures | Example |
|--------|----------|---------|
| ADX | Trend strength | Stock in strong uptrend (ADX 35) |
| Beta | Volatility vs market | Stock moves 1.5x market moves |
| RS | Returns vs market | Stock returned 20% while market 10% |

**HOWEVER**: We don't currently use ADX in our multi-timeframe breakout strategy!

**VERDICT**:
- ✅ **Beta + RS are complementary** (keep both)
- ⚠️ **Consider adding ADX** as a trend strength filter (from adx_dma_scanner.py)

---

## 🎯 Strategy Consultant Opinion

Based on [strategy_consultant.py](agents/backtesting/strategy_consultant.py), the consultant evaluates strategies on:

### Traffic Light System

1. **Performance** 🟢🟡🔴
   - Green: Sharpe >= 1.5 AND return >= 15%
   - Yellow: Sharpe >= 1.0 AND return >= 5%
   - Red: Below yellow thresholds

2. **Risk** 🟢🟡🔴
   - Green: Max DD < 15%
   - Yellow: Max DD < 25%
   - Red: Max DD >= 25%

3. **Robustness** 🟢🟡🔴
   - Checks overfitting risk
   - Validates in-sample vs out-of-sample
   - Evaluates walk-forward stability

4. **Complexity** 🟢🟡🔴
   - Red: Likely overfit (too many parameters)
   - Yellow: Moderate overfitting risk
   - Green: Simple, robust design

### Consultant's Implicit Warnings

From code analysis:
- Flags overfitting if too many parameters
- Requires minimum sample size (backtest_period_years)
- Checks parameter stability across time windows

**OUR STRATEGY**: 10 confluence factors + 4 hard parameters = **14 total parameters**

**CONSULTANT'S LIKELY VERDICT**: 🔴 **High complexity risk**

---

## 📊 Proven Strategy Comparison: ADX + 3-DMA

From [adx_dma_scanner.py](agents/trading/adx_dma_scanner.py):

### Proven Results (12-year backtest)
- **+265% total return**
- **28.24% win rate** (low!)
- **1.681 profit factor** (good)
- **386 trades** (32 trades/year)

### Strategy Parameters (ONLY 4!)
1. Close > 50 DMA
2. Close > 100 DMA
3. Close > 200 DMA
4. ADX > 20

**EXIT**: Close < 50 DMA OR ADX < 10

### Signal Strength Scoring (5 factors)
1. Close > all DMAs by >2%
2. ADX > 25
3. Volume > 2x average
4. DMAs aligned (50>100>200)
5. +DI > -DI by >5

**TOTAL PARAMETERS**: 4 entry + 2 exit + 5 scoring = **11 parameters**

**KEY INSIGHT**: Even this proven strategy has 11 parameters, but:
- ✅ Simple, logical structure
- ✅ Each parameter has clear purpose
- ✅ No redundancy
- ✅ 32 trades/year (practical sample size)

---

## 🔬 OUR STRATEGY ANALYSIS

### Current Parameter Count

**Hard Filters**: 2
- Beta > 1.0
- S/R quality >= 60

**Confluence Factors**: 10
- 7 original + 3 new RS metrics

**Total**: 12 parameters

### Sample Size Problem

**Previous backtest results**:
- 163,496 analyses
- 127,104 beta rejections (78%)
- 36,000+ symbols passed beta
- **TRADES FOUND: 0**

**Root Cause**: NOT sample size (we analyzed 36,000+ instances!)

**Real Issue**: Strategy is **TOO SELECTIVE**

---

## 💡 FUNDAMENTAL STRATEGY PRINCIPLES

Based on consultant code and proven ADX strategy:

### 1. Parameter Efficiency
- ✅ Each parameter must add unique value
- ❌ Avoid measuring same thing multiple ways
- ✅ Simple > Complex (overfitting risk)

### 2. Trade Frequency
- Target: 20-50 trades/year across universe
- Too few trades = overfitting risk
- Too many trades = transaction costs kill returns

### 3. Parameter Independence
- Each metric should measure different aspect:
  - **Trend**: Direction and strength
  - **Momentum**: Rate of change
  - **Volume**: Participation
  - **Structure**: S/R levels
  - **Relative**: vs market/sector

### 4. Logical Filter Hierarchy
1. **Market regime** (bull/bear/sideways)
2. **Stock quality** (beta, RS, liquidity)
3. **Technical setup** (breakout, trend, S/R)
4. **Entry timing** (confluence, volume)

---

## 🎯 RECOMMENDATIONS

### Option A: SIMPLIFY (Consultant-Approved Approach)

**Remove redundant/overlapping metrics:**

1. ❌ **Remove**: "Strong weekly trend" (strength >= 75)
   - **Why**: Already covered by "Weekly uptrend intact" (strength >= 50)
   - **Redundancy**: Same metric, different threshold

2. ❌ **Remove**: "Exceptional volume" (>2.0x)
   - **Why**: Already have "Volume expansion" (>1.5x)
   - **Redundancy**: Same metric, stricter threshold

3. ❌ **Remove**: "Very high beta" (>= 1.5)
   - **Why**: Already filtering for beta > 1.0 as hard filter
   - **Redundancy**: Double-dipping on beta

4. ❌ **Remove**: "Strong sustained outperformance" (RS 90d & 30d > 1.2)
   - **Why**: Already have "Outperforming market" (RS > 1.0)
   - **Redundancy**: Same metric, stricter threshold

**SIMPLIFIED CONFLUENCES** (6 factors):
1. Weekly uptrend intact
2. Daily breakout above resistance
3. Volume expansion (>1.5x)
4. S/R confluence zone (2+ levels)
5. Outperforming market (RS > 1.0)
6. RS trend improving/strengthening

**New minimum**: 2-3 of 6 (instead of 3 of 10)

### Option B: RELAX THRESHOLDS (User's Original Instinct)

**Keep all 10 confluences, but lower minimums:**

1. ✅ Beta > 1.0 (DONE)
2. ✅ S/R quality >= 50 (from 60)
3. ✅ Min confluences = 2 (from 3)

### Option C: ADD ADX FILTER (Proven Strategy Approach)

**Replace beta/RS complexity with simple ADX:**

1. ❌ Remove beta filter
2. ❌ Remove RS metrics
3. ✅ Add ADX > 20 (strong trend requirement)
4. ✅ Keep: breakout, volume, S/R, weekly trend

**Rationale**: ADX proven in 12-year backtest (+265% return)

### Option D: HYBRID (Best of All Worlds)

**Core filters** (must pass):
1. ADX > 20 (trend strength)
2. RS 30-day > 0.8 (not underperforming)
3. Volume > 1.0x average (liquid)

**Confluences** (need 2 of 5):
1. Weekly uptrend intact
2. Daily breakout above resistance
3. Volume expansion (>1.5x)
4. S/R confluence zone
5. RS trend improving

**Total parameters**: 3 filters + 5 confluences = **8 parameters** (down from 14)

---

## 🚦 DECISION MATRIX

| Option | Pros | Cons | Expected Trades |
|--------|------|------|-----------------|
| **A: Simplify** | Removes redundancy, consultant-approved | May still be too strict | 5-20/year |
| **B: Relax** | Quick fix, keeps all logic | Doesn't address redundancy | 10-30/year |
| **C: ADX Only** | Proven strategy, simple | Loses beta/RS insights | 30-50/year |
| **D: Hybrid** | Best balance, proven + insights | Requires most code changes | 20-40/year |

---

## 📋 NEXT STEPS

**Before running another backtest**, we should:

1. ✅ **Choose one option** (A, B, C, or D)
2. ✅ **Update strategy code** accordingly
3. ✅ **Run consultant analysis** on small sample (5-10 stocks)
4. ✅ **Review traffic lights** (performance, risk, robustness, complexity)
5. ✅ **If green/yellow**, run full backtest
6. ✅ **If red**, iterate on parameters

**RECOMMENDED**: Start with **Option A (Simplify)** because:
- ✅ Removes obvious redundancies
- ✅ Keeps proven metrics (beta, RS, S/R, volume)
- ✅ Reduces overfitting risk (6 vs 10 confluences)
- ✅ Consultant will likely approve (lower complexity)
- ✅ Fastest to implement (just remove parameters)

---

## ❓ QUESTION FOR USER

**Which option do you prefer?**

A. Simplify (remove 4 redundant confluences, keep 6)
B. Relax (lower all thresholds)
C. ADX Only (switch to proven ADX+DMA strategy)
D. Hybrid (combine ADX + simplified RS/beta)

**Or do you want to see the consultant's analysis first** on a small sample (e.g., 10 stocks from NIFTY 50) before deciding?