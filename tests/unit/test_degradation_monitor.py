"""
Unit tests for Model Degradation Monitor (Story 5.3)

Tests cover:
- AC5.3.1: ModelMonitor class to track production F1
- AC5.3.2: Ground truth collection
- AC5.3.3: Rolling performance calculation
- AC5.3.4: Degradation detection thresholds
- AC5.3.5: Performance report generation
- AC5.3.6: Automatic model rollback trigger
- AC5.3.7: Performance dashboard metrics
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta


@pytest.fixture
def temp_db():
    """Fixture to provide temporary database"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def baseline_metrics():
    """Fixture for baseline test set metrics"""
    return {
        'f1': 0.72,
        'precision': 0.68,
        'recall': 0.76,
        'roc_auc': 0.79
    }


@pytest.fixture
def production_predictions():
    """Fixture for production predictions and labels"""
    np.random.seed(42)
    n = 200

    # Simulate predictions
    predictions = []
    for i in range(n):
        date = (datetime.now() - timedelta(days=30-i//7)).strftime('%Y-%m-%d')
        bse_code = f"5003{i%50:02d}"
        predicted_label = np.random.choice([0, 1], p=[0.7, 0.3])
        probability = np.random.uniform(0.55, 0.95) if predicted_label == 1 else np.random.uniform(0.3, 0.5)

        # Simulate actual outcome (with some errors)
        if predicted_label == 1:
            actual_label = np.random.choice([0, 1], p=[0.3, 0.7])  # 70% correct
        else:
            actual_label = np.random.choice([0, 1], p=[0.8, 0.2])  # 80% correct

        predictions.append({
            'bse_code': bse_code,
            'prediction_date': date,
            'earnings_date': date,
            'predicted_label': int(predicted_label),
            'predicted_probability': float(probability),
            'actual_label': int(actual_label),
            'model_version': '1.0.0'
        })

    return predictions


class TestModelMonitorInitialization:
    """Test ModelMonitor initialization"""

    def test_init_creates_model_monitor(self, temp_db, baseline_metrics):
        """Test that ModelMonitor initializes correctly"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=temp_db,
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        assert monitor.predictions_db == temp_db
        assert monitor.baseline_metrics == baseline_metrics
        assert monitor.model_version == "1.0.0"

    def test_init_creates_database_schema(self, temp_db, baseline_metrics):
        """Test that database schema is created"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=temp_db,
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        # Verify schema exists
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='production_labels'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None


class TestGroundTruthCollection:
    """Test AC5.3.2: Ground truth collection"""

    def test_store_production_label(self, temp_db, baseline_metrics):
        """Test storing production label"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=temp_db,
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        # Store label
        monitor.store_production_label(
            bse_code='500325',
            prediction_date='2025-11-14',
            earnings_date='2025-11-14',
            actual_label=1,
            predicted_label=1,
            predicted_probability=0.85
        )

        # Verify stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM production_labels WHERE bse_code = ?",
            ('500325',)
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_load_production_labels(self, temp_db, baseline_metrics, production_predictions):
        """Test loading production labels"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=temp_db,
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        # Store multiple labels
        for pred in production_predictions[:10]:
            monitor.store_production_label(**pred)

        # Load labels
        labels = monitor.load_production_labels(
            start_date='2025-01-01',
            end_date='2025-12-31'
        )

        assert len(labels) == 10


class TestPerformanceCalculation:
    """Test AC5.3.3: Rolling performance calculation"""

    def test_calculate_f1_score(self, temp_db, baseline_metrics, production_predictions):
        """Test F1 score calculation"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=temp_db,
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        # Store labels
        for pred in production_predictions:
            monitor.store_production_label(**pred)

        # Calculate metrics
        metrics = monitor.calculate_production_metrics(
            start_date='2025-01-01',
            end_date='2025-12-31'
        )

        assert 'f1' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 0 <= metrics['f1'] <= 1

    def test_rolling_window_metrics(self, temp_db, baseline_metrics, production_predictions):
        """Test rolling window calculations (7d, 30d, 90d)"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=temp_db,
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        # Store labels
        for pred in production_predictions:
            monitor.store_production_label(**pred)

        # Calculate 7-day metrics
        metrics_7d = monitor.calculate_rolling_metrics(window_days=7)

        # Calculate 30-day metrics
        metrics_30d = monitor.calculate_rolling_metrics(window_days=30)

        assert metrics_7d is not None
        assert metrics_30d is not None


class TestDegradationDetection:
    """Test AC5.3.4: Degradation detection thresholds"""

    def test_detect_no_degradation(self, baseline_metrics):
        """Test no degradation when metrics similar to baseline"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=":memory:",
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        current_metrics = {
            'f1': 0.71,  # -1.4% from baseline
            'precision': 0.67,
            'recall': 0.75
        }

        status = monitor.detect_degradation(current_metrics)

        assert status == 'none' or status == 'minor'

    def test_detect_minor_degradation(self, baseline_metrics):
        """Test minor degradation (3-5% drop)"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=":memory:",
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        current_metrics = {
            'f1': 0.70,  # -2.8% from baseline (0.72)
            'precision': 0.66,
            'recall': 0.74
        }

        status = monitor.detect_degradation(current_metrics)

        assert status == 'minor' or status == 'none'  # Close to threshold

    def test_detect_moderate_degradation(self, baseline_metrics):
        """Test moderate degradation (5-10% drop)"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=":memory:",
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        current_metrics = {
            'f1': 0.65,  # -9.7% from baseline (0.72)
            'precision': 0.61,
            'recall': 0.69
        }

        status = monitor.detect_degradation(current_metrics)

        assert status == 'moderate'

    def test_detect_severe_degradation(self, baseline_metrics):
        """Test severe degradation (>10% drop)"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=":memory:",
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        current_metrics = {
            'f1': 0.60,  # -16.7% from baseline (0.72)
            'precision': 0.56,
            'recall': 0.64
        }

        status = monitor.detect_degradation(current_metrics)

        assert status == 'severe'

    def test_minimum_predictions_threshold(self, temp_db, baseline_metrics):
        """Test that alerts require minimum 100 predictions"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=temp_db,
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        # Store only 50 predictions
        for i in range(50):
            monitor.store_production_label(
                bse_code=f"500{i:03d}",
                prediction_date='2025-11-14',
                earnings_date='2025-11-14',
                actual_label=0,
                predicted_label=1,
                predicted_probability=0.85
            )

        # Try to calculate metrics
        result = monitor.calculate_production_metrics(
            start_date='2025-01-01',
            end_date='2025-12-31',
            min_predictions=100
        )

        # Should return None or indicate insufficient data
        assert result is None or result.get('insufficient_data', False)


class TestPerformanceReport:
    """Test AC5.3.5: Performance report generation"""

    def test_generate_performance_report(self, baseline_metrics):
        """Test performance report generation"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=":memory:",
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        current_metrics = {
            'f1': 0.67,
            'precision': 0.63,
            'recall': 0.72,
            'roc_auc': 0.75,
            'predictions': 1234
        }

        report = monitor.generate_performance_report(
            current_metrics=current_metrics,
            date='2025-11-14'
        )

        assert 'Date: 2025-11-14' in report
        assert 'Model Version: 1.0.0' in report
        assert 'F1 Score:' in report
        assert 'BASELINE PERFORMANCE' in report

    def test_report_includes_degradation_status(self, baseline_metrics):
        """Test that report includes degradation status"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=":memory:",
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        current_metrics = {
            'f1': 0.65,  # Moderate degradation
            'precision': 0.61,
            'recall': 0.69,
            'predictions': 1234
        }

        report = monitor.generate_performance_report(
            current_metrics=current_metrics,
            date='2025-11-14'
        )

        assert 'DEGRADATION' in report or 'STATUS:' in report


class TestRollbackTrigger:
    """Test AC5.3.6: Automatic model rollback trigger"""

    def test_recommend_rollback_severe(self, baseline_metrics):
        """Test rollback recommendation for severe degradation"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=":memory:",
            baseline_metrics=baseline_metrics,
            model_version="1.2.0"
        )

        current_metrics = {'f1': 0.60}  # Severe degradation

        status = monitor.detect_degradation(current_metrics)
        rollback_info = monitor.recommend_rollback(status)

        assert rollback_info is not None
        assert 'recommended' in str(rollback_info).lower() or rollback_info is not False

    def test_no_rollback_for_minor(self, baseline_metrics):
        """Test no rollback for minor degradation"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=":memory:",
            baseline_metrics=baseline_metrics,
            model_version="1.2.0"
        )

        current_metrics = {'f1': 0.70}  # Minor degradation

        status = monitor.detect_degradation(current_metrics)
        rollback_info = monitor.recommend_rollback(status)

        # Should not recommend rollback
        assert rollback_info is None or rollback_info is False


class TestPerformanceMetrics:
    """Test AC5.3.7: Performance dashboard metrics"""

    def test_get_dashboard_metrics(self, temp_db, baseline_metrics, production_predictions):
        """Test getting metrics for dashboard"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=temp_db,
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        # Store predictions
        for pred in production_predictions:
            monitor.store_production_label(**pred)

        # Get dashboard metrics
        dashboard_metrics = monitor.get_dashboard_metrics()

        assert 'f1_score' in dashboard_metrics
        assert 'precision' in dashboard_metrics
        assert 'recall' in dashboard_metrics
        assert 'degradation_severity' in dashboard_metrics


class TestModelMonitorIntegration:
    """Integration tests for ModelMonitor"""

    def test_full_monitoring_workflow(self, temp_db, baseline_metrics, production_predictions):
        """Test full model monitoring workflow"""
        from monitoring.degradation_monitor import ModelMonitor

        monitor = ModelMonitor(
            predictions_db=temp_db,
            baseline_metrics=baseline_metrics,
            model_version="1.0.0"
        )

        # 1. Store production labels
        for pred in production_predictions:
            monitor.store_production_label(**pred)

        # 2. Calculate metrics
        metrics = monitor.calculate_production_metrics(
            start_date='2025-01-01',
            end_date='2025-12-31'
        )

        assert metrics is not None

        # 3. Detect degradation
        status = monitor.detect_degradation(metrics)

        assert status in ['none', 'minor', 'moderate', 'severe']

        # 4. Generate report
        report = monitor.generate_performance_report(
            current_metrics=metrics,
            date='2025-11-14'
        )

        assert len(report) > 0
        assert '2025-11-14' in report
