"""
Backtesting & Strategy Consultant Agent System

A comprehensive multi-agent system for autonomous backtesting and strategy consulting.
"""

from agents.backtesting.strategy_consultant import StrategyConsultantAgent
from agents.backtesting.reports.report_generator import ReportGenerator

__all__ = [
    'StrategyConsultantAgent',
    'ReportGenerator'
]
