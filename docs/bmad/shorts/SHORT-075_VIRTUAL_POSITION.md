# SHORT-075: Virtual Position Dataclass

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Paper Trading

## Problem
Need structured position records with real-time P&L calculation.

## Solution
VirtualPosition dataclass with computed properties for value and P&L.

## Implementation

### Fields
- `symbol`: Stock symbol
- `quantity`: Number of shares
- `entry_price`: Entry price per share
- `entry_time`: Entry timestamp
- `current_price`: Latest market price

### Computed Properties
- `current_value`: Current position value
- `pnl`: Absolute profit/loss
- `pnl_pct`: Percentage profit/loss

### API

```python
from src.paper_trading.virtual_account import VirtualPosition

position = VirtualPosition(
    symbol="RELIANCE",
    quantity=10,
    entry_price=2500.0,
    entry_time=datetime.now()
)

# Update price
position.current_price = 2600.0

# Access P&L
print(f"P&L: {position.pnl}")  # 1000.0
print(f"P&L%: {position.pnl_pct}")  # 4.0
```

## Test Requirements
- Dataclass creation
- Property calculations
- Price updates
- P&L accuracy
- Edge cases

## Dependencies
- datetime

## Acceptance Criteria
- ✅ Structured position data
- ✅ Computed P&L properties
- ✅ Real-time updates
- ✅ Clean API
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/paper_trading/virtual_account.py` (lines 12-35)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_virtual_account.py` (to create)
