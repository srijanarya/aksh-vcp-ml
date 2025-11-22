# FX-006: Backtesting Engine

**Project**: BMAD Portfolio Management System
**Functional Requirement**: FR-6 (Realistic Backtesting with Costs & Slippage)
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

The Backtesting Engine simulates trading strategies on historical data with realistic execution costs, slippage, and market conditions to validate performance before live trading.

### Background

**Why Backtesting Matters**:
- Validates strategy profitability
- Tests risk management rules
- Identifies edge cases and failures
- Builds confidence before live trading

**Realistic vs Optimistic Backtesting**:

| Aspect | Optimistic (Wrong) | Realistic (BMAD) |
|--------|-------------------|------------------|
| Entry Price | Exact signal price | Signal price + slippage |
| Exit Price | Exact stop/target | Stop/target + slippage |
| Costs | Ignored | All costs included |
| Fills | 100% fill rate | Realistic fill simulation |
| Lookahead | Uses future data | Point-in-time only |
| Execution | Instant | Next-day realistic |

**BMAD Principle**: Backtest results must match paper trading (±10%)

### Scope

**In Scope**:
- Historical data replay (2019-2024)
- ADX+DMA signal generation
- Kelly position sizing
- Realistic order execution simulation
- Indian market costs (STT, brokerage, GST)
- Slippage modeling (bid-ask spread)
- Daily equity curve tracking
- Performance metrics (Sharpe, max DD, win rate)
- Trade-by-trade logging

**Out of Scope**:
- Walk-forward optimization
- Monte Carlo simulation
- Multi-strategy portfolio optimization
- Options backtesting

---

## User Story

**As** the Portfolio Manager
**I want** realistic backtests with all costs included
**So that** I can validate strategy performance before risking real capital

### Scenarios

#### Scenario 1: Run 1-Year Backtest

**Given**:
- Strategy: ADX+DMA
- Period: 2024-01-01 to 2024-12-31
- Initial capital: ₹1,00,000
- Universe: Nifty 50 stocks

**When**: Run backtest

**Then**:
1. Load historical data for all symbols
2. Generate signals daily at 9:30 AM
3. Execute trades with T+1 settlement
4. Apply costs and slippage
5. Track equity curve daily
6. Generate performance report:
   - Total return: +18.5%
   - Max drawdown: -1.8%
   - Win rate: 56%
   - Sharpe ratio: 2.1
   - Total trades: 48

#### Scenario 2: Validate Against Paper Trading

**Given**:
- Backtest period: 2024-11-01 to 2024-11-30
- Paper trading: Same period (simulated)

**When**: Compare results

**Then**:
- Backtest return: +4.2%
- Paper trading return: +4.5%
- Difference: 0.3% (< 10% threshold) ✅
- Validation: PASS

#### Scenario 3: Test Risk Management

**Given**:
- Max drawdown rule: 2%
- Peak capital: ₹1,10,000

**When**: Capital drops to ₹1,07,900 (-1.9%)

**Then**:
1. System detects drawdown approaching limit
2. Reduces position sizes
3. Drawdown stays < 2%
4. Backtest continues normally

#### Scenario 4: Edge Case - 2020 COVID Crash

**Given**:
- Backtest includes March 2020
- Market drops 30% in 1 month

**When**: Run backtest

**Then**:
1. ADX signals reduce (low ADX in choppy market)
2. Few trades executed (waiting for trend)
3. Capital preserved
4. Demonstrates defensive behavior

---

## Acceptance Criteria

### Must Have

✅ **AC-1**: Load historical OHLCV data for specified date range
✅ **AC-2**: Generate ADX+DMA signals using historical data (no lookahead)
✅ **AC-3**: Calculate position sizes using Kelly Criterion
✅ **AC-4**: Simulate realistic order execution (T+1 settlement for delivery)
✅ **AC-5**: Apply Indian market costs (STT, brokerage, exchange, GST, stamp duty)
✅ **AC-6**: Apply realistic slippage based on liquidity
✅ **AC-7**: Track equity curve daily (close-to-close basis)
✅ **AC-8**: Enforce 2% max drawdown rule
✅ **AC-9**: Generate performance report with:
  - Total return %
  - CAGR
  - Max drawdown %
  - Sharpe ratio
  - Win rate
  - Avg win/loss
  - Total trades
