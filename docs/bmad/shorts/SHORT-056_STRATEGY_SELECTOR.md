# SHORT-056: Strategy Selector by Regime

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Market Regime Detection

## Problem
Different market regimes require different trading strategies for optimal performance.

## Solution
Strategy selection map based on detected regime.

## Implementation

### Strategy Mapping
- **TRENDING** → "trend_following"
- **RANGING** → "mean_reversion"
- **VOLATILE** → "risk_off"

### API

```python
regime = detector.detect_regime(df, adx)
strategy = detector.select_strategy(regime)

if strategy == "trend_following":
    # Use trend-based signals
elif strategy == "mean_reversion":
    # Use range-based signals
else:
    # Reduce exposure or stay flat
```

## Test Requirements
- Strategy mapping accuracy
- All regime types covered
- Return type validation
- Integration with regime detector

## Dependencies
- SHORT-052 (Regime Detector Core)
- SHORT-053 (Market Regime Enum)

## Acceptance Criteria
- ✅ Maps all regimes
- ✅ Returns strategy name
- ✅ Consistent naming
- ✅ Easy integration
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/regime/regime_detector.py` (lines 66-82)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_regime_detector.py` (to create)
