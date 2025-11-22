# SHORT-042: Stop Loss & Target Engine

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Backtest needs automatic stop loss and target execution to simulate realistic exit strategies.

## Solution
Exit logic that checks all positions against stop loss and target levels on each bar.

## Implementation

### Features
1. **Stop Loss Check**: Exits on -2% loss
2. **Target Check**: Exits on +4% gain
3. **Multi-Position Handling**: Checks all positions
4. **P&L Calculation**: Accurate profit/loss tracking

### API

```python
# Exit checking (internal method)
engine._check_exits(date, row, stop_loss_pct=2.0, target_pct=4.0)

# Configurable in run()
result = engine.run(
    data=df,
    signals=signals,
    stop_loss_pct=2.0,  # 2% stop loss
    target_pct=4.0      # 4% target
)
```

## Test Requirements
- Stop loss trigger accuracy
- Target trigger accuracy
- Multiple exit handling
- P&L calculation verification
- Edge cases (exact hit, gap through)

## Dependencies
- SHORT-040 (Backtest Engine Core)
- SHORT-041 (Position Manager)

## Acceptance Criteria
- ✅ Triggers stop loss correctly
- ✅ Triggers target correctly
- ✅ Handles multiple exits per bar
- ✅ Calculates accurate P&L
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py` (lines 135-175)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