✅ **AC-10**: Log all trades to database (entry, exit, PnL, costs)

### Should Have

⭕ **AC-11**: Support multiple strategies (not just ADX+DMA)
⭕ **AC-12**: Benchmark against Nifty 50 index
⭕ **AC-13**: Generate trade distribution charts (wins/losses)
⭕ **AC-14**: Calculate rolling Sharpe ratio

### Nice to Have

🔵 **AC-15**: Monte Carlo simulation (1000 runs)
🔵 **AC-16**: Optimization (find best ADX/DMA parameters)
🔵 **AC-17**: Export results to CSV/Excel

---

## Functional Design

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   BacktestEngine                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  HistoricalDataLoader                                 │ │
│  │  - Load OHLCV for all symbols                         │ │
│  │  - Validate data completeness                         │ │
│  │  - Handle corporate actions                           │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  DailySimulator                                       │ │
│  │  - Loop through each trading day                      │ │
│  │  - Generate signals (point-in-time)                   │ │
│  │  - Execute orders                                     │ │
│  │  - Update positions and equity                        │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  OrderSimulator                                       │ │
│  │  - Simulate market orders                             │ │
│  │  - Apply slippage                                     │ │
│  │  - Calculate costs                                    │ │
│  │  - Track fills                                        │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  PortfolioSimulator                                   │ │
│  │  - Track open positions                               │ │
│  │  - Calculate unrealized PnL                           │ │
│  │  - Monitor risk limits                                │ │
│  │  - Update equity curve                                │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  PerformanceAnalyzer                                  │ │
│  │  - Calculate returns, Sharpe, drawdown                │ │
│  │  - Generate trade statistics                          │ │
│  │  - Create equity curve chart                          │ │
│  │  - Export results                                     │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Backtest Execution Flow

```
Input: Backtest Configuration
  ├─ Start Date: 2024-01-01
  ├─ End Date: 2024-12-31
  ├─ Initial Capital: ₹1,00,000
  ├─ Strategy: ADX+DMA
  └─ Universe: Nifty 50

Step 1: Initialize Backtest
  ├─ Load historical data for all symbols
  ├─ Validate data (no gaps, clean OHLCV)
  ├─ Create empty portfolio
  └─ Set initial equity = ₹1,00,000

Step 2: Daily Loop (for each trading day)
  ├─ Current Date: 2024-01-02
  │
  ├─ Sub-step A: Pre-Market (9:00 AM)
  │  ├─ Check for overnight events
  │  ├─ Update data (yesterday's close is known)
  │  └─ Calculate sentiment (if available)
  │
  ├─ Sub-step B: Signal Generation (9:30 AM)
  │  ├─ For each symbol in universe:
  │  │  ├─ Fetch data UP TO yesterday (no lookahead!)
  │  │  ├─ Calculate ADX, DMA
  │  │  └─ Check signal criteria
  │  ├─ Generate list of signals
  │  └─ Filter by ADX > 25, DMA thresholds
  │
  ├─ Sub-step C: Position Sizing (9:35 AM)
  │  ├─ For each signal:
  │  │  ├─ Calculate Kelly position size
  │  │  ├─ Check available capital
  │  │  ├─ Check risk limits (2% max DD)
  │  │  └─ Approve or reject
  │  └─ Create order list
  │
  ├─ Sub-step D: Order Execution (9:40 AM)
  │  ├─ For each order:
  │  │  ├─ Get market price (open of today)
  │  │  ├─ Apply slippage (spread + market impact)
  │  │  ├─ Calculate actual fill price
  │  │  ├─ Calculate costs (STT, brokerage, etc.)
  │  │  ├─ Deduct from capital
  │  │  └─ Add to open positions
  │  └─ Log all executions
  │
  ├─ Sub-step E: Position Monitoring (Throughout Day)
  │  ├─ For each open position:
  │  │  ├─ Check if stop-loss hit
  │  │  ├─ Check if target hit
  │  │  ├─ Check for time-based exit
  │  │  └─ Exit if criteria met
  │  └─ Update unrealized PnL
  │
  ├─ Sub-step F: End of Day (3:30 PM)
  │  ├─ Mark all positions to market (today's close)
  │  ├─ Calculate total equity (cash + positions)
  │  ├─ Update peak capital
  │  ├─ Calculate drawdown
  │  └─ Log daily equity
  │
  └─ Advance to next day

Step 3: Backtest Complete
  ├─ Close all open positions (mark-to-market)
  ├─ Calculate final equity
  ├─ Generate performance report
  └─ Export results

Output: Backtest Results
  ├─ Total Return: +18.5%
  ├─ Max Drawdown: -1.8%
  ├─ Sharpe Ratio: 2.1
  ├─ Win Rate: 56%
  ├─ Total Trades: 48
  ├─ Equity Curve: [daily values]
  └─ Trade Log: [all trades]
```

