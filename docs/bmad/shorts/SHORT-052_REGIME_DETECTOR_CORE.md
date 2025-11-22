# SHORT-052: Regime Detector Core

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Market Regime Detection

## Problem
Need to detect market regime (trending/ranging/volatile) to select appropriate trading strategies.

## Solution
Regime detection using ADX for trend strength and volatility measures.

## Implementation

### Regimes
1. **TRENDING**: High ADX, directional market
2. **RANGING**: Low ADX, sideways market
3. **VOLATILE**: High volatility, unpredictable

### Thresholds
- ADX > 25: Trending
- ADX < 25: Ranging
- Volatility > 2%: Volatile override

### API

```python
from src.regime.regime_detector import RegimeDetector, MarketRegime

detector = RegimeDetector(
    adx_threshold=25.0,
    volatility_threshold=2.0
)

regime = detector.detect_regime(df, adx_series)

if regime == MarketRegime.TRENDING:
    print("Use trend following strategy")
```

## Test Requirements
- Trending detection
- Ranging detection
- Volatile detection
- Threshold configuration
- Edge cases

## Dependencies
- SHORT-024 (ADX Calculator)
- pandas

## Acceptance Criteria
- ✅ Detects three regime types
- ✅ Uses ADX and volatility
- ✅ Configurable thresholds
- ✅ Returns MarketRegime enum
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/regime/regime_detector.py`
- Tests: `/Users/srijan/Desktop/aksh/tests/test_regime_detector.py` (to create)
