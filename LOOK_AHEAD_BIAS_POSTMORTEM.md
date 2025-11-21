# Look-Ahead Bias Post-Mortem & Prevention Guide

**Date**: November 20, 2025
**Issue**: Critical look-ahead bias in Angel One backtest
**Impact**: Invalid backtest results showing impossible entry prices

---

## 📊 What Happened?

### The Bug
Our backtest used **November 1st, 2024 closing prices** as entry points when the backtest was supposed to end on **October 31st, 2024**.

### Evidence
- **NECCLTD**: Showed entry at ₹33.93 (Nov 1 close) instead of ₹30.85 (Oct 31 close)
- **PRUDENT**: Showed entry at ₹3520.50 (Nov 1 close) instead of ₹3110.02 (Oct 31 close)
- This represents using **future information** that wouldn't be available in real trading

---

## 🔍 Root Cause Analysis

### 1. API Behavior Assumption
```python
# We set end_date to "2024-11-01"
end_date = "2024-11-01"

# Angel One API includes this date (inclusive)
# We assumed it would exclude it
```

### 2. No Date Validation
The code never checked if signal dates were within valid backtest period:
```python
# This line gets the LAST close in the data
current_close = data['close'].iloc[-1]  # Could be Nov 1st!
```

### 3. Silent Failure
- The bug produced plausible results (prices existed, just from wrong date)
- No warnings or errors were generated
- Only discovered when comparing with Yahoo Finance data

---

## 🛡️ How to Prevent This

### 1. Immediate Fix Applied
Changed end date from `2024-11-01` to `2024-10-31` in backtest script.

### 2. Validation Framework Created
Created `BacktestValidator` class with checks for:
- Look-ahead bias detection
- Data integrity validation
- Signal timing verification
- Price sanity checks

### 3. Best Practices to Follow

#### Always Use Exclusive End Dates
```python
# BAD - Ambiguous whether end_date is included
data = fetch_data(start="2022-01-01", end="2024-11-01")

# GOOD - Explicitly exclude end date
data = fetch_data(start="2022-01-01", end="2024-10-31")
# OR
data = data[data.index < end_date]  # Explicitly filter
```

#### Validate Signal Timestamps
```python
def generate_signal(data, backtest_end_date):
    signal_date = data.index[-1]

    # ALWAYS CHECK
    if signal_date >= backtest_end_date:
        raise ValueError(f"Look-ahead bias: Signal uses data from {signal_date}")

    return signal
```

#### Use Safety Buffers
```python
from datetime import timedelta

# Subtract 1 day to ensure no leak
safe_end_date = end_date - timedelta(days=1)
```

#### Cross-Validate with Multiple Sources
```python
# Compare prices from different sources
angel_price = get_angel_price(symbol, date)
yahoo_price = get_yahoo_price(symbol, date)

if abs(angel_price - yahoo_price) / yahoo_price > 0.01:  # >1% difference
    log.warning(f"Price mismatch: Angel={angel_price}, Yahoo={yahoo_price}")
```

---

## 📋 Checklist for Future Backtests

Before running any backtest:

- [ ] Verify end date is EXCLUSIVE (data should not include end date)
- [ ] Check that entry signals use data from BEFORE end date
- [ ] Validate entry prices exist in historical data
- [ ] Cross-check a few signals manually with market data
- [ ] Run validator on backtest parameters
- [ ] Test with known data to verify no future leak

After backtest completes:

- [ ] Check that no signals have timestamps >= end date
- [ ] Verify entry prices match historical prices
- [ ] Compare with alternative data source for validation
- [ ] Review any warnings from validator

---

## 🎯 Key Lessons

### 1. Never Trust, Always Verify
Even with SEBI-registered brokers, always validate data independently.

### 2. Explicit is Better than Implicit
Be explicit about whether dates are inclusive or exclusive.

### 3. Silent Bugs are the Worst
Add validation that fails loudly when assumptions are violated.

### 4. Cross-Validation is Essential
Always compare results with alternative data sources.

### 5. Test Edge Cases
Always test the boundary conditions (first day, last day, etc.).

---

## 🔧 Implementation Standards

### For All Future Backtests

1. **Use the Validator**
```python
from src.backtesting.backtest_validator import BacktestValidator

validator = BacktestValidator()
validator.validate_backtest_params(start_date, end_date, symbols)
```

2. **Ensure Exclusive End Dates**
```python
from src.backtesting.backtest_validator import ensure_exclusive_end_date

# Filter data to exclude end date
clean_data = ensure_exclusive_end_date(data, end_date)
```

3. **Add Assertions**
```python
assert signal_date < backtest_end_date, "Look-ahead bias detected!"
assert entry_price in historical_prices, "Entry price not in historical data!"
```

---

## 📊 Impact Assessment

### What This Bug Cost Us
- ~34 minutes of incorrect backtest
- False confidence in 2 invalid signals
- Time spent debugging the discrepancy

### What It Could Have Cost
- **Real money** if we had traded based on these signals
- **30-40% losses** due to wrong entry prices
- **Complete strategy failure** in production

---

## ✅ Action Items Completed

1. ✅ Fixed end date in backtest script
2. ✅ Created validation framework
3. ✅ Documented issue and prevention measures
4. ✅ Added safety checks to prevent recurrence

---

## 🚀 Going Forward

All backtests will now:
1. Use explicit exclusive end dates
2. Run through validation framework
3. Cross-validate with multiple data sources
4. Include timestamp assertions
5. Generate validation reports

This ensures we **never** have look-ahead bias again.

---

**Remember**: In backtesting, paranoia is a feature, not a bug. Always assume your data is trying to trick you until proven otherwise.