# SHORT-020: Position Cap Enforcer

**Parent**: FX-002 (Kelly Position Sizing)
**Estimated Effort**: 2 hours
**Priority**: HIGH
**Status**: ✅ COMPLETE

## Objective

Implement position cap enforcement to limit single position size to maximum 20% of capital for equity and 4% for F&O, preventing over-concentration regardless of Kelly calculation.

## Acceptance Criteria

- [x] AC-1: Cap equity positions at 20% of capital
- [x] AC-2: Cap F&O positions at 4% of capital
- [x] AC-3: Return min(kelly_fraction, cap)
- [x] AC-4: Handle both instrument types correctly
- [x] AC-5: Test coverage ≥ 95%

## Test Cases

### TC-1: Equity Cap Enforcement
```python
def test_equity_cap():
    enforcer = PositionCapEnforcer()
    assert enforcer.enforce(0.30, "equity") == 0.20  # Capped
    assert enforcer.enforce(0.15, "equity") == 0.15  # Not capped
```

### TC-2: F&O Cap Enforcement
```python
def test_fno_cap():
    enforcer = PositionCapEnforcer()
    assert enforcer.enforce(0.10, "fno") == 0.04  # Capped
    assert enforcer.enforce(0.03, "fno") == 0.03  # Not capped
```

### TC-3: Custom Caps
```python
def test_custom_caps():
    enforcer = PositionCapEnforcer(equity_cap=15.0, fno_cap=3.0)
    assert enforcer.enforce(0.20, "equity") == 0.15
    assert enforcer.enforce(0.05, "fno") == 0.03
```

## Implementation Checklist

- [x] Write all test cases
- [x] Run tests (should FAIL)
- [x] Implement code
- [x] Run tests (should PASS)
- [x] Refactor
- [x] Code coverage ≥ 95%
- [x] Documentation
- [x] Code review

## Dependencies

- SHORT-017 (Kelly Fraction Calculator)

## Implementation

**File**: `/Users/srijan/Desktop/aksh/src/kelly/position_cap_enforcer.py`

```python
class PositionCapEnforcer:
    """Enforce position size caps (20% equity, 4% F&O)"""

    def __init__(self, equity_cap: float = 20.0, fno_cap: float = 4.0):
        """
        Initialize enforcer

        Args:
            equity_cap: Max % of capital in single equity position
            fno_cap: Max % of capital in single F&O position
        """
        self.equity_cap = equity_cap
        self.fno_cap = fno_cap

    def enforce(
        self,
        kelly_fraction: float,
        instrument_type: str = "equity"
    ) -> float:
        """
        Enforce position caps

        Args:
            kelly_fraction: Calculated Kelly fraction
            instrument_type: "equity" or "fno"

        Returns:
            Capped Kelly fraction
        """
        cap = self.equity_cap if instrument_type == "equity" else self.fno_cap
        cap_fraction = cap / 100

        return min(kelly_fraction, cap_fraction)
```

## Definition of Done

- [x] All tests passing
- [x] Code coverage ≥ 95%
- [x] Documentation complete
- [x] Code reviewed
- [x] Integrated with system

---

**Completed**: November 19, 2025
**Implementation Time**: 1.5 hours
**Test Coverage**: 100%
