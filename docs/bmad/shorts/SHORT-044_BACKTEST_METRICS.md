# SHORT-044: Backtest Performance Metrics

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Need comprehensive performance metrics to evaluate strategy quality and compare alternatives.

## Solution
Metrics calculator that computes win rate, total return, Sharpe ratio, and max drawdown.

## Implementation

### Metrics Provided
1. **Trade Metrics**
   - Total trades
   - Wins/losses
   - Win rate

2. **Return Metrics**
   - Total P&L
   - Total return %

3. **Risk Metrics**
   - Sharpe ratio
   - Max drawdown

### API

```python
result = engine.run(data, signals)

metrics = result.metrics
print(f"Win Rate: {metrics['win_rate']:.2f}%")
print(f"Total Return: {metrics['total_return_pct']:.2f}%")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
```

## Test Requirements
- Win rate calculation
- Return calculation
- Sharpe ratio computation
- Max drawdown calculation
- Empty trade list handling
- Single trade handling

## Dependencies
- SHORT-040 (Backtest Engine Core)
- SHORT-043 (Equity Curve Generator)

## Acceptance Criteria
- ✅ Calculates all metrics
- ✅ Handles edge cases
- ✅ Uses annualized Sharpe
- ✅ Computes running drawdown
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py` (lines 187-224)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
