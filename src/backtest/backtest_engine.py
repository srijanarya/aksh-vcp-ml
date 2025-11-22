"""
Backtesting Engine (SHORT-040 to SHORT-051)

Complete backtesting system with performance metrics.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass, field


@dataclass
class Trade:
    """Trade record"""
    symbol: str
    entry_date: datetime
    entry_price: float
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    quantity: int = 0
    pnl: float = 0.0
    pnl_pct: float = 0.0


@dataclass
class BacktestResult:
    """Backtest result"""
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    metrics: Dict[str, Any] = field(default_factory=dict)


class BacktestEngine:
    """Backtesting engine for strategy validation"""

    def __init__(
        self,
        initial_capital: float = 100000,
        cost_calculator: Optional[Any] = None,
        slippage_simulator: Optional[Any] = None
    ):
        """
        Initialize backtest engine

        Args:
            initial_capital: Starting capital
            cost_calculator: Cost calculator instance
            slippage_simulator: Slippage simulator instance
        """
        self.initial_capital = initial_capital
        self.cost_calculator = cost_calculator
        self.slippage_simulator = slippage_simulator

        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []

    def run(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        stop_loss_pct: float = 2.0,
        target_pct: float = 4.0
    ) -> BacktestResult:
        """
        Run backtest

        Args:
            data: OHLC DataFrame
            signals: Buy signals (boolean Series)
            stop_loss_pct: Stop loss percentage
            target_pct: Target percentage

        Returns:
            BacktestResult with trades and metrics
        """
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []

        for date, row in data.iterrows():
            # Check exits first
            self._check_exits(date, row, stop_loss_pct, target_pct)

            # Check new entries
            if signals.loc[date]:
                self._enter_position(date, row)

            # Track equity
            equity = self._calculate_equity(row)
            self.equity_curve.append({'date': date, 'equity': equity})

        # Calculate metrics
        metrics = self._calculate_metrics()

        return BacktestResult(
            trades=self.trades,
            equity_curve=pd.DataFrame(self.equity_curve).set_index('date')['equity'],
            metrics=metrics
        )

    def _enter_position(self, date: datetime, row: pd.Series):
        """Enter new position"""
        if len(self.positions) >= 5:  # Max 5 positions
            return

        price = row['close']
        quantity = int(self.capital * 0.1 / price)  # 10% position size

        if quantity == 0:
            return

        cost = price * quantity
        if self.cost_calculator:
            cost += self.cost_calculator.calculate_equity_delivery_cost(cost)

        if cost > self.capital:
            return

        self.capital -= cost

        trade = Trade(
            symbol='TEST',
            entry_date=date,
            entry_price=price,
            quantity=quantity
        )

        self.positions[date] = trade

    def _check_exits(
        self,
        date: datetime,
        row: pd.Series,
        stop_loss_pct: float,
        target_pct: float
    ):
        """Check for stop loss or target hits"""
        exits = []

        for entry_date, trade in self.positions.items():
            current_price = row['close']
            pnl_pct = (current_price - trade.entry_price) / trade.entry_price * 100

            # Check stop loss
            if pnl_pct <= -stop_loss_pct:
                exits.append(entry_date)
                self._exit_position(trade, date, current_price)

            # Check target
            elif pnl_pct >= target_pct:
                exits.append(entry_date)
                self._exit_position(trade, date, current_price)

        for entry_date in exits:
            del self.positions[entry_date]

    def _exit_position(self, trade: Trade, exit_date: datetime, exit_price: float):
        """Exit position"""
        trade.exit_date = exit_date
        trade.exit_price = exit_price

        # Calculate exit value
        exit_value = exit_price * trade.quantity

        # Calculate exit costs
        exit_cost = 0
        if self.cost_calculator:
            exit_cost = self.cost_calculator.calculate_equity_delivery_cost(exit_value)

        # Net proceeds after exit costs
        proceeds = exit_value - exit_cost

        # P&L = proceeds - entry cost (which was already deducted from capital)
        entry_cost = trade.entry_price * trade.quantity
        if self.cost_calculator:
            entry_cost += self.cost_calculator.calculate_equity_delivery_cost(entry_cost)

        trade.pnl = proceeds - entry_cost
        trade.pnl_pct = (exit_price - trade.entry_price) / trade.entry_price * 100

        # Add proceeds back to capital
        self.capital += proceeds
        self.trades.append(trade)

    def _calculate_equity(self, row: pd.Series) -> float:
        """Calculate current equity"""
        equity = self.capital

        for trade in self.positions.values():
            current_value = row['close'] * trade.quantity
            equity += current_value

        return equity

    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return_pct': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }

        wins = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl < 0]

        total_pnl = sum(t.pnl for t in self.trades)
        total_return_pct = (total_pnl / self.initial_capital) * 100

        # Sharpe ratio
        returns = [t.pnl_pct for t in self.trades]
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 1 else 0

        # Max drawdown
        equity_series = pd.Series([e['equity'] for e in self.equity_curve])
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        max_drawdown = drawdown.min()

        return {
            'total_trades': len(self.trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': len(wins) / len(self.trades) * 100,
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'total_pnl': total_pnl,
            'total_return': total_return_pct,
            'total_return_pct': total_return_pct,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'final_capital': self.capital
        }
