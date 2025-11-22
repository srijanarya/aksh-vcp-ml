# STORY-001: Realistic Backtest Validation

**Epic**: Portfolio Management System
**Story Points**: 8
**Priority**: CRITICAL
**Created**: November 19, 2025
**Status**: Not Started

---

## User Story

**As** the Portfolio Manager
**I want** to backtest my strategy on 2 years of historical data with realistic costs and slippage
**So that** I can validate the system works before risking real money

---

## Acceptance Criteria

### AC-1: Load Historical Data
**Given** I have 2 years of historical OHLCV data for NSE-500 stocks
**When** I run the backtest
**Then** all data is loaded without errors

**Test**:
```python
def test_load_2_years_data():
    engine = BacktestEngine(start_date="2023-01-01", end_date="2024-12-31")
    data = engine.load_data(symbols=get_nse_500_symbols())

    assert len(data) > 0
    assert data.index[0] >= "2023-01-01"
    assert data.index[-1] <= "2024-12-31"
```

---

### AC-2: Generate Signals
**Given** loaded historical data
**When** ADX+DMA scanner runs
**Then** BUY/SELL signals are generated for all valid setups

**Test**:
```python
def test_generate_signals():
    engine = BacktestEngine(...)
    signals = engine.generate_signals(strategy="ADX_DMA")

    # Should find 100+ signals in 2 years
    assert len(signals) >= 100

    # All signals have required fields
    for signal in signals:
        assert "symbol" in signal
        assert "entry_price" in signal
        assert "stop_loss" in signal
```

---

### AC-3: Apply Realistic Costs
**Given** a BUY order at ₹1,00,000
**When** I execute the trade
**Then** all costs are deducted (brokerage, STT, GST, stamp duty, exchange, SEBI)

**Test**:
```python
def test_apply_costs():
    engine = BacktestEngine(...)

    # Execute ₹1L buy
    trade = engine.execute_trade("BUY", 100000, entry_price=2500, shares=40)

    # Costs should be ~₹42
    assert 40 <= trade["costs"] <= 45

    # Capital reduced by cost
    assert engine.capital < 100000
```

---

### AC-4: Apply Realistic Slippage
**Given** a MARKET order
**When** I execute the trade
**Then** slippage is applied based on liquidity, size, volatility, time

**Test**:
```python
def test_apply_slippage():
    engine = BacktestEngine(...)

    # Mid-cap stock, moderate size, market open
    signal = {
        "symbol": "MIDCAP.NS",
        "entry_price": 1000,
        "order_time": time(9, 20),  # Market open
    }

    trade = engine.execute_trade_with_slippage(signal, order_value=500000)

    # Slippage should be > 0.1%
    assert trade["actual_entry_price"] > 1001  # > signal price
    assert trade["slippage_pct"] > 0.001
```

---

### AC-5: Track Capital and Drawdown
**Given** I start with ₹1,00,000
**When** I execute 100 trades
**Then** capital is tracked after each trade and max drawdown calculated

**Test**:
```python
def test_track_capital_and_drawdown():
    engine = BacktestEngine(initial_capital=100000)

    # Run backtest
    results = engine.run_backtest(start_date="2023-01-01", end_date="2024-12-31")

    # Capital should change
    assert results["final_capital"] != 100000

    # Max drawdown should be calculated
    assert "max_drawdown_pct" in results
    assert results["max_drawdown_pct"] >= 0  # Non-negative
```

---

### AC-6: Enforce Risk Limits
**Given** total risk is approaching 2% of peak
**When** a new signal is generated
**Then** position is reduced or trade is skipped

**Test**:
```python
def test_enforce_risk_limits():
    engine = BacktestEngine(initial_capital=100000, max_total_risk_pct=0.02)

    # Open 3 positions with 1.5% risk (total 1.5%)
    engine.execute_trade("BUY", symbol="A", risk=1500)

    # Try to open 4th position with 0.8% risk (would exceed 2%)
    trade4 = engine.execute_trade("BUY", symbol="D", risk=800)

    # Trade should be rejected or reduced
    assert trade4["status"] == "REJECTED" or trade4["risk"] < 800
```

---

### AC-7: Calculate Performance Metrics
**Given** backtest is complete
**When** I generate the report
**Then** all metrics are calculated: Win rate, Calmar, Sharpe, Max DD, etc.

