# SHORT-036: F&O Cost Calculator

**Parent**: FX-004 (Cost Calculator)
**Estimated Effort**: 2 hours
**Priority**: HIGH
**Status**: ✅ COMPLETE

## Objective

Implement F&O cost calculator with flat brokerage and different cost structure.

## Acceptance Criteria

- [x] AC-1: Calculate flat brokerage (₹20 per order)
- [x] AC-2: Calculate STT (0.0625% on sell side for options)
- [x] AC-3: Calculate transaction charges, GST (0.053% total)
- [x] AC-4: Handle futures vs options differences
- [x] AC-5: Test coverage ≥ 95%

## Implementation

**File**: `/Users/srijan/Desktop/aksh/src/costs/cost_calculator.py`

Implementation exists in `CostCalculator.calculate_fno_cost()`.

## Definition of Done

- [x] All tests passing
- [x] Code coverage ≥ 95%
- [x] Documentation complete
- [x] Code reviewed
- [x] Integrated with system

---

**Completed**: November 19, 2025
**Test Coverage**: Verified via test_costs_and_slippage.py
