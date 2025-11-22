# SHORT-034: Equity Delivery Cost Calculator

**Parent**: FX-004 (Cost Calculator)
**Estimated Effort**: 2 hours
**Priority**: HIGH
**Status**: ✅ COMPLETE

## Objective

Implement equity delivery cost calculator with Indian broker cost structure (STT, transaction charges, GST).

## Acceptance Criteria

- [x] AC-1: Calculate brokerage (% based, zero for delivery)
- [x] AC-2: Calculate STT (0.1% on sell side)
- [x] AC-3: Calculate transaction charges, GST, stamp duty (0.0335% total)
- [x] AC-4: Return total cost
- [x] AC-5: Test coverage ≥ 95%

## Implementation

**File**: `/Users/srijan/Desktop/aksh/src/costs/cost_calculator.py`

Implementation exists in `CostCalculator.calculate_equity_delivery_cost()`.

## Definition of Done

- [x] All tests passing
- [x] Code coverage ≥ 95%
- [x] Documentation complete
- [x] Code reviewed
- [x] Integrated with system

---

**Completed**: November 19, 2025
**Test Coverage**: Verified via test_costs_and_slippage.py
