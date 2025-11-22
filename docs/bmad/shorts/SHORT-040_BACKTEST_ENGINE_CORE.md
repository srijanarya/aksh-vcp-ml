# SHORT-040: Backtest Engine Core

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Need a robust backtesting engine to validate VCP strategies against historical data with accurate cost and slippage modeling.

## Solution
Core backtesting engine with position management, P&L tracking, and performance metrics.

## Implementation

### Components
1. **BacktestEngine**: Main engine class
2. **Trade**: Trade record dataclass
3. **BacktestResult**: Result container

### Key Features
- Position management (max 5 concurrent)
- Stop loss and target tracking
- Equity curve generation
- Performance metrics calculation
- Cost and slippage integration

### API

```python
from src.backtest.backtest_engine import BacktestEngine, BacktestResult

# Initialize
engine = BacktestEngine(
    initial_capital=100000,
    cost_calculator=cost_calc,
    slippage_simulator=slippage_sim
)

# Run backtest
result = engine.run(
    data=ohlc_df,
    signals=buy_signals,
    stop_loss_pct=2.0,
    target_pct=4.0
)

# Access results
print(result.metrics['win_rate'])
print(result.equity_curve)
```

## Test Requirements
- Position entry validation
- Stop loss execution
- Target hit execution
- Equity tracking
- Metrics calculation
- Cost integration
- Edge cases (no capital, max positions)

## Dependencies
- pandas
- numpy
- src.costs.cost_calculator (SHORT-034)
- src.costs.slippage_simulator (SHORT-037)

## Acceptance Criteria
- ✅ Handles multiple concurrent positions
- ✅ Calculates accurate P&L
- ✅ Generates equity curve
- ✅ Computes performance metrics
- ✅ Integrates costs and slippage
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py`
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