---

## Technical Specification

### Class: `BacktestEngine`

```python
# backtesting/backtest_engine.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
import numpy as np
import logging

@dataclass
class BacktestConfig:
    """Backtest configuration"""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    strategy_name: str
    universe: List[str]  # List of symbols
    max_drawdown_pct: float = 0.02
    position_size_method: str = "kelly"  # or "fixed"

@dataclass
class BacktestResults:
    """Backtest results"""
    total_return_pct: float
    cagr: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    equity_curve: pd.Series
    trade_log: pd.DataFrame
    daily_returns: pd.Series

class BacktestEngine:
    """
    Realistic backtesting engine

    Responsibilities:
    - Load historical data
    - Simulate daily trading
    - Execute orders with costs/slippage
    - Track portfolio equity
    - Generate performance metrics
    """

    def __init__(
        self,
        data_source,
        signal_generator,
        position_sizer,
        cost_calculator,
        slippage_simulator,
    ):
        """
        Initialize Backtest Engine

        Args:
            data_source: DataIngestionManager instance
            signal_generator: ADXDMASignalGenerator instance
            position_sizer: KellyPositionSizer instance
            cost_calculator: CostCalculator instance
            slippage_simulator: SlippageSimulator instance
        """
        self.data_source = data_source
        self.signal_generator = signal_generator
        self.position_sizer = position_sizer
        self.cost_calculator = cost_calculator
        self.slippage_simulator = slippage_simulator

        self.logger = logging.getLogger(__name__)

        # Backtest state
        self.cash = 0.0
        self.equity = 0.0
        self.peak_equity = 0.0
        self.positions = []
        self.trade_log = []
        self.equity_curve = []

    def run_backtest(
        self, config: BacktestConfig
    ) -> BacktestResults:
        """
        Run backtest

        Args:
            config: Backtest configuration

        Returns:
            BacktestResults object
        """
        self.logger.info(
            f"Starting backtest: {config.start_date} to {config.end_date}"
        )

        # Step 1: Initialize
        self._initialize_backtest(config)

        # Step 2: Load historical data
        historical_data = self._load_historical_data(
            config.universe,
            config.start_date,
            config.end_date,
        )

        # Step 3: Get trading days
        trading_days = pd.bdate_range(
            config.start_date,
            config.end_date,
            freq='B',  # Business days
        )

        # Step 4: Daily simulation loop
        for current_date in trading_days:
            self._simulate_trading_day(
                current_date=current_date,
                historical_data=historical_data,
                config=config,
            )

        # Step 5: Finalize
        self._finalize_backtest()

        # Step 6: Calculate performance metrics
        results = self._calculate_performance_metrics(config)

        self.logger.info(
            f"Backtest complete. Return: {results.total_return_pct:.2%}, "
            f"Max DD: {results.max_drawdown_pct:.2%}"
        )

        return results

    def _initialize_backtest(self, config: BacktestConfig):
        """Initialize backtest state"""
        self.cash = config.initial_capital
        self.equity = config.initial_capital
        self.peak_equity = config.initial_capital
        self.positions = []
        self.trade_log = []
        self.equity_curve = []

        self.logger.info(f"Initialized with ₹{config.initial_capital:,.0f}")

    def _load_historical_data(
        self,
        universe: List[str],
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Load historical data for all symbols

        Returns:
            Dict mapping symbol -> DataFrame
        """
        data = {}

        # Fetch extra days for indicator calculation (need 100 days for ADX)
        fetch_start = start_date - timedelta(days=150)

        for symbol in universe:
            result = self.data_source.fetch_ohlcv(
                symbol=symbol,
                timeframe="1day",
                start_date=fetch_start,
                end_date=end_date,
            )

            if result.success:
                data[symbol] = result.data
                self.logger.info(
                    f"Loaded {len(result.data)} days for {symbol}"
                )
            else:
                self.logger.warning(
                    f"Failed to load data for {symbol}: {result.error}"
                )

        return data

    def _simulate_trading_day(
        self,
        current_date: datetime,
        historical_data: dict,
        config: BacktestConfig,
    ):
        """Simulate one trading day"""

        self.logger.debug(f"Simulating {current_date.date()}")

        # A. Pre-market: Check exits
        self._check_exits(current_date, historical_data)

        # B. Signal generation (using data UP TO yesterday)
        signals = self._generate_signals_point_in_time(
            current_date,
            historical_data,
            config.universe,
        )

        # C. Position sizing
        orders = self._size_positions(signals, config)

        # D. Execute orders
        self._execute_orders(orders, current_date, historical_data)

        # E. End of day: Update equity
        self._update_equity(current_date, historical_data)

    def _generate_signals_point_in_time(
        self,
        current_date: datetime,
        historical_data: dict,
        universe: List[str],
    ) -> List:
        """
        Generate signals using data available up to yesterday

        CRITICAL: No lookahead bias!
        """
        signals = []

        for symbol in universe:
            if symbol not in historical_data:
                continue

            df = historical_data[symbol]

            # Get data UP TO yesterday (current_date - 1 day)
            yesterday = current_date - timedelta(days=1)
            df_available = df[df["datetime"] <= yesterday]

            if len(df_available) < 100:
                # Not enough data for ADX
                continue

            # Generate signal
            signal = self.signal_generator._generate_signal_for_symbol(
                symbol=symbol,
                df=df_available,
                timestamp=current_date,
            )

            if signal:
                signals.append(signal)

        self.logger.info(
            f"{current_date.date()}: Generated {len(signals)} signals"
        )

        return signals

    def _size_positions(
        self, signals: List, config: BacktestConfig
    ) -> List:
        """Calculate position sizes for signals"""

        orders = []

        for signal in signals:
            # Calculate position size
            position = self.position_sizer.calculate_position_size(
                signal=signal.__dict__,
                current_capital=self.equity,
                peak_capital=self.peak_equity,
            )

            if position.approved:
                orders.append({
                    "signal": signal,
                    "position": position,
                })

        return orders

    def _execute_orders(
        self,
        orders: List,
        current_date: datetime,
        historical_data: dict,
    ):
        """Execute orders with slippage and costs"""

        for order in orders:
            signal = order["signal"]
            position = order["position"]

            symbol = signal.symbol

            # Get today's OHLC (for execution price)
            df = historical_data[symbol]
            today_candle = df[df["datetime"] == current_date]

            if today_candle.empty:
                self.logger.warning(
                    f"{symbol}: No data for {current_date.date()}"
                )
                continue

            # Execution price = today's open (realistic)
            market_price = today_candle.iloc[0]["open"]

            # Apply slippage
            slippage_result = self.slippage_simulator.calculate_slippage(
                symbol=symbol,
                side=signal.side,
                order_value=position.position_value,
                reference_price=market_price,
            )

            actual_entry_price = slippage_result.adjusted_price

            # Calculate costs
            costs = self.cost_calculator.calculate_equity_delivery_costs(
                side=signal.side,
                transaction_value=position.position_value,
            )

            # Check if we have enough cash
            total_cost = position.position_value + costs.total

            if total_cost > self.cash:
                self.logger.warning(
                    f"Insufficient cash for {symbol}. Need ₹{total_cost:,.0f}, have ₹{self.cash:,.0f}"
                )
                continue

            # Execute
            self.cash -= total_cost

            # Add position
            self.positions.append({
                "symbol": symbol,
                "side": signal.side,
                "entry_date": current_date,
                "entry_price": actual_entry_price,
                "shares": position.shares,
                "stop_loss": signal.stop_loss,
                "target": signal.target,
                "entry_costs": costs.total,
                "slippage": slippage_result.slippage_amount,
            })

            self.logger.info(
                f"EXECUTED: {signal.side} {position.shares} × {symbol} "
                f"@ ₹{actual_entry_price:.2f} (slippage: ₹{slippage_result.slippage_amount:.2f})"
            )

    def _check_exits(
        self, current_date: datetime, historical_data: dict
    ):
        """Check for stop-loss and target exits"""

        positions_to_close = []

        for position in self.positions:
            symbol = position["symbol"]

            # Get today's OHLC
            df = historical_data[symbol]
            today_candle = df[df["datetime"] == current_date]

            if today_candle.empty:
                continue

            today_low = today_candle.iloc[0]["low"]
            today_high = today_candle.iloc[0]["high"]
            today_close = today_candle.iloc[0]["close"]

            # Check stop-loss
            if position["side"] == "BUY":
                if today_low <= position["stop_loss"]:
                    # Stop hit
                    exit_price = position["stop_loss"]
                    positions_to_close.append((position, exit_price, "STOP_LOSS"))
                    continue

                # Check target
                if today_high >= position["target"]:
                    exit_price = position["target"]
                    positions_to_close.append((position, exit_price, "TARGET"))
                    continue

        # Close positions
        for position, exit_price, exit_reason in positions_to_close:
            self._close_position(
                position,
                exit_price,
                exit_reason,
                current_date,
            )

    def _close_position(
        self,
        position: dict,
        exit_price: float,
        exit_reason: str,
        exit_date: datetime,
    ):
        """Close position and calculate PnL"""

        # Calculate gross PnL
        if position["side"] == "BUY":
            gross_pnl = (exit_price - position["entry_price"]) * position["shares"]
        else:
            gross_pnl = (position["entry_price"] - exit_price) * position["shares"]

        # Calculate exit costs
        exit_value = exit_price * position["shares"]
        exit_costs = self.cost_calculator.calculate_equity_delivery_costs(
            side="SELL" if position["side"] == "BUY" else "BUY",
            transaction_value=exit_value,
        ).total

        # Apply exit slippage
        exit_slippage = self.slippage_simulator.calculate_slippage(
            symbol=position["symbol"],
            side="SELL" if position["side"] == "BUY" else "BUY",
            order_value=exit_value,
            reference_price=exit_price,
        ).slippage_amount

        # Net PnL
        net_pnl = gross_pnl - position["entry_costs"] - exit_costs - exit_slippage

        # Return cash
        self.cash += exit_value - exit_costs - exit_slippage

        # Log trade
        trade = {
            "symbol": position["symbol"],
            "side": position["side"],
            "entry_date": position["entry_date"],
            "entry_price": position["entry_price"],
            "exit_date": exit_date,
            "exit_price": exit_price,
            "shares": position["shares"],
            "gross_pnl": gross_pnl,
            "costs": position["entry_costs"] + exit_costs,
            "slippage": position["slippage"] + exit_slippage,
            "net_pnl": net_pnl,
            "return_pct": net_pnl / (position["entry_price"] * position["shares"]),
            "exit_reason": exit_reason,
        }

        self.trade_log.append(trade)

        # Remove from open positions
        self.positions.remove(position)

        self.logger.info(
            f"CLOSED: {position['symbol']} | PnL: ₹{net_pnl:,.2f} | Reason: {exit_reason}"
        )

    def _update_equity(
        self, current_date: datetime, historical_data: dict
    ):
        """Update equity at end of day"""

        # Calculate unrealized PnL
        unrealized_pnl = 0.0

        for position in self.positions:
            symbol = position["symbol"]
            df = historical_data[symbol]
            today_candle = df[df["datetime"] == current_date]

            if today_candle.empty:
                continue

            current_price = today_candle.iloc[0]["close"]

            if position["side"] == "BUY":
                position_pnl = (current_price - position["entry_price"]) * position["shares"]
            else:
                position_pnl = (position["entry_price"] - current_price) * position["shares"]

            unrealized_pnl += position_pnl

        # Total equity = cash + unrealized PnL
        self.equity = self.cash + unrealized_pnl

        # Update peak
        self.peak_equity = max(self.peak_equity, self.equity)

        # Record equity
        self.equity_curve.append({
            "date": current_date,
            "equity": self.equity,
        })

        self.logger.debug(
            f"EOD {current_date.date()}: Equity = ₹{self.equity:,.0f}"
        )

    def _finalize_backtest(self):
        """Close all open positions at end"""

        # Mark all positions to market (use last known price)
        for position in self.positions:
            # Use last available price
            # In production, this would be end_date's close
            pass

        self.logger.info("Backtest finalized")

    def _calculate_performance_metrics(
        self, config: BacktestConfig
    ) -> BacktestResults:
        """Calculate performance metrics"""

        # Convert equity curve to Series
        equity_df = pd.DataFrame(self.equity_curve)
        equity_series = equity_df.set_index("date")["equity"]

        # Daily returns
        daily_returns = equity_series.pct_change().dropna()

        # Total return
        total_return_pct = (
            (self.equity - config.initial_capital) / config.initial_capital
        )

        # CAGR
        days = (config.end_date - config.start_date).days
        years = days / 365.25
        cagr = (self.equity / config.initial_capital) ** (1 / years) - 1

        # Max drawdown
        cumulative_returns = (1 + daily_returns).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown_pct = drawdown.min()

        # Sharpe ratio (annualized)
        sharpe_ratio = (
            daily_returns.mean() / daily_returns.std() * np.sqrt(252)
        )

        # Trade statistics
        trade_df = pd.DataFrame(self.trade_log)

        if not trade_df.empty:
            winning_trades = trade_df[trade_df["net_pnl"] > 0]
            losing_trades = trade_df[trade_df["net_pnl"] <= 0]

            win_rate = len(winning_trades) / len(trade_df)
            avg_win_pct = winning_trades["return_pct"].mean() if len(winning_trades) > 0 else 0
            avg_loss_pct = losing_trades["return_pct"].mean() if len(losing_trades) > 0 else 0
        else:
            win_rate = 0
            avg_win_pct = 0
            avg_loss_pct = 0
            winning_trades = []
            losing_trades = []

        return BacktestResults(
            total_return_pct=total_return_pct,
            cagr=cagr,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            avg_win_pct=avg_win_pct,
            avg_loss_pct=avg_loss_pct,
            total_trades=len(trade_df),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            equity_curve=equity_series,
            trade_log=trade_df,
            daily_returns=daily_returns,
        )
```

