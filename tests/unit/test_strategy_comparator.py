"""Tests for Strategy Comparison Framework (Epic 6 - Story 6.5)"""
import pytest
import pandas as pd
import numpy as np
from agents.ml.backtesting.strategy_comparator import StrategyComparator, Strategy, StrategyPerformance

class TestStrategyComparator:
    @pytest.fixture
    def comparator(self):
        return StrategyComparator({}, "")

    @pytest.fixture
    def sample_strategies(self):
        return [
            Strategy("XGBoost-25", "XGBoost", [], {}),
            Strategy("LightGBM-25", "LightGBM", [], {}),
            Strategy("Baseline", "LogisticRegression", [], {})
        ]

    def test_initialization(self, comparator):
        assert comparator is not None

    def test_compare_strategies(self, comparator, sample_strategies):
        results = comparator.compare_strategies(sample_strategies, '2023-01-01', '2023-12-31')
        assert len(results) == 3

    def test_strategy_performance_structure(self, comparator, sample_strategies):
        results = comparator.compare_strategies(sample_strategies, '2023-01-01', '2023-12-31')
        for perf in results.values():
            assert isinstance(perf, StrategyPerformance)
            assert hasattr(perf, 'f1')
            assert hasattr(perf, 'sharpe')

    def test_composite_score_calculation(self, comparator):
        score = comparator.calculate_composite_score(0.72, 1.68, -0.162)
        assert 0 <= score <= 1

    def test_rank_strategies(self, comparator):
        performances = {
            'A': StrategyPerformance(Strategy("A", "XGB", [], {}), 0.72, 1.5, -0.15, 120, 0.8, 0),
            'B': StrategyPerformance(Strategy("B", "LGB", [], {}), 0.70, 1.4, -0.18, 100, 0.75, 0)
        }
        ranked = comparator.rank_strategies(performances)
        assert ranked[0].rank == 1
        assert ranked[1].rank == 2

    def test_statistical_significance(self, comparator):
        np.random.seed(42)
        preds1 = pd.Series(np.random.binomial(1, 0.7, 100))
        preds2 = pd.Series(np.random.binomial(1, 0.7, 100))
        actuals = pd.Series(np.random.binomial(1, 0.5, 100))
        p_value = comparator.test_statistical_significance(preds1, preds2, actuals)
        assert 0 <= p_value <= 1

    def test_compare_feature_sets(self, comparator):
        feature_sets = {
            'Technical': ['rsi_14', 'macd'],
            'Financial': ['revenue_growth', 'npm']
        }
        df = comparator.compare_feature_sets(feature_sets)
        assert len(df) == 2
        assert 'F1' in df.columns

    def test_generate_comparison_report(self, comparator, sample_strategies):
        results = comparator.compare_strategies(sample_strategies, '2023-01-01', '2023-12-31')
        report = comparator.generate_comparison_report(results, "/tmp/report.html")
        assert 'STRATEGY COMPARISON' in report

    def test_best_strategy_identification(self, comparator, sample_strategies):
        results = comparator.compare_strategies(sample_strategies, '2023-01-01', '2023-12-31')
        ranked = sorted(results.values(), key=lambda x: x.rank)
        assert ranked[0].rank == 1

    def test_composite_score_weights(self, comparator):
        score1 = comparator.calculate_composite_score(0.8, 2.0, -0.1)
        score2 = comparator.calculate_composite_score(0.6, 2.0, -0.1)
        assert score1 > score2

    def test_empty_strategies(self, comparator):
        results = comparator.compare_strategies([], '2023-01-01', '2023-12-31')
        assert len(results) == 0

    def test_single_strategy(self, comparator):
        strategies = [Strategy("XGBoost", "XGBoost", [], {})]
        results = comparator.compare_strategies(strategies, '2023-01-01', '2023-12-31')
        assert len(results) == 1

    def test_performance_metrics_range(self, comparator, sample_strategies):
        results = comparator.compare_strategies(sample_strategies, '2023-01-01', '2023-12-31')
        for perf in results.values():
            assert 0 <= perf.f1 <= 1
            assert perf.sharpe > 0
            assert perf.max_drawdown <= 0

    def test_training_time_tracking(self, comparator, sample_strategies):
        results = comparator.compare_strategies(sample_strategies, '2023-01-01', '2023-12-31')
        for perf in results.values():
            assert perf.training_time_seconds > 0

    def test_strategy_dataclass(self):
        strategy = Strategy("Test", "XGBoost", ['f1', 'f2'], {'lr': 0.1})
        assert strategy.name == "Test"
        assert len(strategy.features) == 2

    def test_performance_dataclass(self):
        strategy = Strategy("Test", "XGBoost", [], {})
        perf = StrategyPerformance(strategy, 0.72, 1.5, -0.15, 120, 0.8, 1)
        assert perf.f1 == 0.72
        assert perf.rank == 1

    def test_report_includes_winner(self, comparator, sample_strategies):
        results = comparator.compare_strategies(sample_strategies, '2023-01-01', '2023-12-31')
        report = comparator.generate_comparison_report(results, "/tmp/report.html")
        assert 'OVERALL WINNER' in report
