# SHORT-079: Virtual Equity Calculation

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Paper Trading

## Problem
Need total account value (cash + positions) for performance tracking.

## Solution
Equity calculation method that sums cash and current position values.

## Implementation

### Formula
```
Equity = Cash + Sum(Position Values)
Position Value = Current Price × Quantity
```

### API

```python
account = VirtualAccount(initial_capital=100000)

# Make trades
account.buy("RELIANCE", 10, 2500.0)  # -25000
account.update_prices({"RELIANCE": 2600.0})

# Get total equity
equity = account.get_equity()
# equity = 75000 (cash) + 26000 (position) = 101000

print(f"Total Equity: {equity}")
```

## Test Requirements
- Equity with only cash
- Equity with positions
- Multiple positions
- Price impact on equity
- Accuracy verification

## Dependencies
- SHORT-074 (Virtual Account Core)
- SHORT-075 (Virtual Position)

## Acceptance Criteria
- ✅ Calculates total equity
- ✅ Includes cash
- ✅ Includes position values
- ✅ Accurate calculation
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/paper_trading/virtual_account.py` (lines 152-164)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_virtual_account.py` (to create)
