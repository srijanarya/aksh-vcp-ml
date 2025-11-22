#!/usr/bin/env python3
"""
Strategy Consultant Agent - Master Orchestrator

Coordinates all specialist agents and generates final consultant-grade report
with Go/No-Go decision.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, List, Any
from datetime import datetime
import logging

from agents.backtesting.specialists.backtesting_agent import BacktestingSpecialistAgent
from agents.backtesting.specialists.strategy_analyzer import StrategyAnalyzerAgent
from agents.backtesting.specialists.risk_assessor import RiskAssessorAgent
from agents.backtesting.tools.models import ExecutiveSummary

logger = logging.getLogger(__name__)


class StrategyConsultantAgent:
    """
    Master orchestrator for strategy consulting

    Coordinates:
    1. BacktestingSpecialistAgent - Executes backtests
    2. StrategyAnalyzerAgent - Analyzes strategy design
    3. RiskAssessorAgent - Evaluates risk

    Output:
    - Executive summary with Go/No-Go decision
    - Traffic light ratings (🟢🟡🔴)
    - Top 3 strengths and issues
    - Prioritized recommendations
    """

    def __init__(self):
        self.backtesting_agent = BacktestingSpecialistAgent()
        self.strategy_analyzer = StrategyAnalyzerAgent()
        self.risk_assessor = RiskAssessorAgent()

        logger.info("StrategyConsultantAgent initialized")

    def analyze_strategy(
        self,
        strategy: Any,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Complete strategy analysis with consultant-grade report

        Args:
            strategy: Strategy instance
            symbols: List of symbols to test
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Complete consultant report with executive summary
        """
        logger.info("="*70)
        logger.info("STRATEGY CONSULTANT - COMPREHENSIVE ANALYSIS")
        logger.info("="*70)
        logger.info(f"Strategy: {strategy.__class__.__name__}")
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info("="*70)

        # Phase 1: Backtesting
        logger.info("\n[1/3] Running Backtesting Specialist...")
        backtest_report = self.backtesting_agent.analyze(
            strategy, symbols, start_date, end_date
        )

        # Get primary symbol for detailed analysis
        primary_symbol = symbols[0]
        primary_report = next(
            (r for r in backtest_report['symbol_reports'] if r['symbol'] == primary_symbol),
            None
        )

        if not primary_report or primary_report.get('status') == 'failed':
            logger.error("Primary symbol backtest failed")
            return self._create_failed_report(strategy, "Backtest failed")

        # Phase 2: Strategy Analysis
        logger.info("\n[2/3] Running Strategy Analyzer...")

        # Prepare backtest results dict for analyzer
        backtest_results_dict = {
            'full': primary_report['backtest_result'],
            # Add in-sample/out-of-sample if available from walk-forward
        }

        # Get data from backtesting agent (need to refetch for analyzer)
        from agents.backtesting.tools.data_tools import DataFetcherTool
        data_fetcher = DataFetcherTool()
        data = data_fetcher.fetch_multi_timeframe_data(
            symbol=primary_symbol,
            start_date=start_date,
            end_date=end_date,
            timeframes=['daily', 'weekly']
        )

        strategy_analysis = self.strategy_analyzer.analyze(
            strategy=strategy,
            symbol=primary_symbol,
            data=data,
            backtest_results=backtest_results_dict
        )

        # Phase 3: Risk Assessment
        logger.info("\n[3/3] Running Risk Assessor...")
        risk_assessment = self.risk_assessor.analyze(
            backtest_result=primary_report['backtest_result'],
            performance_metrics=primary_report['performance_metrics']
        )

        # Synthesize findings
        logger.info("\nSynthesizing findings...")
        executive_summary = self._create_executive_summary(
            strategy,
            backtest_report,
            strategy_analysis,
            risk_assessment,
            primary_report
        )

        # Create complete report
        complete_report = {
            'executive_summary': executive_summary,
            'backtest_report': backtest_report,
            'strategy_analysis': strategy_analysis,
            'risk_assessment': risk_assessment,
            'generated_at': datetime.now().isoformat()
        }

        logger.info("\n" + "="*70)
        logger.info(f"ANALYSIS COMPLETE - Decision: {executive_summary.decision}")
        logger.info("="*70)

        return complete_report

    def _create_executive_summary(
        self,
        strategy: Any,
        backtest_report: Dict,
        strategy_analysis: Dict,
        risk_assessment: Dict,
        primary_report: Dict
    ) -> ExecutiveSummary:
        """Create executive summary with Go/No-Go decision"""

        perf_metrics = primary_report['performance_metrics']
        risk_metrics = primary_report['risk_metrics']

        # Extract key metrics
        total_return = perf_metrics.total_return_pct
        sharpe = perf_metrics.sharpe_ratio
        max_dd = abs(risk_metrics.max_drawdown_pct)
        win_rate = perf_metrics.win_rate_pct

        # Determine traffic lights
        # Performance
        if sharpe >= 1.5 and total_return >= 15:
            perf_status = "green"
        elif sharpe >= 1.0 and total_return >= 5:
            perf_status = "yellow"
        else:
            perf_status = "red"

        # Risk
        if max_dd < 15:
            risk_status = "green"
        elif max_dd < 25:
            risk_status = "yellow"
        else:
            risk_status = "red"

        # Robustness (from strategy analysis)
        if strategy_analysis['status'] == 'PASS':
            robustness_status = "green"
        elif strategy_analysis['status'] == 'WARNING':
            robustness_status = "yellow"
        else:
            robustness_status = "red"

        # Complexity (from overfitting assessment)
        overfitting = strategy_analysis.get('overfitting_assessment')
        if overfitting and overfitting.is_likely_overfit:
            complexity_status = "red"
        elif overfitting and overfitting.risk_score > 40:
            complexity_status = "yellow"
        else:
            complexity_status = "green"

        # Collect all issues
        critical_issues = []
        warnings = []

        # From backtest
        if primary_report.get('issues'):
            for issue in primary_report['issues']:
                if 'CRITICAL' in issue:
                    critical_issues.append(issue)
                else:
                    warnings.append(issue)

        # From strategy analysis
        if strategy_analysis.get('issues'):
            critical_issues.extend(strategy_analysis['issues'])
        if strategy_analysis.get('warnings'):
            warnings.extend(strategy_analysis['warnings'])

        # From risk assessment
        if risk_assessment.get('issues'):
            critical_issues.extend(risk_assessment['issues'])
        if risk_assessment.get('warnings'):
            warnings.extend(risk_assessment['warnings'])

        # Collect recommendations
        recommendations = []
        if strategy_analysis.get('recommendations'):
            recommendations.extend(strategy_analysis['recommendations'])
        if risk_assessment.get('recommendations'):
            recommendations.extend(risk_assessment['recommendations'])

        # Calculate backtest period
        backtest_result = primary_report['backtest_result']
        period_years = (backtest_result.end_date - backtest_result.start_date).days / 365.25

        # Create summary
        summary = ExecutiveSummary(
            strategy_name=strategy.__class__.__name__,
            analyzed_date=datetime.now(),
            total_return_pct=total_return,
            sharpe_ratio=sharpe,
            max_drawdown_pct=max_dd,
            win_rate_pct=win_rate,
            performance_status=perf_status,
            risk_status=risk_status,
            robustness_status=robustness_status,
            complexity_status=complexity_status,
            critical_issues=critical_issues[:5],  # Top 5
            warnings=warnings[:5],  # Top 5
            recommendations=recommendations[:5],  # Top 5
            sample_size=perf_metrics.total_trades,
            backtest_period_years=period_years
        )

        # Determine final decision
        summary.determine_decision()

        return summary

    def _create_failed_report(self, strategy: Any, reason: str) -> Dict:
        """Create report for failed analysis"""

        summary = ExecutiveSummary(
            strategy_name=strategy.__class__.__name__,
            analyzed_date=datetime.now(),
            decision="NO GO",
            confidence_score=0.0,
            critical_issues=[reason],
            performance_status="red",
            risk_status="red",
            robustness_status="red",
            complexity_status="red"
        )

        return {
            'executive_summary': summary,
            'error': reason,
            'generated_at': datetime.now().isoformat()
        }


