# SHORT-041: Trade Position Manager

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Backtest engine needs sophisticated position management to handle multiple concurrent trades, risk limits, and position sizing.

## Solution
Position management logic embedded in BacktestEngine with configurable position limits.

## Implementation

### Features
1. **Position Limits**: Max 5 concurrent positions
2. **Position Sizing**: 10% of capital per position
3. **Capital Management**: Real-time capital tracking
4. **Risk Controls**: Prevents over-allocation

### API

```python
# Position entry (internal method)
engine._enter_position(date, row)

# Position exit (internal method)
engine._exit_position(trade, exit_date, exit_price)

# Position tracking
current_positions = engine.positions
```

## Test Requirements
- Max position limit enforcement
- Position sizing calculation
- Capital allocation tracking
- Insufficient capital handling
- Position updates

## Dependencies
- SHORT-040 (Backtest Engine Core)

## Acceptance Criteria
- ✅ Enforces max position limits
- ✅ Calculates position sizes correctly
- ✅ Tracks capital accurately
- ✅ Handles insufficient capital
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py` (lines 106-134)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
