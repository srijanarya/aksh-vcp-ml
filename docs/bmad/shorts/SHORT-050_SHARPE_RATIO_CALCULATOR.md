# SHORT-050: Sharpe Ratio Calculator

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Need risk-adjusted return metric to compare strategies with different volatility profiles.

## Solution
Annualized Sharpe ratio calculation using trade returns.

## Implementation

### Formula
```
Sharpe = (mean_return / std_return) * sqrt(252)
```

### Features
1. **Trade-Based**: Uses individual trade returns
2. **Annualized**: Multiplied by sqrt(252)
3. **Edge Cases**: Returns 0 for < 2 trades

### API

```python
result = engine.run(data, signals)
sharpe = result.metrics['sharpe_ratio']

# Higher is better (> 1 is good, > 2 is excellent)
```

## Test Requirements
- Calculation accuracy
- Annualization factor
- Edge case handling
- Multiple trade scenarios
- Negative returns

## Dependencies
- SHORT-044 (Backtest Metrics)

## Acceptance Criteria
- ✅ Calculates Sharpe correctly
- ✅ Annualizes properly
- ✅ Handles edge cases
- ✅ Uses trade returns
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py` (lines 205-207)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
