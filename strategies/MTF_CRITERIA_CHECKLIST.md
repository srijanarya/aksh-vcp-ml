# Multi-Timeframe Breakout Strategy - Complete Criteria

## 🎯 Entry Criteria Summary

**Trade only when you have 4+ of 7 confluences AND all mandatory filters pass**

---

## ⚡ MANDATORY FILTERS (Must Pass All)

### 1. High Beta Requirement
```
✅ Beta > 1.2 vs Nifty 50
❌ Skip if Beta < 1.2
```

**Why:** We need stocks that move significantly more than the market for profit potential.

**How to Check:**
- Scanner calculates automatically
- 1 year of price data vs Nifty
- Beta = Stock Volatility / Market Volatility

---

## 📊 TIMEFRAME ANALYSIS

### Weekly Timeframe (Macro Trend)

**What We Check:**
1. **20-week EMA** (≈4 months)
2. **50-week EMA** (≈1 year)
3. **Price position** relative to EMAs
4. **Structure:** Higher highs and higher lows

**Requirements for PASS:**

**Strong Uptrend (Best):**
```
✅ Current Price > 20 EMA > 50 EMA
✅ Higher highs in last 8 weeks
✅ Higher lows in last 8 weeks
Score: 100/100
```

**Uptrend (Good):**
```
✅ Current Price > 20 EMA
⚠️ 20 EMA may be below 50 EMA
Score: 75/100
```

**Weak Uptrend (Acceptable):**
```
✅ Current Price > 50 EMA
⚠️ Below 20 EMA
Score: 50/100
```

**Downtrend (REJECT):**
```
❌ Price < 50 EMA
Score: 0/100
→ SKIP THIS STOCK
```

**Minimum Required:** Score ≥ 50/100

---

### Daily Timeframe (Breakout Setup)

**What We Check:**
1. **20-day high** (resistance level)
2. **Volume vs 20-day average**
3. **ATR** (Average True Range for volatility)
4. **Price structure**

**Breakout Criteria (ALL must be true):**

```
✅ Current Close > 20-day High (resistance break)
✅ Volume > 1.5x 20-day average (confirmation)
✅ Price within 3 ATR of breakout (not extended)
```

**Example:**
```
20-day High: ₹975
Current Close: ₹982 ✅ (above resistance)
Volume Today: 2.3M
Volume Avg: 1.0M
Volume Ratio: 2.3x ✅ (above 1.5x)
ATR: ₹15
Distance: ₹982 - ₹975 = ₹7
Max Allowed: 3 × ₹15 = ₹45 ✅ (not extended)
```

**If ANY condition fails → NO BREAKOUT → Skip**

---

### 4-Hour Timeframe (Momentum Confirmation)

**What We Check:**
1. **RSI (14)** - Relative Strength Index
2. **MACD** - Moving Average Convergence Divergence
3. **Trend direction**

**Momentum Criteria:**

```
✅ RSI between 50 and 70 (bullish but not overbought)
✅ MACD > Signal Line (momentum positive)
✅ RSI trending up (last 3 bars)
✅ MACD trending up (last 3 bars)
```

**RSI Interpretation:**
- 0-30: Oversold (too weak)
- 30-50: Weak momentum (not good)
- **50-70: IDEAL (strong but room to run)**
- 70-100: Overbought (likely pullback)

**MACD Interpretation:**
- MACD < Signal: Bearish ❌
- **MACD > Signal: Bullish ✅**

**Momentum Score Calculation:**
```
RSI Score: (Current RSI - 50) × 2 (max 40 points)
MACD Score: 30 points if MACD > Signal
Trend Score: 30 points if both increasing
Total: 0-100 points

Pass: Score > 50
```

---

## ✅ CONFLUENCE CHECKLIST

**Minimum Required: 4 of 7**

### Confluence #1: Weekly Uptrend
```
□ Weekly strength score ≥ 50/100
□ Price above key moving averages
□ Upward trending structure
```
**Worth:** 1 confluence point

---

### Confluence #2: Daily Breakout
```
□ Price > 20-day high
□ Clean breakout (decisive move)
□ Not choppy or whipsaw
```
**Worth:** 1 confluence point

---

### Confluence #3: Volume Expansion
```
□ Volume > 1.5x 20-day average
□ Clear accumulation signal
□ Institutional participation
```
**Worth:** 1 confluence point

---

### Confluence #4: 4H Momentum
```
□ RSI 50-70
□ MACD > Signal
□ Both trending up
□ Momentum score > 50/100
```
**Worth:** 1 confluence point

