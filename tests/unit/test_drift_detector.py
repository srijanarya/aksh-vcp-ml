"""
Unit tests for Data Drift Detector (Story 5.2)

Tests cover:
- AC5.2.1: DriftDetector class with statistical tests
- AC5.2.2: Kolmogorov-Smirnov test for continuous features
- AC5.2.3: Population Stability Index (PSI) for all features
- AC5.2.4: Baseline distribution storage
- AC5.2.5: Daily drift detection job
- AC5.2.6: Drift report generation
- AC5.2.7: Alert thresholds and escalation
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
import os
import sqlite3
from pathlib import Path
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
def baseline_data():
    """Fixture to provide baseline feature distributions"""
    np.random.seed(42)
    return {
        'revenue_growth_yoy': np.random.normal(15, 5, 1000),
        'npm_trend': np.random.normal(10, 3, 1000),
        'rsi_14': np.random.uniform(30, 70, 1000),
        'volume_ratio_30d': np.random.lognormal(0, 0.5, 1000),
        'macd_signal': np.random.normal(0, 1, 1000)
    }


@pytest.fixture
def production_data_no_drift(baseline_data):
    """Fixture for production data with no drift"""
    np.random.seed(43)
    return {
        'revenue_growth_yoy': np.random.normal(15, 5, 500),
        'npm_trend': np.random.normal(10, 3, 500),
        'rsi_14': np.random.uniform(30, 70, 500),
        'volume_ratio_30d': np.random.lognormal(0, 0.5, 500),
        'macd_signal': np.random.normal(0, 1, 500)
    }


@pytest.fixture
def production_data_with_drift(baseline_data):
    """Fixture for production data with significant drift"""
    np.random.seed(44)
    return {
        'revenue_growth_yoy': np.random.normal(15, 5, 500),  # No drift
        'npm_trend': np.random.normal(10, 3, 500),  # No drift
        'rsi_14': np.random.uniform(50, 90, 500),  # DRIFT: shifted distribution
        'volume_ratio_30d': np.random.lognormal(0.5, 0.7, 500),  # DRIFT: different scale
        'macd_signal': np.random.normal(0, 1, 500)  # No drift
    }


class TestDriftDetectorInitialization:
    """Test DriftDetector initialization"""

    def test_init_creates_drift_detector(self, temp_db):
        """Test that DriftDetector initializes correctly"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(
            baseline_db=temp_db,
            model_version="1.0.0"
        )

        assert detector.baseline_db == temp_db
        assert detector.model_version == "1.0.0"

    def test_init_creates_database_schema(self, temp_db):
        """Test that database schema is created"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(
            baseline_db=temp_db,
            model_version="1.0.0"
        )

        # Verify schema exists
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='drift_baselines'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None


class TestKSStatistic:
    """Test AC5.2.2: Kolmogorov-Smirnov test"""

    def test_calculate_ks_statistic_no_drift(self, baseline_data, production_data_no_drift):
        """Test KS statistic for distributions with no drift"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=":memory:", model_version="1.0.0")

        # Test on revenue_growth_yoy (no drift expected)
        ks_stat = detector.calculate_ks_statistic(
            baseline_data['revenue_growth_yoy'],
            production_data_no_drift['revenue_growth_yoy']
        )

        # Should be low (< 0.3)
        assert ks_stat < 0.3
        assert ks_stat >= 0  # KS stat is always non-negative

    def test_calculate_ks_statistic_with_drift(self, baseline_data, production_data_with_drift):
        """Test KS statistic for distributions with drift"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=":memory:", model_version="1.0.0")

        # Test on rsi_14 (drift expected: uniform(30,70) -> uniform(50,90))
        ks_stat = detector.calculate_ks_statistic(
            baseline_data['rsi_14'],
            production_data_with_drift['rsi_14']
        )

        # Should be high (> 0.3)
        assert ks_stat > 0.3

    def test_ks_statistic_returns_p_value(self, baseline_data, production_data_no_drift):
        """Test that KS test returns p-value"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=":memory:", model_version="1.0.0")

        ks_stat, p_value = detector.calculate_ks_statistic_with_pvalue(
            baseline_data['revenue_growth_yoy'],
            production_data_no_drift['revenue_growth_yoy']
        )

        assert 0 <= p_value <= 1


