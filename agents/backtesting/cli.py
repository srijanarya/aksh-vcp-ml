#!/usr/bin/env python3
"""
Strategy Consultant CLI

Command-line interface for running comprehensive strategy analysis.

Usage:
    python cli.py analyze --strategy <file> --start-date <date> --end-date <date> --symbols <symbols>
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
import logging
from datetime import datetime
import importlib.util

from agents.backtesting.strategy_consultant import StrategyConsultantAgent
from agents.backtesting.reports.report_generator import ReportGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_strategy_from_file(strategy_path: str):
    """
    Load strategy class from Python file

    Args:
        strategy_path: Path to strategy .py file

    Returns:
        Strategy instance
    """
    logger.info(f"Loading strategy from {strategy_path}")

    # Load module
    spec = importlib.util.spec_from_file_location("user_strategy", strategy_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load strategy from {strategy_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find strategy class (convention: ends with "Strategy")
    strategy_class = None
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and name.endswith("Strategy"):
            strategy_class = obj
            break

    if strategy_class is None:
        raise ImportError(f"No strategy class found in {strategy_path}")

    # Instantiate
    strategy = strategy_class()
    logger.info(f"Loaded strategy: {strategy_class.__name__}")

    return strategy


def analyze_command(args):
    """Execute strategy analysis"""

    print("\n" + "="*70)
    print("STRATEGY CONSULTANT - Comprehensive Analysis")
    print("="*70)

    # Load strategy
    try:
        strategy = load_strategy_from_file(args.strategy)
    except Exception as e:
        logger.error(f"Failed to load strategy: {e}")
        sys.exit(1)

    # Parse symbols
    symbols = [s.strip() for s in args.symbols.split(',')]

    # Create consultant
    consultant = StrategyConsultantAgent()

    # Run analysis
    print(f"\nAnalyzing strategy: {strategy.__class__.__name__}")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Period: {args.start_date} to {args.end_date}")
    print("\nThis may take several minutes...\n")

    try:
        report = consultant.analyze_strategy(
            strategy=strategy,
            symbols=symbols,
            start_date=args.start_date,
            end_date=args.end_date
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)

    # Generate report
    report_gen = ReportGenerator()

    # Print executive summary to console
    print("\n" + "="*70)
    summary_text = report_gen.generate_executive_summary(report)
    print(summary_text)
    print("="*70 + "\n")

    # Save reports if output specified
    if args.output:
        output_base = Path(args.output).stem
        output_dir = Path(args.output).parent

        # Executive summary
        summary_path = output_dir / f"{output_base}_summary.md"
        report_gen.save_report(report, str(summary_path), detailed=False)
        print(f"📄 Executive summary saved: {summary_path}")

        # Detailed report
        if args.detailed:
            detailed_path = output_dir / f"{output_base}_detailed.md"
            report_gen.save_report(report, str(detailed_path), detailed=True)
            print(f"📄 Detailed report saved: {detailed_path}")

    # Print final decision
    summary = report['executive_summary']
    print("\n" + "="*70)
    print(f"FINAL DECISION: {summary.decision}")
    print(f"CONFIDENCE: {summary.confidence_score:.0f}%")
    print("="*70 + "\n")

    if summary.decision == "GO":
        print("✅ Strategy approved for live trading")
        return 0
    elif summary.decision == "PROCEED WITH CAUTION":
        print("⚠️  Strategy needs improvements before live deployment")
        return 1
    else:
        print("❌ Strategy NOT recommended for live trading")
        return 2


def main():
    """Main CLI entry point"""

    parser = argparse.ArgumentParser(
        description='Strategy Consultant - Comprehensive backtesting and analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze strategy on single symbol
  python cli.py analyze --strategy strategies/my_strategy.py \\
      --start-date 2023-01-01 --end-date 2024-11-01 \\
      --symbols TATAMOTORS.NS

  # Multiple symbols with detailed report
  python cli.py analyze --strategy strategies/my_strategy.py \\
      --start-date 2023-01-01 --end-date 2024-11-01 \\
      --symbols "TATAMOTORS.NS,RELIANCE.NS,TCS.NS" \\
      --output reports/analysis --detailed

  # Custom output location
  python cli.py analyze --strategy strategies/my_strategy.py \\
      --start-date 2022-01-01 --end-date 2024-11-01 \\
      --symbols TATAMOTORS.NS \\
      --output /tmp/backtest_report
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze trading strategy')
    analyze_parser.add_argument(
        '--strategy',
        required=True,
        help='Path to strategy Python file'
    )
    analyze_parser.add_argument(
        '--start-date',
        required=True,
        help='Backtest start date (YYYY-MM-DD)'
    )
    analyze_parser.add_argument(
        '--end-date',
        required=True,
        help='Backtest end date (YYYY-MM-DD)'
    )
    analyze_parser.add_argument(
        '--symbols',
        required=True,
        help='Comma-separated list of symbols (e.g., "TATAMOTORS.NS,RELIANCE.NS")'
    )
    analyze_parser.add_argument(
        '--output',
        default=None,
        help='Output file path (without extension)'
    )
    analyze_parser.add_argument(
        '--detailed',
        action='store_true',
        help='Generate detailed report in addition to executive summary'
    )

    args = parser.parse_args()

    if args.command == 'analyze':
        return analyze_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
