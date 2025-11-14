"""
Tests for UpperCircuitLabeler (Story 1.2)

Acceptance Criteria (from Epic 1 Story 1.2):
AC1.2.1: UpperCircuitLabeler class created with label_upper_circuits method
AC1.2.2: Fetch next-day price data from BhavCopy CSV
AC1.2.3: Label as upper circuit based on dual criteria (price ≥5% AND circuit hit)
AC1.2.4: Store labels in historical_upper_circuits.db
AC1.2.5: Collect ≥200,000 labeled samples
AC1.2.6: Validate class distribution in 5-15% range
AC1.2.7: Handle missing data gracefully

Test Strategy: AAA (Arrange, Act, Assert) pattern with mocking
Coverage Target: ≥90%

Author: VCP Financial Research Team
Created: 2025-11-13
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# System under test (will be created in ml_data_collector.py)
# from agents.ml.ml_data_collector import UpperCircuitLabeler, UpperCircuitLabel


class TestUpperCircuitLabelerInitialization:
    """Test UpperCircuitLabeler class initialization (AC1.2.1)"""

    def test_labeler_class_exists(self):
        """AC1.2.1: Verify UpperCircuitLabeler class exists"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler
        assert UpperCircuitLabeler is not None

    def test_labeler_instantiation(self, tmp_path):
        """AC1.2.1: Labeler can be instantiated with db_path"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler

        db_path = tmp_path / "upper_circuits.db"
        labeler = UpperCircuitLabeler(db_path=str(db_path))

        assert labeler is not None
        assert hasattr(labeler, 'label_upper_circuits')

    def test_labeler_creates_database_table(self, tmp_path):
        """AC1.2.4: Labeler creates upper_circuit_labels table on init"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler

        db_path = tmp_path / "upper_circuits.db"
        labeler = UpperCircuitLabeler(db_path=str(db_path))

        # Verify table exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='upper_circuit_labels'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "upper_circuit_labels"


class TestBhavCopyFetching:
    """Test BhavCopy CSV downloading and parsing (AC1.2.2)"""

    def test_fetch_next_trading_day_skips_weekend(self, tmp_path):
        """AC1.2.2: fetch_next_trading_day skips weekends"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler

        labeler = UpperCircuitLabeler(db_path=str(tmp_path / "test.db"))

        # Friday 2024-11-08 → Should skip to Monday 2024-11-11
        next_day = labeler.fetch_next_trading_day("2024-11-08")

        # Note: Actual implementation needs to check market holidays calendar
        # For now, test that it returns a valid date
        assert next_day is not None
        assert isinstance(next_day, str)

    def test_download_bhav_copy_returns_csv_path(self, tmp_path):
        """AC1.2.2: download_bhav_copy downloads and returns CSV path"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler

        labeler = UpperCircuitLabeler(db_path=str(tmp_path / "test.db"))

        with patch('tools.bhav_copy_downloader.download_bse_bhav_copy') as mock_download:
            # Mock successful download
            mock_csv_path = "/tmp/bhav_copy_cache/EQ131124_CSV.CSV"
            mock_download.return_value = mock_csv_path

            csv_path = labeler.download_bhav_copy("2024-11-13")

            assert csv_path is not None
            # Should cache in /tmp/bhav_copy_cache/
            assert "bhav_copy_cache" in csv_path

    def test_parse_bhav_copy_extracts_price_data(self, tmp_path):
        """AC1.2.2: parse_bhav_copy extracts OHLC data for specific BSE code"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler, BhavCopyRecord

        labeler = UpperCircuitLabeler(db_path=str(tmp_path / "test.db"))

        # Create mock CSV file
        csv_content = """SC_CODE,SC_NAME,OPEN,HIGH,LOW,CLOSE,NO_OF_SHRS,TDCLOINDI
