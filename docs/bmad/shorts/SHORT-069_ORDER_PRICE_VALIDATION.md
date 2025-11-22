# SHORT-069: Order Price Validation

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Order Execution

## Problem
Invalid prices can cause API rejection or unintended trade execution.

## Solution
Price validation that considers order type (LIMIT requires price, MARKET doesn't).

## Implementation

### Validation Rules
1. **LIMIT Orders**: Price must be > 0
2. **MARKET Orders**: Price can be 0 (ignored)
3. **Negative Prices**: Always rejected

### API

```python
# LIMIT order requires valid price
valid = executor.validate_order(
    symbol="RELIANCE",
    quantity=10,
    price=2500.0,
    order_type=OrderType.LIMIT
)  # True

# MARKET order doesn't need price
valid = executor.validate_order(
    symbol="RELIANCE",
    quantity=10,
    price=0.0,
    order_type=OrderType.MARKET
)  # True
```

## Test Requirements
- LIMIT order price validation
- MARKET order price handling
- Zero price with LIMIT rejection
- Negative price rejection
- Valid price acceptance

## Dependencies
- SHORT-060 (Order Validator)
- SHORT-061 (Order Type Enum)

## Acceptance Criteria
- ✅ Validates LIMIT prices
- ✅ Allows zero for MARKET
- ✅ Rejects invalid prices
- ✅ Type-aware validation
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/order_executor/order_executor.py` (lines 76-78)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_order_executor.py` (to create)
