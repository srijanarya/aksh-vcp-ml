"""Risk Metrics Calculation (Epic 6 - Story 6.3)"""
import numpy as np
import pandas as pd
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    volatility: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    max_consecutive_losses: int

class RiskCalculator:
    def __init__(self, risk_free_rate: float = 0.07):
        self.risk_free_rate = risk_free_rate

    def simulate_trading_strategy(self, predictions: pd.DataFrame, min_probability: float = 0.7) -> pd.DataFrame:
        """Simulate trading based on predictions"""
        # Mock simulation
        dates = pd.date_range('2022-01-01', '2024-12-31', freq='D')
        returns = np.random.normal(0.001, 0.02, len(dates))
        cumulative = (1 + pd.Series(returns)).cumprod()

        return pd.DataFrame({
            'date': dates,
            'daily_return': returns,
            'cumulative_return': cumulative
        })

    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = None) -> float:
        """Calculate annualized Sharpe ratio"""
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate

        excess_returns = returns - (risk_free_rate / 252)
        if excess_returns.std() == 0:
            return 0.0
        return float((excess_returns.mean() / excess_returns.std()) * np.sqrt(252))

    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = None) -> float:
        """Calculate annualized Sortino ratio"""
        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate

        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0

        return float((excess_returns.mean() / downside_returns.std()) * np.sqrt(252))

    def calculate_max_drawdown(self, cumulative_returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns - peak) / peak
        return float(drawdown.min())

    def calculate_all_metrics(self, returns: pd.Series) -> RiskMetrics:
        """Calculate all risk metrics"""
        cumulative = (1 + returns).cumprod()

        wins = returns[returns > 0]
        losses = returns[returns < 0]

        # Calculate consecutive losses
        consecutive_losses = 0
        max_consecutive_losses = 0
        for r in returns:
            if r < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0

        return RiskMetrics(
            total_return=float(cumulative.iloc[-1] - 1) if len(cumulative) > 0 else 0.0,
            annualized_return=float(((cumulative.iloc[-1]) ** (252/len(returns)) - 1)) if len(returns) > 0 else 0.0,
            sharpe_ratio=self.calculate_sharpe_ratio(returns),
            sortino_ratio=self.calculate_sortino_ratio(returns),
            max_drawdown=self.calculate_max_drawdown(cumulative),
            volatility=float(returns.std() * np.sqrt(252)),
            win_rate=float(len(wins) / len(returns)) if len(returns) > 0 else 0.0,
            profit_factor=float(wins.sum() / abs(losses.sum())) if len(losses) > 0 and losses.sum() != 0 else 0.0,
            avg_win=float(wins.mean()) if len(wins) > 0 else 0.0,
            avg_loss=float(losses.mean()) if len(losses) > 0 else 0.0,
            max_consecutive_losses=max_consecutive_losses
        )

    def generate_risk_report(self, metrics: RiskMetrics, start_date: str, end_date: str) -> str:
        """Generate risk report"""
        report = f"""
========================================
RISK METRICS REPORT
========================================
Period: {start_date} to {end_date}

RETURN METRICS:
- Total Return: {metrics.total_return*100:.1f}%
- Annualized Return: {metrics.annualized_return*100:.1f}%

RISK METRICS:
- Sharpe Ratio: {metrics.sharpe_ratio:.2f}
- Sortino Ratio: {metrics.sortino_ratio:.2f}
- Maximum Drawdown: {metrics.max_drawdown*100:.1f}%
- Volatility: {metrics.volatility*100:.1f}%

TRADING STATISTICS:
- Win Rate: {metrics.win_rate*100:.1f}%
- Profit Factor: {metrics.profit_factor:.2f}
- Average Win: {metrics.avg_win*100:.2f}%
- Average Loss: {metrics.avg_loss*100:.2f}%
- Max Consecutive Losses: {metrics.max_consecutive_losses}
========================================
"""
        return report