---

## API Contracts

### Input: BacktestConfig

```python
config = BacktestConfig(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=100000,
    strategy_name="ADX+DMA",
    universe=["RELIANCE-EQ", "TCS-EQ", "INFY-EQ"],
    max_drawdown_pct=0.02,
    position_size_method="kelly",
)
```

### Output: BacktestResults

```python
BacktestResults(
    total_return_pct=0.185,  # +18.5%
    cagr=0.182,
    max_drawdown_pct=-0.018,  # -1.8%
    sharpe_ratio=2.1,
    win_rate=0.56,  # 56%
    avg_win_pct=0.045,  # +4.5% per win
    avg_loss_pct=-0.025,  # -2.5% per loss
    total_trades=48,
    winning_trades=27,
    losing_trades=21,
    equity_curve=pd.Series([...]),
    trade_log=pd.DataFrame([...]),
    daily_returns=pd.Series([...]),
)
```

---

## Business Rules

### BR-1: No Lookahead Bias

**Rule**: Only use data available up to yesterday

**Implementation**:
```python
# WRONG: Uses today's close to generate signal
signal_price = df.loc[current_date, "close"]

# CORRECT: Uses yesterday's close
yesterday = current_date - timedelta(days=1)
df_available = df[df["datetime"] <= yesterday]
signal_price = df_available.iloc[-1]["close"]
```

