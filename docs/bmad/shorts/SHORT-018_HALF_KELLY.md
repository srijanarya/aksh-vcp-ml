# SHORT-018: Half-Kelly Implementation

**Parent**: FX-002 (Kelly Position Sizing)
**Estimated Effort**: 2 hours
**Priority**: HIGH
**Status**: ✅ COMPLETE

## Objective

Implement Half-Kelly calculator to provide conservative position sizing by using 50% of the full Kelly fraction, reducing risk while maintaining mathematical edge.

## Acceptance Criteria

- [x] AC-1: Calculate Half-Kelly as exactly 50% of full Kelly fraction
- [x] AC-2: Handle edge cases (zero, negative, very large fractions)
- [x] AC-3: Integration with Kelly Fraction Calculator
- [x] AC-4: Test coverage ≥ 95%

## Test Cases

### TC-1: Basic Half-Kelly Calculation
```python
def test_basic_half_kelly():
    calculator = HalfKellyCalculator()
    assert calculator.calculate(0.20) == 0.10
    assert calculator.calculate(0.50) == 0.25
```

### TC-2: Edge Cases
```python
def test_edge_cases():
    calculator = HalfKellyCalculator()
    assert calculator.calculate(0.0) == 0.0
    assert calculator.calculate(1.0) == 0.5
```

### TC-3: Negative Input
```python
def test_negative_kelly():
    calculator = HalfKellyCalculator()
    assert calculator.calculate(-0.10) == -0.05
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

**File**: `/Users/srijan/Desktop/aksh/src/kelly/half_kelly.py`

```python
class HalfKellyCalculator:
    """Calculate Half-Kelly (more conservative than full Kelly)"""

    def calculate(self, kelly_fraction: float) -> float:
        """
        Calculate Half-Kelly fraction

        Args:
            kelly_fraction: Full Kelly fraction

        Returns:
            Half of Kelly fraction
        """
        return kelly_fraction * 0.5
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
