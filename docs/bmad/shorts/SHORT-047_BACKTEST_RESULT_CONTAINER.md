# SHORT-047: Backtest Result Container

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Need clean container to return backtest results with trades, equity curve, and metrics.

## Solution
BacktestResult dataclass that packages all backtest outputs together.

## Implementation

### Fields
- `trades`: List of Trade objects
- `equity_curve`: Pandas Series with equity over time
- `metrics`: Dict of performance metrics

### API

```python
from src.backtest.backtest_engine import BacktestResult

result = engine.run(data, signals)

# Access components
for trade in result.trades:
    print(f"P&L: {trade.pnl}")

result.equity_curve.plot()
print(result.metrics['sharpe_ratio'])
```

## Test Requirements
- Result creation
- Field access
- Default values
- Type validation
- Integration with engine

## Dependencies
- SHORT-046 (Trade Dataclass)

## Acceptance Criteria
- ✅ Clean result packaging
- ✅ All fields accessible
- ✅ Default factories work
- ✅ Type-safe structure
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py` (lines 28-33)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
