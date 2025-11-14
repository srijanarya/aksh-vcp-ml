"""Tests for Risk Metrics Calculation (Epic 6 - Story 6.3)"""
import pytest
import pandas as pd
import numpy as np
from agents.ml.backtesting.risk_calculator import RiskCalculator, RiskMetrics

class TestRiskCalculator:
    @pytest.fixture
    def calculator(self):
        return RiskCalculator(risk_free_rate=0.07)

    @pytest.fixture
    def sample_returns(self):
        np.random.seed(42)
        return pd.Series(np.random.normal(0.001, 0.02, 252))

    def test_initialization(self, calculator):
        assert calculator.risk_free_rate == 0.07

    def test_sharpe_ratio_calculation(self, calculator, sample_returns):
        sharpe = calculator.calculate_sharpe_ratio(sample_returns)
        assert isinstance(sharpe, float)

    def test_sortino_ratio_calculation(self, calculator, sample_returns):
        sortino = calculator.calculate_sortino_ratio(sample_returns)
        assert isinstance(sortino, float)

    def test_max_drawdown_calculation(self, calculator):
        cumulative = pd.Series([1.0, 1.1, 1.05, 0.95, 1.0, 1.15])
        mdd = calculator.calculate_max_drawdown(cumulative)
        assert mdd < 0

    def test_simulate_trading_strategy(self, calculator):
        predictions = pd.DataFrame({'bse_code': ['500325'], 'probability': [0.8]})
        result = calculator.simulate_trading_strategy(predictions)
        assert isinstance(result, pd.DataFrame)

    def test_calculate_all_metrics(self, calculator, sample_returns):
        metrics = calculator.calculate_all_metrics(sample_returns)
        assert isinstance(metrics, RiskMetrics)

    def test_risk_metrics_structure(self, calculator, sample_returns):
        metrics = calculator.calculate_all_metrics(sample_returns)
        assert hasattr(metrics, 'sharpe_ratio')
        assert hasattr(metrics, 'max_drawdown')

    def test_win_rate_calculation(self, calculator):
        returns = pd.Series([0.01, -0.01, 0.02, 0.01, -0.005])
        metrics = calculator.calculate_all_metrics(returns)
        assert 0 <= metrics.win_rate <= 1

    def test_profit_factor(self, calculator):
        returns = pd.Series([0.01, -0.01, 0.02, 0.01, -0.005])
        metrics = calculator.calculate_all_metrics(returns)
        assert metrics.profit_factor >= 0

    def test_max_consecutive_losses(self, calculator):
        returns = pd.Series([0.01, -0.01, -0.01, -0.01, 0.02])
        metrics = calculator.calculate_all_metrics(returns)
        assert metrics.max_consecutive_losses == 3

    def test_generate_risk_report(self, calculator, sample_returns):
        metrics = calculator.calculate_all_metrics(sample_returns)
        report = calculator.generate_risk_report(metrics, '2022-01-01', '2024-12-31')
        assert 'RISK METRICS' in report

    def test_volatility_calculation(self, calculator, sample_returns):
        metrics = calculator.calculate_all_metrics(sample_returns)
        assert metrics.volatility >= 0

    def test_total_return(self, calculator):
        returns = pd.Series([0.01, 0.02, -0.01, 0.03])
        metrics = calculator.calculate_all_metrics(returns)
        assert isinstance(metrics.total_return, float)

    def test_annualized_return(self, calculator, sample_returns):
        metrics = calculator.calculate_all_metrics(sample_returns)
        assert isinstance(metrics.annualized_return, float)

    def test_avg_win_loss(self, calculator):
        returns = pd.Series([0.02, -0.01, 0.03, -0.02])
        metrics = calculator.calculate_all_metrics(returns)
        assert metrics.avg_win > 0
        assert metrics.avg_loss < 0

    def test_empty_returns(self, calculator):
        returns = pd.Series([])
        metrics = calculator.calculate_all_metrics(returns)
        assert metrics.total_return == 0

    def test_all_positive_returns(self, calculator):
        returns = pd.Series([0.01, 0.02, 0.01, 0.03])
        metrics = calculator.calculate_all_metrics(returns)
        assert metrics.max_drawdown == 0

    def test_all_negative_returns(self, calculator):
        returns = pd.Series([-0.01, -0.02, -0.01, -0.03])
        metrics = calculator.calculate_all_metrics(returns)
        assert metrics.win_rate == 0

    def test_sharpe_with_custom_rf_rate(self, calculator, sample_returns):
        sharpe = calculator.calculate_sharpe_ratio(sample_returns, risk_free_rate=0.05)
        assert isinstance(sharpe, float)

    def test_sortino_with_custom_rf_rate(self, calculator, sample_returns):
        sortino = calculator.calculate_sortino_ratio(sample_returns, risk_free_rate=0.05)
        assert isinstance(sortino, float)

    def test_report_formatting(self, calculator, sample_returns):
        metrics = calculator.calculate_all_metrics(sample_returns)
        report = calculator.generate_risk_report(metrics, '2022-01-01', '2024-12-31')
        assert 'Sharpe Ratio' in report
        assert 'Win Rate' in report

    def test_metrics_dataclass(self):
        metrics = RiskMetrics(0.15, 0.12, 1.5, 2.0, -0.18, 0.20, 0.65, 2.1, 0.02, -0.01, 5)
        assert metrics.sharpe_ratio == 1.5
        assert metrics.win_rate == 0.65
