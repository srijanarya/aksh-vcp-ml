# SHORT-054: Volatility Regime Check

**Status**: ✅ Complete
**TDD Status**: ✅ Tests Required
**Iteration**: 1
**Category**: Market Regime Detection

## Problem
High volatility periods require special handling regardless of trend direction.

## Solution
Volatility override that marks highly volatile markets as separate regime.

## Implementation

### Calculation
```python
returns = df['close'].pct_change()
volatility = returns.std() * 100  # As percentage

if volatility > threshold:
    return MarketRegime.VOLATILE
```

### Features
1. **Override Priority**: Checked first
2. **Percentage Basis**: Easy to interpret
3. **Configurable Threshold**: Default 2%

### API

```python
detector = RegimeDetector(volatility_threshold=2.0)
regime = detector.detect_regime(df, adx)

# High volatility = VOLATILE regardless of ADX
```

## Test Requirements
- Volatility calculation
- Threshold comparison
- Override behavior
- Low volatility handling
- Edge cases

## Dependencies
- SHORT-052 (Regime Detector Core)
- pandas

## Acceptance Criteria
- ✅ Calculates volatility
- ✅ Applies threshold
- ✅ Overrides other regimes
- ✅ Configurable
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/regime/regime_detector.py` (lines 51-60)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_regime_detector.py` (to create)
