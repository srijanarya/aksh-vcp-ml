"""
Performance and Risk Analysis Tools

Calculate comprehensive performance metrics and risk metrics
using research-backed formulas.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List
import logging

from agents.backtesting.tools.models import (
    Trade, BacktestResult, PerformanceMetrics, RiskMetrics
)

logger = logging.getLogger(__name__)


class PerformanceMetricsCalculator:
    """Calculate performance metrics from backtest results"""

    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize calculator

        Args:
            risk_free_rate: Annual risk-free rate (default 5%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate(
        self,
        backtest_result: BacktestResult
    ) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics

        Args:
            backtest_result: Backtest results with trades and equity curve

        Returns:
            PerformanceMetrics object
        """
        logger.info("Calculating performance metrics...")

        trades = backtest_result.trades
        equity_curve = backtest_result.equity_curve

        if not trades:
            logger.warning("No trades to analyze")
            return PerformanceMetrics()

        # Calculate returns
        total_return_pct = backtest_result.total_return_pct
        annualized_return = self._calculate_annualized_return(
            backtest_result.initial_capital,
            backtest_result.final_capital,
            backtest_result.start_date,
            backtest_result.end_date
        )
        cagr = annualized_return  # Same calculation

        # Calculate risk-adjusted returns
        sharpe = self._calculate_sharpe_ratio(equity_curve)
        sortino = self._calculate_sortino_ratio(equity_curve)

        # Calculate Calmar ratio (return / max drawdown)
        max_dd = self._calculate_max_drawdown(equity_curve)
        calmar = annualized_return / abs(max_dd) if max_dd != 0 else 0

        # Win/Loss statistics
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]

        total_trades = len(trades)
        num_wins = len(winning_trades)
        num_losses = len(losing_trades)

        win_rate = (num_wins / total_trades * 100) if total_trades > 0 else 0

        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Expectancy
        total_pnl = sum(t.pnl for t in trades)
        expectancy = total_pnl / total_trades if total_trades > 0 else 0

        avg_pnl_pct = sum(t.pnl_pct for t in trades) / total_trades if total_trades > 0 else 0

        # Win/Loss averages
        avg_win_pct = (sum(t.pnl_pct for t in winning_trades) / num_wins
                       if num_wins > 0 else 0)
        avg_loss_pct = (sum(t.pnl_pct for t in losing_trades) / num_losses
                        if num_losses > 0 else 0)

        # Largest win/loss
        largest_win = max([t.pnl_pct for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t.pnl_pct for t in losing_trades]) if losing_trades else 0

        # Trade duration
        avg_duration = (sum(t.trade_duration_days for t in trades) / total_trades
                       if total_trades > 0 else 0)
        avg_win_duration = (sum(t.trade_duration_days for t in winning_trades) / num_wins
                           if num_wins > 0 else 0)
        avg_loss_duration = (sum(t.trade_duration_days for t in losing_trades) / num_losses
                            if num_losses > 0 else 0)

        # Consecutive stats
        max_consec_wins, max_consec_losses = self._calculate_consecutive_stats(trades)

        # Statistical significance
        backtest_years = (backtest_result.end_date - backtest_result.start_date).days / 365.25
        sample_size_adequate = total_trades >= 30
        time_period_adequate = backtest_years >= 2.0

        # Simple significance test (could be improved with proper statistical tests)
        is_significant = (
            sample_size_adequate and
            time_period_adequate and
            win_rate > 40 and  # Above random
            profit_factor > 1.0  # Profitable
        )

        metrics = PerformanceMetrics(
            total_return_pct=total_return_pct,
            annualized_return_pct=annualized_return,
            cagr_pct=cagr,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            win_rate_pct=win_rate,
            profit_factor=profit_factor,
            expectancy=expectancy,
            expectancy_pct=avg_pnl_pct,
            total_trades=total_trades,
            winning_trades=num_wins,
            losing_trades=num_losses,
            avg_win_pct=avg_win_pct,
            avg_loss_pct=avg_loss_pct,
            largest_win_pct=largest_win,
            largest_loss_pct=largest_loss,
            avg_trade_duration_days=avg_duration,
            avg_winning_duration_days=avg_win_duration,
            avg_losing_duration_days=avg_loss_duration,
            max_consecutive_wins=max_consec_wins,
            max_consecutive_losses=max_consec_losses,
            is_statistically_significant=is_significant,
            sample_size_adequate=sample_size_adequate,
            time_period_adequate=time_period_adequate
        )

        logger.info(
            f"Performance metrics calculated - Sharpe: {sharpe:.2f}, "
            f"Win rate: {win_rate:.1f}%, Profit factor: {profit_factor:.2f}"
        )

        return metrics

    def _calculate_annualized_return(
        self,
        initial: float,
        final: float,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate annualized return (CAGR)"""
        years = (end_date - start_date).days / 365.25
        if years <= 0:
            return 0.0

        if initial <= 0:
            return 0.0

        cagr = ((final / initial) ** (1 / years) - 1) * 100
        return cagr

    def _calculate_sharpe_ratio(self, equity_curve: pd.DataFrame) -> float:
        """Calculate Sharpe ratio from equity curve"""
        if equity_curve.empty:
            return 0.0

        # Calculate daily returns
        returns = equity_curve['equity'].pct_change().dropna()

        if len(returns) < 2:
            return 0.0

        # Annualize
        avg_return = returns.mean() * 252  # Trading days
        std_return = returns.std() * np.sqrt(252)

        if std_return == 0:
            return 0.0

        sharpe = (avg_return - self.risk_free_rate) / std_return
        return sharpe

    def _calculate_sortino_ratio(self, equity_curve: pd.DataFrame) -> float:
        """Calculate Sortino ratio (uses downside volatility only)"""
        if equity_curve.empty:
            return 0.0

        returns = equity_curve['equity'].pct_change().dropna()

        if len(returns) < 2:
            return 0.0

        # Only negative returns for downside deviation
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            return 0.0

        avg_return = returns.mean() * 252
        downside_std = downside_returns.std() * np.sqrt(252)

        if downside_std == 0:
            return 0.0

        sortino = (avg_return - self.risk_free_rate) / downside_std
        return sortino

    def _calculate_max_drawdown(self, equity_curve: pd.DataFrame) -> float:
        """Calculate maximum drawdown percentage"""
        if equity_curve.empty:
            return 0.0

        equity = equity_curve['equity']
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax * 100

        max_dd = drawdown.min()
        return max_dd

    def _calculate_consecutive_stats(self, trades: List[Trade]) -> tuple[int, int]:
        """Calculate max consecutive wins and losses"""
        if not trades:
            return 0, 0

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses


class RiskMetricsCalculator:
    """Calculate risk metrics from backtest results"""

    def calculate(
        self,
        backtest_result: BacktestResult
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics

        Args:
            backtest_result: Backtest results

        Returns:
            RiskMetrics object
        """
        logger.info("Calculating risk metrics...")

        equity_curve = backtest_result.equity_curve

        if equity_curve.empty:
            logger.warning("No equity curve to analyze")
            return RiskMetrics()

        # Calculate drawdowns
        max_dd_pct, max_dd_duration, avg_dd_pct, current_dd_pct = self._calculate_drawdowns(
            equity_curve
        )

        # Calculate volatility
        daily_vol, annual_vol, downside_vol = self._calculate_volatility(equity_curve)

        # Calculate Value at Risk
        var_95, var_99, cvar_95 = self._calculate_var(equity_curve)

        metrics = RiskMetrics(
            max_drawdown_pct=max_dd_pct,
            max_drawdown_duration_days=max_dd_duration,
            avg_drawdown_pct=avg_dd_pct,
            current_drawdown_pct=current_dd_pct,
            daily_volatility_pct=daily_vol,
            annualized_volatility_pct=annual_vol,
            downside_volatility_pct=downside_vol,
            var_95_pct=var_95,
            var_99_pct=var_99,
            cvar_95_pct=cvar_95
        )

        logger.info(
            f"Risk metrics calculated - Max DD: {max_dd_pct:.2f}%, "
            f"Volatility: {annual_vol:.2f}%, VaR(95): {var_95:.2f}%"
        )

        return metrics

    def _calculate_drawdowns(
        self,
        equity_curve: pd.DataFrame
    ) -> tuple[float, int, float, float]:
        """Calculate drawdown statistics"""
        equity = equity_curve['equity']
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax * 100

        # Max drawdown
        max_dd = drawdown.min()

        # Max drawdown duration
        # Find periods in drawdown
        in_dd = drawdown < -0.01  # More than 0.01% down
        dd_periods = []
        start_idx = None

        for idx, is_dd in enumerate(in_dd):
            if is_dd and start_idx is None:
                start_idx = idx
            elif not is_dd and start_idx is not None:
                dd_periods.append(idx - start_idx)
                start_idx = None

        max_dd_duration = max(dd_periods) if dd_periods else 0

        # Average drawdown
        dd_values = drawdown[drawdown < -0.01]
        avg_dd = dd_values.mean() if len(dd_values) > 0 else 0.0

        # Current drawdown
        current_dd = drawdown.iloc[-1]

        return max_dd, max_dd_duration, avg_dd, current_dd

    def _calculate_volatility(
        self,
        equity_curve: pd.DataFrame
    ) -> tuple[float, float, float]:
        """Calculate volatility metrics"""
        returns = equity_curve['equity'].pct_change().dropna()

        if len(returns) < 2:
            return 0.0, 0.0, 0.0

        # Daily volatility
        daily_vol = returns.std() * 100

        # Annualized volatility
        annual_vol = daily_vol * np.sqrt(252)

        # Downside volatility (only negative returns)
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252) * 100 if len(downside_returns) > 0 else 0.0

        return daily_vol, annual_vol, downside_vol

    def _calculate_var(
        self,
        equity_curve: pd.DataFrame
    ) -> tuple[float, float, float]:
        """Calculate Value at Risk (VaR) and Conditional VaR (CVaR)"""
        returns = equity_curve['equity'].pct_change().dropna() * 100

        if len(returns) < 2:
            return 0.0, 0.0, 0.0

        # VaR at 95% confidence (5th percentile loss)
        var_95 = np.percentile(returns, 5)

        # VaR at 99% confidence (1st percentile loss)
        var_99 = np.percentile(returns, 1)

        # CVaR (expected loss beyond VaR 95%)
        losses_beyond_var = returns[returns <= var_95]
        cvar_95 = losses_beyond_var.mean() if len(losses_beyond_var) > 0 else var_95

        return var_95, var_99, cvar_95
