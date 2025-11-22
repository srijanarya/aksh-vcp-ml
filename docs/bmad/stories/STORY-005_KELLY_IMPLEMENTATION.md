# STORY-005: Kelly Criterion Implementation

**Epic**: Portfolio Management System
**Story Points**: 8
**Priority**: HIGH
**Created**: November 19, 2025
**Status**: Not Started

---

## User Story

**As** the Trading System
**I want** Kelly Criterion position sizing fully implemented and tested
**So that** I maximize long-term capital growth while controlling risk

---

## Background

Kelly Criterion determines optimal bet size to maximize logarithmic wealth growth.

**Formula**:
```
Kelly % = (Win Rate × Avg Win - Loss Rate × Avg Loss) / Avg Win
```

**Why Kelly?**
- Mathematically optimal for long-term growth
- Self-adjusts based on performance
- Prevents over-betting
- Accounts for win rate AND payoff ratio

**Why Half-Kelly?**
- Full Kelly can be volatile
- Half-Kelly = 75% of growth, 50% of volatility
- More conservative, safer for real money

---

## Acceptance Criteria

### AC-1: Calculate Kelly from Strategy Performance

**Given**:
- Strategy: ADX+DMA
- Last 100 trades:
  - Wins: 55
  - Losses: 45
  - Avg win: +5%
  - Avg loss: -3%

**When**: Calculate Kelly

**Then**:
- Win rate = 55/100 = 0.55
- Loss rate = 45/100 = 0.45
- Kelly = (0.55 × 0.05 - 0.45 × 0.03) / 0.05
- Kelly = (0.0275 - 0.0135) / 0.05
- Kelly = 0.28 (28%)
- Half-Kelly = 0.14 (14%)

**Test**:
```python
def test_kelly_calculation():
    tracker = StrategyPerformanceTracker(db_path="trades.db")

    stats = tracker.get_strategy_stats("ADX+DMA")

    assert stats.win_rate == 0.55
    assert stats.avg_win_pct == 0.05
    assert stats.avg_loss_pct == 0.03

    sizer = KellyPositionSizer(...)
    kelly = sizer._calculate_kelly_fraction(stats)

    assert kelly == pytest.approx(0.28, abs=0.01)

    half_kelly = kelly / 2
    assert half_kelly == pytest.approx(0.14, abs=0.01)
```

---

### AC-2: Apply Profit Scaling

**Given**:
- Initial capital: ₹1,00,000
- Current capital: ₹1,10,000 (+10%)
- Base Kelly: 0.14

**When**: Apply profit scaling

**Then**:
- Profit level: +10%
- Scale factor: 1.5× (per scaling rules)
- Scaled Kelly: 0.14 × 1.5 = 0.21

**Test**:
```python
def test_profit_scaling():
    sizer = KellyPositionSizer(initial_capital=100000)

    base_kelly = 0.14
    scaled_kelly = sizer._apply_profit_scaling(
        kelly=base_kelly,
        current_capital=110000,
        initial_capital=100000,
    )

    assert scaled_kelly == pytest.approx(0.21, abs=0.01)
```

---

### AC-3: Position Size Calculation

**Given**:
- Current capital: ₹1,10,000
- Kelly: 0.21
- Signal: BUY RELIANCE @ ₹2,500

**When**: Calculate position size

**Then**:
- Position value: ₹1,10,000 × 0.21 = ₹23,100
- Cap check: ₹23,100 > ₹22,000 (20% limit) ❌
- Final position: ₹22,000 (capped)
- Shares: ₹22,000 / ₹2,500 = 8.8 → 8 shares
- Actual value: 8 × ₹2,500 = ₹20,000 ✅

---

### AC-4: Weekly Kelly Update

**Given** end of week (Friday 3:30 PM)
**When** Calculate updated Kelly fractions
**Then**:
- Query last 100 trades for each strategy
- Recalculate Kelly fractions
- Update cached values
- Log changes
- Send weekly update via Telegram

**Test**:
```python
def test_weekly_kelly_update():
    updater = KellyUpdater(db_path="trades.db")

    # Simulate Friday 3:30 PM
    updater.update_kelly_fractions()

    # Check updated values stored
    new_kelly = updater.get_cached_kelly("ADX+DMA")

    assert new_kelly is not None
    assert 0 <= new_kelly <= 0.50
```

---

### AC-5: Minimum Trade History Requirement

**Given**:
- New strategy with only 15 trades

**When**: Calculate Kelly

**Then**:
- Detect insufficient history (< 30 trades)
- Use conservative default Kelly = 0.10
- Flag as "INSUFFICIENT_HISTORY"
- Wait for more trades before using actual Kelly

---

## Definition of Done

- [ ] Kelly calculation implemented
- [ ] Profit scaling implemented
- [ ] Position size calculation with caps
- [ ] Weekly update mechanism
- [ ] Minimum history enforcement
- [ ] 15 unit tests passing
- [ ] Integration with signal generator
- [ ] Documentation complete
- [ ] Code reviewed

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: STORY-006 (Drawdown Protection)