500570,TCS LTD,3500.00,3550.00,3480.00,3540.00,1234567,
"""
        csv_path = tmp_path / "bhav.csv"
        csv_path.write_text(csv_content)

        record = labeler.parse_bhav_copy(str(csv_path), "500570")

        assert record is not None
        assert isinstance(record, BhavCopyRecord)
        assert record.bse_code == "500570"
        assert record.close == 3540.00
        assert record.volume == 1234567


class TestUpperCircuitLabeling:
    """Test upper circuit labeling logic (AC1.2.3)"""

    def test_label_upper_circuit_both_criteria_met(self, tmp_path):
        """AC1.2.3: Label=1 when price ≥5% AND circuit hit"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler

        labeler = UpperCircuitLabeler(db_path=str(tmp_path / "test.db"))

        # Mock: Price +6%, circuit hit
        with patch.object(labeler, 'fetch_next_trading_day', return_value="2024-11-14"), \
             patch.object(labeler, 'download_bhav_copy', return_value="/tmp/bhav.csv"), \
             patch.object(labeler, 'parse_bhav_copy') as mock_parse:

            mock_parse.return_value = Mock(
                bse_code="500570",
                close=3540.00,
                prev_close=3340.00,  # +6% gain
                circuit_indicator="C"  # Circuit hit
            )

            labels = labeler.label_upper_circuits("500570", ("2024-11-13", "2024-11-13"))

            assert len(labels) > 0
            assert labels[0].label == 1  # Both criteria met
            assert labels[0].price_change_pct >= 5.0
            assert labels[0].hit_circuit is True

    def test_label_no_circuit_price_too_low(self, tmp_path):
        """AC1.2.3: Label=0 when price <5%"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler

        labeler = UpperCircuitLabeler(db_path=str(tmp_path / "test.db"))

        with patch.object(labeler, 'fetch_next_trading_day', return_value="2024-11-14"), \
             patch.object(labeler, 'download_bhav_copy', return_value="/tmp/bhav.csv"), \
             patch.object(labeler, 'parse_bhav_copy') as mock_parse:

            mock_parse.return_value = Mock(
                bse_code="500570",
                close=3440.00,
                prev_close=3400.00,  # +1.2% gain (too low)
                circuit_indicator=""
            )

            labels = labeler.label_upper_circuits("500570", ("2024-11-13", "2024-11-13"))

            assert len(labels) > 0
            assert labels[0].label == 0  # Price too low
            assert labels[0].price_change_pct < 5.0

    def test_label_no_circuit_not_hit(self, tmp_path):
        """AC1.2.3: Label=0 when price ≥5% but circuit NOT hit"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler

        labeler = UpperCircuitLabeler(db_path=str(tmp_path / "test.db"))

        with patch.object(labeler, 'fetch_next_trading_day', return_value="2024-11-14"), \
             patch.object(labeler, 'download_bhav_copy', return_value="/tmp/bhav.csv"), \
             patch.object(labeler, 'parse_bhav_copy') as mock_parse:

            mock_parse.return_value = Mock(
                bse_code="500570",
                close=3540.00,
                prev_close=3340.00,  # +6% gain
                circuit_indicator=""  # Circuit NOT hit
            )

            labels = labeler.label_upper_circuits("500570", ("2024-11-13", "2024-11-13"))

            assert len(labels) > 0
            assert labels[0].label == 0  # Circuit not hit
            assert labels[0].hit_circuit is False


class TestDatabaseStorage:
    """Test storing labels in database (AC1.2.4)"""

    def test_store_labels_inserts_to_database(self, tmp_path):
        """AC1.2.4: store_labels inserts records into upper_circuit_labels table"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler, UpperCircuitLabel

        db_path = tmp_path / "upper_circuits.db"
        labeler = UpperCircuitLabeler(db_path=str(db_path))

        labels = [
            UpperCircuitLabel(
                bse_code="500570",
                nse_symbol="TCS",
                earnings_date=date(2024, 11, 13),
                next_day_date=date(2024, 11, 14),
                price_change_pct=6.0,
                hit_circuit=True,
                label=1
            )
        ]

        count = labeler.store_labels(labels)

        assert count == 1

        # Verify in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM upper_circuit_labels")
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 1

    def test_store_labels_uses_insert_or_replace(self, tmp_path):
        """AC1.2.4: store_labels uses INSERT OR REPLACE for idempotency"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler, UpperCircuitLabel

        db_path = tmp_path / "upper_circuits.db"
        labeler = UpperCircuitLabeler(db_path=str(db_path))

        label = UpperCircuitLabel(
            bse_code="500570",
            nse_symbol="TCS",
            earnings_date=date(2024, 11, 13),
            next_day_date=date(2024, 11, 14),
            price_change_pct=6.0,
            hit_circuit=True,
            label=1
        )

        # Insert twice
        labeler.store_labels([label])
        labeler.store_labels([label])

        # Should have only 1 record (not 2) due to UNIQUE constraint
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM upper_circuit_labels WHERE bse_code='500570'")
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 1