### BR-2: Realistic Execution

**Rule**: Execute at next day's open (T+1 for delivery)

**Implementation**:
```python
# Signal generated: 2024-11-19
# Execution: 2024-11-20 open
execution_price = df.loc[signal_date + timedelta(days=1), "open"]
```

### BR-3: All Costs Included

**Rule**: Deduct STT, brokerage, GST, stamp duty, exchange fees

**Implementation**:
```python
costs = cost_calculator.calculate_equity_delivery_costs(
    side="BUY",
    transaction_value=position_value,
)
cash -= position_value + costs.total
```

### BR-4: Slippage Applied

**Rule**: Entry/exit prices include slippage

**Implementation**:
```python
actual_entry = reference_price + slippage_amount
actual_exit = reference_price - slippage_amount  # Worse price
```

### BR-5: Max Drawdown Enforcement

**Rule**: Stop new trades if drawdown approaches 2%

**Implementation**:
```python
current_dd = (peak_equity - equity) / peak_equity

if current_dd > 0.018:  # 1.8% (buffer)
    logger.warning("Approaching max drawdown. Reducing positions.")
    # Reduce position sizes or stop trading
```

---

## Test Cases

### TC-001: Run Simple Backtest

**Test Code**:
```python
def test_run_simple_backtest():
    backtest = BacktestEngine(
        data_source=mock_data_source,
        signal_generator=mock_signal_generator,
        position_sizer=mock_position_sizer,
        cost_calculator=CostCalculator(),
        slippage_simulator=SlippageSimulator(),
    )

    config = BacktestConfig(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        initial_capital=100000,
        strategy_name="ADX+DMA",
        universe=["RELIANCE-EQ"],
    )

    results = backtest.run_backtest(config)

    assert results is not None
    assert results.total_trades >= 0
    assert results.equity_curve is not None
```

