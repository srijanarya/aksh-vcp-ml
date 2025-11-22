#!/usr/bin/env python3
"""
Backtesting Specialist Agent

Orchestrates comprehensive backtesting with statistical validation.
Uses: Data fetcher, backtest executor, walk-forward analysis, performance metrics.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pandas as pd
from typing import Dict, List, Any
from datetime import datetime
import logging

from agents.backtesting.tools.data_tools import DataFetcherTool
from agents.backtesting.tools.backtest_tools import BacktestExecutorTool
from agents.backtesting.tools.analysis_tools import PerformanceMetricsCalculator, RiskMetricsCalculator
from agents.backtesting.skills.walk_forward import WalkForwardSkill

logger = logging.getLogger(__name__)


class BacktestingSpecialistAgent:
    """
    Specialist agent for comprehensive backtesting

    Responsibilities:
    1. Execute full backtest
    2. Run walk-forward analysis
    3. Calculate performance metrics
    4. Validate statistical significance
    5. Generate backtest report

    Checks:
    - Minimum 30 trades
    - Minimum 2 years data
    - Walk-forward consistency
    - Out-of-sample validation
    """

    def __init__(self):
        self.data_fetcher = DataFetcherTool()
        self.backtest_executor = BacktestExecutorTool()
        self.metrics_calculator = PerformanceMetricsCalculator()
        self.risk_calculator = RiskMetricsCalculator()
        self.walk_forward = WalkForwardSkill()

        logger.info("BacktestingSpecialistAgent initialized")

    def analyze(
        self,
        strategy: Any,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Run comprehensive backtest analysis

        Args:
            strategy: Strategy instance
            symbols: List of symbols to test
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dict with backtest report
        """
        logger.info(
            f"Starting backtest analysis: {len(symbols)} symbols, "
            f"{start_date} to {end_date}"
        )

        reports = []

        for symbol in symbols:
            logger.info(f"\nAnalyzing {symbol}...")

            try:
                report = self._analyze_single_symbol(
                    strategy, symbol, start_date, end_date
                )
                reports.append(report)
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
                reports.append({
                    'symbol': symbol,
                    'error': str(e),
                    'status': 'failed'
                })

        # Aggregate results
        summary = self._create_summary(reports)

        return {
            'summary': summary,
            'symbol_reports': reports,
            'overall_status': self._determine_overall_status(summary)
        }

    def _analyze_single_symbol(
        self,
        strategy: Any,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Analyze single symbol"""

        # 1. Fetch data
        logger.info(f"  Fetching data for {symbol}...")
        data = self.data_fetcher.fetch_multi_timeframe_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframes=['daily', 'weekly']
        )

        if not data or data.get('daily', pd.DataFrame()).empty:
            raise ValueError(f"No data available for {symbol}")

        # 2. Run full backtest
        logger.info(f"  Running full backtest...")
        full_result = self.backtest_executor.run_backtest(
            strategy=strategy,
            symbol=symbol,
            data=data,
            start_date=pd.to_datetime(start_date),
            end_date=pd.to_datetime(end_date)
        )

        # 3. Calculate metrics
        logger.info(f"  Calculating metrics...")
        perf_metrics = self.metrics_calculator.calculate(full_result)
        risk_metrics = self.risk_calculator.calculate(full_result)

        # 4. Run walk-forward analysis
        logger.info(f"  Running walk-forward analysis...")
        wf_analysis = self.walk_forward.execute(strategy, symbol, data)

        # 5. Validate minimum requirements
        issues = self._validate_requirements(full_result, perf_metrics, wf_analysis)

        # 6. Determine status
        if len(issues) == 0:
            status = 'PASS'
            rating = '🟢'
        elif any('CRITICAL' in issue for issue in issues):
            status = 'FAIL'
            rating = '🔴'
        else:
            status = 'WARNING'
            rating = '🟡'

        return {
            'symbol': symbol,
            'status': status,
            'rating': rating,
            'backtest_result': full_result,
            'performance_metrics': perf_metrics,
            'risk_metrics': risk_metrics,
            'walk_forward_analysis': wf_analysis,
            'issues': issues
        }

    def _validate_requirements(
        self,
        backtest_result: Any,
        metrics: Any,
        walk_forward: Any
    ) -> List[str]:
        """Validate minimum requirements for reliable backtest"""

        issues = []

        # 1. Minimum trades
        if metrics.total_trades < 30:
            issues.append(
                f"CRITICAL: Insufficient trades ({metrics.total_trades} < 30). "
                "Need more trades for statistical significance."
            )

        # 2. Minimum time period
        if not metrics.time_period_adequate:
            issues.append(
                "WARNING: Test period less than 2 years. "
                "Results may not be representative."
            )

        # 3. Statistical significance
        if not metrics.is_statistically_significant:
            issues.append(
                "WARNING: Results not statistically significant. "
                "Consider more trades or longer period."
            )

        # 4. Walk-forward consistency
        if walk_forward and not walk_forward.is_robust:
            if walk_forward.avg_return_degradation_pct > 50:
                issues.append(
                    f"CRITICAL: Severe walk-forward degradation "
                    f"({walk_forward.avg_return_degradation_pct:.1f}%). "
                    "Strategy likely overfit."
                )
            else:
                issues.append(
                    f"WARNING: Walk-forward shows degradation "
                    f"({walk_forward.avg_return_degradation_pct:.1f}%). "
                    "Monitor out-of-sample performance."
                )

        return issues

    def _create_summary(self, reports: List[Dict]) -> Dict[str, Any]:
        """Create summary across all symbols"""

        valid_reports = [r for r in reports if r.get('status') != 'failed']

        if not valid_reports:
            return {
                'total_symbols': len(reports),
                'failed': len(reports),
                'avg_sharpe': 0,
                'avg_return': 0,
                'avg_max_dd': 0
            }

        return {
            'total_symbols': len(reports),
            'passed': sum(1 for r in valid_reports if r['status'] == 'PASS'),
            'warnings': sum(1 for r in valid_reports if r['status'] == 'WARNING'),
            'failed': sum(1 for r in reports if r.get('status') == 'failed'),
            'avg_sharpe': sum(
                r['performance_metrics'].sharpe_ratio for r in valid_reports
            ) / len(valid_reports),
            'avg_return': sum(
                r['performance_metrics'].total_return_pct for r in valid_reports
            ) / len(valid_reports),
            'avg_max_dd': sum(
                r['risk_metrics'].max_drawdown_pct for r in valid_reports
            ) / len(valid_reports),
            'total_trades': sum(
                r['performance_metrics'].total_trades for r in valid_reports
            )
        }

    def _determine_overall_status(self, summary: Dict) -> str:
        """Determine overall status"""

        if summary['failed'] > 0:
            return 'FAIL'
        elif summary['passed'] >= summary['total_symbols'] * 0.7:
            return 'PASS'
        else:
            return 'WARNING'


# Test function
if __name__ == '__main__':
    print("Testing BacktestingSpecialistAgent...")

    # Simple test strategy
    class SimpleStrategy:
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

    # Run analysis
    agent = BacktestingSpecialistAgent()
    strategy = SimpleStrategy()

    results = agent.analyze(
        strategy=strategy,
        symbols=['TATAMOTORS.NS'],
        start_date='2023-01-01',
        end_date='2024-11-01'
    )

    # Print results
    print(f"\n=== Backtest Analysis Results ===")
    print(f"Overall Status: {results['overall_status']}")

    print(f"\n=== Summary ===")
    for key, value in results['summary'].items():
        print(f"  {key}: {value}")

    print(f"\n=== Symbol Reports ===")
    for report in results['symbol_reports']:
        print(f"\n{report['symbol']}: {report.get('rating', '?')} {report['status']}")

        if report.get('performance_metrics'):
            pm = report['performance_metrics']
            print(f"  Trades: {pm.total_trades}")
            print(f"  Sharpe: {pm.sharpe_ratio:.2f}")
            print(f"  Return: {pm.total_return_pct:.1f}%")
            print(f"  Win Rate: {pm.win_rate_pct:.1f}%")

        if report.get('issues'):
            print(f"  Issues:")
            for issue in report['issues']:
                print(f"    - {issue}")
