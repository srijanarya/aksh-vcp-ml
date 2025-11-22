"""
Tests for Data Quality Metrics Dashboard (SHORT-014)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
import pandas as pd
import json


class TestDataQualityDashboard:
    """Test data quality metrics and dashboard"""

    @pytest.fixture
    def sample_data(self):
        """Sample OHLCV data with some gaps"""
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        data = pd.DataFrame({
            'open': [100.0] * len(dates),
            'high': [105.0] * len(dates),
            'low': [95.0] * len(dates),
            'close': [102.0] * len(dates),
            'volume': [1000000] * len(dates)
        }, index=dates)
        # Remove some dates to create gaps
        return data.iloc[[i for i in range(len(data)) if i % 7 != 0]]

    def test_calculate_completeness(self, sample_data):
        """TC-1: Calculate data completeness metrics"""
        from src.data.data_quality_dashboard import DataQualityDashboard

        dashboard = DataQualityDashboard()

        metrics = dashboard.calculate_completeness(
            symbol="TCS",
            data=sample_data,
            expected_days=31
        )

        # Should calculate correct completeness
        assert 'completeness_pct' in metrics
        assert 0 <= metrics['completeness_pct'] <= 100
        assert metrics['total_points'] > 0
        assert metrics['missing_points'] >= 0
        assert metrics['expected_points'] == 31

    def test_track_validation_failures(self):
        """TC-2: Track validation failure rates"""
        from src.data.data_quality_dashboard import DataQualityDashboard

        dashboard = DataQualityDashboard()

        # Record validation results
        dashboard.record_validation("TCS", success=True)
        dashboard.record_validation("TCS", success=True)
        dashboard.record_validation("TCS", success=False)
        dashboard.record_validation("INFY", success=True)

        metrics = dashboard.get_validation_metrics()

        # Should track per-symbol metrics
        assert "TCS" in metrics
        assert metrics["TCS"]["total"] == 3
        assert metrics["TCS"]["failures"] == 1
        assert metrics["TCS"]["failure_rate"] == pytest.approx(33.33, abs=0.1)

    def test_monitor_freshness(self):
        """TC-3: Monitor data freshness"""
        from src.data.data_quality_dashboard import DataQualityDashboard

        dashboard = DataQualityDashboard()

        # Record data updates
        now = datetime.now()
        old_time = now - timedelta(hours=5)

        dashboard.record_update("TCS", now)
        dashboard.record_update("INFY", old_time)

        freshness = dashboard.check_freshness(threshold_hours=4)

        # Should identify stale data
        assert "TCS" in freshness["fresh"]
        assert "INFY" in freshness["stale"]
        assert freshness["stale"]["INFY"]["hours_old"] > 4

    def test_detect_data_gaps(self, sample_data):
        """Test gap detection in data"""
        from src.data.data_quality_dashboard import DataQualityDashboard

        dashboard = DataQualityDashboard()

        gaps = dashboard.detect_gaps(
            symbol="TCS",
            data=sample_data,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )

        # Should detect missing dates
        assert len(gaps) > 0
        assert 'gap_dates' in gaps
        assert 'gap_count' in gaps

    def test_generate_summary_report(self):
        """Test summary report generation"""
        from src.data.data_quality_dashboard import DataQualityDashboard

        dashboard = DataQualityDashboard()

        # Add some test data
        dashboard.record_validation("TCS", success=True)
        dashboard.record_validation("INFY", success=False)
        dashboard.record_update("TCS", datetime.now())

        report = dashboard.generate_summary_report()

        # Report should have all sections
        assert 'validation' in report
        assert 'freshness' in report
        assert 'timestamp' in report

    def test_export_metrics_json(self):
        """Test exporting metrics to JSON"""
        from src.data.data_quality_dashboard import DataQualityDashboard

        dashboard = DataQualityDashboard()
        dashboard.record_validation("TCS", success=True)

        json_str = dashboard.export_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert isinstance(data, dict)
        assert 'validation' in data

    def test_export_metrics_csv(self, tmp_path):
        """Test exporting metrics to CSV"""
        from src.data.data_quality_dashboard import DataQualityDashboard

        dashboard = DataQualityDashboard()
        dashboard.record_validation("TCS", success=True)
        dashboard.record_validation("INFY", success=False)

        csv_file = tmp_path / "metrics.csv"
        dashboard.export_csv(str(csv_file))

        # CSV should be created
        assert csv_file.exists()

        # Should contain data
        df = pd.read_csv(csv_file)
        assert len(df) > 0

    def test_daily_report(self):
        """Test daily report generation"""
        from src.data.data_quality_dashboard import DataQualityDashboard

        dashboard = DataQualityDashboard()

        # Add metrics for today
        now = datetime.now()
        dashboard.record_validation("TCS", success=True, timestamp=now)
        dashboard.record_update("TCS", now)

        report = dashboard.generate_daily_report()

        # Should contain daily metrics
        assert 'date' in report
        assert 'validation_summary' in report
        assert 'freshness_summary' in report

    def test_weekly_report(self):
        """Test weekly report generation"""
        from src.data.data_quality_dashboard import DataQualityDashboard

        dashboard = DataQualityDashboard()

        # Add metrics across week
        for i in range(7):
            timestamp = datetime.now() - timedelta(days=i)
            dashboard.record_validation("TCS", success=True, timestamp=timestamp)

        report = dashboard.generate_weekly_report()

        # Should aggregate weekly metrics
        assert 'week_start' in report
        assert 'week_end' in report
        assert 'total_validations' in report

    def test_per_source_metrics(self):
        """Test tracking metrics per data source"""
        from src.data.data_quality_dashboard import DataQualityDashboard

        dashboard = DataQualityDashboard()

        # Record from different sources
        dashboard.record_validation("TCS", success=True, source="angel_one")
        dashboard.record_validation("TCS", success=True, source="yahoo")
        dashboard.record_validation("TCS", success=False, source="angel_one")

        metrics = dashboard.get_source_metrics()

        # Should track per source
        assert "angel_one" in metrics
        assert "yahoo" in metrics
        assert metrics["angel_one"]["total"] == 2
        assert metrics["yahoo"]["total"] == 1