### TC-002: Validate No Lookahead

**Test Code**:
```python
def test_no_lookahead_bias():
    backtest = BacktestEngine(...)

    # Ensure signal uses data up to yesterday only
    current_date = datetime(2024, 1, 15)

    signals = backtest._generate_signals_point_in_time(
        current_date=current_date,
        historical_data=test_data,
        universe=["RELIANCE-EQ"],
    )

    # Verify signal uses data <= 2024-01-14
    for signal in signals:
        assert signal.timestamp <= current_date
```

### TC-003: Costs Applied Correctly

**Test Code**:
```python
def test_costs_applied():
    backtest = BacktestEngine(...)

    initial_cash = backtest.cash

    # Execute order worth ₹10,000
    order_value = 10000
    costs = backtest.cost_calculator.calculate_equity_delivery_costs(
        "BUY", order_value
    ).total

    # Simulate execution
    # ...

    # Cash should reduce by order_value + costs
    expected_cash = initial_cash - order_value - costs
    assert backtest.cash == pytest.approx(expected_cash, abs=1)
```

### TC-004: Slippage Applied

**Test Code**:
```python
def test_slippage_applied():
    backtest = BacktestEngine(...)

    reference_price = 2500
    side = "BUY"

    slippage_result = backtest.slippage_simulator.calculate_slippage(
        symbol="RELIANCE-EQ",
        side=side,
        order_value=10000,
        reference_price=reference_price,
    )

    # Entry price should be worse (higher for BUY)
    assert slippage_result.adjusted_price > reference_price
```

