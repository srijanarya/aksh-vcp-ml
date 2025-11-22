# SHORT-045: Cost & Slippage Integration

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Backtest must account for realistic trading costs (brokerage, taxes) and slippage to avoid overly optimistic results.

## Solution
Integration points for cost calculator and slippage simulator in entry and exit logic.

## Implementation

### Integration Points
1. **Entry Costs**: Added to capital deduction
2. **Exit Costs**: Subtracted from P&L
3. **Optional Components**: Works without them

### API

```python
from src.costs.cost_calculator import CostCalculator
from src.costs.slippage_simulator import SlippageSimulator

# Initialize with cost models
engine = BacktestEngine(
    initial_capital=100000,
    cost_calculator=CostCalculator(),
    slippage_simulator=SlippageSimulator()
)

# Costs automatically applied
result = engine.run(data, signals)
```

## Test Requirements
- Cost calculation on entry
- Cost calculation on exit
- Works without cost calculator
- Accurate P&L after costs
- Integration with cost components

## Dependencies
- SHORT-040 (Backtest Engine Core)
- SHORT-034 (Equity Delivery Costs)
- SHORT-037 (Spread Slippage)

## Acceptance Criteria
- ✅ Integrates cost calculator
- ✅ Applies costs on entry/exit
- ✅ Works without cost models
- ✅ Accurate P&L calculation
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py` (lines 42, 54, 118-119, 172)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
