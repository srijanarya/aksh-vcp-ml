#!/usr/bin/env python3
"""
Risk Assessor Specialist Agent

Evaluates risk and drawdown characteristics.
Uses: Drawdown calculator, VaR calculator, risk metrics.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from typing import Dict, List, Any
import logging

from agents.backtesting.tools.risk_tools import RiskMetricsCalculator

logger = logging.getLogger(__name__)


class RiskAssessorAgent:
    """
    Specialist agent for risk assessment

    Responsibilities:
    1. Analyze drawdowns
    2. Calculate VaR/CVaR
    3. Validate position sizing
    4. Assess risk-adjusted returns
    5. Generate risk report
    """

    def __init__(self):
        self.risk_calculator = RiskMetricsCalculator()

        # Risk thresholds (research-based)
        self.max_dd_acceptable = 20.0  # 20%
        self.max_dd_critical = 30.0  # 30%
        self.min_calmar = 1.0
        self.min_sharpe = 1.0

        logger.info("RiskAssessorAgent initialized")

    def analyze(
        self,
        backtest_result: Any,
        performance_metrics: Any
    ) -> Dict[str, Any]:
        """
        Analyze risk characteristics

        Args:
            backtest_result: Backtest results with equity curve
            performance_metrics: Performance metrics

        Returns:
            Risk assessment report
        """
        logger.info("Analyzing risk characteristics...")

        # 1. Calculate risk metrics
        risk_metrics = self.risk_calculator.calculate(backtest_result)

        # 2. Analyze underwater periods
        logger.info("  Analyzing underwater periods...")
        underwater_periods = self.risk_calculator.analyze_underwater_periods(
            backtest_result.equity_curve
        )

        # 3. Calculate recovery stats
        logger.info("  Calculating recovery statistics...")
        recovery_stats = self.risk_calculator.calculate_recovery_stats(
            backtest_result.equity_curve
        )

        # 4. Assess risk levels
        issues, warnings = self._assess_risk_levels(
            risk_metrics, performance_metrics, recovery_stats
        )

        # 5. Determine overall status
        if len(issues) > 0:
            status = 'FAIL'
            rating = '🔴'
        elif len(warnings) > 1:
            status = 'WARNING'
            rating = '🟡'
        else:
            status = 'PASS'
            rating = '🟢'

        return {
            'status': status,
            'rating': rating,
            'risk_metrics': risk_metrics,
            'underwater_periods': underwater_periods,
            'recovery_stats': recovery_stats,
            'issues': issues,
            'warnings': warnings,
            'recommendations': self._generate_recommendations(
                risk_metrics, performance_metrics, issues, warnings
            )
        }

    def _assess_risk_levels(
        self,
        risk_metrics: Any,
        perf_metrics: Any,
        recovery_stats: Dict
    ) -> tuple:
        """Assess if risk levels are acceptable"""

        issues = []
        warnings = []

        # 1. Maximum drawdown
        max_dd = abs(risk_metrics.max_drawdown_pct)

        if max_dd > self.max_dd_critical:
            issues.append(
                f"CRITICAL: Max drawdown {max_dd:.1f}% exceeds {self.max_dd_critical}%"
            )
        elif max_dd > self.max_dd_acceptable:
            warnings.append(
                f"Max drawdown {max_dd:.1f}% exceeds {self.max_dd_acceptable}% target"
            )

        # 2. Drawdown duration
        if risk_metrics.max_drawdown_duration_days > 365:
            warnings.append(
                f"Long drawdown period: {risk_metrics.max_drawdown_duration_days} days (>1 year)"
            )

        # 3. Risk-adjusted returns
        if perf_metrics.calmar_ratio < self.min_calmar:
            warnings.append(
                f"Low Calmar ratio {perf_metrics.calmar_ratio:.2f} (< {self.min_calmar})"
            )

        if perf_metrics.sharpe_ratio < self.min_sharpe:
            warnings.append(
                f"Low Sharpe ratio {perf_metrics.sharpe_ratio:.2f} (< {self.min_sharpe})"
            )

        # 4. VaR assessment
        var_95 = abs(risk_metrics.var_95_pct)
        if var_95 > 5.0:  # 5% daily loss at 95% confidence
            warnings.append(
                f"High VaR(95%): {var_95:.2f}% - large potential daily losses"
            )

        # 5. Recovery time
        avg_recovery = recovery_stats.get('avg_recovery_days', 0)
        if avg_recovery > 180:  # 6 months
            warnings.append(
                f"Long average recovery time: {avg_recovery:.0f} days"
            )

        return issues, warnings

    def _generate_recommendations(
        self,
        risk_metrics: Any,
        perf_metrics: Any,
        issues: List[str],
        warnings: List[str]
    ) -> List[str]:
        """Generate risk management recommendations"""

        recommendations = []

        # Drawdown recommendations
        max_dd = abs(risk_metrics.max_drawdown_pct)

        if max_dd > self.max_dd_critical:
            recommendations.append(
                "CRITICAL: Reduce position size or add stop-loss protection"
            )
            recommendations.append(
                "Consider maximum portfolio heat limits (e.g., 10% total risk)"
            )
        elif max_dd > self.max_dd_acceptable:
            recommendations.append(
                "Consider tighter stop-losses or smaller position sizes"
            )

        # Risk-adjusted return recommendations
        if perf_metrics.sharpe_ratio < self.min_sharpe:
            recommendations.append(
                "Improve Sharpe ratio by reducing losing trades or increasing winners"
            )

        if perf_metrics.calmar_ratio < self.min_calmar:
            recommendations.append(
                "Focus on reducing drawdowns rather than maximizing returns"
            )

        # VaR recommendations
        var_95 = abs(risk_metrics.var_95_pct)
        if var_95 > 5.0:
            recommendations.append(
                "High tail risk - consider position size limits and portfolio diversification"
            )

        # General recommendations
        if not recommendations:
            recommendations.append(
                "Risk levels are acceptable - maintain current risk management approach"
            )

        return recommendations


# Test
if __name__ == '__main__':
    print("RiskAssessorAgent implemented successfully")