# Test function
if __name__ == '__main__':
    print("Testing StrategyConsultantAgent...")

    # Simple test strategy
    class TestStrategy:
        def __init__(self):
            self.sma_period = 20
            self.atr_mult = 2.0

        def generate_signal(self, data, current_date):
            import pandas as pd
            daily = data.get('daily', pd.DataFrame())
            if len(daily) < 50:
                return None

            sma = daily['close'].rolling(self.sma_period).mean()
            current_price = daily['close'].iloc[-1]

            if current_price > sma.iloc[-1]:
                atr = (daily['high'] - daily['low']).rolling(14).mean().iloc[-1]
                return {
                    'entry_price': current_price,
                    'stop_loss': current_price - (self.atr_mult * atr),
                    'target': current_price + (3 * atr)
                }
            return None

    # Run full analysis
    consultant = StrategyConsultantAgent()
    strategy = TestStrategy()

    report = consultant.analyze_strategy(
        strategy=strategy,
        symbols=['TATAMOTORS.NS'],
        start_date='2023-01-01',
        end_date='2024-11-01'
    )

    # Print executive summary
    summary = report['executive_summary']

    print(f"\n{'='*70}")
    print(f"EXECUTIVE SUMMARY")
    print(f"{'='*70}")
    print(f"Strategy: {summary.strategy_name}")
    print(f"Decision: {summary.decision}")
    print(f"Confidence: {summary.confidence_score:.0f}%")

    print(f"\n=== Traffic Lights ===")
    print(f"Performance: {summary.performance_status}")
    print(f"Risk: {summary.risk_status}")
    print(f"Robustness: {summary.robustness_status}")
    print(f"Complexity: {summary.complexity_status}")

    print(f"\n=== Key Metrics ===")
    print(f"Return: {summary.total_return_pct:.1f}%")
    print(f"Sharpe: {summary.sharpe_ratio:.2f}")
    print(f"Max DD: {summary.max_drawdown_pct:.1f}%")
    print(f"Win Rate: {summary.win_rate_pct:.1f}%")

    if summary.critical_issues:
        print(f"\n=== Critical Issues ===")
        for issue in summary.critical_issues:
            print(f"  🔴 {issue}")

    if summary.recommendations:
        print(f"\n=== Recommendations ===")
        for i, rec in enumerate(summary.recommendations, 1):
            print(f"  {i}. {rec}")

    print(f"\n{'='*70}")
