# FX-009: Paper Trading Engine

**Project**: BMAD Portfolio Management System
**Functional Requirement**: FR-9 (Paper Trading with Virtual Capital)
**Priority**: CRITICAL
**Created**: November 19, 2025
**Status**: Specification

---

## Table of Contents

1. [Overview](#overview)
2. [User Story](#user-story)
3. [Acceptance Criteria](#acceptance-criteria)
4. [Functional Design](#functional-design)
5. [Technical Specification](#technical-specification)
6. [API Contracts](#api-contracts)
7. [Data Models](#data-models)
8. [Business Rules](#business-rules)
9. [Test Cases](#test-cases)
10. [Edge Cases](#edge-cases)
11. [Performance Requirements](#performance-requirements)
12. [Dependencies](#dependencies)

---

## Overview

### Purpose

The Paper Trading Engine validates the trading system with virtual capital in real market conditions before risking real money. It's the FINAL gate before live trading.

### Background

**Why Paper Trading?**
- Validates backtest results in live markets
- Tests real-time execution logic
- Identifies production bugs before going live
- Builds operator confidence
- Required for 30-day validation period

**Paper Trading vs Backtesting**:

| Aspect | Backtesting | Paper Trading |
|--------|-------------|---------------|
| Data | Historical | Live/Real-time |
| Speed | Fast (days in seconds) | Real-time (1 day = 1 day) |
| Purpose | Strategy validation | System validation |
| Lookahead | Risk of bias | Zero risk |
| Costs | Simulated | Simulated (same) |
| Execution | Simulated | Simulated |

**Paper Trading vs Live Trading**:

| Aspect | Paper | Live |
|--------|-------|------|
| Capital | Virtual (₹1L) | Real (₹1L) |
| Orders | Simulated | Real API calls |
| Fills | Guaranteed | Market-dependent |
| Slippage | Simulated | Real |
| Risk | Zero | Real money risk |

### Scope

**In Scope**:
- Virtual capital management (₹1,00,000)
- Real-time signal generation
- Virtual order execution
- Real-time position tracking
- Stop-loss/target monitoring
- Daily PnL reports
- Telegram notifications
- 30-day validation period

**Out of Scope**:
- Real money trading
- Live order placement (handled by FX-010)
- Options paper trading

---

## User Story

**As** the Portfolio Manager
**I want** paper trading with virtual capital for 30 days
**So that** I can validate the system before risking real money

### Scenarios

#### Scenario 1: Start Paper Trading

**Given**:
- Backtest passed all criteria
- Initial virtual capital: ₹1,00,000

**When**: Start paper trading on 2025-11-19

**Then**:
1. Create virtual account with ₹1L
2. Initialize signal generator
3. Connect to live data source (Angel One)
4. Start daily trading cycle
5. Send startup notification via Telegram

#### Scenario 2: Daily Trading Cycle

**Given**:
- Paper trading active
- Date: 2025-11-20

**When**: Market opens (9:15 AM)

**Then**:
1. **9:00 AM**: Pre-market analysis
   - Fetch overnight news
   - Calculate sentiment
   - Detect market regime

2. **9:30 AM**: Signal generation
   - Generate ADX+DMA signals
   - Calculate position sizes
   - Create virtual orders

3. **9:40 AM**: Execute virtual orders
   - Simulate order placement
   - Apply slippage
   - Deduct costs from virtual capital
   - Add to virtual positions

4. **Throughout day**: Monitor positions
   - Check stop-losses every 5 minutes
   - Check targets
   - Exit if hit

5. **3:30 PM**: End-of-day reconciliation
   - Mark positions to market
   - Calculate daily PnL
   - Update virtual capital
   - Send daily report via Telegram

#### Scenario 3: Virtual Order Execution

**Given**:
- Signal: BUY RELIANCE @ ₹2,500
- Position size: 40 shares (₹1,00,000)
- Virtual capital: ₹1,00,000

**When**: Execute virtual order at 9:40 AM

**Then**:
1. Get live market price: ₹2,502 (slightly moved)
2. Apply slippage: +₹2 → Entry: ₹2,504
3. Calculate costs: ₹182 (STT, brokerage, GST, etc.)
4. Total cost: (40 × ₹2,504) + ₹182 = ₹1,00,342
5. Check: ₹1,00,342 > ₹1,00,000 ❌
6. Reduce shares: 39 shares → ₹97,656 + ₹178 = ₹97,834 ✅
7. Deduct from virtual capital: ₹1,00,000 - ₹97,834 = ₹2,166
8. Add position to virtual portfolio
9. Log: "VIRTUAL BUY: RELIANCE 39 shares @ ₹2,504"

#### Scenario 4: Stop-Loss Hit

**Given**:
- Virtual position: RELIANCE 39 shares, entry ₹2,504, stop ₹2,429
- Current time: 10:15 AM
- Live price: ₹2,425 (below stop)

**When**: Monitor positions (every 5 minutes)

**Then**:
1. Detect: Price (₹2,425) <= Stop (₹2,429) ✅
2. Create virtual exit order
3. Apply exit slippage: -₹2 → Exit: ₹2,423
4. Calculate gross PnL: (₹2,423 - ₹2,504) × 39 = -₹3,159
5. Calculate exit costs: ₹178
6. Net PnL: -₹3,159 - ₹178 - ₹182 (entry) = -₹3,519
7. Return cash: (39 × ₹2,423) - ₹178 = ₹94,319
8. Virtual capital: ₹2,166 + ₹94,319 = ₹96,485
9. Log trade: "VIRTUAL SELL: RELIANCE -₹3,519 (STOP_LOSS)"
10. Send Telegram alert: "⚠️ Stop-loss hit: RELIANCE -₹3,519"

---

## Acceptance Criteria

### Must Have

✅ **AC-1**: Initialize virtual account with ₹1,00,000
✅ **AC-2**: Generate real-time signals using live data (Angel One)
✅ **AC-3**: Execute virtual orders with realistic slippage and costs
✅ **AC-4**: Track all virtual positions with current PnL
✅ **AC-5**: Monitor stop-losses and targets every 5 minutes
✅ **AC-6**: Automatically exit positions when stop/target hit
✅ **AC-7**: Calculate daily PnL and update virtual capital
✅ **AC-8**: Send daily reports via Telegram:
  - Daily PnL
  - Current virtual capital
  - Open positions
  - Trades executed
✅ **AC-9**: Log all virtual trades to database
✅ **AC-10**: Run for 30 consecutive trading days without errors
✅ **AC-11**: Enforce 2% max drawdown rule
✅ **AC-12**: Match backtest predictions (±10%)

### Should Have

⭕ **AC-13**: Web dashboard to view virtual portfolio
⭕ **AC-14**: Historical equity curve visualization
⭕ **AC-15**: Trade alerts via email

### Nice to Have

🔵 **AC-16**: Pause/resume paper trading
🔵 **AC-17**: Reset virtual capital mid-session
🔵 **AC-18**: Compare paper vs live performance

---

## Functional Design

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  PaperTradingEngine                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  VirtualAccountManager                                │ │
│  │  - Track virtual cash                                 │ │
│  │  - Track virtual positions                            │ │
│  │  - Calculate total equity                             │ │
│  │  - Enforce risk limits                                │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  RealTimeDataFeed                                     │ │
│  │  - Connect to Angel One                               │ │
│  │  - Fetch live prices                                  │ │
│  │  - Stream market data                                 │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  DailyTradingCycle                                    │ │
│  │  - Pre-market: Sentiment analysis                     │ │
│  │  - 9:30 AM: Generate signals                          │ │
│  │  - 9:40 AM: Execute virtual orders                    │ │
│  │  - Throughout: Monitor positions                      │ │
│  │  - 3:30 PM: Reconciliation                            │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  VirtualOrderExecutor                                 │ │
│  │  - Simulate order placement                           │ │
│  │  - Apply slippage (realistic)                         │ │
│  │  - Calculate costs                                    │ │
│  │  - Update virtual portfolio                           │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  PositionMonitor                                      │ │
│  │  - Fetch live prices every 5 min                      │ │
│  │  - Check stop-losses                                  │ │
│  │  - Check targets                                      │ │
│  │  - Trigger exits                                      │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  TelegramNotifier                                     │ │
│  │  - Send daily reports                                 │ │
│  │  - Send trade alerts                                  │ │
│  │  - Send error notifications                           │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Daily Workflow

```
Time: 9:00 AM (Pre-Market)
├─ Fetch overnight news
├─ Calculate sentiment score
├─ Detect market regime
└─ Prepare for signal generation

Time: 9:30 AM (Signal Generation)
├─ For each symbol in watchlist:
│  ├─ Fetch latest OHLCV (up to yesterday)
│  ├─ Calculate ADX, DMA
│  ├─ Check signal criteria
│  └─ Generate BUY/SELL signal
├─ Calculate position sizes (Kelly)
├─ Check risk limits
└─ Create virtual order list

Time: 9:40 AM (Order Execution)
├─ For each virtual order:
│  ├─ Get live market price
│  ├─ Simulate order placement
│  ├─ Apply slippage
│  ├─ Calculate costs
│  ├─ Deduct from virtual capital
│  └─ Add to virtual positions
└─ Log all executions

Time: 10:00 AM - 3:30 PM (Position Monitoring)
├─ Every 5 minutes:
│  ├─ Fetch live prices for open positions
│  ├─ Check stop-losses
│  ├─ Check targets
│  ├─ Exit if hit
│  └─ Update unrealized PnL

Time: 3:30 PM (End-of-Day Reconciliation)
├─ Mark all positions to market (closing prices)
├─ Calculate total equity
├─ Calculate daily PnL
├─ Update peak capital
├─ Calculate drawdown
├─ Generate daily report
└─ Send Telegram notification
```

---

## Technical Specification

### Class: `PaperTradingEngine`

```python
# paper_trading/paper_engine.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
import time
import logging

@dataclass
class VirtualPosition:
    """Virtual position"""
    symbol: str
    side: str
    entry_date: datetime
    entry_price: float
    shares: int
    stop_loss: float
    target: float
    entry_costs: float
    entry_slippage: float
    unrealized_pnl: float = 0.0

@dataclass
class DailyReport:
    """Daily paper trading report"""
    date: datetime
    starting_capital: float
    ending_capital: float
    daily_pnl: float
    daily_return_pct: float
    trades_executed: int
    open_positions: int
    peak_capital: float
    current_drawdown_pct: float

class PaperTradingEngine:
    """
    Paper trading with virtual capital

    Responsibilities:
    - Manage virtual account
    - Execute virtual orders
    - Monitor positions in real-time
    - Generate daily reports
    - Validate system before live trading
    """

    def __init__(
        self,
        initial_capital: float,
        data_source,
        signal_generator,
        position_sizer,
        cost_calculator,
        slippage_simulator,
        telegram_bot,
    ):
        """
        Initialize Paper Trading Engine

        Args:
            initial_capital: Starting virtual capital
            data_source: DataIngestionManager (live data)
            signal_generator: ADXDMASignalGenerator
            position_sizer: KellyPositionSizer
            cost_calculator: CostCalculator
            slippage_simulator: SlippageSimulator
            telegram_bot: TelegramBot instance
        """
        self.initial_capital = initial_capital
        self.virtual_cash = initial_capital
        self.virtual_equity = initial_capital
        self.peak_capital = initial_capital

        self.data_source = data_source
        self.signal_generator = signal_generator
        self.position_sizer = position_sizer
        self.cost_calculator = cost_calculator
        self.slippage_simulator = slippage_simulator
        self.telegram_bot = telegram_bot

        self.logger = logging.getLogger(__name__)

        # State
        self.virtual_positions: List[VirtualPosition] = []
        self.trade_log = []
        self.daily_equity = []
        self.start_date = None
        self.is_running = False

    def start_paper_trading(self, watchlist: List[str]):
        """
        Start paper trading

        Args:
            watchlist: List of symbols to trade
        """
        self.start_date = datetime.now()
        self.is_running = True

        self.logger.info(
            f"Starting paper trading with ₹{self.initial_capital:,.0f}"
        )

        # Send startup notification
        self.telegram_bot.send_message(
            f"📊 Paper Trading Started\n"
            f"💰 Virtual Capital: ₹{self.initial_capital:,.0f}\n"
            f"📅 Start Date: {self.start_date.date()}\n"
            f"📈 Watchlist: {len(watchlist)} symbols"
        )

        # Run daily trading cycle
        self.run_daily_cycle(watchlist)

    def run_daily_cycle(self, watchlist: List[str]):
        """Run daily trading cycle"""

        while self.is_running:
            current_time = datetime.now()

            # Check if market is open (9:15 AM - 3:30 PM IST)
            if not self._is_market_open(current_time):
                self.logger.info("Market closed. Waiting...")
                time.sleep(300)  # Check every 5 minutes
                continue

            # Step 1: Pre-market (9:00-9:30 AM)
            if current_time.hour == 9 and current_time.minute < 30:
                self._pre_market_routine()

            # Step 2: Signal generation (9:30 AM)
            if current_time.hour == 9 and current_time.minute == 30:
                self._generate_and_execute_signals(watchlist)

            # Step 3: Position monitoring (throughout day)
            if current_time.hour >= 9 and current_time.hour < 15:
                self._monitor_positions()
                time.sleep(300)  # Check every 5 minutes

            # Step 4: End-of-day (3:30 PM)
            if current_time.hour == 15 and current_time.minute == 30:
                self._end_of_day_routine()

            time.sleep(60)  # Check every minute

    def _pre_market_routine(self):
        """Pre-market analysis"""
        self.logger.info("Pre-market routine...")

        # Fetch sentiment, regime, etc.
        # (Placeholder for now)

    def _generate_and_execute_signals(self, watchlist: List[str]):
        """Generate signals and execute virtual orders"""

        self.logger.info("Generating signals...")

        # Generate signals
        signals = self.signal_generator.generate_signals(
            watchlist=watchlist,
            data_source=self.data_source,
            timestamp=datetime.now(),
        )

        self.logger.info(f"Generated {len(signals)} signals")

        # Execute virtual orders
        for signal in signals:
            self._execute_virtual_order(signal)

    def _execute_virtual_order(self, signal):
        """Execute virtual order"""

        # Calculate position size
        position = self.position_sizer.calculate_position_size(
            signal=signal.__dict__,
            current_capital=self.virtual_equity,
            peak_capital=self.peak_capital,
        )

        if not position.approved:
            self.logger.warning(
                f"Position rejected: {position.rejection_reason}"
            )
            return

        # Get live market price
        live_price_result = self.data_source.fetch_ohlcv(
            symbol=signal.symbol,
            timeframe="1min",
            use_cache=False,
        )

        if not live_price_result.success:
            self.logger.error(f"Failed to get live price for {signal.symbol}")
            return

        current_price = live_price_result.data.iloc[-1]["close"]

        # Apply slippage
        slippage_result = self.slippage_simulator.calculate_slippage(
            symbol=signal.symbol,
            side=signal.side,
            order_value=position.position_value,
            reference_price=current_price,
        )

        actual_entry_price = slippage_result.adjusted_price

        # Calculate costs
        costs = self.cost_calculator.calculate_equity_delivery_costs(
            side=signal.side,
            transaction_value=position.position_value,
        )

        # Total cost
        total_cost = position.position_value + costs.total

        # Check if we have enough cash
        if total_cost > self.virtual_cash:
            self.logger.warning(
                f"Insufficient virtual cash. Need ₹{total_cost:,.0f}, "
                f"have ₹{self.virtual_cash:,.0f}"
            )
            return

        # Execute
        self.virtual_cash -= total_cost

        # Add position
        virtual_position = VirtualPosition(
            symbol=signal.symbol,
            side=signal.side,
            entry_date=datetime.now(),
            entry_price=actual_entry_price,
            shares=position.shares,
            stop_loss=signal.stop_loss,
            target=signal.target,
            entry_costs=costs.total,
            entry_slippage=slippage_result.slippage_amount,
        )

        self.virtual_positions.append(virtual_position)

        self.logger.info(
            f"VIRTUAL {signal.side}: {signal.symbol} {position.shares} shares "
            f"@ ₹{actual_entry_price:.2f} "
            f"(slippage: ₹{slippage_result.slippage_amount:.2f})"
        )

        # Send Telegram notification
        self.telegram_bot.send_message(
            f"✅ Virtual {signal.side}\n"
            f"📊 {signal.symbol}\n"
            f"🔢 Qty: {position.shares}\n"
            f"💰 Price: ₹{actual_entry_price:.2f}\n"
            f"🛑 Stop: ₹{signal.stop_loss:.2f}\n"
            f"🎯 Target: ₹{signal.target:.2f}"
        )

    def _monitor_positions(self):
        """Monitor positions and check for exits"""

        for position in self.virtual_positions[:]:  # Copy list
            # Get live price
            live_price_result = self.data_source.fetch_ohlcv(
                symbol=position.symbol,
                timeframe="1min",
                use_cache=False,
            )

            if not live_price_result.success:
                continue

            current_price = live_price_result.data.iloc[-1]["close"]

            # Update unrealized PnL
            if position.side == "BUY":
                position.unrealized_pnl = (
                    (current_price - position.entry_price) * position.shares
                )
            else:
                position.unrealized_pnl = (
                    (position.entry_price - current_price) * position.shares
                )

            # Check stop-loss
            if position.side == "BUY" and current_price <= position.stop_loss:
                self._exit_virtual_position(position, "STOP_LOSS", current_price)
                continue

            # Check target
            if position.side == "BUY" and current_price >= position.target:
                self._exit_virtual_position(position, "TARGET", current_price)
                continue

    def _exit_virtual_position(
        self,
        position: VirtualPosition,
        exit_reason: str,
        exit_price: float,
    ):
        """Exit virtual position"""

        # Apply exit slippage
        exit_slippage_result = self.slippage_simulator.calculate_slippage(
            symbol=position.symbol,
            side="SELL" if position.side == "BUY" else "BUY",
            order_value=exit_price * position.shares,
            reference_price=exit_price,
        )

        actual_exit_price = exit_slippage_result.adjusted_price

        # Calculate exit costs
        exit_costs = self.cost_calculator.calculate_equity_delivery_costs(
            side="SELL" if position.side == "BUY" else "BUY",
            transaction_value=exit_price * position.shares,
        ).total

        # Calculate PnL
        if position.side == "BUY":
            gross_pnl = (actual_exit_price - position.entry_price) * position.shares
        else:
            gross_pnl = (position.entry_price - actual_exit_price) * position.shares

        net_pnl = (
            gross_pnl
            - position.entry_costs
            - exit_costs
            - position.entry_slippage
            - exit_slippage_result.slippage_amount
        )

        # Return cash
        self.virtual_cash += (
            actual_exit_price * position.shares - exit_costs
        )

        # Log trade
        trade = {
            "symbol": position.symbol,
            "side": position.side,
            "entry_date": position.entry_date,
            "entry_price": position.entry_price,
            "exit_date": datetime.now(),
            "exit_price": actual_exit_price,
            "shares": position.shares,
            "net_pnl": net_pnl,
            "exit_reason": exit_reason,
        }

        self.trade_log.append(trade)

        # Remove position
        self.virtual_positions.remove(position)

        self.logger.info(
            f"VIRTUAL EXIT: {position.symbol} @ ₹{actual_exit_price:.2f} "
            f"| PnL: ₹{net_pnl:,.2f} | Reason: {exit_reason}"
        )

        # Send Telegram alert
        emoji = "✅" if net_pnl > 0 else "❌"
        self.telegram_bot.send_message(
            f"{emoji} Virtual {exit_reason}\n"
            f"📊 {position.symbol}\n"
            f"💰 Exit: ₹{actual_exit_price:.2f}\n"
            f"📈 PnL: ₹{net_pnl:,.2f}"
        )

    def _end_of_day_routine(self):
        """End-of-day reconciliation"""

        self.logger.info("End-of-day routine...")

        # Calculate unrealized PnL
        unrealized_pnl = sum(
            pos.unrealized_pnl for pos in self.virtual_positions
        )

        # Total equity
        self.virtual_equity = self.virtual_cash + unrealized_pnl

        # Update peak
        self.peak_capital = max(self.peak_capital, self.virtual_equity)

        # Calculate daily PnL
        yesterday_equity = (
            self.daily_equity[-1]["equity"] if self.daily_equity else self.initial_capital
        )
        daily_pnl = self.virtual_equity - yesterday_equity
        daily_return_pct = daily_pnl / yesterday_equity

        # Record equity
        self.daily_equity.append({
            "date": datetime.now().date(),
            "equity": self.virtual_equity,
        })

        # Calculate drawdown
        drawdown_pct = (self.peak_capital - self.virtual_equity) / self.peak_capital

        # Generate report
        report = DailyReport(
            date=datetime.now(),
            starting_capital=yesterday_equity,
            ending_capital=self.virtual_equity,
            daily_pnl=daily_pnl,
            daily_return_pct=daily_return_pct,
            trades_executed=len(self.trade_log),
            open_positions=len(self.virtual_positions),
            peak_capital=self.peak_capital,
            current_drawdown_pct=drawdown_pct,
        )

        # Send daily report
        self._send_daily_report(report)

    def _send_daily_report(self, report: DailyReport):
        """Send daily report via Telegram"""

        emoji = "📈" if report.daily_pnl > 0 else "📉"

        message = (
            f"{emoji} Daily Paper Trading Report\n"
            f"📅 Date: {report.date.date()}\n"
            f"💰 Capital: ₹{report.ending_capital:,.0f}\n"
            f"📊 Daily PnL: ₹{report.daily_pnl:,.0f} ({report.daily_return_pct:.2%})\n"
            f"🔝 Peak: ₹{report.peak_capital:,.0f}\n"
            f"📉 Drawdown: {report.current_drawdown_pct:.2%}\n"
            f"📈 Open: {report.open_positions}\n"
            f"✅ Trades: {report.trades_executed}"
        )

        self.telegram_bot.send_message(message)

        self.logger.info(f"Daily report sent: {report.date.date()}")

    def _is_market_open(self, current_time: datetime) -> bool:
        """Check if market is open"""

        # Market hours: 9:15 AM - 3:30 PM IST
        # Weekdays only

        if current_time.weekday() >= 5:  # Saturday/Sunday
            return False

        hour = current_time.hour
        minute = current_time.minute

        if hour < 9 or (hour == 9 and minute < 15):
            return False

        if hour > 15 or (hour == 15 and minute > 30):
            return False

        return True
```

---

## API Contracts

### Input: Start Paper Trading

```python
paper_engine = PaperTradingEngine(
    initial_capital=100000,
    data_source=ingestion_manager,
    signal_generator=adx_dma_generator,
    position_sizer=kelly_sizer,
    cost_calculator=cost_calc,
    slippage_simulator=slippage_sim,
    telegram_bot=telegram,
)

watchlist = ["RELIANCE-EQ", "TCS-EQ", "INFY-EQ"]

paper_engine.start_paper_trading(watchlist)
```

### Output: Daily Report

```python
DailyReport(
    date=datetime(2025, 11, 20),
    starting_capital=100000,
    ending_capital=101200,
    daily_pnl=1200,
    daily_return_pct=0.012,  # +1.2%
    trades_executed=3,
    open_positions=2,
    peak_capital=101200,
    current_drawdown_pct=0.0,
)
```

---

## Business Rules

### BR-1: Virtual vs Real Capital

**Rule**: Virtual capital tracked separately from real money

**Implementation**:
```python
# Never mix virtual and real capital
virtual_cash = 100000  # Virtual
real_cash = 0  # Real (not used in paper trading)
```

### BR-2: Realistic Slippage

**Rule**: Same slippage model as backtest and live

**Implementation**:
```python
# Use same SlippageSimulator as backtest
slippage_result = slippage_simulator.calculate_slippage(...)
```

### BR-3: Real-Time Execution

**Rule**: Execute orders with live data (not delayed)

**Implementation**:
```python
# Fetch live price (use_cache=False)
live_price = data_source.fetch_ohlcv(use_cache=False)
```

### BR-4: 30-Day Validation

**Rule**: Must run for 30 consecutive trading days

**Implementation**:
```python
trading_days = 0
while trading_days < 30:
    if is_market_open():
        run_daily_cycle()
        trading_days += 1
```

---

## Test Cases

### TC-001: Initialize Paper Trading

**Test Code**:
```python
def test_initialize_paper_trading():
    engine = PaperTradingEngine(initial_capital=100000, ...)

    assert engine.virtual_cash == 100000
    assert engine.virtual_equity == 100000
    assert len(engine.virtual_positions) == 0
```

### TC-002: Execute Virtual Order

**Test Code**:
```python
def test_execute_virtual_order(mocker):
    engine = PaperTradingEngine(...)

    # Mock signal
    signal = TradingSignal(
        symbol="RELIANCE",
        side="BUY",
        entry_price=2500,
        stop_loss=2400,
        target=2700,
        # ...
    )

    # Execute
    engine._execute_virtual_order(signal)

    # Check position added
    assert len(engine.virtual_positions) == 1
    assert engine.virtual_cash < 100000  # Cash reduced
```

### TC-003: Stop-Loss Exit

**Test Code**:
```python
def test_stop_loss_exit(mocker):
    engine = PaperTradingEngine(...)

    # Add position
    position = VirtualPosition(
        symbol="RELIANCE",
        side="BUY",
        entry_price=2500,
        stop_loss=2400,
        shares=10,
        # ...
    )
    engine.virtual_positions.append(position)

    # Mock price dropping
    mocker.patch.object(
        engine.data_source,
        "fetch_ohlcv",
        return_value=DataFetchResult(
            success=True,
            data=pd.DataFrame({"close": [2390]}),
            source="live",
        ),
    )

    # Monitor positions
    engine._monitor_positions()

    # Position should be closed
    assert len(engine.virtual_positions) == 0
    assert len(engine.trade_log) == 1
```

---

## Edge Cases

### Edge Case 1: Market Closed

**Scenario**: Try to trade on Saturday

**Expected**:
- Detect market closed
- Skip trading
- Wait until Monday

**Implementation**:
```python
if current_time.weekday() >= 5:
    logger.info("Market closed (weekend)")
    return
```

### Edge Case 2: No Live Data

**Scenario**: Angel One API fails

**Expected**:
- Log error
- Skip order execution
- Retry on next cycle

**Implementation**:
```python
if not live_price_result.success:
    logger.error("Failed to fetch live price")
    return  # Skip this order
```

---

## Performance Requirements

### PR-1: Position Monitoring Latency

**Requirement**: Check positions within 10 seconds

**Implementation**:
- Use efficient price fetch
- Cache positions in memory
- Parallelize checks if > 10 positions

### PR-2: Daily Report Generation

**Requirement**: Send report within 1 minute of market close

---

## Dependencies

### Internal Dependencies

- **FX-001**: Data Ingestion (live data)
- **FX-002**: Kelly Position Sizer
- **FX-003**: Signal Generator
- **FX-004**: Cost Calculator
- **FX-005**: Slippage Simulator

### External Dependencies

- **Telegram Bot API**: For notifications
- **Angel One API**: For live data

---

## Implementation Checklist

- [ ] Create `paper_trading/paper_engine.py`
- [ ] Implement virtual account management
- [ ] Implement real-time data feed
- [ ] Implement position monitoring
- [ ] Implement Telegram notifications
- [ ] Write 10 unit tests
- [ ] Write 3 integration tests
- [ ] 30-day validation test
- [ ] Documentation

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: FX-010 (Order Executor Angel One)
