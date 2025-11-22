#!/usr/bin/env python3
"""
Market Regime Testing Skill

Tests strategy performance across different market conditions:
- Bull markets (strong uptrend)
- Bear markets (downtrend)
- Sideways/choppy markets

Helps identify if strategy is regime-dependent.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging

from agents.backtesting.tools.backtest_tools import BacktestExecutorTool
from agents.backtesting.tools.analysis_tools import PerformanceMetricsCalculator

logger = logging.getLogger(__name__)


class MarketRegimeSkill:
    """
    Test strategy across different market regimes

    Identifies regimes using simple moving averages:
    - Bull: Price > SMA(200) and SMA(50) > SMA(200)
    - Bear: Price < SMA(200) and SMA(50) < SMA(200)
    - Sideways: Everything else

    Measures consistency of returns across regimes.
    """

    def __init__(self):
        self.backtest_executor = BacktestExecutorTool()
        self.metrics_calculator = PerformanceMetricsCalculator()

    def execute(
        self,
        strategy: Any,
        symbol: str,
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Test strategy across market regimes

        Args:
            strategy: Strategy instance
            symbol: Stock symbol
            data: Multi-timeframe data

        Returns:
            Dict with regime analysis results
        """
        logger.info("Testing strategy across market regimes...")

        daily_data = data.get('daily', pd.DataFrame())

        if daily_data.empty:
            logger.error("No daily data available")
            return {}

        # Identify regimes
        regimes = self._identify_regimes(daily_data)

        # Test in each regime
        results = {}

        for regime_name, regime_periods in regimes.items():
            if not regime_periods:
                continue

            logger.info(f"Testing in {regime_name} regime...")

            # Combine all periods for this regime
            regime_results = []

            for start_date, end_date in regime_periods:
                period_result = self._test_period(
                    strategy, symbol, data, start_date, end_date
                )
                if period_result:
                    regime_results.append(period_result)

            if regime_results:
                # Aggregate results
                total_trades = sum(r.total_trades for r in regime_results)
                winning_trades = sum(r.winning_trades for r in regime_results)
                avg_return = np.mean([r.total_return_pct for r in regime_results])

                results[regime_name] = {
                    'num_periods': len(regime_periods),
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
                    'avg_return_pct': avg_return,
                    'periods': regime_results
                }

                logger.info(
                    f"  {regime_name}: {total_trades} trades, "
                    f"{results[regime_name]['win_rate']:.1f}% win rate, "
                    f"{avg_return:.1f}% avg return"
                )

        # Analyze consistency
        consistency = self._analyze_consistency(results)

        return {
            'regime_results': results,
            'consistency': consistency,
            'recommendations': self._get_recommendations(results, consistency)
        }

    def _identify_regimes(
        self, daily_data: pd.DataFrame
    ) -> Dict[str, List[Tuple[datetime, datetime]]]:
        """
        Identify bull/bear/sideways periods

        Returns:
            Dict with regime name -> list of (start_date, end_date) tuples
        """
        # Calculate moving averages
        data = daily_data.copy()
        data['sma_50'] = data['close'].rolling(50).mean()
        data['sma_200'] = data['close'].rolling(200).mean()

        # Classify each day
        regime_labels = []

        for idx, row in data.iterrows():
            if pd.isna(row['sma_50']) or pd.isna(row['sma_200']):
                regime_labels.append('unknown')
                continue

            if row['close'] > row['sma_200'] and row['sma_50'] > row['sma_200']:
                regime_labels.append('bull')
            elif row['close'] < row['sma_200'] and row['sma_50'] < row['sma_200']:
                regime_labels.append('bear')
            else:
                regime_labels.append('sideways')

        data['regime'] = regime_labels

        # Extract continuous periods
        regimes = {'bull': [], 'bear': [], 'sideways': []}

        current_regime = None
        period_start = None

        for idx, row in data.iterrows():
            regime = row['regime']

            if regime == 'unknown':
                continue

            if regime != current_regime:
                # Regime changed
                if current_regime and period_start:
                    regimes[current_regime].append((period_start, idx))

                current_regime = regime
                period_start = idx

        # Add final period
        if current_regime and period_start:
            regimes[current_regime].append((period_start, data.index[-1]))

        logger.info(
            f"Identified regimes: Bull={len(regimes['bull'])}, "
            f"Bear={len(regimes['bear'])}, Sideways={len(regimes['sideways'])}"
        )

        return regimes

    def _test_period(
        self,
        strategy: Any,
        symbol: str,
        data: Dict[str, pd.DataFrame],
        start_date: datetime,
        end_date: datetime
    ) -> Any:
        """Test strategy in a specific period"""

        # Filter data to period
        period_data = {}
        for timeframe, df in data.items():
            if not df.empty:
                period_data[timeframe] = df.loc[start_date:end_date]

        # Skip if period too short
        if len(period_data.get('daily', [])) < 30:
            return None

        # Run backtest
        result = self.backtest_executor.run_backtest(
            strategy=strategy,
            symbol=symbol,
            data=period_data,
            start_date=start_date,
            end_date=end_date
        )

        return result

    def _analyze_consistency(self, regime_results: Dict) -> Dict[str, Any]:
        """
        Analyze consistency across regimes

        Returns:
            Dict with consistency metrics
        """
        if not regime_results:
            return {'score': 0, 'level': 'unknown'}

        # Get returns for each regime
        returns = {
            regime: data['avg_return_pct']
            for regime, data in regime_results.items()
            if data['total_trades'] >= 5  # Min trades requirement
        }

        if len(returns) < 2:
            return {'score': 0, 'level': 'insufficient_data'}

        # Calculate consistency score
        # Lower variance = more consistent
        return_values = list(returns.values())
        avg_return = np.mean(return_values)
        std_return = np.std(return_values)

        # Coefficient of variation
        cv = (std_return / abs(avg_return)) if avg_return != 0 else float('inf')

        # Consistency score (0-100, higher is better)
        if cv < 0.5:
            score = 100
            level = 'excellent'
        elif cv < 1.0:
            score = 75
            level = 'good'
        elif cv < 2.0:
            score = 50
            level = 'moderate'
        else:
            score = 25
            level = 'poor'

        # Check if profitable in all regimes
        all_profitable = all(r > 0 for r in returns.values())

        return {
            'score': score,
            'level': level,
            'cv': cv,
            'all_profitable': all_profitable,
            'regime_returns': returns
        }

    def _get_recommendations(
        self, regime_results: Dict, consistency: Dict
    ) -> List[str]:
        """Get recommendations based on regime testing"""

        recommendations = []

        if consistency['level'] == 'excellent':
            recommendations.append(
                "Strategy shows excellent consistency across all market conditions"
            )
        elif consistency['level'] in ['good', 'moderate']:
            recommendations.append(
                "Strategy works reasonably well across regimes but has some variance"
            )
        else:
            recommendations.append(
                "Strategy is highly regime-dependent - consider regime filters"
            )

        # Identify best/worst regimes
        regime_returns = consistency.get('regime_returns', {})
        if regime_returns:
            best_regime = max(regime_returns, key=regime_returns.get)
            worst_regime = min(regime_returns, key=regime_returns.get)

            if regime_returns[worst_regime] < 0:
                recommendations.append(
                    f"Strategy loses money in {worst_regime} markets - "
                    f"consider adding regime filter"
                )

            if regime_returns[best_regime] > regime_returns[worst_regime] * 3:
                recommendations.append(
                    f"Strategy performs 3x better in {best_regime} markets - "
                    f"consider regime-specific position sizing"
                )

        return recommendations


