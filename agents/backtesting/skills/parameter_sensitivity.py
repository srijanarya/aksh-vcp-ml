#!/usr/bin/env python3
"""
Parameter Sensitivity Analysis Skill

Tests how sensitive strategy performance is to parameter changes.
Robust strategies should have low sensitivity (performance doesn't collapse with small parameter changes).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
import copy
import logging

from agents.backtesting.tools.backtest_tools import BacktestExecutorTool
from agents.backtesting.tools.analysis_tools import PerformanceMetricsCalculator

logger = logging.getLogger(__name__)


class ParameterSensitivitySkill:
    """
    Test parameter sensitivity

    For each parameter:
    1. Vary by ±20%, ±10%, 0%
    2. Measure impact on Sharpe ratio
    3. Calculate sensitivity score

    Rating:
    - <20% Sharpe variation = ROBUST
    - 20-40% variation = MODERATE
    - >40% variation = FRAGILE
    """

    def __init__(self, variation_pcts: List[float] = [-20, -10, 0, 10, 20]):
        """
        Initialize parameter sensitivity analyzer

        Args:
            variation_pcts: List of percentage variations to test
        """
        self.variation_pcts = variation_pcts
        self.backtest_executor = BacktestExecutorTool()
        self.metrics_calculator = PerformanceMetricsCalculator()

    def execute(
        self,
        strategy: Any,
        symbol: str,
        data: Dict[str, pd.DataFrame],
        parameters_to_test: List[str] = None
    ) -> Dict[str, Any]:
        """
        Execute parameter sensitivity analysis

        Args:
            strategy: Strategy instance
            symbol: Stock symbol
            data: Multi-timeframe data
            parameters_to_test: List of parameter names (if None, test all numeric params)

        Returns:
            Dict with sensitivity results for each parameter
        """
        logger.info("Starting parameter sensitivity analysis...")

        # Get parameters to test
        if parameters_to_test is None:
            parameters_to_test = self._get_numeric_parameters(strategy)

        if not parameters_to_test:
            logger.warning("No numeric parameters found to test")
            return {}

        logger.info(f"Testing {len(parameters_to_test)} parameters: {parameters_to_test}")

        # Run baseline backtest
        logger.info("Running baseline backtest...")
        baseline_result = self._run_backtest(strategy, symbol, data)
        baseline_metrics = self.metrics_calculator.calculate(baseline_result)
        baseline_sharpe = baseline_metrics.sharpe_ratio

        logger.info(f"Baseline Sharpe: {baseline_sharpe:.2f}")

        # Test each parameter
        sensitivity_results = {}

        for param_name in parameters_to_test:
            logger.info(f"\nTesting parameter: {param_name}")

            param_results = self._test_parameter(
                strategy, symbol, data, param_name, baseline_sharpe
            )

            sensitivity_results[param_name] = param_results

        # Calculate overall robustness
        overall_robustness = self._calculate_overall_robustness(sensitivity_results)

        return {
            'baseline_sharpe': baseline_sharpe,
            'parameter_sensitivities': sensitivity_results,
            'overall_robustness': overall_robustness,
            'recommendations': self._get_recommendations(sensitivity_results, overall_robustness)
        }

    def _get_numeric_parameters(self, strategy: Any) -> List[str]:
        """
        Extract numeric parameters from strategy

        Looks for numeric attributes that are likely parameters
        """
        params = []

        for attr_name in dir(strategy):
            if attr_name.startswith('_'):
                continue

            attr_value = getattr(strategy, attr_name, None)

            if isinstance(attr_value, (int, float)) and not callable(attr_value):
                params.append(attr_name)

        return params

    def _test_parameter(
        self,
        strategy: Any,
        symbol: str,
        data: Dict[str, pd.DataFrame],
        param_name: str,
        baseline_sharpe: float
    ) -> Dict[str, Any]:
        """Test sensitivity for a single parameter"""

        original_value = getattr(strategy, param_name)
        sharpe_values = []

        for variation_pct in self.variation_pcts:
            # Calculate new value
            if variation_pct == 0:
                new_value = original_value
            else:
                new_value = original_value * (1 + variation_pct / 100)

                # Round to reasonable precision
                if isinstance(original_value, int):
                    new_value = int(round(new_value))
                else:
                    new_value = round(new_value, 2)

            # Set parameter
            setattr(strategy, param_name, new_value)

            # Run backtest
            try:
                result = self._run_backtest(strategy, symbol, data)
                metrics = self.metrics_calculator.calculate(result)
                sharpe = metrics.sharpe_ratio
            except Exception as e:
                logger.warning(f"Backtest failed for {param_name}={new_value}: {e}")
                sharpe = 0.0

            sharpe_values.append(sharpe)

            logger.debug(f"  {param_name}={new_value} ({variation_pct:+.0f}%): Sharpe={sharpe:.2f}")

        # Restore original value
        setattr(strategy, param_name, original_value)

        # Calculate sensitivity metrics
        sharpe_range = max(sharpe_values) - min(sharpe_values)
        sharpe_variation_pct = (sharpe_range / abs(baseline_sharpe) * 100) if baseline_sharpe != 0 else 0

        # Determine robustness rating
        if sharpe_variation_pct < 20:
            rating = 'ROBUST'
            color = '🟢'
        elif sharpe_variation_pct < 40:
            rating = 'MODERATE'
            color = '🟡'
        else:
            rating = 'FRAGILE'
            color = '🔴'

        return {
            'original_value': original_value,
            'sharpe_values': sharpe_values,
            'sharpe_range': sharpe_range,
            'sharpe_variation_pct': sharpe_variation_pct,
            'rating': rating,
            'color': color
        }

    def _run_backtest(
        self,
        strategy: Any,
        symbol: str,
        data: Dict[str, pd.DataFrame]
    ) -> Any:
        """Run backtest with current strategy parameters"""

        daily_data = data.get('daily', pd.DataFrame())

        if daily_data.empty:
            raise ValueError("No daily data available")

        start_date = daily_data.index[0]
        end_date = daily_data.index[-1]

        result = self.backtest_executor.run_backtest(
            strategy=strategy,
            symbol=symbol,
            data=data,
            start_date=start_date,
            end_date=end_date
        )

        return result

    def _calculate_overall_robustness(
        self, sensitivity_results: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Calculate overall robustness score"""

        if not sensitivity_results:
            return {'score': 0, 'level': 'unknown'}

        # Count ratings
        robust_count = sum(1 for r in sensitivity_results.values() if r['rating'] == 'ROBUST')
        moderate_count = sum(1 for r in sensitivity_results.values() if r['rating'] == 'MODERATE')
        fragile_count = sum(1 for r in sensitivity_results.values() if r['rating'] == 'FRAGILE')

        total = len(sensitivity_results)

        # Calculate score
        score = (robust_count * 100 + moderate_count * 60 + fragile_count * 20) / total

        # Determine level
        if score >= 80:
            level = 'excellent'
        elif score >= 60:
            level = 'good'
        elif score >= 40:
            level = 'moderate'
        else:
            level = 'poor'

        return {
            'score': score,
            'level': level,
            'robust_params': robust_count,
            'moderate_params': moderate_count,
            'fragile_params': fragile_count,
            'total_params': total
        }

    def _get_recommendations(
        self,
        sensitivity_results: Dict[str, Dict],
        overall_robustness: Dict
    ) -> List[str]:
        """Generate recommendations based on sensitivity analysis"""

        recommendations = []

        if overall_robustness['level'] == 'excellent':
            recommendations.append(
                "Strategy shows excellent parameter robustness - parameters are well-chosen"
            )
        elif overall_robustness['level'] in ['good', 'moderate']:
            recommendations.append(
                "Strategy has acceptable robustness but could be improved"
            )
        else:
            recommendations.append(
                "Strategy is highly sensitive to parameters - high risk of curve-fitting"
            )

        # Identify fragile parameters
        fragile_params = [
            name for name, results in sensitivity_results.items()
            if results['rating'] == 'FRAGILE'
        ]

        if fragile_params:
            recommendations.append(
                f"Fragile parameters detected: {', '.join(fragile_params)}. "
                "Consider using parameter ranges or simplifying strategy."
            )

        # Suggest using round numbers
        recommendations.append(
            "Use round numbers (10, 20, 50) instead of optimized values for robustness"
        )

        return recommendations


