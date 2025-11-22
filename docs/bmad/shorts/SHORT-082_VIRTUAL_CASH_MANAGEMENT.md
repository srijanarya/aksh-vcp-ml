# SHORT-082: Virtual Cash Management

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Paper Trading

## Problem
Accurate cash tracking is critical for realistic paper trading simulation.

## Solution
Cash balance tracking with deductions on buy and additions on sell.

## Implementation

### Features
1. **Initial Capital**: Starting cash amount
2. **Buy Deductions**: Cost = quantity × price
3. **Sell Additions**: Proceeds = quantity × price
4. **Validation**: Prevent buying with insufficient cash

### API

```python
account = VirtualAccount(initial_capital=100000)

print(f"Initial Cash: {account.cash}")  # 100000

# Buy reduces cash
account.buy("RELIANCE", 10, 2500.0)
print(f"After Buy: {account.cash}")  # 75000

# Sell increases cash
account.sell("RELIANCE", 2600.0)
print(f"After Sell: {account.cash}")  # 101000
```

## Test Requirements
- Initial capital setup
- Cash deduction on buy
- Cash addition on sell
- Insufficient funds handling
- Balance accuracy

## Dependencies
- SHORT-074 (Virtual Account Core)
- SHORT-076 (Virtual Buy Order)
- SHORT-077 (Virtual Sell Order)

## Acceptance Criteria
- ✅ Tracks cash accurately
- ✅ Prevents overdraft
- ✅ Updates on trades
- ✅ Maintains balance
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/paper_trading/virtual_account.py` (lines 47-48, 74-79, 125-127)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_virtual_account.py` (to create)
