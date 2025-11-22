# SHORT-023: Sentiment-Based Kelly Adjuster

**Parent**: FX-002 (Kelly Position Sizing)
**Estimated Effort**: 2 hours
**Priority**: MEDIUM
**Status**: COMPLETE

## Objective

Implement sentiment-based Kelly adjuster that scales Kelly fractions based on market sentiment (bullish/bearish/neutral), reducing positions in unfavorable conditions.

## Acceptance Criteria

- [x] AC-1: Scale Kelly based on sentiment score (-1 to +1)
- [x] AC-2: Reduce to 50% Kelly in bearish sentiment (< -0.3)
- [x] AC-3: Use full Kelly in bullish sentiment (> +0.3)
- [x] AC-4: Use 75% Kelly in neutral sentiment
- [x] AC-5: Test coverage ≥ 95%

## Implementation

**File**: `/Users/srijan/Desktop/aksh/src/kelly/sentiment_kelly_adjuster.py`
