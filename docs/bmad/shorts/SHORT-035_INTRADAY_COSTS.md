# SHORT-035: Intraday Cost Calculator

**Parent**: FX-004 (Cost Calculator)
**Estimated Effort**: 2 hours
**Priority**: HIGH
**Status**: ✅ COMPLETE

## Objective

Implement intraday cost calculator with higher brokerage and lower STT (0.025%).

## Acceptance Criteria

- [x] AC-1: Calculate brokerage (0.03% or ₹20 per trade, whichever lower)
- [x] AC-2: Calculate STT (0.025% on sell side)
- [x] AC-3: Calculate transaction charges, GST (0.0335% total)
- [x] AC-4: Return total cost for round trip
- [x] AC-5: Test coverage ≥ 95%

## Implementation

**File**: `/Users/srijan/Desktop/aksh/src/costs/cost_calculator.py`

Implementation exists in `CostCalculator.calculate_intraday_cost()`.

## Definition of Done

- [x] All tests passing
- [x] Code coverage ≥ 95%
- [x] Documentation complete
- [x] Code reviewed
- [x] Integrated with system

---

**Completed**: November 19, 2025
**Test Coverage**: Verified via test_costs_and_slippage.py
