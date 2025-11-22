# SHORT-022: Weekly Kelly Fraction Updater

**Parent**: FX-002 (Kelly Position Sizing)
**Estimated Effort**: 3 hours
**Priority**: MEDIUM
**Status**: COMPLETE

## Objective

Implement weekly Kelly fraction updater that recalculates Kelly fractions based on recent performance, adapting to changing win rates and risk-reward ratios.

## Acceptance Criteria

- [x] AC-1: Update Kelly fraction weekly based on recent trade history
- [x] AC-2: Use configurable lookback window (default 20 trades)
- [x] AC-3: Validate minimum trades before updating (default 10)
- [x] AC-4: Preserve Kelly history for analysis
- [x] AC-5: Test coverage ≥ 95%

## Implementation

**File**: `/Users/srijan/Desktop/aksh/src/kelly/weekly_kelly_updater.py`
