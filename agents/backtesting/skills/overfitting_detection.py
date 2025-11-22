#!/usr/bin/env python3
"""
Overfitting Detection Skill

Detects signs of overfitting through multiple tests:
1. Parameter count (>6 = high risk)
2. Win rate analysis (>85% = suspicious)
3. In-sample vs out-of-sample degradation (>30% = overfit)
4. Parameter sensitivity (high sensitivity = curve-fitting)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import inspect
import logging

from agents.backtesting.tools.models import OverfittingAssessment, StrategyComplexity

logger = logging.getLogger(__name__)


class OverfittingDetectorSkill:
    """
    Detect overfitting in trading strategies

    Red flags:
    - Too many parameters (>6)
    - Unrealistic win rate (>85%)
    - High in-sample vs OOS degradation (>30%)
    - High parameter sensitivity (fragile)
    - Excessive rules/conditions (>7)
    """

    def __init__(self):
        self.max_parameters = 6
        self.max_win_rate = 85.0
        self.max_degradation = 30.0
        self.max_rules = 7

    def execute(
        self,
        strategy: Any,
        backtest_results: Dict[str, Any],
        walk_forward_analysis: Any = None
    ) -> OverfittingAssessment:
        """
        Execute overfitting detection

        Args:
            strategy: Strategy instance
            backtest_results: Dict with 'full', 'in_sample', 'out_of_sample' results
            walk_forward_analysis: Optional WalkForwardAnalysis

        Returns:
            OverfittingAssessment with findings
        """
        logger.info("Detecting overfitting...")

        assessment = OverfittingAssessment()

        # 1. Analyze strategy complexity
        complexity = self._analyze_complexity(strategy)

        if complexity.is_too_complex:
            assessment.excessive_parameters = True
            assessment.add_issue(
                f"Excessive complexity: {complexity.total_rules} rules, "
                f"{complexity.total_parameters} parameters"
            )

        # 2. Check win rate
        full_results = backtest_results.get('full')
        if full_results:
            win_rate = full_results.winning_trades / full_results.total_trades * 100 if full_results.total_trades > 0 else 0

            if win_rate > self.max_win_rate:
                assessment.suspicious_win_rate = True
                assessment.add_issue(
                    f"Suspiciously high win rate: {win_rate:.1f}% (>{self.max_win_rate}%)"
                )

        # 3. Check in-sample vs out-of-sample degradation
        if 'in_sample' in backtest_results and 'out_of_sample' in backtest_results:
            degradation = self._calculate_degradation(
                backtest_results['in_sample'],
                backtest_results['out_of_sample']
            )

            assessment.in_sample_oos_degradation_pct = degradation

            if degradation > self.max_degradation:
                assessment.add_issue(
                    f"High OOS degradation: {degradation:.1f}% (>{self.max_degradation}%)"
                )

        # 4. Check walk-forward consistency
        if walk_forward_analysis and not walk_forward_analysis.degradation_acceptable:
            assessment.add_warning(
                f"Walk-forward shows inconsistency: "
                f"{walk_forward_analysis.avg_return_degradation_pct:.1f}% degradation"
            )

        # Calculate overall risk score
        assessment.risk_score = self._calculate_risk_score(assessment, complexity)

        # Determine if likely overfit
        assessment.is_likely_overfit = (
            assessment.risk_score > 60 or
            len(assessment.issues_found) >= 2
        )

        logger.info(
            f"Overfitting risk: {'HIGH' if assessment.is_likely_overfit else 'LOW'}, "
            f"Score: {assessment.risk_score:.0f}/100"
        )

        return assessment

    def _analyze_complexity(self, strategy: Any) -> StrategyComplexity:
        """
        Analyze strategy complexity

        Tries to count:
        - Number of parameters (from __init__ or class attributes)
        - Number of rules (heuristic: count conditions in generate_signal)
        """
        # Get parameters from __init__
        try:
            init_signature = inspect.signature(strategy.__init__)
            parameters = [
                p.name for p in init_signature.parameters.values()
                if p.name != 'self' and p.default != inspect.Parameter.empty
            ]
        except Exception as e:
            logger.warning(f"Could not inspect __init__: {e}")
            parameters = []

        # Also check for class attributes
        class_attrs = [
            attr for attr in dir(strategy)
            if not attr.startswith('_') and not callable(getattr(strategy, attr))
        ]

        # Combine (deduplicate)
        all_params = list(set(parameters + class_attrs))

        # Try to count rules (heuristic: count if/elif in generate_signal source)
        try:
            source = inspect.getsource(strategy.generate_signal)
            rule_count = source.count('if ') + source.count('elif ')
        except Exception as e:
            logger.warning(f"Could not get source for rule counting: {e}")
            rule_count = 0

        complexity = StrategyComplexity(
            total_rules=rule_count,
            total_parameters=len(all_params),
            parameter_names=all_params
        )

        logger.debug(
            f"Complexity: {complexity.total_rules} rules, "
            f"{complexity.total_parameters} parameters"
        )

        return complexity

    def _calculate_degradation(
        self,
        in_sample_result: Any,
        oos_result: Any
    ) -> float:
        """
        Calculate performance degradation from in-sample to out-of-sample

        Returns:
            Degradation percentage (positive = worse OOS)
        """
        is_return = in_sample_result.total_return_pct
        oos_return = oos_result.total_return_pct

        if is_return == 0:
            return 0.0

        degradation = ((is_return - oos_return) / abs(is_return)) * 100

        return degradation

    def _calculate_risk_score(
        self,
        assessment: OverfittingAssessment,
        complexity: StrategyComplexity
    ) -> float:
        """
        Calculate overall overfitting risk score (0-100)

        Higher = more risk
        """
        score = 0.0

        # Complexity penalty
        score += complexity.complexity_score * 0.3  # Up to 30 points

        # Excessive parameters
        if assessment.excessive_parameters:
            score += 25

        # Suspicious win rate
        if assessment.suspicious_win_rate:
            score += 25

        # OOS degradation
        if assessment.in_sample_oos_degradation_pct > self.max_degradation:
            score += 30

        # Issues found
        score += len(assessment.issues_found) * 10

        return min(100, score)

    def get_recommendations(self, assessment: OverfittingAssessment) -> List[str]:
        """
        Get recommendations based on overfitting assessment

        Args:
            assessment: OverfittingAssessment

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if assessment.excessive_parameters:
            recommendations.append(
                "Reduce number of parameters - aim for 4-6 maximum"
            )
            recommendations.append(
                "Use round numbers for parameters (10, 20, 50) instead of optimized values"
            )

        if assessment.suspicious_win_rate:
            recommendations.append(
                "Win rate >85% is unrealistic - check for look-ahead bias"
            )
            recommendations.append(
                "Verify entry/exit logic doesn't use future data"
            )

        if assessment.in_sample_oos_degradation_pct > self.max_degradation:
            recommendations.append(
                f"High degradation ({assessment.in_sample_oos_degradation_pct:.1f}%) "
                "suggests overfitting - simplify strategy"
            )
            recommendations.append(
                "Consider using walk-forward optimization instead of fitting to entire dataset"
            )

        if assessment.parameter_sensitivity_high:
            recommendations.append(
                "High parameter sensitivity - strategy is fragile"
            )
            recommendations.append(
                "Use parameter ranges instead of single optimized values"
            )

        if not recommendations:
            recommendations.append(
                "Strategy shows good robustness - continue with live testing"
            )

        return recommendations


