# SHORT-046: Trade Record Dataclass

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Backtesting Infrastructure

## Problem
Need structured trade records to store entry, exit, and P&L information for analysis.

## Solution
Trade dataclass with all necessary fields for comprehensive trade tracking.

## Implementation

### Fields
- `symbol`: Stock symbol
- `entry_date`: Entry timestamp
- `entry_price`: Entry price
- `exit_date`: Exit timestamp (optional)
- `exit_price`: Exit price (optional)
- `quantity`: Number of shares
- `pnl`: Absolute profit/loss
- `pnl_pct`: Percentage profit/loss

### API

```python
from src.backtest.backtest_engine import Trade

trade = Trade(
    symbol="RELIANCE.NS",
    entry_date=datetime(2024, 1, 1),
    entry_price=2500.0,
    quantity=40
)

# After exit
trade.exit_date = datetime(2024, 1, 15)
trade.exit_price = 2600.0
trade.pnl = 4000.0
trade.pnl_pct = 4.0
```

## Test Requirements
- Dataclass creation
- Field validation
- Optional field handling
- Data serialization
- Trade list operations

## Dependencies
- None (pure dataclass)

## Acceptance Criteria
- ✅ All required fields present
- ✅ Optional fields work
- ✅ Clean data structure
- ✅ Easy to serialize
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/backtest/backtest_engine.py` (lines 14-25)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_backtest_engine.py` (to create)
