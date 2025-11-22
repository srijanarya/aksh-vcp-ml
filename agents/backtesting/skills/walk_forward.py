#!/usr/bin/env python3
"""
Walk-Forward Analysis Skill

Implements walk-forward testing to detect overfitting and validate robustness.
Splits data into multiple train/test windows and tests consistency.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
import logging

from agents.backtesting.tools.models import (
    WalkForwardResult, WalkForwardAnalysis, BacktestResult
)
from agents.backtesting.tools.backtest_tools import BacktestExecutorTool
from agents.backtesting.tools.analysis_tools import PerformanceMetricsCalculator

logger = logging.getLogger(__name__)


class WalkForwardSkill:
    """
    Walk-forward analysis to prevent overfitting

    Process:
    1. Split data into N windows
    2. For each window: train on first 80%, test on last 20%
    3. Measure out-of-sample performance
    4. Check for degradation vs in-sample
    5. Assess consistency across windows

    Thresholds (research-based):
    - Acceptable degradation: < 30% drop in Sharpe/returns
    - Consistency score: > 60 for robust strategy
    - Min windows: 5
    """

    def __init__(self, num_windows: int = 5, train_pct: float = 0.8):
        """
        Initialize walk-forward skill

        Args:
            num_windows: Number of walk-forward windows
            train_pct: Percentage of data for training (0.8 = 80%)
        """
        self.num_windows = num_windows
        self.train_pct = train_pct
        self.backtest_executor = BacktestExecutorTool()
        self.metrics_calculator = PerformanceMetricsCalculator()

    def execute(
        self,
        strategy: Any,
        symbol: str,
        data: Dict[str, pd.DataFrame]
    ) -> WalkForwardAnalysis:
        """
        Execute walk-forward analysis

        Args:
            strategy: Strategy instance
            symbol: Stock symbol
            data: Multi-timeframe data

        Returns:
            WalkForwardAnalysis with results from all windows
        """
        logger.info(f"Starting walk-forward analysis: {self.num_windows} windows")

        # Get daily data for windowing
        daily_data = data.get('daily', pd.DataFrame())

        if daily_data.empty:
            logger.error("No daily data available")
            return WalkForwardAnalysis(num_windows=0)

        # Calculate window size
        total_bars = len(daily_data)
        window_size = total_bars // self.num_windows

        if window_size < 50:
            logger.error(f"Window too small ({window_size} bars), need more data")
            return WalkForwardAnalysis(num_windows=0)

        logger.info(f"Total bars: {total_bars}, Window size: {window_size}")

        # Execute walk-forward windows
        window_results: List[WalkForwardResult] = []

        for i in range(self.num_windows):
            logger.info(f"Processing window {i+1}/{self.num_windows}...")

            window_result = self._execute_single_window(
                strategy, symbol, data, i, window_size
            )

            if window_result:
                window_results.append(window_result)

        # Create analysis
        analysis = WalkForwardAnalysis(
            num_windows=len(window_results),
            window_results=window_results
        )

        # Calculate consistency
        analysis.calculate_consistency()

        logger.info(
            f"Walk-forward complete: {len(window_results)} windows, "
            f"Avg degradation: {analysis.avg_return_degradation_pct:.1f}%, "
            f"Robust: {analysis.is_robust}"
        )

        return analysis

    def _execute_single_window(
        self,
        strategy: Any,
        symbol: str,
        data: Dict[str, pd.DataFrame],
        window_num: int,
        window_size: int
    ) -> WalkForwardResult:
        """Execute single walk-forward window"""

        daily_data = data['daily']

        # Calculate window boundaries
        window_start = window_num * window_size
        window_end = window_start + window_size

        # Make sure we don't exceed data
        if window_end > len(daily_data):
            window_end = len(daily_data)

        # Split into train/test
        train_end_idx = window_start + int(window_size * self.train_pct)

        train_start_date = daily_data.index[window_start]
        train_end_date = daily_data.index[train_end_idx - 1]
        test_start_date = daily_data.index[train_end_idx]
        test_end_date = daily_data.index[window_end - 1]

        # Convert timezone-aware to timezone-naive to avoid comparison issues
        if hasattr(train_start_date, 'tz') and train_start_date.tz is not None:
            train_start_date = train_start_date.tz_localize(None)
            train_end_date = train_end_date.tz_localize(None)
            test_start_date = test_start_date.tz_localize(None)
            test_end_date = test_end_date.tz_localize(None)

        logger.debug(
            f"  Train: {train_start_date.date()} to {train_end_date.date()}, "
            f"Test: {test_start_date.date()} to {test_end_date.date()}"
        )

        # Run backtest on training period
        train_result = self._run_backtest_for_period(
            strategy, symbol, data, train_start_date, train_end_date
        )

        # Run backtest on test period (out-of-sample)
        test_result = self._run_backtest_for_period(
            strategy, symbol, data, test_start_date, test_end_date
        )

        # Calculate metrics for both
        train_metrics = self.metrics_calculator.calculate(train_result)
        test_metrics = self.metrics_calculator.calculate(test_result)

        # Create window result
        window_result = WalkForwardResult(
            window_number=window_num + 1,
            train_start=train_start_date,
            train_end=train_end_date,
            test_start=test_start_date,
            test_end=test_end_date,
            in_sample_return_pct=train_metrics.total_return_pct,
            in_sample_sharpe=train_metrics.sharpe_ratio,
            in_sample_max_dd_pct=abs(train_metrics.calmar_ratio),  # Placeholder
            in_sample_trades=train_metrics.total_trades,
            oos_return_pct=test_metrics.total_return_pct,
            oos_sharpe=test_metrics.sharpe_ratio,
            oos_max_dd_pct=0.0,  # Would need risk metrics
            oos_trades=test_metrics.total_trades
        )

        logger.debug(
            f"  Window {window_num + 1}: "
            f"IS Return={train_metrics.total_return_pct:.1f}%, "
            f"OOS Return={test_metrics.total_return_pct:.1f}%, "
            f"Degradation={window_result.return_degradation_pct:.1f}%"
        )

        return window_result

    def _run_backtest_for_period(
        self,
        strategy: Any,
        symbol: str,
        data: Dict[str, pd.DataFrame],
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Run backtest for a specific period"""

        # Filter data to period
        period_data = {}
        for timeframe, df in data.items():
            if not df.empty:
                # Ensure timezone-naive comparison
                df_index = df.index
                if hasattr(df_index, 'tz') and df_index.tz is not None:
                    df_index = df_index.tz_localize(None)
                    df = df.copy()
                    df.index = df_index

                period_data[timeframe] = df.loc[start_date:end_date]

        # Run backtest
        result = self.backtest_executor.run_backtest(
            strategy=strategy,
            symbol=symbol,
            data=period_data,
            start_date=start_date,
            end_date=end_date
        )

        return result

    def get_summary(self, analysis: WalkForwardAnalysis) -> str:
        """
        Get text summary of walk-forward results

        Args:
            analysis: WalkForwardAnalysis object

        Returns:
            Formatted text summary
        """
        if not analysis.window_results:
            return "No walk-forward results available."

        lines = [
            "=== Walk-Forward Analysis Summary ===",
            f"Number of windows: {analysis.num_windows}",
            f"Average return degradation: {analysis.avg_return_degradation_pct:.1f}%",
            f"Average Sharpe degradation: {analysis.avg_sharpe_degradation_pct:.1f}%",
            f"Consistency score: {analysis.consistency_score:.1f}/100",
            f"Degradation acceptable: {'YES' if analysis.degradation_acceptable else 'NO'}",
            f"Strategy robust: {'YES' if analysis.is_robust else 'NO'}",
            "",
            "Window Details:"
        ]

        for w in analysis.window_results:
            lines.append(
                f"  Window {w.window_number}: "
                f"IS={w.in_sample_return_pct:.1f}%, "
                f"OOS={w.oos_return_pct:.1f}% "
                f"(Degradation: {w.return_degradation_pct:.1f}%)"
            )

        return "\n".join(lines)


