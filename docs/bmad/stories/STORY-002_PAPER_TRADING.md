# STORY-002: 30-Day Paper Trading Validation

**Epic**: Portfolio Management System
**Story Points**: 13
**Priority**: CRITICAL
**Created**: November 19, 2025
**Status**: Not Started

---

## User Story

**As** the Portfolio Manager
**I want** to paper trade for 30 days with virtual capital
**So that** I can validate the system works in real market conditions before going live

---

## Background

**User Requirement**: *"Also make sure we have a robust fact testing engine and a robust paper trading mechanism before we take any strategy live"*

Paper trading is the FINAL gate before live trading with real money. It must:
- Match backtest predictions
- Execute in real-time (no lookahead bias)
- Handle live market conditions
- Prove risk management works

---

## Acceptance Criteria

### AC-1: Initialize Paper Trading Account
**Given** backtest passed all criteria
**When** I start paper trading
**Then** virtual account is created with ₹1,00,000

**Test**:
```python
def test_initialize_paper_account():
    paper_trader = PaperTradingEngine(initial_capital=100000)

    assert paper_trader.virtual_capital == 100000
    assert paper_trader.peak_capital == 100000
    assert len(paper_trader.positions) == 0
    assert paper_trader.status == "ACTIVE"
```

---

### AC-2: Generate Real-Time Signals
**Given** market is open
**When** it's 9:30 AM
**Then** ADX+DMA signals are generated from live data

**Test**:
```python
def test_generate_realtime_signals():
    paper_trader = PaperTradingEngine(...)

    # Simulate 9:30 AM
    signals = paper_trader.generate_signals(timestamp="2025-11-19 09:30:00")

    # Should get signals for some stocks
    assert len(signals) >= 0  # May be 0 on some days

    # Signals use LIVE data (not historical)
    for signal in signals:
        assert signal["timestamp"] == "2025-11-19 09:30:00"
        assert signal["data_source"] == "LIVE"
```

---

### AC-3: Execute Virtual Orders
**Given** a BUY signal
**When** I place a virtual order
**Then** order is executed with realistic slippage and costs

**Test**:
```python
def test_execute_virtual_order():
    paper_trader = PaperTradingEngine(...)

    signal = {
        "symbol": "RELIANCE.NS",
        "side": "BUY",
        "entry_price": 2500,  # Signal price
        "shares": 40,
    }

    # Execute virtually
    trade = paper_trader.execute_virtual_order(signal)

    # Entry price has slippage
    assert trade["actual_entry_price"] > 2500

    # Costs deducted
    assert trade["costs"] > 0

    # Capital reduced
    assert paper_trader.virtual_capital < 100000
```

---

### AC-4: Track Virtual Positions
**Given** I have 3 open positions
**When** I query my portfolio
**Then** all positions are tracked with current PnL

**Test**:
```python
def test_track_virtual_positions():
    paper_trader = PaperTradingEngine(...)

    # Open 3 positions
    paper_trader.execute_virtual_order({"symbol": "A", ...})
    paper_trader.execute_virtual_order({"symbol": "B", ...})
    paper_trader.execute_virtual_order({"symbol": "C", ...})

    positions = paper_trader.get_open_positions()

    assert len(positions) == 3

    # Each position has current PnL
    for pos in positions:
        assert "unrealized_pnl" in pos
        assert "current_price" in pos
```

---

### AC-5: Execute Stop-Loss Exits
**Given** I have a position with stop-loss at ₹2,425
**When** price hits ₹2,424 (below stop)
**Then** position is automatically exited

**Test**:
```python
def test_stop_loss_exit():
    paper_trader = PaperTradingEngine(...)

    # Open position with stop-loss
    trade = paper_trader.execute_virtual_order({
        "symbol": "RELIANCE.NS",
        "side": "BUY",
        "entry_price": 2500,
        "stop_loss": 2425,
        "shares": 40,
    })

    # Simulate price dropping to ₹2,424
    paper_trader.update_market_prices({"RELIANCE.NS": 2424})

    # Check for exits
    paper_trader.check_exits()

    # Position should be closed
    positions = paper_trader.get_open_positions()
    assert "RELIANCE.NS" not in [p["symbol"] for p in positions]

    # Exit recorded in trade log
    assert trade["exit_reason"] == "STOP_LOSS"
```

