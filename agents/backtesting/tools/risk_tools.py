#!/usr/bin/env python3
"""
Risk Metrics Calculator - Extended Risk Tools

Calculates comprehensive risk metrics beyond basic performance:
- Drawdown analysis
- Value at Risk (VaR) and CVaR
- Recovery time analysis
- Underwater periods
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from datetime import datetime, timedelta
import logging

from agents.backtesting.tools.models import BacktestResult, RiskMetrics

logger = logging.getLogger(__name__)


class RiskMetricsCalculator:
    """
    Calculate comprehensive risk metrics

    Features:
    - Maximum drawdown and recovery time
    - Value at Risk (VaR) at 95% and 99% confidence
    - Conditional VaR (CVaR/Expected Shortfall)
    - Underwater period analysis
    - Risk-adjusted returns (Sharpe, Sortino, Calmar)
    """

    def __init__(self, confidence_levels: List[float] = [0.95, 0.99]):
        """
        Initialize risk calculator

        Args:
            confidence_levels: VaR confidence levels (default: 95%, 99%)
        """
        self.confidence_levels = confidence_levels

    def calculate(self, backtest_result: BacktestResult) -> RiskMetrics:
        """
        Calculate all risk metrics from backtest result

        Args:
            backtest_result: Backtest results with equity curve

        Returns:
            RiskMetrics object with all risk measurements
        """
        logger.info("Calculating comprehensive risk metrics...")

        equity_curve = backtest_result.equity_curve

        if equity_curve.empty:
            logger.warning("No equity curve data, returning empty risk metrics")
            return RiskMetrics()

        # 1. Drawdown metrics
        max_dd_pct, max_dd_duration, avg_dd_pct, current_dd_pct = self._calculate_drawdown_metrics(
            equity_curve
        )

        # 2. Volatility metrics
        daily_vol, annual_vol, downside_vol = self._calculate_volatility_metrics(equity_curve)

        # 3. Value at Risk
        var_95, var_99, cvar_95 = self._calculate_var_metrics(equity_curve)

        # Create risk metrics object
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
            f"Risk metrics: Max DD={max_dd_pct:.2f}%, "
            f"Vol={annual_vol:.2f}%, VaR(95)={var_95:.2f}%, "
            f"Risk Level={metrics.drawdown_risk_level}"
        )

        return metrics

    def _calculate_drawdown_metrics(
        self, equity_curve: pd.DataFrame
    ) -> Tuple[float, int, float, float]:
        """
        Calculate drawdown-related metrics

        Returns:
            (max_drawdown_pct, max_duration_days, avg_drawdown_pct, current_drawdown_pct)
        """
        equity = equity_curve['equity']

        # Running maximum
        cummax = equity.cummax()

        # Drawdown series (negative values)
        drawdown = (equity - cummax) / cummax * 100

        # Maximum drawdown
        max_dd_pct = drawdown.min()

        # Maximum drawdown duration
        max_dd_duration = self._calculate_max_drawdown_duration(drawdown)

        # Average drawdown (only when in drawdown)
        drawdown_periods = drawdown[drawdown < -0.01]  # > 0.01% drawdown
        avg_dd_pct = drawdown_periods.mean() if len(drawdown_periods) > 0 else 0.0

        # Current drawdown
        current_dd_pct = drawdown.iloc[-1]

        return max_dd_pct, max_dd_duration, avg_dd_pct, current_dd_pct

    def _calculate_max_drawdown_duration(self, drawdown_series: pd.Series) -> int:
        """
        Calculate the longest underwater period (days in drawdown)

        Args:
            drawdown_series: Series of drawdown percentages

        Returns:
            Maximum number of consecutive days in drawdown
        """
        # Find periods where in drawdown (< -0.01%)
        in_drawdown = drawdown_series < -0.01

        # Find consecutive periods
        max_duration = 0
        current_duration = 0

        for is_dd in in_drawdown:
            if is_dd:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0

        return max_duration

    def _calculate_volatility_metrics(
        self, equity_curve: pd.DataFrame
    ) -> Tuple[float, float, float]:
        """
        Calculate volatility metrics

        Returns:
            (daily_volatility_pct, annualized_volatility_pct, downside_volatility_pct)
        """
        # Calculate returns
        returns = equity_curve['equity'].pct_change().dropna()

        if len(returns) < 2:
            return 0.0, 0.0, 0.0

        # Daily volatility (standard deviation of returns)
        daily_vol = returns.std() * 100

        # Annualized volatility (252 trading days)
        annual_vol = daily_vol * np.sqrt(252)

        # Downside volatility (only negative returns)
        downside_returns = returns[returns < 0]

        if len(downside_returns) > 0:
            downside_daily_vol = downside_returns.std() * 100
            downside_vol = downside_daily_vol * np.sqrt(252)
        else:
            downside_vol = 0.0

        return daily_vol, annual_vol, downside_vol

    def _calculate_var_metrics(
        self, equity_curve: pd.DataFrame
    ) -> Tuple[float, float, float]:
        """
        Calculate Value at Risk (VaR) and Conditional VaR (CVaR)

        VaR: Maximum expected loss at given confidence level
        CVaR: Expected loss beyond VaR (tail risk)

        Returns:
            (var_95_pct, var_99_pct, cvar_95_pct)
        """
        # Calculate returns
        returns = equity_curve['equity'].pct_change().dropna() * 100  # In percentage

        if len(returns) < 10:
            return 0.0, 0.0, 0.0

        # VaR at 95% confidence (5th percentile)
        # Interpretation: 95% of days, loss won't exceed this
        var_95 = np.percentile(returns, 5)

        # VaR at 99% confidence (1st percentile)
        var_99 = np.percentile(returns, 1)

        # CVaR (Conditional VaR) at 95%
        # Expected loss when loss exceeds VaR
        losses_beyond_var = returns[returns <= var_95]
        cvar_95 = losses_beyond_var.mean() if len(losses_beyond_var) > 0 else var_95

        return var_95, var_99, cvar_95

    def analyze_underwater_periods(
        self, equity_curve: pd.DataFrame
    ) -> List[Dict]:
        """
        Analyze all underwater periods (periods in drawdown)

        Returns:
            List of dicts with underwater period details
        """
        equity = equity_curve['equity']
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax * 100

        # Find underwater periods
        in_drawdown = drawdown < -0.01
        underwater_periods = []

        start_idx = None
        for idx, is_dd in enumerate(in_drawdown):
            if is_dd and start_idx is None:
                # Start of underwater period
                start_idx = idx
            elif not is_dd and start_idx is not None:
                # End of underwater period
                period_data = self._analyze_single_underwater_period(
                    equity_curve.iloc[start_idx:idx],
                    drawdown.iloc[start_idx:idx]
                )
                underwater_periods.append(period_data)
                start_idx = None

        # Handle if still underwater at end
        if start_idx is not None:
            period_data = self._analyze_single_underwater_period(
                equity_curve.iloc[start_idx:],
                drawdown.iloc[start_idx:]
            )
            underwater_periods.append(period_data)

        logger.info(f"Found {len(underwater_periods)} underwater periods")
        return underwater_periods

    def _analyze_single_underwater_period(
        self,
        period_equity: pd.DataFrame,
        period_drawdown: pd.Series
    ) -> Dict:
        """Analyze a single underwater period"""
        return {
            'start_date': period_equity.index[0],
            'end_date': period_equity.index[-1],
            'duration_days': len(period_equity),
            'max_drawdown_pct': period_drawdown.min(),
            'avg_drawdown_pct': period_drawdown.mean()
        }

    def calculate_recovery_stats(
        self, equity_curve: pd.DataFrame
    ) -> Dict:
        """
        Calculate recovery statistics

        Returns:
            Dict with recovery time metrics
        """
        equity = equity_curve['equity']
        cummax = equity.cummax()

        # Time to recover from drawdowns
        recovery_times = []

        # Find peaks and recoveries
        at_peak = equity >= cummax * 0.999  # Within 0.1% of peak

        in_recovery = False
        recovery_start_idx = None

        for idx, at_peak_now in enumerate(at_peak):
            if not at_peak_now and not in_recovery:
                # Entered drawdown
                in_recovery = True
                recovery_start_idx = idx
            elif at_peak_now and in_recovery:
                # Recovered to new peak
                recovery_time = idx - recovery_start_idx
                recovery_times.append(recovery_time)
                in_recovery = False

        stats = {
            'num_recoveries': len(recovery_times),
            'avg_recovery_days': np.mean(recovery_times) if recovery_times else 0,
            'max_recovery_days': max(recovery_times) if recovery_times else 0,
            'min_recovery_days': min(recovery_times) if recovery_times else 0
        }

        logger.info(
            f"Recovery stats: {stats['num_recoveries']} recoveries, "
            f"avg {stats['avg_recovery_days']:.0f} days"
        )

        return stats


# Test function
if __name__ == '__main__':
    from agents.backtesting.tools.data_tools import DataFetcherTool
    from agents.backtesting.tools.backtest_tools import BacktestExecutorTool

    print("Testing RiskMetricsCalculator...")

    # Create sample backtest result
    # (In real usage, this would come from BacktestExecutorTool)

    # Create sample equity curve
    dates = pd.date_range('2023-01-01', '2024-11-01', freq='D')
    np.random.seed(42)

    # Simulate equity curve with some volatility and drawdowns
    returns = np.random.normal(0.001, 0.02, len(dates))  # Daily returns
    equity = 100000 * (1 + returns).cumprod()

    equity_curve = pd.DataFrame({
        'equity': equity,
        'cash': equity * 0.8,
        'position_value': equity * 0.2
    }, index=dates)

    # Create dummy backtest result
    result = BacktestResult(
        strategy_name="TestStrategy",
        symbol="TEST.NS",
        start_date=dates[0],
        end_date=dates[-1],
        initial_capital=100000,
        final_capital=equity[-1],
        trades=[],
        equity_curve=equity_curve
    )

    # Calculate risk metrics
    calculator = RiskMetricsCalculator()
    metrics = calculator.calculate(result)

    print(f"\n=== Risk Metrics ===")
    print(f"Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
    print(f"Max DD Duration: {metrics.max_drawdown_duration_days} days")
    print(f"Avg Drawdown: {metrics.avg_drawdown_pct:.2f}%")
    print(f"Current Drawdown: {metrics.current_drawdown_pct:.2f}%")
    print(f"\nVolatility:")
    print(f"  Daily: {metrics.daily_volatility_pct:.2f}%")
    print(f"  Annualized: {metrics.annualized_volatility_pct:.2f}%")
    print(f"  Downside: {metrics.downside_volatility_pct:.2f}%")
    print(f"\nValue at Risk:")
    print(f"  VaR (95%): {metrics.var_95_pct:.2f}%")
    print(f"  VaR (99%): {metrics.var_99_pct:.2f}%")
    print(f"  CVaR (95%): {metrics.cvar_95_pct:.2f}%")
    print(f"\nRisk Level: {metrics.drawdown_risk_level}")

    # Test underwater periods
    print(f"\n=== Underwater Periods ===")
    underwater = calculator.analyze_underwater_periods(equity_curve)
    for i, period in enumerate(underwater[:5], 1):
        print(f"{i}. {period['start_date'].date()} to {period['end_date'].date()}")
        print(f"   Duration: {period['duration_days']} days")
        print(f"   Max DD: {period['max_drawdown_pct']:.2f}%")

    # Test recovery stats
    print(f"\n=== Recovery Statistics ===")
    recovery_stats = calculator.calculate_recovery_stats(equity_curve)
    print(f"Number of recoveries: {recovery_stats['num_recoveries']}")
    print(f"Average recovery time: {recovery_stats['avg_recovery_days']:.0f} days")
    print(f"Max recovery time: {recovery_stats['max_recovery_days']:.0f} days")