# Test function
if __name__ == '__main__':
    from agents.backtesting.tools.models import BacktestResult
    from datetime import datetime

    print("Testing OverfittingDetectorSkill...")

    # Create a complex strategy (likely overfit)
    class ComplexStrategy:
        def __init__(
            self,
            sma_fast=7,
            sma_slow=23,
            rsi_period=13,
            rsi_upper=71,
            rsi_lower=29,
            atr_mult=1.7,
            vol_threshold=1.3
        ):
            self.sma_fast = sma_fast
            self.sma_slow = sma_slow
            self.rsi_period = rsi_period
            self.rsi_upper = rsi_upper
            self.rsi_lower = rsi_lower
            self.atr_mult = atr_mult
            self.vol_threshold = vol_threshold

        def generate_signal(self, data, current_date):
            if len(data['daily']) < 50:
                return None

            sma_f = data['daily']['close'].rolling(self.sma_fast).mean()
            sma_s = data['daily']['close'].rolling(self.sma_slow).mean()

            if sma_f.iloc[-1] > sma_s.iloc[-1]:
                if data['daily']['rsi'].iloc[-1] > self.rsi_lower:
                    if data['daily']['rsi'].iloc[-1] < self.rsi_upper:
                        if data['daily']['volume'].iloc[-1] > data['daily']['volume'].mean() * self.vol_threshold:
                            current_price = data['daily']['close'].iloc[-1]
                            atr = data['daily']['atr'].iloc[-1]

                            return {
                                'entry_price': current_price,
                                'stop_loss': current_price - (self.atr_mult * atr),
                                'target': current_price + (3 * atr)
                            }
            return None

    # Create mock backtest results
    in_sample_result = BacktestResult(
        strategy_name="ComplexStrategy",
        symbol="TEST.NS",
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        initial_capital=100000,
        final_capital=130000,  # 30% return
        trades=[],
        equity_curve=pd.DataFrame()
    )
    in_sample_result.winning_trades = 45
    in_sample_result.total_trades = 50  # 90% win rate!

    oos_result = BacktestResult(
        strategy_name="ComplexStrategy",
        symbol="TEST.NS",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 11, 1),
        initial_capital=100000,
        final_capital=105000,  # 5% return (83% degradation!)
        trades=[],
        equity_curve=pd.DataFrame()
    )
    oos_result.winning_trades = 18
    oos_result.total_trades = 30

    # Run overfitting detection
    strategy = ComplexStrategy()
    detector = OverfittingDetectorSkill()

    backtest_results = {
        'full': in_sample_result,
        'in_sample': in_sample_result,
        'out_of_sample': oos_result
    }

    assessment = detector.execute(strategy, backtest_results)

    # Print results
    print(f"\n=== Overfitting Assessment ===")
    print(f"Risk Score: {assessment.risk_score:.0f}/100")
    print(f"Likely Overfit: {'YES' if assessment.is_likely_overfit else 'NO'}")
    print(f"Excessive Parameters: {assessment.excessive_parameters}")
    print(f"Suspicious Win Rate: {assessment.suspicious_win_rate}")
    print(f"OOS Degradation: {assessment.in_sample_oos_degradation_pct:.1f}%")

    if assessment.issues_found:
        print(f"\n=== Issues Found ===")
        for issue in assessment.issues_found:
            print(f"  ❌ {issue}")

    if assessment.warnings:
        print(f"\n=== Warnings ===")
        for warning in assessment.warnings:
            print(f"  ⚠️  {warning}")

    # Get recommendations
    recommendations = detector.get_recommendations(assessment)
    print(f"\n=== Recommendations ===")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