---

### AC-6: Daily Reconciliation
**Given** I've traded for 1 day
**When** market closes (3:30 PM)
**Then** daily PnL is calculated and logged

**Test**:
```python
def test_daily_reconciliation():
    paper_trader = PaperTradingEngine(...)

    # Trade for 1 day
    paper_trader.run_for_day(date="2025-11-19")

    # Daily report generated
    report = paper_trader.get_daily_report("2025-11-19")

    assert "date" in report
    assert "daily_pnl" in report
    assert "end_of_day_capital" in report
    assert "trades_executed" in report
```

---

### AC-7: Enforce 2% Max Drawdown
**Given** virtual capital drops by 1.9% from peak
**When** a new signal arrives
**Then** position size is reduced to stay within 2% limit

**Test**:
```python
def test_enforce_max_drawdown():
    paper_trader = PaperTradingEngine(initial_capital=100000)

    # Lose ₹1,900 (1.9% from peak)
    paper_trader.virtual_capital = 98100
    paper_trader.peak_capital = 100000

    # Try to take new trade with ₹500 risk
    signal = {"symbol": "A", "risk": 500, ...}

    # Trade should be rejected or reduced
    trade = paper_trader.execute_virtual_order(signal)

    # Total risk must not exceed 2% of peak (₹2,000)
    total_risk = paper_trader.calculate_total_risk()
    assert total_risk <= 2000
```

---

### AC-8: Send Daily Reports
**Given** day ends
**When** I generate the daily report
**Then** report is sent via Telegram with:
- Daily PnL
- Current capital
- Open positions
- Trades executed today

**Test**:
```python
def test_send_daily_report(mocker):
    paper_trader = PaperTradingEngine(...)

    # Mock Telegram bot
    mock_telegram = mocker.patch("telegram.Bot.send_message")

    # End of day
    paper_trader.send_daily_report()

    # Telegram message sent
    mock_telegram.assert_called_once()

    # Message contains key info
    message = mock_telegram.call_args[0][1]
    assert "Daily PnL" in message
    assert "Current Capital" in message
```

---

### AC-9: Match Backtest Predictions
**Given** I've paper traded for 30 days
**When** I compare to backtest predictions
**Then** results match within ±10%

**Test**:
```python
def test_match_backtest_predictions():
    # Run backtest for 30 days
    backtest = BacktestEngine(...)
    backtest_results = backtest.run_backtest(
        start_date="2025-11-01",
        end_date="2025-11-30"
    )

    # Run paper trading for same 30 days (simulated)
    paper_trader = PaperTradingEngine(...)
    paper_results = paper_trader.run_for_period(
        start_date="2025-11-01",
        end_date="2025-11-30"
    )

    # Compare
    backtest_return = backtest_results["total_return_pct"]
    paper_return = paper_results["total_return_pct"]

    # Should match within 10%
    difference = abs(backtest_return - paper_return)
    assert difference / backtest_return < 0.10, \
        f"Backtest: {backtest_return:.2%}, Paper: {paper_return:.2%}"
```

---

### AC-10: Pass 30-Day Validation
**Given** 30 days of paper trading complete
**When** I evaluate results
**Then**:
- Max drawdown < 2%
- Win rate within ±5% of backtest
- No system crashes or errors
- All trades executed correctly

**Test**:
```python
def test_30_day_validation():
    paper_trader = PaperTradingEngine(initial_capital=100000)

    # Run for 30 days
    results = paper_trader.run_for_period(
        start_date="2025-11-01",
        end_date="2025-11-30"
    )

    # Success criteria
    assert results["max_drawdown_pct"] < 2.0, "Max DD must be < 2%"

    # Win rate matches backtest (assumed 55%)
    backtest_win_rate = 0.55
    win_rate_diff = abs(results["win_rate"] - backtest_win_rate)
    assert win_rate_diff < 0.05, "Win rate must match backtest ±5%"

    # No errors
    assert results["errors"] == 0, "No system errors allowed"

    # All trades executed
    assert results["failed_trades"] == 0, "All trades must execute"

    print("✅ 30-day paper trading validation PASSED!")
```