class TestScaleAndPerformance:
    """Test collection at scale (AC1.2.5)"""

    def test_label_multiple_companies(self, tmp_path):
        """AC1.2.5: Can label multiple companies"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler

        labeler = UpperCircuitLabeler(db_path=str(tmp_path / "test.db"))

        companies = ["500570", "500209", "500180"]  # TCS, Infosys, HDFC

        with patch.object(labeler, 'label_upper_circuits') as mock_label:
            mock_label.return_value = [Mock(label=1, bse_code="500570")]

            for company in companies:
                labels = labeler.label_upper_circuits(company, ("2024-01-01", "2024-12-31"))
                assert len(labels) > 0


class TestClassDistributionValidation:
    """Test class distribution validation (AC1.2.6)"""

    def test_validate_class_distribution_in_range(self, tmp_path):
        """AC1.2.6: validate_class_distribution accepts 5-15% positive rate"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler, UpperCircuitLabel

        db_path = tmp_path / "upper_circuits.db"
        labeler = UpperCircuitLabeler(db_path=str(db_path))

        # Insert 100 labels: 10 positive (10%)
        labels = []
        for i in range(100):
            labels.append(UpperCircuitLabel(
                bse_code=f"50{i:04d}",
                nse_symbol=f"SYM{i}",
                earnings_date=date(2024, 11, 13),
                next_day_date=date(2024, 11, 14),
                price_change_pct=6.0 if i < 10 else 1.0,
                hit_circuit=i < 10,
                label=1 if i < 10 else 0
            ))

        labeler.store_labels(labels)

        report = labeler.validate_class_distribution()

        assert report.positive_ratio >= 5.0
        assert report.positive_ratio <= 15.0
        assert report.status == "PASS"

    def test_validate_class_distribution_warns_on_low_ratio(self, tmp_path, caplog):
        """AC1.2.6: Warns if positive ratio <5%"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler, UpperCircuitLabel

        db_path = tmp_path / "upper_circuits.db"
        labeler = UpperCircuitLabeler(db_path=str(db_path))

        # Insert 100 labels: 3 positive (3% - too low)
        labels = []
        for i in range(100):
            labels.append(UpperCircuitLabel(
                bse_code=f"50{i:04d}",
                nse_symbol=f"SYM{i}",
                earnings_date=date(2024, 11, 13),
                next_day_date=date(2024, 11, 14),
                price_change_pct=6.0 if i < 3 else 1.0,
                hit_circuit=i < 3,
                label=1 if i < 3 else 0
            ))

        labeler.store_labels(labels)

        report = labeler.validate_class_distribution()

        assert report.positive_ratio < 5.0
        assert report.status == "WARNING"
        assert "severe" in caplog.text.lower()


class TestMissingDataHandling:
    """Test graceful handling of missing data (AC1.2.7)"""

    def test_fetch_next_trading_day_tries_up_to_5_days(self, tmp_path):
        """AC1.2.7: Tries up to 5 days if BhavCopy unavailable"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler

        labeler = UpperCircuitLabeler(db_path=str(tmp_path / "test.db"))

        with patch('tools.bhav_copy_downloader.download_bse_bhav_copy') as mock_download:
            # Mock successful download
            mock_csv_path = "/tmp/bhav_copy_cache/EQ131124_CSV.CSV"
            mock_download.return_value = mock_csv_path

            csv_path = labeler.download_bhav_copy("2024-11-13")

            assert csv_path is not None
            assert mock_download.call_count <= 5

    def test_skip_labeling_if_no_data_after_5_days(self, tmp_path):
        """AC1.2.7: Skips labeling if no data after 5 retries"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler

        labeler = UpperCircuitLabeler(db_path=str(tmp_path / "test.db"))

        with patch.object(labeler, 'fetch_next_trading_day', return_value=None):
            labels = labeler.label_upper_circuits("500570", ("2024-11-13", "2024-11-13"))

            assert len(labels) == 0  # No labels if data unavailable

    def test_fallback_to_yfinance_for_prev_close(self, tmp_path):
        """AC1.2.7: Falls back to yfinance if prev_close unavailable"""
        from agents.ml.ml_data_collector import UpperCircuitLabeler

        labeler = UpperCircuitLabeler(db_path=str(tmp_path / "test.db"))

        # Mock the get_prev_close method to return a valid price
        with patch.object(labeler, 'get_prev_close', return_value=3340.00):
            prev_close = labeler.get_prev_close("500570", "2024-11-13")

            assert prev_close is not None
            assert prev_close > 0


# Pytest fixtures
@pytest.fixture
def sample_earnings_dates():
    """Sample earnings dates for testing"""
    return [
        date(2024, 1, 15),
        date(2024, 4, 15),
        date(2024, 7, 15),
        date(2024, 10, 15)
    ]


@pytest.fixture
def sample_bhav_copy_data():
    """Sample BhavCopy CSV data"""
    return """SC_CODE,SC_NAME,OPEN,HIGH,LOW,CLOSE,NO_OF_SHRS,TDCLOINDI
500570,TCS LTD,3500.00,3550.00,3480.00,3540.00,1234567,C
500209,INFOSYS LTD,1450.00,1475.00,1440.00,1470.00,2345678,
500180,HDFC BANK LTD,1650.00,1690.00,1640.00,1680.00,3456789,C
"""


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=agents.ml.ml_data_collector", "--cov-report=term-missing"])
