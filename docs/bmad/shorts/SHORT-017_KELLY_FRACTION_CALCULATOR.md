# SHORT-017: Kelly Fraction Calculator

**Parent**: FX-002 (Kelly Position Sizing)
**Estimated Effort**: 3 hours
**Priority**: HIGH

## Objective

Calculate Kelly fraction (optimal position size) using formula: F = (W * R - L) / R
where W = win rate, R = avg win / avg loss, L = loss rate

## Acceptance Criteria

- [ ] AC-1: Calculate Kelly fraction from performance stats
- [ ] AC-2: Handle edge cases (zero trades, 100% win rate, etc.)
- [ ] AC-3: Return fraction between 0 and 1
- [ ] AC-4: Validate inputs
