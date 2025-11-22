# SHORT-057: Regime-Based Position Sizing

**Status**: 🔲 Not Started
**TDD Status**: 🔲 Tests Required
**Iteration**: 1
**Category**: Market Regime Detection

## Problem
Position sizes should adapt to market regime - smaller in volatile/uncertain markets, larger in trending markets.

## Solution
Position size multiplier based on regime type.

## Implementation

### Position Multipliers
- **TRENDING**: 1.0x (full size)
- **RANGING**: 0.7x (reduced size)
- **VOLATILE**: 0.3x (minimal exposure)

### API

```python
from src.regime.position_size_adjuster import RegimePositionSizer

sizer = RegimePositionSizer()
base_size = 10000  # Base position size

regime = detector.detect_regime(df, adx)
adjusted_size = sizer.adjust_size(base_size, regime)

# TRENDING: 10000, RANGING: 7000, VOLATILE: 3000
```

## Test Requirements
- Multiplier application
- All regime types
- Edge cases (zero size)
- Integration with regime detector

## Dependencies
- SHORT-052 (Regime Detector Core)
- SHORT-053 (Market Regime Enum)

## Acceptance Criteria
- 🔲 Adjusts position size by regime
- 🔲 Reduces size in volatile markets
- 🔲 Configurable multipliers
- 🔲 Returns adjusted size
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/regime/position_size_adjuster.py` (to create)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_position_size_adjuster.py` (to create)