---

## Definition of Done

- [ ] All 10 acceptance criteria pass
- [ ] 30 consecutive trading days completed without errors
- [ ] Max drawdown < 2% maintained
- [ ] Daily reports sent every day
- [ ] Paper trading results match backtest (±10%)
- [ ] Code coverage ≥ 95% for paper trading engine
- [ ] Documentation complete
- [ ] Code reviewed and approved
- [ ] User approval for soft launch

---

## Technical Notes

### Paper Trading Engine Architecture

```python
class PaperTradingEngine:
    """
    Paper trading with virtual capital

    Runs in REAL-TIME with LIVE data
    """

    def __init__(self, initial_capital):
        self.virtual_capital = initial_capital
        self.peak_capital = initial_capital
        self.positions = []
        self.trade_log = []
        self.daily_equity = []

        # Components (same as backtest)
        self.signal_generator = ADXDMAScanner()
        self.kelly_sizer = KellyPositionSizer(...)
        self.cost_calculator = CostCalculator()
        self.slippage_simulator = SlippageSimulator()
        self.risk_manager = RiskManager(...)

        # Real-time data source
        self.data_source = AngelOneClient()  # LIVE data

    def run_daily_cycle(self):
        """Run daily trading cycle (call this every trading day)"""

        # 1. Morning: Generate signals (9:30 AM)
        signals = self.generate_signals()

        # 2. Execute new trades
        for signal in signals:
            # Calculate position size
            position = self.kelly_sizer.calculate_position_size(signal, ...)

            # Check risk limits
            if self.risk_manager.can_take_trade(position):
                # Execute virtually
                self.execute_virtual_order(signal, position)

        # 3. Monitor positions throughout day
        self.monitor_positions()

        # 4. End of day: Reconcile and report
        self.daily_reconciliation()
        self.send_daily_report()

    def execute_virtual_order(self, signal, position):
        """Execute order virtually (no real money)"""

        # Get current LIVE price
        current_price = self.data_source.get_current_price(signal["symbol"])

        # Apply slippage
        slippage_result = self.slippage_simulator.calculate_slippage(
            signal["symbol"],
            signal["side"],
            position["position_value"],
            current_price,
        )

        actual_entry_price = slippage_result.adjusted_price

        # Calculate costs
        costs = self.cost_calculator.calculate_equity_delivery_costs(
            signal["side"],
            position["position_value"],
        )

        # Update virtual capital
        self.virtual_capital -= position["position_value"]
        self.virtual_capital -= costs.total

        # Create virtual position
        virtual_position = {
            "symbol": signal["symbol"],
            "entry_price": actual_entry_price,
            "shares": position["shares"],
            "stop_loss": signal["stop_loss"],
            "entry_time": datetime.now(),
            "costs": costs.total,
            "slippage": slippage_result.slippage_amount,
        }

        self.positions.append(virtual_position)

        self.logger.info(
            f"VIRTUAL BUY: {signal['symbol']} × {position['shares']} "
            f"@ ₹{actual_entry_price:.2f} (slippage: ₹{slippage_result.slippage_amount:.2f})"
        )

        return virtual_position

    def monitor_positions(self):
        """Monitor positions and check for exits"""

        for position in self.positions:
            # Get current price
            current_price = self.data_source.get_current_price(position["symbol"])

            # Check stop-loss
            if current_price <= position["stop_loss"]:
                self.exit_position(position, "STOP_LOSS", current_price)

            # Check target (if set)
            if "target" in position and current_price >= position["target"]:
                self.exit_position(position, "TARGET", current_price)

    def exit_position(self, position, reason, exit_price):
        """Exit virtual position"""

        # Calculate PnL
        gross_pnl = (exit_price - position["entry_price"]) * position["shares"]

        # Calculate exit costs
        exit_value = exit_price * position["shares"]
        exit_costs = self.cost_calculator.calculate_equity_delivery_costs(
            "SELL", exit_value
        ).total

        # Apply exit slippage
        exit_slippage = self.slippage_simulator.calculate_slippage(
            position["symbol"],
            "SELL",
            exit_value,
            exit_price,
        )

        # Net PnL
        net_pnl = gross_pnl - position["costs"] - exit_costs - exit_slippage.slippage_amount

        # Update capital
        self.virtual_capital += exit_value
        self.virtual_capital -= exit_costs
        self.virtual_capital -= exit_slippage.slippage_amount

        # Update peak
        self.peak_capital = max(self.peak_capital, self.virtual_capital)

        # Log trade
        self.trade_log.append({
            "symbol": position["symbol"],
            "entry_price": position["entry_price"],
            "exit_price": exit_price,
            "shares": position["shares"],
            "net_pnl": net_pnl,
            "exit_reason": reason,
            "entry_time": position["entry_time"],
            "exit_time": datetime.now(),
        })

        # Remove position
        self.positions.remove(position)

        self.logger.info(
            f"VIRTUAL SELL: {position['symbol']} @ ₹{exit_price:.2f} "
            f"| PnL: ₹{net_pnl:.2f} | Reason: {reason}"
        )
```

