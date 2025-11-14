"""
Backtesting and Validation Module (Epic 6)

This module provides comprehensive backtesting and validation capabilities:
- Historical performance analysis across time periods
- Walk-forward validation with periodic retraining
- Risk metrics calculation (Sharpe, Sortino, drawdown)
- Interactive report generation
- Strategy comparison framework
"""

from .historical_analyzer import HistoricalAnalyzer, PeriodPerformance

__all__ = [
    'HistoricalAnalyzer',
    'PeriodPerformance',
]
