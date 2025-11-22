# SHORT-055: ADX-Based Regime Classifier

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Market Regime Detection

## Problem
Need to distinguish trending from ranging markets for strategy selection.

## Solution
Use ADX threshold (default 25) to classify trending vs ranging regimes.

## Implementation

### Logic
```python
current_adx = adx.iloc[-1]

if current_adx >= adx_threshold:
    return MarketRegime.TRENDING
else:
    return MarketRegime.RANGING
```

### ADX Interpretation
- **ADX > 25**: Strong trend (use trend following)
- **ADX < 25**: Weak trend (use mean reversion)

### API

```python
detector = RegimeDetector(adx_threshold=25.0)
regime = detector.detect_regime(df, adx_series)

# Trending strategies work better in trending regimes
```

## Test Requirements
- ADX threshold comparison
- Trending classification
- Ranging classification
- Latest value extraction
- Threshold configuration

## Dependencies
- SHORT-052 (Regime Detector Core)
- SHORT-024 (ADX Calculator)

## Acceptance Criteria
- ✅ Uses ADX threshold
- ✅ Classifies correctly
- ✅ Configurable threshold
- ✅ Uses latest ADX value
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/regime/regime_detector.py` (lines 56-64)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_regime_detector.py` (to create)