---

## Daily Workflow

### Morning (9:00-9:30 AM)
1. Fetch overnight news → Calculate sentiment
2. Detect regime (expansion, trending, etc.)
3. Select optimal strategy

### 9:30 AM (Signal Generation)
1. ADX+DMA scanner runs on live data
2. Generate BUY/SELL signals
3. Calculate position sizes (Kelly + sentiment)
4. Check risk limits
5. Execute virtual orders

### Throughout Day (Monitoring)
1. Fetch live prices every 5 minutes
2. Check stop-losses
3. Check targets
4. Exit positions as needed

### End of Day (3:30 PM)
1. Calculate unrealized PnL
2. Update equity curve
3. Generate daily report
4. Send Telegram notification

---

## Risk Management

### Pre-Trade Checks
```python
def can_take_trade(self, position):
    # 1. Check max drawdown
    current_dd = (self.peak_capital - self.virtual_capital) / self.peak_capital
    if current_dd >= 0.018:  # 1.8% (buffer before 2%)
        self.logger.warning("Approaching max drawdown limit. Reducing positions.")
        return False

    # 2. Check total risk
    total_risk = self.calculate_total_risk()
    max_risk = self.peak_capital * 0.02
    if total_risk + position["risk"] > max_risk:
        self.logger.warning("Total risk would exceed 2% limit.")
        return False

    # 3. Check position concentration
    if position["position_value"] > self.virtual_capital * 0.20:
        self.logger.warning("Position exceeds 20% of capital.")
        return False

    return True
```

---

## Validation Criteria

### Gate to Soft Launch

Paper trading must pass these gates:

✅ **30 consecutive trading days** (no crashes)
✅ **Max drawdown < 2%** from peak
✅ **Win rate within ±5%** of backtest
✅ **Returns within ±10%** of backtest
✅ **All stop-losses executed** correctly
✅ **Daily reports sent** every day
✅ **No manual intervention** required

**If ALL gates pass** → Proceed to Soft Launch (₹25K)
**If ANY gate fails** → Fix issues, restart 30-day clock

---

## Dependencies

- **STORY-001**: Backtest must pass first
- **FX-001**: Angel One API for live data
- **FX-010**: Order execution logic (adapted for virtual)
- **Infrastructure**: Server running 24/7 during paper trading

---

## Estimated Effort

- **Development**: 5 days
- **Testing**: 3 days
- **30-day validation**: 30 days (calendar time)
- **Total**: 8 days dev + 30 days live

---

**Status**: ✅ Story Complete
**Ready for Implementation**: After STORY-001 passes