# Test function
if __name__ == '__main__':
    from agents.backtesting.tools.data_tools import DataFetcherTool

    print("Testing MarketRegimeSkill...")

    # Simple test strategy
    class TrendStrategy:
        def generate_signal(self, data, current_date):
            daily = data.get('daily', pd.DataFrame())
            if len(daily) < 50:
                return None

            sma_20 = daily['close'].rolling(20).mean()
            current_price = daily['close'].iloc[-1]

            if current_price > sma_20.iloc[-1]:
                atr = (daily['high'] - daily['low']).rolling(14).mean().iloc[-1]
                return {
                    'entry_price': current_price,
                    'stop_loss': current_price - (2 * atr),
                    'target': current_price + (3 * atr)
                }
            return None

    # Fetch data
    fetcher = DataFetcherTool()
    data = fetcher.fetch_multi_timeframe_data(
        symbol="TATAMOTORS.NS",
        start_date="2020-01-01",
        end_date="2024-11-01",
        timeframes=['daily', 'weekly']
    )

    # Test across regimes
    strategy = TrendStrategy()
    regime_skill = MarketRegimeSkill()
    results = regime_skill.execute(strategy, "TATAMOTORS.NS", data)

    # Print results
    print(f"\n=== Regime Testing Results ===")
    for regime, data_dict in results['regime_results'].items():
        print(f"\n{regime.upper()} Market:")
        print(f"  Periods: {data_dict['num_periods']}")
        print(f"  Trades: {data_dict['total_trades']}")
        print(f"  Win Rate: {data_dict['win_rate']:.1f}%")
        print(f"  Avg Return: {data_dict['avg_return_pct']:.1f}%")

    print(f"\n=== Consistency Analysis ===")
    print(f"Score: {results['consistency']['score']:.0f}/100")
    print(f"Level: {results['consistency']['level']}")
    print(f"All Profitable: {results['consistency'].get('all_profitable', False)}")

    print(f"\n=== Recommendations ===")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"{i}. {rec}")
