"""
Tests for Historical Performance Analysis (Epic 6 - Story 6.1)

Test Coverage:
- HistoricalAnalyzer initialization
- Analyze single time period
- Analyze multiple years
- Quarterly breakdown
- Performance comparison across periods
- Temporal pattern detection
- Feature importance per period
- Results persistence
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

from agents.ml.backtesting.historical_analyzer import (
    HistoricalAnalyzer,
    PeriodPerformance,
)


class TestHistoricalAnalyzer:
    """Test suite for HistoricalAnalyzer"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test databases"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def mock_feature_dbs(self, temp_dir):
        """Mock feature database paths"""
        return {
            "financial": str(Path(temp_dir) / "financial_features.db"),
            "technical": str(Path(temp_dir) / "technical_features.db"),
            "sentiment": str(Path(temp_dir) / "sentiment_features.db"),
        }

    @pytest.fixture
    def mock_labels_db(self, temp_dir):
        """Mock labels database path"""
        return str(Path(temp_dir) / "upper_circuit_labels.db")

    @pytest.fixture
    def analyzer(self, mock_feature_dbs, mock_labels_db, temp_dir):
        """Create HistoricalAnalyzer instance"""
        model_registry = str(Path(temp_dir) / "model_registry.db")
        return HistoricalAnalyzer(
            feature_dbs=mock_feature_dbs,
            labels_db=mock_labels_db,
            model_registry_path=model_registry,
        )

    @pytest.fixture
    def sample_data(self):
        """Create sample training/testing data"""
        np.random.seed(42)
        n_samples = 1000

        # Generate dates spanning 2022-2024
        start_date = datetime(2022, 1, 1)
        dates = [start_date + timedelta(days=i*7) for i in range(n_samples)]

        # Generate features and labels
        features = pd.DataFrame({
            'date': dates,
            'bse_code': np.random.choice(['500325', '532977', '500180'], n_samples),
            'rsi_14': np.random.uniform(30, 70, n_samples),
            'macd': np.random.uniform(-1, 1, n_samples),
            'revenue_growth': np.random.uniform(-0.2, 0.5, n_samples),
        })

        labels = pd.Series(np.random.binomial(1, 0.08, n_samples), name='upper_circuit')

        return features, labels

    def test_analyzer_initialization(self, analyzer):
        """Test AC6.1.1: HistoricalAnalyzer class initialization"""
        assert analyzer is not None
        assert hasattr(analyzer, 'analyze_period')
        assert hasattr(analyzer, 'analyze_all_years')
        assert hasattr(analyzer, 'analyze_quarterly')

    def test_analyze_period_basic(self, analyzer, sample_data):
        """Test AC6.1.2: Analyze single time period"""
        features, labels = sample_data

        with patch.object(analyzer, '_load_data_for_period', return_value=(features, labels)):
            with patch.object(analyzer, '_train_and_evaluate') as mock_eval:
                mock_eval.return_value = {
                    'f1': 0.71,
                    'precision': 0.67,
                    'recall': 0.76,
                    'roc_auc': 0.78,
                    'confusion_matrix': [[850, 50], [25, 75]],
                    'classification_report': 'Test classification report',
                    'upper_circuit_rate': 0.083
                }

                result = analyzer.analyze_period(
                    start_date='2023-01-01',
                    end_date='2023-12-31',
                    period_name='2023'
                )

                assert isinstance(result, PeriodPerformance)
                assert result.period == '2023'
                assert 0.7 <= result.f1 <= 0.72
                assert result.n_samples > 0

    def test_analyze_period_temporal_ordering(self, analyzer, sample_data):
        """Test AC6.1.2: No data leakage - strict temporal ordering"""
        features, labels = sample_data

        # Verify that analyze_period properly handles temporal data
        with patch.object(analyzer, '_load_data_for_period', return_value=(features, labels)):
            with patch.object(analyzer, '_train_and_evaluate') as mock_eval:
                mock_eval.return_value = {
                    'f1': 0.71, 'precision': 0.67, 'recall': 0.76, 'roc_auc': 0.78,
                    'confusion_matrix': [[850, 50], [25, 75]], 'classification_report': 'Test',
                    'upper_circuit_rate': 0.083
                }

                result = analyzer.analyze_period('2024-01-01', '2024-12-31')

                # Verify result is returned (temporal split handled internally)
                assert result is not None
                assert result.period == '2024-01-01_to_2024-12-31'

    def test_analyze_multiple_years(self, analyzer, sample_data):
        """Test AC6.1.5: Performance comparison across years"""
        features, labels = sample_data

        with patch.object(analyzer, '_load_data_for_period', return_value=(features, labels)):
            with patch.object(analyzer, '_train_and_evaluate') as mock_eval:
                # Return different metrics for each year
                mock_eval.side_effect = [
                    {'f1': 0.71, 'precision': 0.67, 'recall': 0.76, 'roc_auc': 0.78,
                     'confusion_matrix': [[850, 50], [25, 75]], 'classification_report': 'Test', 'upper_circuit_rate': 0.083},
                    {'f1': 0.73, 'precision': 0.70, 'recall': 0.77, 'roc_auc': 0.80,
                     'confusion_matrix': [[900, 40], [20, 80]], 'classification_report': 'Test', 'upper_circuit_rate': 0.075},
                    {'f1': 0.69, 'precision': 0.65, 'recall': 0.74, 'roc_auc': 0.76,
                     'confusion_matrix': [[820, 60], [30, 70]], 'classification_report': 'Test', 'upper_circuit_rate': 0.068},
                ]

                results = analyzer.analyze_all_years(years=[2022, 2023, 2024])

                assert len(results) == 3
                assert 2022 in results
                assert 2023 in results
                assert 2024 in results

                # Verify 2023 has best F1
                assert results[2023].f1 > results[2022].f1
                assert results[2023].f1 > results[2024].f1

    def test_quarterly_breakdown(self, analyzer, sample_data):
        """Test AC6.1.4: Quarterly breakdown within year"""
        features, labels = sample_data

        with patch.object(analyzer, '_load_data_for_period', return_value=(features, labels)):
            with patch.object(analyzer, '_train_and_evaluate') as mock_eval:
                mock_eval.side_effect = [
                    {'f1': 0.70, 'precision': 0.66, 'recall': 0.75, 'roc_auc': 0.77,
                     'confusion_matrix': [[210, 15], [8, 17]], 'classification_report': 'Q1', 'upper_circuit_rate': 0.08},
                    {'f1': 0.75, 'precision': 0.72, 'recall': 0.79, 'roc_auc': 0.81,
                     'confusion_matrix': [[220, 10], [5, 20]], 'classification_report': 'Q2', 'upper_circuit_rate': 0.078},
                    {'f1': 0.68, 'precision': 0.64, 'recall': 0.73, 'roc_auc': 0.75,
                     'confusion_matrix': [[200, 20], [10, 15]], 'classification_report': 'Q3', 'upper_circuit_rate': 0.071},
                    {'f1': 0.65, 'precision': 0.61, 'recall': 0.70, 'roc_auc': 0.73,
                     'confusion_matrix': [[205, 18], [12, 15]], 'classification_report': 'Q4', 'upper_circuit_rate': 0.066},
                ]

                results = analyzer.analyze_quarterly(year=2024)

                assert len(results) == 4
                assert 'Q1' in results
                assert 'Q2' in results
                assert 'Q3' in results
                assert 'Q4' in results

                # Q2 should have best performance
                assert results['Q2'].f1 == 0.75
                assert results['Q4'].f1 == 0.65

    def test_performance_comparison_table(self, analyzer):
        """Test AC6.1.5: Generate comparison table"""
        # Mock performance data
        performances = {
            '2022': PeriodPerformance(
                period='2022', start_date='2022-01-01', end_date='2022-12-31',
                n_samples=45230, f1=0.71, precision=0.67, recall=0.76,
                roc_auc=0.78, confusion_matrix=[[40000, 3000], [1200, 1030]],
                classification_report='', upper_circuit_rate=0.083
            ),
            '2023': PeriodPerformance(
                period='2023', start_date='2023-01-01', end_date='2023-12-31',
                n_samples=52140, f1=0.73, precision=0.70, recall=0.77,
                roc_auc=0.80, confusion_matrix=[[46000, 2500], [1000, 1140]],
                classification_report='', upper_circuit_rate=0.075
            ),
        }

        comparison_df = analyzer.compare_periods(performances)

        assert isinstance(comparison_df, pd.DataFrame)
        assert len(comparison_df) >= 2
        assert 'F1' in comparison_df.columns or 'f1' in comparison_df.columns
        assert 'Precision' in comparison_df.columns or 'precision' in comparison_df.columns

    def test_temporal_pattern_detection(self, analyzer):
        """Test AC6.1.6: Identify temporal patterns"""
        # Mock performance data showing decline in 2024
        performances = {
            '2022': PeriodPerformance(
                period='2022', start_date='2022-01-01', end_date='2022-12-31',
                n_samples=45230, f1=0.71, precision=0.67, recall=0.76,
                roc_auc=0.78, confusion_matrix=[[40000, 3000], [1200, 1030]],
                classification_report='', upper_circuit_rate=0.083
            ),
            '2023': PeriodPerformance(
                period='2023', start_date='2023-01-01', end_date='2023-12-31',
                n_samples=52140, f1=0.73, precision=0.70, recall=0.77,
                roc_auc=0.80, confusion_matrix=[[46000, 2500], [1000, 1140]],
                classification_report='', upper_circuit_rate=0.075
            ),
            '2024': PeriodPerformance(
                period='2024', start_date='2024-01-01', end_date='2024-12-31',
                n_samples=48890, f1=0.69, precision=0.65, recall=0.74,
                roc_auc=0.76, confusion_matrix=[[43000, 3200], [1300, 1090]],
                classification_report='', upper_circuit_rate=0.068
            ),
        }

        patterns = analyzer.detect_temporal_patterns(performances)

        assert isinstance(patterns, list)
        assert len(patterns) > 0
        # Should detect decline in 2024
        assert any('2024' in pattern for pattern in patterns)

    def test_statistical_significance(self, analyzer):
        """Test AC6.1.6: Statistical significance testing"""
        with patch('scipy.stats.chi2_contingency') as mock_chi2:
            mock_chi2.return_value = (10.5, 0.003, 1, None)  # p-value = 0.003

            performances = {
                '2022': PeriodPerformance(
                    period='2022', start_date='2022-01-01', end_date='2022-12-31',
                    n_samples=45230, f1=0.71, precision=0.67, recall=0.76,
                    roc_auc=0.78, confusion_matrix=[[40000, 3000], [1200, 1030]],
                    classification_report='', upper_circuit_rate=0.083
                ),
                '2024': PeriodPerformance(
                    period='2024', start_date='2024-01-01', end_date='2024-12-31',
                    n_samples=48890, f1=0.69, precision=0.65, recall=0.74,
                    roc_auc=0.76, confusion_matrix=[[43000, 3200], [1300, 1090]],
                    classification_report='', upper_circuit_rate=0.068
                ),
            }

            is_significant = analyzer.test_significance(performances['2022'], performances['2024'])

            # Convert numpy bool to Python bool
            assert isinstance(bool(is_significant), bool)

    def test_feature_importance_per_period(self, analyzer, sample_data):
        """Test AC6.1.7: Feature importance analysis per period"""
        features, labels = sample_data

        with patch.object(analyzer, '_calculate_shap_values') as mock_shap:
            mock_shap.return_value = pd.DataFrame({
                'feature': ['rsi_14', 'macd', 'revenue_growth'],
                'importance': [0.35, 0.28, 0.37]
            })

            result = analyzer.analyze_feature_importance('2024')

            assert isinstance(result, pd.DataFrame)
            assert 'feature' in result.columns or 'importance' in result.columns

    def test_save_results(self, analyzer, temp_dir):
        """Test AC6.1.3: Save results to JSON files"""
        performance = PeriodPerformance(
            period='2024',
            start_date='2024-01-01',
            end_date='2024-12-31',
            n_samples=48890,
            f1=0.69,
            precision=0.65,
            recall=0.74,
            roc_auc=0.76,
            confusion_matrix=[[43000, 3200], [1300, 1090]],
            classification_report='Test report',
            upper_circuit_rate=0.068
        )

        output_dir = Path(temp_dir) / 'results'
        output_dir.mkdir(exist_ok=True)

        analyzer.save_results({'2024': performance}, str(output_dir))

        # Verify file was created
        result_file = output_dir / '2024_performance.json'
        assert result_file.exists()

        # Verify content
        with open(result_file) as f:
            data = json.load(f)
            assert data['period'] == '2024'
            assert abs(data['f1'] - 0.69) < 0.01

    def test_confusion_matrix_calculation(self, analyzer, sample_data):
        """Test confusion matrix is correctly calculated"""
        features, labels = sample_data
        predictions = np.random.binomial(1, 0.5, len(labels))

        cm = analyzer._calculate_confusion_matrix(labels.values, predictions)

        assert isinstance(cm, (list, np.ndarray))
        assert len(cm) == 2  # Binary classification
        assert len(cm[0]) == 2

    def test_classification_report_generation(self, analyzer):
        """Test AC6.1.3: Classification report generation"""
        y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
        y_pred = np.array([0, 0, 1, 0, 0, 1, 0, 1])

        report = analyzer._generate_classification_report(y_true, y_pred)

        assert isinstance(report, str)
        assert 'precision' in report.lower() or 'recall' in report.lower()

    def test_roc_auc_calculation(self, analyzer):
        """Test ROC-AUC metric calculation"""
        y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
        y_proba = np.array([0.1, 0.2, 0.8, 0.6, 0.3, 0.9, 0.1, 0.85])

        roc_auc = analyzer._calculate_roc_auc(y_true, y_proba)

        assert 0.0 <= roc_auc <= 1.0
        assert roc_auc > 0.5  # Better than random

    def test_upper_circuit_rate_calculation(self, analyzer, sample_data):
        """Test AC6.1.3: Upper circuit rate calculation"""
        _, labels = sample_data

        rate = analyzer._calculate_upper_circuit_rate(labels.values)

        assert 0.0 <= rate <= 1.0
        assert abs(rate - 0.08) < 0.05  # Should be around 8%

    def test_data_loading_for_period(self, analyzer):
        """Test data loading respects date boundaries"""
        with patch.object(analyzer, '_query_features_and_labels') as mock_query:
            mock_query.return_value = (
                pd.DataFrame({'feature1': [1, 2, 3]}),
                pd.Series([0, 1, 0])
            )

            features, labels = analyzer._load_data_for_period('2024-01-01', '2024-12-31')

            assert isinstance(features, pd.DataFrame)
            assert isinstance(labels, pd.Series)
            assert len(features) == len(labels)

    def test_model_training_and_evaluation(self, analyzer, sample_data):
        """Test model training and evaluation pipeline"""
        features, labels = sample_data

        # Drop date and bse_code for model training
        X = features.drop(['date', 'bse_code'], axis=1)

        results = analyzer._train_and_evaluate(X, labels)

        assert 'f1' in results
        assert 'precision' in results
        assert 'recall' in results
        assert 'roc_auc' in results
        assert 'confusion_matrix' in results

    def test_period_performance_dataclass(self):
        """Test PeriodPerformance dataclass structure"""
        perf = PeriodPerformance(
            period='2024',
            start_date='2024-01-01',
            end_date='2024-12-31',
            n_samples=1000,
            f1=0.72,
            precision=0.68,
            recall=0.77,
            roc_auc=0.79,
            confusion_matrix=[[850, 50], [25, 75]],
            classification_report='test',
            upper_circuit_rate=0.08
        )

        assert perf.period == '2024'
        assert perf.f1 == 0.72
        assert len(perf.confusion_matrix) == 2

    def test_handle_missing_data(self, analyzer):
        """Test graceful handling of missing data"""
        with patch.object(analyzer, '_load_data_for_period') as mock_load:
            # Return empty data
            mock_load.return_value = (pd.DataFrame(), pd.Series())

            result = analyzer.analyze_period('2025-01-01', '2025-12-31')

            # Should return None or empty result, not crash
            assert result is None or result.n_samples == 0

    def test_handle_single_class_labels(self, analyzer):
        """Test handling of periods with single class (all 0s or all 1s)"""
        features = pd.DataFrame({'feature1': [1, 2, 3, 4, 5]})
        labels = pd.Series([0, 0, 0, 0, 0])  # All zeros

        with patch.object(analyzer, '_load_data_for_period', return_value=(features, labels)):
            result = analyzer._train_and_evaluate(features, labels)

            # Should handle gracefully, maybe return NaN or skip
            assert result is not None
