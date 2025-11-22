# SHORT-078: Virtual Price Updates

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Paper Trading

## Problem
Need to update position prices in real-time for accurate P&L calculation.

## Solution
Price update method that syncs positions with latest market prices.

## Implementation

### Features
1. **Bulk Updates**: Update multiple positions at once
2. **Selective Updates**: Only updates if symbol in prices dict
3. **Real-time P&L**: Positions automatically recalculate P&L

### API

```python
# Hold positions
account.buy("RELIANCE", 10, 2500.0)
account.buy("TCS", 5, 3500.0)

# Update prices from market data
prices = {
    "RELIANCE": 2600.0,
    "TCS": 3600.0
}
account.update_prices(prices)

# P&L automatically updated
for symbol, position in account.positions.items():
    print(f"{symbol} P&L: {position.pnl}")
```

## Test Requirements
- Single position update
- Multiple position updates
- Missing symbol handling
- P&L recalculation
- Edge cases

## Dependencies
- SHORT-074 (Virtual Account Core)
- SHORT-075 (Virtual Position)

## Acceptance Criteria
- ✅ Updates position prices
- ✅ Handles multiple symbols
- ✅ Skips missing symbols
- ✅ Triggers P&L recalc
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/paper_trading/virtual_account.py` (lines 141-150)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_virtual_account.py` (to create)
