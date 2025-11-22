# STORY-003: Soft Launch (₹25K for 1 Week)

**Epic**: Portfolio Management System
**Story Points**: 8
**Priority**: CRITICAL
**Created**: November 19, 2025
**Status**: Not Started

---

## User Story

**As** the Portfolio Manager
**I want** to trade with ₹25,000 for 1 week
**So that** I can validate live trading with minimal risk before scaling to ₹1L

---

## Background

**Purpose of Soft Launch**:
- Final validation with REAL money
- Test live order execution
- Verify real slippage and costs
- Build confidence before full launch
- Identify any production-only issues

**Why ₹25K (not ₹1L)?**
- Lower risk for initial live testing
- Quarter of target capital
- Allows 4x safety margin
- Can recover from mistakes

**Why 1 Week?**
- 5 trading days minimum
- Enough data to validate
- Short enough to limit exposure
- Can scale up quickly if successful

---

## Acceptance Criteria

### AC-1: Fund Angel One Account with ₹25,000

**Given** paper trading passed all criteria
**When** I transfer ₹25K to Angel One
**Then** funds are available for trading

**Test**:
```python
def test_account_funded():
    executor = AngelOneExecutor(...)

    margin = executor.get_available_margin()

    assert margin >= 25000
```

---

### AC-2: Configure System for ₹25K Capital

**Given** system configured for ₹1L
**When** I update configuration to ₹25K
**Then**:
- Initial capital = ₹25,000
- Max position size = ₹5,000 (20% cap)
- Max F&O position = ₹1,000 (4% cap)
- Max total risk = ₹500 (2% of ₹25K)

**Test**:
```python
def test_capital_configuration():
    config = SystemConfig(initial_capital=25000)

    assert config.max_position_value == 5000
    assert config.max_fno_position == 1000
    assert config.max_total_risk == 500
```

---

### AC-3: Place First Live Order

**Given**:
- Signal generated: BUY RELIANCE
- Position size calculated: 2 shares (₹5,000)
- All validations passed

**When**: Execute first live order

**Then**:
1. Order placed via Angel One API
2. Order ID received
3. Telegram alert sent
4. Audit log created
5. Wait for fill confirmation

**Test**:
```python
def test_first_live_order(mocker):
    executor = AngelOneExecutor(...)

    result = executor.place_order(
        symbol="RELIANCE-EQ",
        side="BUY",
        quantity=2,
        price=2500,
    )

    assert result["success"] is True
    assert result["order_id"] is not None
```

---

### AC-4: Monitor Live Position

**Given** order filled
**When** position is open
**Then**:
- Track live PnL every 5 minutes
- Check stop-loss
- Check target
- Update portfolio value

**Test**:
```python
def test_monitor_live_position():
    portfolio = LivePortfolio(...)

    # Add position
    portfolio.add_position(
        symbol="RELIANCE",
        entry_price=2500,
        quantity=2,
        stop_loss=2425,
    )

    # Fetch live price
    current_price = 2520

    # Calculate PnL
    pnl = portfolio.calculate_position_pnl("RELIANCE", current_price)

    assert pnl == (2520 - 2500) * 2  # ₹40
```

---

### AC-5: Execute Stop-Loss Exit (Live)

**Given** position with stop-loss at ₹2,425
**When** live price hits ₹2,424
**Then**:
- Detect stop-loss breach
- Place LIMIT exit order at ₹2,424
- Log exit reason
- Send Telegram alert
- Update capital

**Test**:
```python
def test_live_stop_loss_exit(mocker):
    portfolio = LivePortfolio(...)

    # Mock live price hitting stop
    mocker.patch.object(
        data_source,
        "fetch_ohlcv",
        return_value=DataFetchResult(
            success=True,
            data=pd.DataFrame({"close": [2424]}),
        ),
    )

    # Monitor positions
    portfolio.check_exits()

    # Exit order should be placed
    assert executor.last_order["side"] == "SELL"
    assert executor.last_order["price"] == 2424
```

---

### AC-6: Daily Reconciliation (Live)

**Given** trading day complete
**When** market closes (3:30 PM)
**Then**:
- Mark positions to market
- Calculate realized PnL (closed trades)
- Calculate unrealized PnL (open positions)
- Update total capital
- Calculate daily return
- Send daily report via Telegram

**Test**:
```python
def test_daily_reconciliation():
    portfolio = LivePortfolio(initial_capital=25000)

    # Simulate 1 day of trading
    # Opened: 1 trade (₹5,000)
    # Closed: 0 trades
    # Unrealized PnL: +₹200

    portfolio.reconcile_day()

    # Capital = ₹25,000 - ₹5,000 (in position) = ₹20,000 cash
    # Total equity = ₹20,000 + ₹5,200 (position value) = ₹25,200

    assert portfolio.total_equity == 25200
    assert portfolio.daily_return_pct == 0.008  # +0.8%
```

---

### AC-7: 1-Week Performance Report

**Given** soft launch complete (5 trading days)
**When** I generate final report
**Then** report includes:
- Total return %
- CAGR (annualized)
- Max drawdown
- Win rate
- Total trades executed
- Avg trade PnL
- Comparison to paper trading
- Decision: Proceed to full launch or extend soft launch

**Test**:
```python
def test_one_week_performance_report():
    portfolio = LivePortfolio(...)

    # Simulate 1 week (5 days)
    # Starting: ₹25,000
    # Ending: ₹25,600
    # Trades: 8
    # Max DD: -0.8%

    report = portfolio.generate_weekly_report()

    assert report["total_return_pct"] == 0.024  # +2.4%
    assert report["max_drawdown_pct"] < 0.02  # < 2%
    assert report["total_trades"] == 8
```