# Test function
if __name__ == '__main__':
    from agents.backtesting.tools.data_tools import DataFetcherTool

    # Simple test strategy
    class SimpleStrategy:
        def generate_signal(self, data, current_date):
            # Simple moving average crossover
            daily = data.get('daily', pd.DataFrame())
            if len(daily) < 50:
                return None

            sma_20 = daily['close'].rolling(20).mean()
            sma_50 = daily['close'].rolling(50).mean()

            if sma_20.iloc[-1] > sma_50.iloc[-1]:
                # Bullish - generate signal
                current_price = daily['close'].iloc[-1]
                atr = (daily['high'] - daily['low']).rolling(14).mean().iloc[-1]

                return {
                    'entry_price': current_price,
                    'stop_loss': current_price - (2 * atr),
                    'target': current_price + (3 * atr)
                }

            return None

    print("Testing WalkForwardSkill...")

    # Fetch data
    fetcher = DataFetcherTool()
    data = fetcher.fetch_multi_timeframe_data(
        symbol="TATAMOTORS.NS",
        start_date="2022-01-01",
        end_date="2024-11-01",
        timeframes=['daily', 'weekly']
    )

    # Create strategy
    strategy = SimpleStrategy()

    # Run walk-forward analysis
    wf_skill = WalkForwardSkill(num_windows=5, train_pct=0.8)
    analysis = wf_skill.execute(strategy, "TATAMOTORS.NS", data)

    # Print results
    print("\n" + wf_skill.get_summary(analysis))

    # Detailed assessment
    if analysis.is_robust:
        print("\n✅ Strategy appears ROBUST across multiple periods")
    elif analysis.degradation_acceptable:
        print("\n🟡 Strategy has ACCEPTABLE degradation but low consistency")
    else:
        print("\n❌ Strategy shows HIGH DEGRADATION - likely overfit")
