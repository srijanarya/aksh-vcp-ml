# STORY-006: 2% Max Drawdown Protection

**Epic**: Portfolio Management System
**Story Points**: 8
**Priority**: CRITICAL
**Created**: November 19, 2025
**Status**: Not Started

---

## User Story

**As** the Portfolio Manager
**I want** automatic drawdown protection at 2% limit
**So that** I prevent catastrophic losses and protect capital

---

## Background

**Why 2%?**
- Conservative risk limit
- Prevents large losses
- Preserves capital for recovery
- Psychological safety net

**Drawdown Calculation**:
```
Drawdown % = (Peak Capital - Current Capital) / Peak Capital
```

**Example**:
- Peak capital: ₹1,10,000
- Current capital: ₹1,07,800
- Drawdown: (₹1,10,000 - ₹1,07,800) / ₹1,10,000 = 2%

---

## Acceptance Criteria

### AC-1: Track Peak Capital

**Given** trading active
**When** capital reaches new high
**Then**:
- Update peak capital
- Reset drawdown to 0%
- Log event

**Test**:
```python
def test_track_peak_capital():
    portfolio = Portfolio(initial_capital=100000)

    # Initial state
    assert portfolio.peak_capital == 100000

    # Capital increases
    portfolio.update_capital(105000)

    assert portfolio.peak_capital == 105000
    assert portfolio.current_drawdown_pct == 0.0
```

---

### AC-2: Calculate Current Drawdown

**Given**:
- Peak capital: ₹1,10,000
- Current capital: ₹1,08,000

**When**: Calculate drawdown

**Then**:
- Drawdown: (₹1,10,000 - ₹1,08,000) / ₹1,10,000
- Drawdown: ₹2,000 / ₹1,10,000
- Drawdown: 1.82%

**Test**:
```python
def test_calculate_drawdown():
    portfolio = Portfolio(initial_capital=100000)

    portfolio.peak_capital = 110000
    portfolio.current_capital = 108000

    dd = portfolio.calculate_drawdown_pct()

    assert dd == pytest.approx(0.0182, abs=0.0001)  # 1.82%
```

---

### AC-3: Alert at 1.5% Drawdown

**Given** drawdown reaches 1.5%
**When** Check drawdown
**Then**:
- Log warning: "Approaching max drawdown limit"
- Send Telegram alert
- Reduce position sizes by 50%
- Continue trading cautiously

**Test**:
```python
def test_alert_at_1_5_pct_drawdown(mocker):
    portfolio = Portfolio(initial_capital=100000)
    mock_telegram = mocker.Mock()

    portfolio.peak_capital = 110000
    portfolio.current_capital = 108350  # -1.5%

    portfolio.check_drawdown_limits(telegram_bot=mock_telegram)

    # Alert sent
    mock_telegram.send_message.assert_called_once()

    # Message contains warning
    message = mock_telegram.send_message.call_args[0][0]
    assert "Approaching max drawdown" in message
```

---

### AC-4: Halt Trading at 2% Drawdown

**Given** drawdown hits 2%
**When** Check drawdown
**Then**:
- **HALT ALL NEW TRADES**
- Log critical error
- Send urgent Telegram alert
- Activate defensive mode:
  - Close risky positions
  - Keep safe positions
  - Stop taking new signals

**Test**:
```python
def test_halt_trading_at_2_pct():
    portfolio = Portfolio(initial_capital=100000)

    portfolio.peak_capital = 110000
    portfolio.current_capital = 107800  # Exactly -2%

    portfolio.check_drawdown_limits()

    # Trading halted
    assert portfolio.trading_halted is True

    # Try to place new order (should fail)
    with pytest.raises(TradingHaltedError):
        portfolio.place_order(...)
```

---

### AC-5: Gradual Position Reduction

**Given** drawdown = 1.8%
**When** New signal arrives
**Then**:
- Calculate normal position size: ₹14,000
- Apply drawdown adjustment: -50%
- Adjusted position: ₹7,000
- Place order with reduced size

**Implementation**:
```python
if drawdown_pct > 0.015:  # 1.5%
    # Reduce position sizes
    reduction_factor = 0.5

    position_value = position_value * reduction_factor

    logger.warning(
        f"Drawdown at {drawdown_pct:.2%}. "
        f"Reducing position size by 50%"
    )
```

---

### AC-6: Recovery Mode

**Given**:
- Drawdown was 2% (trading halted)
- Capital recovers to 1% drawdown

**When**: Check if can resume

**Then**:
- Log: "Drawdown recovered to 1%"
- Resume trading (manual approval required)
- Send Telegram notification
- Start with reduced position sizes (50%)
- Gradually increase as drawdown decreases

**Test**:
```python
def test_recovery_mode():
    portfolio = Portfolio(...)

    # Drawdown was 2%, trading halted
    portfolio.trading_halted = True
    portfolio.peak_capital = 110000
    portfolio.current_capital = 107800  # -2%

    # Capital recovers
    portfolio.current_capital = 108900  # -1%

    # Check if can resume (requires manual approval)
    can_resume = portfolio.can_resume_trading()

    assert can_resume is True  # Eligible for resume

    # Resume (manual)
    portfolio.resume_trading(approved_by="user")

    assert portfolio.trading_halted is False
```

---

## Drawdown Response Levels

| Drawdown | Status | Action |
|----------|--------|--------|
| 0-1% | 🟢 Normal | Full position sizing |
| 1-1.5% | 🟡 Caution | Monitor closely, log warnings |
| 1.5-1.8% | 🟠 Warning | Reduce positions 50%, alert user |
| 1.8-2% | 🔴 Critical | Reduce positions 75%, prepare to halt |
| 2%+ | ⛔ Halt | **STOP all new trades, close risky positions** |

---

## Definition of Done

- [ ] Peak capital tracking implemented
- [ ] Drawdown calculation implemented
- [ ] Alert at 1.5% implemented
- [ ] Trading halt at 2% implemented
- [ ] Gradual position reduction implemented
- [ ] Recovery mode implemented
- [ ] 12 unit tests passing
- [ ] Integration with portfolio manager
- [ ] Telegram alerts working
- [ ] Documentation complete
- [ ] Code reviewed

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: SHORTS Directory & Task Breakdown
