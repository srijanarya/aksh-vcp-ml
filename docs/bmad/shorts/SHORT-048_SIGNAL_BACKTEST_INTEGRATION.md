# SHORT-048: Signal-Backtest Integration

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Need seamless integration between signal generation and backtesting engine.

## Solution
Accept pandas Series of boolean signals aligned with OHLC data index.

## Implementation

### Features
1. **Boolean Signals**: True = buy signal
2. **Index Alignment**: Signals match data index
3. **Flexible Input**: Works with any signal generator

### API

```python
# Generate signals
signals = signal_filter.generate_signals(df)

# Pass to backtest
result = engine.run(
    data=df,
    signals=signals,
    stop_loss_pct=2.0,
    target_pct=4.0
)
```

## Test Requirements
- Signal alignment validation
- Boolean signal handling
- Missing signal dates
- Signal timing accuracy
- Multi-signal testing

## Dependencies
- SHORT-040 (Backtest Engine Core)
- SHORT-028 (Signal Filter)

## Acceptance Criteria
- ✅ Accepts pandas Series
- ✅ Handles boolean signals
- ✅ Aligns with data index
- ✅ Works with signal generators
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py` (lines 62-95)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
