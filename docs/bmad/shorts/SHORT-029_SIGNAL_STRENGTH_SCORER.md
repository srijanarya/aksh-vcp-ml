# SHORT-029: Signal Strength Scorer

**Parent**: FX-003 (Signal Generation)
**Estimated Effort**: 3 hours
**Priority**: MEDIUM
**Status**: IN PROGRESS

## Objective

Implement signal strength scorer that assigns quality scores (0-100) to trading signals based on multiple factors (ADX strength, distance from DMA, volume, etc.).

## Acceptance Criteria

- [ ] AC-1: Score signals based on ADX strength (0-100 scale)
- [ ] AC-2: Score based on distance above DMA (higher = stronger)
- [ ] AC-3: Score based on volume confirmation (> avg volume)
- [ ] AC-4: Combine scores into overall signal strength (0-100)
- [ ] AC-5: Test coverage ≥ 95%

## Implementation Plan

**File**: `/Users/srijan/Desktop/aksh/src/signals/signal_strength_scorer.py`