---

### AC-8: Validate Against Paper Trading

**Given**:
- Paper trading return: +4.2% (30 days)
- Soft launch return: +2.4% (5 days)

**When**: Compare results

**Then**:
- Annualized soft launch: +2.4% × 52 weeks = +124% (unrealistic)
- More realistic: Compare daily returns
- Paper trading daily return: +4.2% / 30 = +0.14%/day
- Soft launch daily return: +2.4% / 5 = +0.48%/day
- Difference: Acceptable (small sample size)
- Validation: PASS (both positive, risk controlled)

---

### AC-9: Make Go/No-Go Decision

**Given** soft launch complete
**When** I review results
**Then** make decision:

**Proceed to Full Launch (₹1L) IF**:
- ✅ Return > 0% (profitable)
- ✅ Max drawdown < 2%
- ✅ No system errors
- ✅ All orders executed correctly
- ✅ Stop-losses working
- ✅ No manual intervention needed

**Extend Soft Launch IF**:
- ⚠️ Return < 0% but > -2%
- ⚠️ Minor system issues (non-critical)
- ⚠️ Need more data

**HALT Trading IF**:
- ❌ Max drawdown > 2%
- ❌ System errors causing losses
- ❌ Orders not executing properly
- ❌ Risk management failing

---

## Definition of Done

- [ ] Angel One account funded with ₹25,000
- [ ] System configured for ₹25K capital
- [ ] First live order placed successfully
- [ ] At least 1 complete trading day (open to close)
- [ ] At least 1 live position closed (stop or target)
- [ ] 5 trading days completed (1 week)
- [ ] Daily reports sent every day
- [ ] Final performance report generated
- [ ] Comparison to paper trading documented
- [ ] Go/No-Go decision made and documented
- [ ] User approval for next phase

---

## Daily Workflow (Soft Launch)

### Morning (9:00-9:30 AM)
1. System health check
2. Review overnight events
3. Check Angel One account status
4. Verify kill switch is OFF

### 9:30 AM (Trading Start)
1. Generate signals (ADX+DMA)
2. Calculate position sizes (scaled for ₹25K)
3. Validate orders
4. Place live orders via Angel One

### Throughout Day
1. Monitor positions every 5 minutes
2. Check stop-losses
3. Execute exits if triggered
4. Track live PnL

### 3:30 PM (Market Close)
1. Mark positions to market
2. Calculate daily PnL
3. Generate daily report
4. Send Telegram summary

### Evening
1. Review day's trades
2. Check for any issues
3. Plan for next day

---

## Risk Management

### Position Sizing for ₹25K

With ₹25K capital (instead of ₹1L), position sizes scale proportionally:

| Rule | ₹1L Capital | ₹25K Capital |
|------|-------------|--------------|
| Max position (20%) | ₹20,000 | ₹5,000 |
| Max F&O (4%) | ₹4,000 | ₹1,000 |
| Max total risk (2%) | ₹2,000 | ₹500 |

**Example Trade**:
- Signal: BUY RELIANCE @ ₹2,500
- Kelly suggests: 10% of capital = ₹2,500
- Shares: ₹2,500 / ₹2,500 = 1 share
- Stop-loss: ₹2,425 (3% risk)
- Risk: 1 × ₹75 = ₹75 (< ₹500 max) ✅

---

## Expected Outcomes

### Best Case
- Return: +3-5% (1 week)
- Max DD: < 1%
- All systems working perfectly
- Decision: Proceed to full launch immediately

### Realistic Case
- Return: +1-2% (1 week)
- Max DD: 1-2%
- Minor issues identified and fixed
- Decision: Proceed to full launch after fixes

### Worst Case
- Return: -1% (1 week)
- Max DD: 1.5-2%
- System issues requiring investigation
- Decision: Extend soft launch or halt

---

## Telegram Alerts (Soft Launch)

### Daily Summary (3:30 PM)
```
📊 Soft Launch Day 3/5

💰 Capital: ₹25,400 (+1.6%)
📈 Daily PnL: +₹200 (+0.8%)
🔝 Peak: ₹25,400
📉 Drawdown: 0%

✅ Trades Today: 2
📊 Open Positions: 1

Trades:
✅ RELIANCE: +₹150
✅ TCS: +₹50

Open:
📊 INFY: +₹120 (unrealized)
```

### Order Alerts
```
✅ LIVE Order Placed
📊 RELIANCE-EQ
🔢 BUY 1 share
💰 Price: ₹2,500
🆔 Order ID: 123456
```

```
❌ Stop-Loss Hit
📊 RELIANCE-EQ
💰 Exit: ₹2,424
📉 PnL: -₹76
```

---

## Dependencies

- **Paper Trading**: Must pass 30-day validation
- **Angel One Account**: Funded with ₹25K
- **FX-010**: Order Executor working
- **All FX modules**: Data, signals, sizing, costs, slippage

---

## Estimated Timeline

- **Funding**: 1 day (bank transfer to Angel One)
- **Configuration**: 1 day (update system for ₹25K)
- **Testing**: 1 day (testnet validation)
- **Soft Launch**: 5 trading days (1 week)
- **Analysis**: 1 day (review results, make decision)
- **Total**: 9 days (including weekends)

---

## Rollback Plan

If soft launch fails:

1. **Activate kill switch** (halt trading)
2. **Close all positions** at market price
3. **Withdraw funds** from Angel One
4. **Analyze failures** (full post-mortem)
5. **Fix issues** in code
6. **Re-run paper trading** (30 days)
7. **Retry soft launch** when confident

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: STORY-004 (Full Launch with ₹1L)
