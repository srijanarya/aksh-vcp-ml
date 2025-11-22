#!/usr/bin/env python3
"""
Report Generator

Formats consultant reports as markdown with traffic lights and executive summaries.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate formatted reports

    Output formats:
    - Executive summary (markdown)
    - Detailed backtest report
    - Strategy analysis report
    - Risk assessment report
    """

    def __init__(self):
        self.emoji_map = {
            'green': '🟢',
            'yellow': '🟡',
            'red': '🔴',
            'PASS': '✅',
            'WARNING': '⚠️',
            'FAIL': '❌'
        }

    def generate_executive_summary(self, report: Dict) -> str:
        """
        Generate executive summary markdown

        Args:
            report: Complete consultant report

        Returns:
            Formatted markdown string
        """
        summary = report.get('executive_summary')

        if not summary:
            return "No executive summary available"

        lines = [
            "# Strategy Consultant Report",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"**Strategy**: {summary.strategy_name}",
            f"**Period**: {summary.backtest_period_years:.1f} years ({summary.sample_size} trades)",
            "",
            f"### 🎯 Decision: **{summary.decision}**",
            f"**Confidence**: {summary.confidence_score:.0f}%",
            "",
            "### Performance Scorecard",
            "",
            f"| Category | Rating | Score |",
            f"|----------|--------|-------|",
            f"| Performance | {self._get_emoji(summary.performance_status)} {summary.performance_status.upper()} | {summary.total_return_pct:.1f}% return, {summary.sharpe_ratio:.2f} Sharpe |",
            f"| Risk | {self._get_emoji(summary.risk_status)} {summary.risk_status.upper()} | {summary.max_drawdown_pct:.1f}% max DD |",
            f"| Robustness | {self._get_emoji(summary.robustness_status)} {summary.robustness_status.upper()} | Cross-validation & regime testing |",
            f"| Complexity | {self._get_emoji(summary.complexity_status)} {summary.complexity_status.upper()} | Overfitting analysis |",
            "",
            "### Key Metrics",
            "",
            f"- **Total Return**: {summary.total_return_pct:.2f}%",
            f"- **Sharpe Ratio**: {summary.sharpe_ratio:.2f}",
            f"- **Max Drawdown**: {summary.max_drawdown_pct:.2f}%",
            f"- **Win Rate**: {summary.win_rate_pct:.1f}%",
            f"- **Sample Size**: {summary.sample_size} trades",
            "",
        ]

        # Critical issues
        if summary.critical_issues:
            lines.extend([
                "### 🔴 Critical Issues",
                ""
            ])
            for issue in summary.critical_issues:
                lines.append(f"- {issue}")
            lines.append("")

        # Warnings
        if summary.warnings:
            lines.extend([
                "### ⚠️ Warnings",
                ""
            ])
            for warning in summary.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        # Recommendations
        if summary.recommendations:
            lines.extend([
                "### 💡 Recommendations",
                ""
            ])
            for i, rec in enumerate(summary.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        # Add decision explanation
        lines.extend([
            "---",
            "",
            "### Decision Rationale",
            ""
        ])

        if summary.decision == "GO":
            lines.append("✅ **Strategy approved for live trading** with the following conditions:")
            lines.append("- Monitor performance closely in first 30 days")
            lines.append("- Implement kill switches for max drawdown limits")
            lines.append("- Review weekly to ensure consistency with backtest")
        elif summary.decision == "PROCEED WITH CAUTION":
            lines.append("⚠️ **Strategy shows promise but has warnings**:")
            lines.append("- Address critical issues before live deployment")
            lines.append("- Consider paper trading for 1-2 months")
            lines.append("- Implement strict risk controls")
        else:
            lines.append("❌ **Strategy NOT recommended for live trading**:")
            lines.append("- Critical issues must be resolved")
            lines.append("- Consider redesigning strategy from scratch")
            lines.append("- Do not proceed without addressing issues")

        return "\n".join(lines)

    def generate_detailed_report(self, report: Dict) -> str:
        """Generate complete detailed report"""

        sections = [
            self.generate_executive_summary(report),
            "",
            "---",
            "",
            self._generate_backtest_section(report.get('backtest_report', {})),
            "",
            "---",
            "",
            self._generate_strategy_analysis_section(report.get('strategy_analysis', {})),
            "",
            "---",
            "",
            self._generate_risk_section(report.get('risk_assessment', {})),
        ]

        return "\n".join(sections)

    def _generate_backtest_section(self, backtest_report: Dict) -> str:
        """Generate backtest section"""

        if not backtest_report:
            return "## Backtest Results\n\nNo data available"

        lines = [
            "## Detailed Backtest Results",
            "",
            f"**Overall Status**: {self._get_emoji(backtest_report.get('overall_status', 'FAIL'))} {backtest_report.get('overall_status', 'UNKNOWN')}",
            ""
        ]

        summary = backtest_report.get('summary', {})

        if summary:
            lines.extend([
                "### Summary Statistics",
                "",
                f"- Symbols tested: {summary.get('total_symbols', 0)}",
                f"- Passed: {summary.get('passed', 0)}",
                f"- Warnings: {summary.get('warnings', 0)}",
                f"- Failed: {summary.get('failed', 0)}",
                f"- Average Sharpe: {summary.get('avg_sharpe', 0):.2f}",
                f"- Average Return: {summary.get('avg_return', 0):.1f}%",
                f"- Total Trades: {summary.get('total_trades', 0)}",
                ""
            ])

        return "\n".join(lines)

    def _generate_strategy_analysis_section(self, strategy_analysis: Dict) -> str:
        """Generate strategy analysis section"""

        if not strategy_analysis:
            return "## Strategy Analysis\n\nNo data available"

        lines = [
            "## Strategy Analysis",
            "",
            f"**Status**: {self._get_emoji(strategy_analysis.get('status', 'FAIL'))} {strategy_analysis.get('status', 'UNKNOWN')}",
            "",
            "### Overfitting Assessment",
            ""
        ]

        overfitting = strategy_analysis.get('overfitting_assessment')
        if overfitting:
            lines.append(f"- **Risk Score**: {overfitting.risk_score:.0f}/100")
            lines.append(f"- **Likely Overfit**: {'YES' if overfitting.is_likely_overfit else 'NO'}")
            lines.append(f"- **Degradation**: {overfitting.in_sample_oos_degradation_pct:.1f}%")
            lines.append("")

        # Parameter sensitivity
        param_sens = strategy_analysis.get('parameter_sensitivity', {})
        if param_sens:
            robustness = param_sens.get('overall_robustness', {})
            lines.extend([
                "### Parameter Robustness",
                "",
                f"- **Score**: {robustness.get('score', 0):.0f}/100",
                f"- **Level**: {robustness.get('level', 'unknown').upper()}",
                ""
            ])

        return "\n".join(lines)

    def _generate_risk_section(self, risk_assessment: Dict) -> str:
        """Generate risk assessment section"""

        if not risk_assessment:
            return "## Risk Assessment\n\nNo data available"

        lines = [
            "## Risk Assessment",
            "",
            f"**Status**: {self._get_emoji(risk_assessment.get('status', 'FAIL'))} {risk_assessment.get('status', 'UNKNOWN')}",
            ""
        ]

        risk_metrics = risk_assessment.get('risk_metrics')
        if risk_metrics:
            lines.extend([
                "### Risk Metrics",
                "",
                f"- **Max Drawdown**: {abs(risk_metrics.max_drawdown_pct):.2f}%",
                f"- **Recovery Time**: {risk_metrics.max_drawdown_duration_days} days",
                f"- **Volatility (Annual)**: {risk_metrics.annualized_volatility_pct:.2f}%",
                f"- **VaR (95%)**: {abs(risk_metrics.var_95_pct):.2f}%",
                f"- **CVaR (95%)**: {abs(risk_metrics.cvar_95_pct):.2f}%",
                f"- **Risk Level**: {risk_metrics.drawdown_risk_level.upper()}",
                ""
            ])

        return "\n".join(lines)

    def _get_emoji(self, status: str) -> str:
        """Get emoji for status"""
        return self.emoji_map.get(status, '❓')

    def save_report(self, report: Dict, output_path: str, detailed: bool = False):
        """
        Save report to file

        Args:
            report: Consultant report
            output_path: Path to save file
            detailed: If True, save detailed report; else executive summary only
        """
        if detailed:
            content = self.generate_detailed_report(report)
        else:
            content = self.generate_executive_summary(report)

        with open(output_path, 'w') as f:
            f.write(content)

        logger.info(f"Report saved to {output_path}")


# Test
if __name__ == '__main__':
    print("ReportGenerator implemented successfully")