class TestPSI:
    """Test AC5.2.3: Population Stability Index"""

    def test_calculate_psi_no_drift(self, baseline_data, production_data_no_drift):
        """Test PSI for distributions with no drift"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=":memory:", model_version="1.0.0")

        psi = detector.calculate_psi(
            baseline_data['revenue_growth_yoy'],
            production_data_no_drift['revenue_growth_yoy'],
            bins=10
        )

        # PSI < 0.1: No significant drift
        assert psi < 0.1

    def test_calculate_psi_moderate_drift(self):
        """Test PSI for moderate drift"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=":memory:", model_version="1.0.0")

        # Create slightly shifted distributions
        baseline = np.random.normal(10, 2, 1000)
        production = np.random.normal(10.3, 2, 1000)  # Small shift

        psi = detector.calculate_psi(baseline, production, bins=10)

        # Should show some drift (PSI > 0)
        assert psi > 0
        # For this small shift, PSI should be moderate
        assert psi < 1.0  # Reasonable upper bound

    def test_calculate_psi_significant_drift(self, baseline_data, production_data_with_drift):
        """Test PSI for significant drift"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=":memory:", model_version="1.0.0")

        psi = detector.calculate_psi(
            baseline_data['rsi_14'],
            production_data_with_drift['rsi_14'],
            bins=10
        )

        # PSI >= 0.25: Significant drift
        assert psi >= 0.25

    def test_psi_formula_correctness(self):
        """Test PSI formula: Σ (actual% - expected%) * ln(actual% / expected%)"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=":memory:", model_version="1.0.0")

        # Simple test case
        baseline = np.array([1, 1, 1, 2, 2, 2, 3, 3, 3])
        production = np.array([1, 1, 2, 2, 2, 3, 3, 3, 3])

        psi = detector.calculate_psi(baseline, production, bins=3)

        # PSI should be a small positive number
        assert psi >= 0
        assert psi < 0.5  # Minor change


