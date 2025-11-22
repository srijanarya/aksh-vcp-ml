# SHORT-049: Capital Tracking System

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Accurate capital tracking is critical to prevent over-allocation and simulate realistic position sizing.

## Solution
Real-time capital tracking with deductions on entry and additions on exit.

## Implementation

### Features
1. **Initial Capital**: Configurable starting amount
2. **Entry Deductions**: Cost + costs
3. **Exit Additions**: Proceeds after costs
4. **Running Balance**: Tracked throughout backtest

### API

```python
engine = BacktestEngine(initial_capital=100000)

# Capital automatically tracked
result = engine.run(data, signals)

# Verify capital usage
final_capital = result.equity_curve.iloc[-1]
```

## Test Requirements
- Initial capital setup
- Capital deduction on entry
- Capital addition on exit
- Insufficient capital handling
- Capital conservation check

## Dependencies
- SHORT-040 (Backtest Engine Core)

## Acceptance Criteria
- ✅ Tracks capital accurately
- ✅ Prevents over-allocation
- ✅ Updates on trades
- ✅ Maintains balance
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py` (lines 52, 56, 80, 124, 174)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