---

### Confluence #5: Strong Weekly Trend
```
□ Weekly strength ≥ 75/100
□ Strong uptrend confirmed
□ Multiple higher highs/lows
```
**Worth:** 1 confluence point (BONUS)

---

### Confluence #6: Exceptional Volume
```
□ Volume > 2.0x average
□ Massive institutional interest
□ Breakout with conviction
```
**Worth:** 1 confluence point (BONUS)

---

### Confluence #7: Very High Beta
```
□ Beta > 1.5 (vs Beta > 1.2 minimum)
□ Exceptional volatility
□ Maximum profit potential
```
**Worth:** 1 confluence point (BONUS)

---

## 🎯 ENTRY LEVEL CALCULATION

### Entry Price
```
Entry = Current Breakout Price
Alternative = Pullback to breakout level (if available)
```

**Timing:**
- **Aggressive:** Enter on breakout candle close
- **Conservative:** Wait for pullback to breakout level + 4H momentum

---

## 🛑 STOP LOSS CALCULATION

**Two Methods - Use MAXIMUM (Looser Stop):**

### Method 1: Swing Low Method
```
1. Find lowest low in last 10 days
2. Subtract 2% (buffer)
3. That's your swing low stop

Example:
Lowest Low (10d): ₹480
Stop: ₹480 × 0.98 = ₹470.40
```

### Method 2: ATR Method
```
1. Calculate 14-day ATR
2. Entry - (1.5 × ATR) = Stop

Example:
Entry: ₹500
ATR: ₹12
Stop: ₹500 - (1.5 × ₹12) = ₹482
```

### Final Stop Loss
```
Stop Loss = MAX(Swing Low Stop, ATR Stop)

Example:
Swing Stop: ₹470
ATR Stop: ₹482
Final Stop: ₹482 ✅ (use higher/looser stop)
```

**Why Looser Stop?**
- High beta stocks are volatile
- Tighter stops = premature stop-outs
- Need room for natural price movement

---

## 🎯 TARGET CALCULATION

**Risk/Reward Based:**

### Standard Target (Most Trades)
```
Risk per share = Entry - Stop Loss
Target = Entry + (2.5 × Risk)

Example:
Entry: ₹500
Stop: ₹482
Risk: ₹18

Target: ₹500 + (2.5 × ₹18) = ₹545
Risk/Reward: 1:2.5
```

### Aggressive Target (Strong Setups)
```
Use when 6+ confluences present
Target = Entry + (3.0 × Risk)

Example:
Target: ₹500 + (3.0 × ₹18) = ₹554
Risk/Reward: 1:3
```

### Partial Profit Strategy
```
Exit 50% at 1:2 (₹536)
→ Move stop to breakeven
→ Let 50% run to 1:3 (₹554)
→ Or trail stop by 1 ATR
```

---

## 💰 POSITION SIZING

### Maximum Risk Per Trade
```
Max Risk = 2% of capital

Capital: ₹100,000
Max Risk: ₹2,000 per trade
```

### Position Size Calculation
```
Risk per share = Entry - Stop
Max Quantity = Max Risk ÷ Risk per share

Example:
Entry: ₹500
Stop: ₹482
Risk per share: ₹18
Max Risk: ₹2,000

Quantity = ₹2,000 ÷ ₹18 = 111 shares
Position Value = 111 × ₹500 = ₹55,500
```

### Position Size Cap
```
Max position = 10% of capital

If position > 10%:
    Cap position at 10%
    Accept less than 2% risk

Example:
₹55,500 > ₹10,000 (10% cap)
Adjusted Quantity = ₹10,000 ÷ ₹500 = 20 shares
Actual Risk = 20 × ₹18 = ₹360 (0.36%)
```

---

## 📋 COMPLETE TRADE EXAMPLE

### SAIL - Complete Analysis

#### Step 1: Beta Check
```
Beta: 1.47 ✅ (> 1.2 threshold)
→ PASS: High beta confirmed
```

#### Step 2: Weekly Analysis
```
Price: ₹145
20 EMA: ₹138
50 EMA: ₹125
Structure: Higher highs, higher lows

Result: Strong Uptrend
Score: 100/100 ✅
Confluence #1: Weekly Uptrend ✅
Confluence #5: Strong Weekly Trend ✅ (score ≥75)
```