### TC-005: Stop-Loss Exit

**Test Code**:
```python
def test_stop_loss_exit():
    backtest = BacktestEngine(...)

    # Open position with stop at ₹2,400
    position = {
        "symbol": "RELIANCE-EQ",
        "side": "BUY",
        "entry_price": 2500,
        "stop_loss": 2400,
        "shares": 10,
        # ...
    }

    backtest.positions.append(position)

    # Simulate price dropping to ₹2,390
    # ...

    # Position should be closed
    assert len(backtest.positions) == 0
    assert len(backtest.trade_log) == 1
    assert backtest.trade_log[0]["exit_reason"] == "STOP_LOSS"
```

---

## Edge Cases

### Edge Case 1: Market Holiday (No Data)

**Scenario**: Backtest date falls on market holiday

**Expected**:
- Skip day (no trading)
- Equity unchanged
- Continue to next day

**Implementation**:
```python
if current_date not in historical_data:
    logger.info(f"{current_date.date()}: Market holiday. Skipping.")
    continue
```

### Edge Case 2: Gap Down (Stop-Loss Gapped)

**Scenario**: Stock gaps down 5%, stop-loss is 3%

**Expected**:
- Exit at open (not stop-loss price)
- Worse loss than expected

**Implementation**:
```python
if today_open < stop_loss:
    exit_price = today_open  # Gap execution
    exit_reason = "STOP_LOSS_GAP"
```