**Test**:
```python
def test_calculate_metrics():
    engine = BacktestEngine(...)
    results = engine.run_backtest(...)

    # Required metrics
    assert "win_rate" in results
    assert "calmar_ratio" in results
    assert "sharpe_ratio" in results
    assert "max_drawdown_pct" in results
    assert "total_trades" in results
    assert "avg_return_pct" in results

    # Metrics are sane
    assert 0 <= results["win_rate"] <= 1
    assert results["total_trades"] > 0
```

---

### AC-8: Compare to Buy & Hold
**Given** backtest results
**When** I compare to Nifty 50 buy & hold
**Then** alpha (excess return) is calculated

**Test**:
```python
def test_compare_to_buy_hold():
    engine = BacktestEngine(...)
    results = engine.run_backtest(...)

    # Fetch Nifty 50 return for same period
    nifty_return = engine.calculate_buy_hold_return("^NSEI", "2023-01-01", "2024-12-31")

    # Calculate alpha
    alpha = results["total_return_pct"] - nifty_return

    assert "alpha" in results
    assert results["alpha"] == alpha
```

---

### AC-9: Generate Trade Log
**Given** backtest is complete
**When** I export the trade log
**Then** all trades are logged with details

**Test**:
```python
def test_generate_trade_log():
    engine = BacktestEngine(...)
    results = engine.run_backtest(...)

    trade_log = engine.export_trade_log()

    # Should have 100+ trades
    assert len(trade_log) >= 100

    # Each trade has required fields
    for trade in trade_log:
        assert "entry_date" in trade
        assert "exit_date" in trade
        assert "net_pnl" in trade
        assert "costs" in trade
        assert "slippage" in trade
```

---

### AC-10: Backtest Passes Success Criteria
**Given** 2-year backtest results
**When** I evaluate against success criteria
**Then**:
- Win rate ≥ 40%
- Calmar ratio ≥ 2.0
- Max drawdown < 10%
- Final capital > ₹1.2L (+20% from ₹1L)

**Test**:
```python
def test_backtest_success_criteria():
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run_backtest(start_date="2023-01-01", end_date="2024-12-31")

    # Success criteria
    assert results["win_rate"] >= 0.40, "Win rate must be >= 40%"
    assert results["calmar_ratio"] >= 2.0, "Calmar must be >= 2.0"
    assert results["max_drawdown_pct"] < 10.0, "Max DD must be < 10%"
    assert results["final_capital"] > 120000, "Final capital must be > ₹1.2L"

    print("✅ Backtest passed all success criteria!")
```

---

## Definition of Done

- [ ] All 10 acceptance criteria pass
- [ ] Code coverage ≥ 95% for backtest engine
- [ ] Documentation complete (how to run backtest)
- [ ] Trade log exported to CSV
- [ ] Performance report generated (PDF/HTML)
- [ ] Validated against manual calculations (sample 10 trades)
- [ ] Code reviewed and approved
- [ ] User approval obtained

---

## Technical Notes

### Backtest Engine Architecture

```python
class BacktestEngine:
    def __init__(self, initial_capital, start_date, end_date):
        self.capital = initial_capital
        self.peak_capital = initial_capital
        self.positions = []
        self.trade_log = []
        self.equity_curve = []

        # Components
        self.signal_generator = ADXDMAScanner()
        self.kelly_sizer = KellyPositionSizer(...)
        self.cost_calculator = CostCalculator()
        self.slippage_simulator = SlippageSimulator()
        self.risk_manager = RiskManager(...)

    def run_backtest(self):
        """Main backtest loop"""
        for date in trading_days:
            # 1. Generate signals
            signals = self.signal_generator.scan_all(date)

            # 2. For each signal
            for signal in signals:
                # 3. Calculate position size
                position = self.kelly_sizer.calculate_position_size(signal, ...)

                # 4. Check risk limits
                if not self.risk_manager.can_take_trade(position):
                    continue

                # 5. Execute with costs and slippage
                trade = self.execute_trade(signal, position)

                # 6. Track position
                self.positions.append(trade)

            # 7. Check exits
            self.check_exits(date)

            # 8. Update equity curve
            self.equity_curve.append(self.get_current_value())

        # 9. Calculate metrics
        return self.calculate_metrics()
```

---

## Dependencies

- **FX-003**: Signal Generation (ADX+DMA)
- **FX-002**: Kelly Position Sizing
- **FX-004**: Cost Calculator
- **FX-005**: Slippage Simulator
- **Data**: 2 years of historical OHLCV data

---

## Estimated Effort

- **Development**: 3 days
- **Testing**: 2 days
- **Validation**: 1 day
- **Total**: 6 days (8 story points)

---

**Status**: ✅ Story Complete
**Ready for Implementation**: Yes
