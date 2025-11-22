# SHORT-051: Max Drawdown Calculator

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Need to measure worst peak-to-trough decline to assess strategy risk.

## Solution
Running max drawdown calculation using equity curve.

## Implementation

### Formula
```
Drawdown = (Equity - RunningMax) / RunningMax * 100
MaxDrawdown = min(Drawdown)
```

### Features
1. **Running Maximum**: Tracks highest equity reached
2. **Percentage Basis**: Relative to peak
3. **Negative Value**: More negative = worse

### API

```python
result = engine.run(data, signals)
max_dd = result.metrics['max_drawdown']

# Example: -15.5 means 15.5% drawdown from peak
```

## Test Requirements
- Calculation accuracy
- Running max tracking
- Percentage conversion
- Edge cases (no drawdown)
- Multiple peaks

## Dependencies
- SHORT-044 (Backtest Metrics)
- SHORT-043 (Equity Curve Generator)

## Acceptance Criteria
- ✅ Calculates max drawdown
- ✅ Uses running maximum
- ✅ Returns percentage
- ✅ Handles edge cases
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py` (lines 209-213)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