#### Step 3: Daily Breakout
```
20-day High: ₹143
Current Close: ₹145 ✅ (breakout!)
Volume Today: 23M
Volume Avg: 10M
Volume Ratio: 2.3x ✅
ATR: ₹3.5
Distance: ₹145 - ₹143 = ₹2
Max: 3 × ₹3.5 = ₹10.5 ✅

Result: Clean Breakout ✅
Confluence #2: Daily Breakout ✅
Confluence #3: Volume Expansion ✅
Confluence #6: Exceptional Volume ✅ (2.0x+)
```

#### Step 4: 4H Momentum
```
RSI: 58 ✅ (50-70 range)
MACD: 0.8 > Signal: 0.5 ✅
Trend: Both increasing ✅
Score: 85/100

Result: Strong Momentum ✅
Confluence #4: 4H Momentum ✅
```

#### Step 5: Total Confluences
```
✅ Weekly Uptrend (1)
✅ Daily Breakout (2)
✅ Volume Expansion (3)
✅ 4H Momentum (4)
✅ Strong Weekly Trend (5)
✅ Exceptional Volume (6)
Total: 6 of 7 confluences

→ EXCELLENT SETUP! TRADE IT!
```

#### Step 6: Entry Levels
```
Entry: ₹145

Stop Loss Calculation:
- Swing Low (10d): ₹137 → Stop: ₹134 (2% below)
- ATR Stop: ₹145 - (1.5 × ₹3.5) = ₹139.75
- Final Stop: ₹139.75 (higher of two)

Risk: ₹145 - ₹139.75 = ₹5.25

Target: ₹145 + (2.5 × ₹5.25) = ₹158.13
Risk/Reward: 1:2.5
```

#### Step 7: Position Sizing
```
Capital: ₹100,000
Max Risk: ₹2,000 (2%)
Risk per share: ₹5.25
Quantity: ₹2,000 ÷ ₹5.25 = 380 shares
Position Value: 380 × ₹145 = ₹55,100

Check 10% cap:
₹55,100 > ₹10,000 (exceeds cap)

Adjusted:
Quantity: ₹10,000 ÷ ₹145 = 68 shares
Actual Risk: 68 × ₹5.25 = ₹357 (0.36%)
```

#### Step 8: Trade Summary
```
Symbol: SAIL
Entry: ₹145
Quantity: 68 shares
Stop: ₹139.75
Target: ₹158.13
Risk: ₹357
Reward: ₹893
R:R: 1:2.5
Confluences: 6/7
Strength: 90/100
```

---

## 🚫 REJECTION CRITERIA

**Immediately SKIP if ANY of these:**

### Hard Rejections (No Trade)
```
❌ Beta < 1.2
❌ Weekly downtrend (score < 50)
❌ No daily breakout
❌ Volume < 1.5x average
❌ Less than 4 confluences
❌ Price extended > 3 ATR
❌ 4H RSI > 70 (overbought)
```

### Soft Warnings (Trade with Caution)
```
⚠️ Only 4 confluences (minimum)
⚠️ Weekly trend weak (50-75 score)
⚠️ 4H momentum weak (50-60 score)
⚠️ Volume just barely > 1.5x
⚠️ Risk/Reward < 1:2
```

---

## ✅ FINAL CHECKLIST

Before entering ANY trade, verify:

**Pre-Trade Checklist:**
```
□ Beta > 1.2 confirmed
□ Weekly trend score ≥ 50
□ Daily breakout confirmed
□ Volume > 1.5x average
□ 4H momentum confirmed (if data available)
□ Minimum 4 confluences present
□ Entry level calculated
□ Stop loss calculated (max of swing/ATR)
□ Target calculated (2.5x risk)
□ Position size within 10% cap
□ Risk within 2% of capital
□ Trade logged in journal
```

**Only trade if ALL boxes checked!**

---

## 📊 Quick Reference Card

```
MANDATORY:
Beta > 1.2

TIMEFRAMES:
Weekly: Uptrend (score ≥50)
Daily: Breakout + Volume 1.5x+
4H: RSI 50-70, MACD bullish

CONFLUENCES:
Minimum 4 of 7

STOPS:
MAX(Swing Low -2%, Entry - 1.5 ATR)

TARGETS:
Entry + (2.5 × Risk)

POSITION:
Max 10% of capital
Max 2% risk per trade

REJECTION:
Weekly downtrend → Skip
No breakout → Skip
Low volume → Skip
< 4 confluences → Skip
```

---

**This is your complete criteria! Print this and keep it next to your desk. Follow it EXACTLY.** 🎯
