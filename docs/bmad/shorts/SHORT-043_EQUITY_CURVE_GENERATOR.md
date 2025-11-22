# SHORT-043: Equity Curve Generator

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Need to track portfolio value over time to visualize performance and calculate drawdowns.

## Solution
Equity curve tracking that combines cash and position values on each bar.

## Implementation

### Features
1. **Real-time Tracking**: Updates every bar
2. **Combined Value**: Cash + open positions
3. **Pandas Series Output**: Easy plotting
4. **Date Indexing**: Time-series ready

### API

```python
# Generate during backtest
result = engine.run(data, signals)

# Access equity curve
equity_curve = result.equity_curve
equity_curve.plot()  # Visualize performance
```

## Test Requirements
- Accurate equity calculation
- Proper date indexing
- Open position value tracking
- Empty portfolio handling
- Time-series format validation

## Dependencies
- SHORT-040 (Backtest Engine Core)
- SHORT-041 (Position Manager)

## Acceptance Criteria
- ✅ Calculates equity correctly
- ✅ Includes open positions
- ✅ Maintains date index
- ✅ Returns pandas Series
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py` (lines 177-185, 94-95, 102)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
