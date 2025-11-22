# SHORT-074: Virtual Account Core

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Paper Trading

## Problem
Need realistic paper trading environment to validate strategies before live deployment.

## Solution
VirtualAccount class that simulates real trading with positions and P&L tracking.

## Implementation

### Features
1. **Cash Management**: Track available capital
2. **Position Management**: Hold multiple positions
3. **Trade History**: Record all transactions
4. **Performance Metrics**: Real-time P&L

### API

```python
from src.paper_trading.virtual_account import VirtualAccount

account = VirtualAccount(initial_capital=100000)

# Buy shares
success = account.buy(
    symbol="RELIANCE",
    quantity=10,
    price=2500.0
)

# Sell shares
success = account.sell(
    symbol="RELIANCE",
    price=2600.0
)

# Get performance
perf = account.get_performance()
print(f"Total Return: {perf['total_return_pct']:.2f}%")
```

## Test Requirements
- Account initialization
- Buy order execution
- Sell order execution
- Cash tracking
- Position management
- Performance calculation

## Dependencies
- None (standalone)

## Acceptance Criteria
- ✅ Simulates real trading
- ✅ Tracks cash and positions
- ✅ Records trade history
- ✅ Calculates performance
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/paper_trading/virtual_account.py`
- Tests: `/Users/srijan/Desktop/aksh/tests/test_virtual_account.py` (to create)