class TestBaselineStorage:
    """Test AC5.2.4: Baseline distribution storage"""

    def test_store_baseline_distribution(self, temp_db, baseline_data):
        """Test storing baseline distribution"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=temp_db, model_version="1.0.0")

        # Store baseline
        detector.store_baseline_distribution(
            feature_name='revenue_growth_yoy',
            distribution=baseline_data['revenue_growth_yoy']
        )

        # Verify stored
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM drift_baselines WHERE feature_name = ? AND model_version = ?",
            ('revenue_growth_yoy', '1.0.0')
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_load_baseline_distribution(self, temp_db, baseline_data):
        """Test loading baseline distribution"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=temp_db, model_version="1.0.0")

        # Store baseline
        detector.store_baseline_distribution(
            feature_name='revenue_growth_yoy',
            distribution=baseline_data['revenue_growth_yoy']
        )

        # Load baseline
        loaded = detector.load_baseline_distribution('revenue_growth_yoy')

        assert loaded is not None
        assert len(loaded) > 0

    def test_baseline_statistics_stored(self, temp_db, baseline_data):
        """Test that mean, std, min, max, percentiles are stored"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=temp_db, model_version="1.0.0")

        detector.store_baseline_distribution(
            feature_name='revenue_growth_yoy',
            distribution=baseline_data['revenue_growth_yoy']
        )

        # Verify statistics
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT mean, std, min, max, percentiles FROM drift_baselines WHERE feature_name = ?",
            ('revenue_growth_yoy',)
        )
        result = cursor.fetchone()
        conn.close()

        assert result[0] is not None  # mean
        assert result[1] is not None  # std
        assert result[2] is not None  # min
        assert result[3] is not None  # max
        assert result[4] is not None  # percentiles JSON


class TestDriftDetection:
    """Test AC5.2.5: Daily drift detection"""

    def test_detect_drift_all_features(self, temp_db, baseline_data, production_data_no_drift):
        """Test detecting drift across all features"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=temp_db, model_version="1.0.0")

        # Store all baselines
        for feature_name, distribution in baseline_data.items():
            detector.store_baseline_distribution(feature_name, distribution)

        # Detect drift
        drift_results = detector.detect_drift(production_data_no_drift)

        assert len(drift_results) == len(baseline_data)
        assert all('ks_statistic' in result for result in drift_results.values())
        assert all('psi' in result for result in drift_results.values())

    def test_detect_drift_identifies_drifted_features(self, temp_db, baseline_data, production_data_with_drift):
        """Test that drift detection identifies drifted features"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=temp_db, model_version="1.0.0")

        # Store all baselines
        for feature_name, distribution in baseline_data.items():
            detector.store_baseline_distribution(feature_name, distribution)

        # Detect drift
        drift_results = detector.detect_drift(production_data_with_drift)

        # rsi_14 and volume_ratio_30d should show drift
        assert drift_results['rsi_14']['psi'] > 0.25 or drift_results['rsi_14']['ks_statistic'] > 0.3
        assert drift_results['volume_ratio_30d']['psi'] > 0.25


class TestDriftReport:
    """Test AC5.2.6: Drift report generation"""

    def test_generate_drift_report(self, temp_db, baseline_data, production_data_with_drift):
        """Test drift report generation"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=temp_db, model_version="1.0.0")

        # Store baselines
        for feature_name, distribution in baseline_data.items():
            detector.store_baseline_distribution(feature_name, distribution)

        # Detect drift
        drift_results = detector.detect_drift(production_data_with_drift)

        # Generate report
        report = detector.generate_drift_report(drift_results, date="2025-11-14")

        assert 'Date: 2025-11-14' in report
        assert 'Model Version: 1.0.0' in report
        assert 'Features Tested:' in report
        assert 'Features with Drift:' in report

    def test_report_includes_severity(self, temp_db, baseline_data, production_data_with_drift):
        """Test that report includes drift severity"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=temp_db, model_version="1.0.0")

        # Store baselines
        for feature_name, distribution in baseline_data.items():
            detector.store_baseline_distribution(feature_name, distribution)

        drift_results = detector.detect_drift(production_data_with_drift)
        report = detector.generate_drift_report(drift_results, date="2025-11-14")

        # Should mention severity
        assert 'Severity:' in report or 'DRIFT' in report


class TestAlertThresholds:
    """Test AC5.2.7: Alert thresholds and escalation"""

    def test_determine_alert_severity_low(self):
        """Test alert severity for low drift (PSI < 0.1)"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=":memory:", model_version="1.0.0")

        severity = detector.determine_alert_severity(psi=0.05, ks_stat=0.1)

        assert severity == 'low' or severity == 'none'

    def test_determine_alert_severity_moderate(self):
        """Test alert severity for moderate drift (0.1 <= PSI < 0.25)"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=":memory:", model_version="1.0.0")

        severity = detector.determine_alert_severity(psi=0.15, ks_stat=0.2)

        assert severity == 'moderate'

    def test_determine_alert_severity_high(self):
        """Test alert severity for high drift (PSI >= 0.25)"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=":memory:", model_version="1.0.0")

        severity = detector.determine_alert_severity(psi=0.3, ks_stat=0.4)

        assert severity == 'high'

    def test_determine_alert_severity_critical(self):
        """Test alert severity for critical drift (PSI >= 0.4 or >30% features drifting)"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=":memory:", model_version="1.0.0")

        severity = detector.determine_alert_severity(psi=0.45, ks_stat=0.5)

        assert severity == 'critical' or severity == 'high'


class TestDriftDetectorIntegration:
    """Integration tests for DriftDetector"""

    def test_full_drift_detection_workflow(self, temp_db, baseline_data, production_data_with_drift):
        """Test full drift detection workflow"""
        from monitoring.drift_detector import DriftDetector

        detector = DriftDetector(baseline_db=temp_db, model_version="1.0.0")

        # 1. Store baselines
        for feature_name, distribution in baseline_data.items():
            detector.store_baseline_distribution(feature_name, distribution)

        # 2. Detect drift
        drift_results = detector.detect_drift(production_data_with_drift)

        # 3. Generate report
        report = detector.generate_drift_report(drift_results, date="2025-11-14")

        # 4. Verify report contains key info
        assert len(report) > 0
        assert '2025-11-14' in report

        # 5. Verify drift detected
        drifted_features = [
            name for name, result in drift_results.items()
            if result['psi'] > 0.25
        ]
        assert len(drifted_features) > 0

    def test_multiple_model_versions(self, temp_db, baseline_data):
        """Test handling multiple model versions"""
        from monitoring.drift_detector import DriftDetector

        # Store baselines for v1.0.0
        detector_v1 = DriftDetector(baseline_db=temp_db, model_version="1.0.0")
        detector_v1.store_baseline_distribution('revenue_growth_yoy', baseline_data['revenue_growth_yoy'])

        # Store baselines for v1.1.0
        detector_v2 = DriftDetector(baseline_db=temp_db, model_version="1.1.0")
        detector_v2.store_baseline_distribution('revenue_growth_yoy', baseline_data['npm_trend'])

        # Load v1.0.0 baseline
        loaded_v1 = detector_v1.load_baseline_distribution('revenue_growth_yoy')

        # Load v1.1.0 baseline
        loaded_v2 = detector_v2.load_baseline_distribution('revenue_growth_yoy')

        # Should be different
        assert not np.array_equal(loaded_v1, loaded_v2)