# Test function
if __name__ == '__main__':
    from agents.backtesting.tools.data_tools import DataFetcherTool

    print("Testing ParameterSensitivitySkill...")

    # Test strategy with parameters
    class ParameterizedStrategy:
        def __init__(self):
            self.sma_fast = 20
            self.sma_slow = 50
            self.atr_multiplier = 2.0

        def generate_signal(self, data, current_date):
            daily = data.get('daily', pd.DataFrame())

            if len(daily) < self.sma_slow + 1:
                return None

            sma_f = daily['close'].rolling(self.sma_fast).mean()
            sma_s = daily['close'].rolling(self.sma_slow).mean()

            if sma_f.iloc[-1] > sma_s.iloc[-1]:
                current_price = daily['close'].iloc[-1]
                atr = (daily['high'] - daily['low']).rolling(14).mean().iloc[-1]

                return {
                    'entry_price': current_price,
                    'stop_loss': current_price - (self.atr_multiplier * atr),
                    'target': current_price + (3 * atr)
                }

            return None

    # Fetch data
    fetcher = DataFetcherTool()
    data = fetcher.fetch_multi_timeframe_data(
        symbol="TATAMOTORS.NS",
        start_date="2023-01-01",
        end_date="2024-11-01",
        timeframes=['daily', 'weekly']
    )

    # Run sensitivity analysis
    strategy = ParameterizedStrategy()
    sensitivity_skill = ParameterSensitivitySkill()

    results = sensitivity_skill.execute(
        strategy,
        "TATAMOTORS.NS",
        data,
        parameters_to_test=['sma_fast', 'sma_slow', 'atr_multiplier']
    )

    # Print results
    print(f"\n=== Parameter Sensitivity Results ===")
    print(f"Baseline Sharpe: {results['baseline_sharpe']:.2f}")

    print(f"\n=== Parameter Sensitivities ===")
    for param, data_dict in results['parameter_sensitivities'].items():
        print(f"\n{param} (Original: {data_dict['original_value']})")
        print(f"  Sharpe Range: {data_dict['sharpe_range']:.2f}")
        print(f"  Variation: {data_dict['sharpe_variation_pct']:.1f}%")
        print(f"  Rating: {data_dict['color']} {data_dict['rating']}")

    print(f"\n=== Overall Robustness ===")
    rob = results['overall_robustness']
    print(f"Score: {rob['score']:.0f}/100")
    print(f"Level: {rob['level']}")
    print(f"Robust params: {rob['robust_params']}/{rob['total_params']}")
    print(f"Fragile params: {rob['fragile_params']}/{rob['total_params']}")

    print(f"\n=== Recommendations ===")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"{i}. {rec}")