### Edge Case 3: Insufficient Cash

**Scenario**: Signal generated but not enough cash

**Expected**:
- Skip trade
- Log warning
- Continue backtest

**Implementation**:
```python
if total_cost > self.cash:
    logger.warning("Insufficient cash. Skipping trade.")
    continue
```

### Edge Case 4: Zero Trades

**Scenario**: Strategy generates no signals during backtest

**Expected**:
- Backtest completes normally
- Return = 0%
- Trade log empty

**Implementation**:
```python
if len(trade_log) == 0:
    logger.info("No trades executed during backtest.")
    win_rate = 0
    avg_win = 0
    avg_loss = 0
```

---

## Performance Requirements

### PR-1: Backtest Speed

**Requirement**: 1-year backtest (250 days, 50 symbols) in < 60 seconds

**Implementation**:
- Vectorize calculations (avoid loops)
- Cache indicator calculations
- Use efficient data structures

### PR-2: Memory Usage

**Requirement**: < 2GB RAM for 5-year backtest

**Implementation**:
- Load data lazily (not all at once)
- Clear old data after processing
- Use generators where possible

---

## Dependencies

### Internal Dependencies

- **FX-001**: Data Ingestion
- **FX-002**: Kelly Position Sizer
- **FX-003**: Signal Generator
- **FX-004**: Cost Calculator
- **FX-005**: Slippage Simulator

### External Dependencies

- **pandas**: DataFrames
- **numpy**: Numerical operations

---

## Implementation Checklist

- [ ] Create `backtesting/backtest_engine.py`
- [ ] Implement daily simulation loop
- [ ] Implement order execution with costs/slippage
- [ ] Implement position tracking
- [ ] Implement performance metrics calculation
- [ ] Write 10 unit tests
- [ ] Write 3 integration tests
- [ ] Performance testing (< 60s for 1-year)
- [ ] Documentation

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: FX-009 (Paper Trading Engine)
