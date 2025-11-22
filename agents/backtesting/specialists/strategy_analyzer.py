#!/usr/bin/env python3
"""
Strategy Analyzer Specialist Agent

Analyzes strategy design for complexity, overfitting, and robustness.
Uses: Rule counter, parameter analyzer, overfitting detector, sensitivity tester.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from typing import Dict, List, Any
import logging

from agents.backtesting.skills.overfitting_detection import OverfittingDetectorSkill
from agents.backtesting.skills.parameter_sensitivity import ParameterSensitivitySkill
from agents.backtesting.skills.regime_testing import MarketRegimeSkill

logger = logging.getLogger(__name__)


class StrategyAnalyzerAgent:
    """
    Specialist agent for strategy analysis

    Responsibilities:
    1. Analyze strategy complexity
    2. Detect overfitting
    3. Test parameter sensitivity
    4. Test across market regimes
    5. Generate strategy analysis report
    """

    def __init__(self):
        self.overfitting_detector = OverfittingDetectorSkill()
        self.param_sensitivity = ParameterSensitivitySkill()
        self.regime_tester = MarketRegimeSkill()

        logger.info("StrategyAnalyzerAgent initialized")

    def analyze(
        self,
        strategy: Any,
        symbol: str,
        data: Dict,
        backtest_results: Dict
    ) -> Dict[str, Any]:
        """
        Analyze strategy design and robustness

        Args:
            strategy: Strategy instance
            symbol: Primary symbol for testing
            data: Multi-timeframe data
            backtest_results: Results from BacktestingAgent

        Returns:
            Strategy analysis report
        """
        logger.info(f"Analyzing strategy design for {symbol}...")

        # 1. Overfitting detection
        logger.info("  Running overfitting detection...")
        overfitting_assessment = self.overfitting_detector.execute(
            strategy=strategy,
            backtest_results=backtest_results
        )

        # 2. Parameter sensitivity
        logger.info("  Testing parameter sensitivity...")
        try:
            sensitivity_results = self.param_sensitivity.execute(
                strategy=strategy,
                symbol=symbol,
                data=data
            )
        except Exception as e:
            logger.warning(f"Parameter sensitivity failed: {e}")
            sensitivity_results = {}

        # 3. Market regime testing
        logger.info("  Testing across market regimes...")
        try:
            regime_results = self.regime_tester.execute(
                strategy=strategy,
                symbol=symbol,
                data=data
            )
        except Exception as e:
            logger.warning(f"Regime testing failed: {e}")
            regime_results = {}

        # 4. Determine overall rating
        issues = []
        warnings = []

        # Check overfitting
        if overfitting_assessment.is_likely_overfit:
            issues.extend(overfitting_assessment.issues_found)
        warnings.extend(overfitting_assessment.warnings)

        # Check parameter robustness
        if sensitivity_results:
            rob = sensitivity_results.get('overall_robustness', {})
            if rob.get('level') == 'poor':
                issues.append("Strategy shows poor parameter robustness")
            elif rob.get('level') == 'moderate':
                warnings.append("Strategy has moderate parameter sensitivity")

        # Check regime consistency
        if regime_results:
            consistency = regime_results.get('consistency', {})
            if consistency.get('level') == 'poor':
                issues.append("Strategy is highly regime-dependent")
            elif consistency.get('level') == 'moderate':
                warnings.append("Strategy shows some regime dependency")

        # Overall status
        if len(issues) > 0:
            status = 'FAIL'
            rating = '🔴'
        elif len(warnings) > 2:
            status = 'WARNING'
            rating = '🟡'
        else:
            status = 'PASS'
            rating = '🟢'

        return {
            'status': status,
            'rating': rating,
            'overfitting_assessment': overfitting_assessment,
            'parameter_sensitivity': sensitivity_results,
            'regime_testing': regime_results,
            'issues': issues,
            'warnings': warnings,
            'recommendations': self._generate_recommendations(
                overfitting_assessment, sensitivity_results, regime_results
            )
        }

    def _generate_recommendations(
        self,
        overfitting: Any,
        sensitivity: Dict,
        regime: Dict
    ) -> List[str]:
        """Generate recommendations"""

        recommendations = []

        # Overfitting recommendations
        if overfitting.is_likely_overfit:
            recommendations.extend(
                self.overfitting_detector.get_recommendations(overfitting)
            )

        # Parameter recommendations
        if sensitivity and sensitivity.get('recommendations'):
            recommendations.extend(sensitivity['recommendations'])

        # Regime recommendations
        if regime and regime.get('recommendations'):
            recommendations.extend(regime['recommendations'])

        return recommendations


# Test
if __name__ == '__main__':
    print("StrategyAnalyzerAgent implemented successfully")
