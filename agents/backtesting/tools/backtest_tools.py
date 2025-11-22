"""
Backtest Execution Tools

Walk-forward through historical data executing strategy signals.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import importlib.util

# Add to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.backtesting.tools.models import Trade, BacktestResult

logger = logging.getLogger(__name__)


class BacktestExecutorTool:
    """
    Execute backtest by walking forward through historical data

    Loads strategy from file, walks through data day-by-day,
    executes trades based on signals, tracks equity curve.
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        position_size_pct: float = 0.1,  # 10% of capital per trade
        max_positions: int = 5,
        slippage_pct: float = 0.1,  # 0.1% slippage
        commission_pct: float = 0.1  # 0.1% commission
    ):
        """
        Initialize backtest executor

        Args:
            initial_capital: Starting capital
            position_size_pct: % of capital per trade
            max_positions: Maximum concurrent positions
            slippage_pct: Slippage percentage
            commission_pct: Commission percentage
        """
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.max_positions = max_positions
        self.slippage_pct = slippage_pct
        self.commission_pct = commission_pct

        logger.info(
            f"BacktestExecutor initialized - Capital: {initial_capital}, "
            f"Position size: {position_size_pct*100}%, Max positions: {max_positions}"
        )

    def load_strategy(self, strategy_file_path: str) -> Any:
        """
        Dynamically load strategy from Python file

        Args:
            strategy_file_path: Path to strategy .py file

        Returns:
            Strategy class instance

        Raises:
            ImportError: If strategy file cannot be loaded
        """
        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location("strategy", strategy_file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load strategy from {strategy_file_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Try to find strategy class
            # Convention: Look for class ending in "Strategy"
            strategy_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and name.endswith("Strategy"):
                    strategy_class = obj
                    break

            if strategy_class is None:
                raise ImportError("No strategy class found in file")

            # Instantiate strategy
            strategy = strategy_class()
            logger.info(f"Loaded strategy: {strategy_class.__name__}")

            return strategy

        except Exception as e:
            logger.error(f"Error loading strategy: {e}")
            raise

    def run_backtest(
        self,
        strategy: Any,
        symbol: str,
        data: Dict[str, pd.DataFrame],
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """
        Execute backtest by walking through data

        Args:
            strategy: Strategy instance with generate_signal() method
            symbol: Stock symbol
            data: Multi-timeframe data dict
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            BacktestResult with trades and equity curve
        """
        logger.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")

        # Initialize tracking
        trades: List[Trade] = []
        equity_curve: List[Dict] = []
        current_capital = self.initial_capital
        position: Optional[Dict] = None  # Current open position

        # Get daily data for walking through
        daily_data = data.get('daily', pd.DataFrame())
        if daily_data.empty:
            logger.error("No daily data available")
            return self._create_empty_result(symbol, start_date, end_date)

        # Ensure index is datetime and reset to column if needed
        if not isinstance(daily_data.index, pd.DatetimeIndex):
            if 'timestamp' in daily_data.columns:
                daily_data = daily_data.set_index('timestamp')

        # Convert timezone-aware index to timezone-naive for comparison
        if daily_data.index.tz is not None:
            daily_data.index = daily_data.index.tz_localize(None)

        # Filter to backtest period
        daily_data = daily_data[
            (daily_data.index >= start_date) &
            (daily_data.index <= end_date)
        ].copy()

        if daily_data.empty:
            logger.error("No data in backtest period")
            return self._create_empty_result(symbol, start_date, end_date)

        logger.info(f"Walking through {len(daily_data)} days...")

        # Walk through each day
        for current_date, row in daily_data.iterrows():
            current_price = row['close']

            # If we have a position, check for exit
            if position is not None:
                exit_signal, exit_reason = self._check_exit_conditions(
                    position, row, strategy
                )

                if exit_signal:
                    # Close position
                    trade = self._close_position(
                        position, current_date, current_price, exit_reason
                    )
                    trades.append(trade)
                    current_capital += trade.pnl
                    position = None
                    logger.debug(f"Closed position: {exit_reason}, PnL: {trade.pnl:.2f}")

            # If no position, check for entry signal
            if position is None and len(trades) < 1000:  # Safety limit
                # Generate signal using strategy
                try:
                    signal = strategy.generate_signal(symbol)

                    if signal is not None:
                        # Open new position
                        position = self._open_position(
                            signal, current_date, current_capital
                        )
                        logger.debug(
                            f"Opened position at {current_price:.2f}, "
                            f"SL: {signal.stop_loss:.2f}, Target: {signal.target:.2f}"
                        )
                except Exception as e:
                    logger.warning(f"Error generating signal on {current_date}: {e}")

            # Update equity curve
            position_value = 0
            if position is not None:
                position_value = (current_price - position['entry_price']) * position['shares']

            equity = current_capital + position_value

            equity_curve.append({
                'timestamp': current_date,
                'equity': equity,
                'cash': current_capital,
                'position_value': position_value
            })

        # Close any remaining position at end
        if position is not None:
            final_price = daily_data.iloc[-1]['close']
            final_date = daily_data.iloc[-1]['timestamp']
            trade = self._close_position(
                position, final_date, final_price, "end_of_backtest"
            )
            trades.append(trade)
            current_capital += trade.pnl

        # Create result
        result = BacktestResult(
            strategy_name=strategy.__class__.__name__,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=current_capital,
            trades=trades,
            equity_curve=pd.DataFrame(equity_curve)
        )

        logger.info(
            f"Backtest complete - Trades: {len(trades)}, "
            f"Final capital: {current_capital:.2f}, "
            f"Return: {result.total_return_pct:.2f}%"
        )

        return result

    def _open_position(
        self,
        signal: Any,
        entry_date: datetime,
        current_capital: float
    ) -> Dict:
        """Open a new position based on signal"""
        # Calculate position size
        risk_amount = current_capital * self.position_size_pct
        entry_price = signal.entry_price

        # Apply slippage (pay slightly more on entry)
        entry_price_with_slippage = entry_price * (1 + self.slippage_pct / 100)

        # Calculate shares (integer)
        shares = int(risk_amount / entry_price_with_slippage)

        if shares <= 0:
            shares = 1

        # Calculate commission
        commission = (shares * entry_price_with_slippage) * (self.commission_pct / 100)

        position = {
            'entry_date': entry_date,
            'entry_price': entry_price_with_slippage,
            'shares': shares,
            'stop_loss': signal.stop_loss,
            'target': signal.target,
            'commission': commission,
            'max_price': entry_price_with_slippage,
            'min_price': entry_price_with_slippage
        }

        return position

    def _close_position(
        self,
        position: Dict,
        exit_date: datetime,
        exit_price: float,
        exit_reason: str
    ) -> Trade:
        """Close position and create trade record"""
        # Apply slippage (receive slightly less on exit)
        exit_price_with_slippage = exit_price * (1 - self.slippage_pct / 100)

        # Calculate commission
        commission = (position['shares'] * exit_price_with_slippage) * (self.commission_pct / 100)

        # Calculate P&L
        gross_pnl = (exit_price_with_slippage - position['entry_price']) * position['shares']
        net_pnl = gross_pnl - position['commission'] - commission

        # Calculate MFE/MAE
        mfe = (position['max_price'] - position['entry_price']) * position['shares']
        mae = (position['entry_price'] - position['min_price']) * position['shares']

        trade = Trade(
            symbol="SYMBOL",  # Would need to pass from caller
            entry_date=position['entry_date'],
            entry_price=position['entry_price'],
            exit_date=exit_date,
            exit_price=exit_price_with_slippage,
            position_size=position['shares'],
            pnl=net_pnl,
            pnl_pct=((exit_price_with_slippage - position['entry_price']) /
                     position['entry_price']) * 100,
            max_favorable_excursion=mfe,
            max_adverse_excursion=mae,
            exit_reason=exit_reason
        )

        return trade

    def _check_exit_conditions(
        self,
        position: Dict,
        current_bar: pd.Series,
        strategy: Any
    ) -> tuple[bool, str]:
        """Check if position should be exited"""
        current_price = current_bar['close']
        high = current_bar['high']
        low = current_bar['low']

        # Update MFE/MAE
        position['max_price'] = max(position['max_price'], high)
        position['min_price'] = min(position['min_price'], low)

        # Check stop loss
        if low <= position['stop_loss']:
            return True, "stop_loss"

        # Check target
        if high >= position['target']:
            return True, "target"

        # Could add time-based exit, trailing stop, etc.

        return False, ""

    def _create_empty_result(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Create empty result when backtest fails"""
        return BacktestResult(
            strategy_name="Unknown",
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            trades=[],
            equity_curve=pd.DataFrame()
        )
