"""
Tests for Data Gap Detection & Filling

TDD Approach: RED Phase - All tests will fail initially
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock
from src.data.data_gap_detector import DataGapDetector, Gap, GapReport


class TestGapDetection:
    """Test gap detection"""

    def test_detect_intraday_gap(self):
        """Test detection of intraday gap"""
        detector = DataGapDetector()

        # Create 1-minute data with 10-minute gap
        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100},
            {'timestamp': datetime(2025, 1, 1, 9, 31), 'open': 100.5, 'high': 102, 'low': 100, 'close': 101, 'volume': 150},
            # Gap from 9:31 to 9:42 (10 minutes missing)
            {'timestamp': datetime(2025, 1, 1, 9, 42), 'open': 101, 'high': 103, 'low': 101, 'close': 102, 'volume': 200}
        ])

        gaps = detector.detect_gaps(df, '1m')

        assert len(gaps) == 1
        assert gaps[0].start_time == datetime(2025, 1, 1, 9, 31)
        assert gaps[0].end_time == datetime(2025, 1, 1, 9, 42)
        assert gaps[0].expected_rows == 10

    def test_detect_daily_gap(self):
        """Test detection of daily gap"""
        detector = DataGapDetector()

        # Create daily data with 3-day gap (excluding weekends)
        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 1000},
            {'timestamp': datetime(2025, 1, 2), 'open': 100.5, 'high': 102, 'low': 100, 'close': 101, 'volume': 1500},
            # Gap from Jan 2 to Jan 6 (3 trading days missing: Jan 3, 5, 6)
            {'timestamp': datetime(2025, 1, 7), 'open': 101, 'high': 103, 'low': 101, 'close': 102, 'volume': 2000}
        ])

        gaps = detector.detect_gaps(df, '1d')

        assert len(gaps) == 1
        # Jan 4-5 is weekend, so gap is Jan 2 -> Jan 6
        assert gaps[0].start_time == datetime(2025, 1, 2)
        assert gaps[0].end_time == datetime(2025, 1, 7)

    def test_no_gaps_detected(self):
        """Test when there are no gaps"""
        detector = DataGapDetector()

        # Create continuous 1-minute data
        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30) + timedelta(minutes=i),
             'open': 100 + i, 'high': 101 + i, 'low': 99 + i, 'close': 100.5 + i, 'volume': 100}
            for i in range(5)
        ])

        gaps = detector.detect_gaps(df, '1m')

        assert len(gaps) == 0

    def test_detect_multiple_gaps(self):
        """Test detection of multiple gaps"""
        detector = DataGapDetector()

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100},
            # Gap 1: 9:30 to 9:35
            {'timestamp': datetime(2025, 1, 1, 9, 35), 'open': 100.5, 'high': 102, 'low': 100, 'close': 101, 'volume': 150},
            {'timestamp': datetime(2025, 1, 1, 9, 36), 'open': 101, 'high': 103, 'low': 101, 'close': 102, 'volume': 200},
            # Gap 2: 9:36 to 9:40
            {'timestamp': datetime(2025, 1, 1, 9, 40), 'open': 102, 'high': 104, 'low': 102, 'close': 103, 'volume': 250}
        ])

        gaps = detector.detect_gaps(df, '1m')

        assert len(gaps) == 2


class TestGapFilling:
    """Test gap filling strategies"""

    def test_fill_gap_forward_fill(self):
        """Test forward-fill strategy"""
        detector = DataGapDetector()

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100},
            # Gap: 9:31, 9:32 missing
            {'timestamp': datetime(2025, 1, 1, 9, 33), 'open': 101, 'high': 103, 'low': 101, 'close': 102, 'volume': 200}
        ])

        filled_df = detector.fill_gaps(df, '1m', strategy='forward_fill')

        assert len(filled_df) == 4  # Original 2 + 2 filled
        # Check that 9:31 and 9:32 are filled with 9:30 values
        assert filled_df.iloc[1]['close'] == 100.5  # Forward-filled from 9:30

    def test_fill_gap_interpolation(self):
        """Test interpolation strategy"""
        detector = DataGapDetector()

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100, 'volume': 100},
            # Gap: 9:31 missing
            {'timestamp': datetime(2025, 1, 1, 9, 32), 'open': 102, 'high': 103, 'low': 101, 'close': 102, 'volume': 200}
        ])

        filled_df = detector.fill_gaps(df, '1m', strategy='interpolate')

        assert len(filled_df) == 3  # Original 2 + 1 filled
        # Check that 9:31 is interpolated (midpoint between 100 and 102)
        assert filled_df.iloc[1]['close'] == 101

    def test_fill_gap_zero(self):
        """Test zero-fill strategy"""
        detector = DataGapDetector()

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100},
            # Gap: 9:31 missing
            {'timestamp': datetime(2025, 1, 1, 9, 32), 'open': 101, 'high': 103, 'low': 101, 'close': 102, 'volume': 200}
        ])

        filled_df = detector.fill_gaps(df, '1m', strategy='zero')

        assert len(filled_df) == 3  # Original 2 + 1 filled
        # Check that 9:31 is filled with zeros
        assert filled_df.iloc[1]['volume'] == 0

    def test_fill_multiple_gaps(self):
        """Test filling multiple gaps"""
        detector = DataGapDetector()

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100, 'volume': 100},
            # Gap 1
            {'timestamp': datetime(2025, 1, 1, 9, 32), 'open': 101, 'high': 102, 'low': 100, 'close': 101, 'volume': 150},
            # Gap 2
            {'timestamp': datetime(2025, 1, 1, 9, 34), 'open': 102, 'high': 103, 'low': 101, 'close': 102, 'volume': 200}
        ])

        filled_df = detector.fill_gaps(df, '1m', strategy='forward_fill')

        assert len(filled_df) == 5  # Original 3 + 2 filled


class TestMarketCalendar:
    """Test market calendar integration"""

    def test_weekend_not_gap(self):
        """Test that weekends are not detected as gaps"""
        # Create mock market calendar
        calendar = Mock()
        calendar.is_trading_day.side_effect = lambda d: d.weekday() < 5  # Mon-Fri only

        detector = DataGapDetector(market_calendar=calendar)

        # Daily data with weekend gap
        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 3), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 1000},  # Friday
            # Weekend gap
            {'timestamp': datetime(2025, 1, 6), 'open': 101, 'high': 102, 'low': 100, 'close': 101, 'volume': 1500}  # Monday
        ])

        gaps = detector.detect_gaps(df, '1d')

        # Weekend should not be counted as gap
        assert len(gaps) == 0

    def test_holiday_not_gap(self):
        """Test that holidays are not detected as gaps"""
        # Create mock market calendar
        calendar = Mock()
        holidays = [datetime(2025, 1, 26)]  # Republic Day
        calendar.is_trading_day.side_effect = lambda d: d not in holidays and d.weekday() < 5

        detector = DataGapDetector(market_calendar=calendar)

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 24), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 1000},
            # Jan 26 is holiday
            {'timestamp': datetime(2025, 1, 27), 'open': 101, 'high': 102, 'low': 100, 'close': 101, 'volume': 1500}
        ])

        gaps = detector.detect_gaps(df, '1d')

        # Holiday should not be counted as gap
        assert len(gaps) == 0

    def test_trading_day_gap_detected(self):
        """Test that missing trading day is detected as gap"""
        calendar = Mock()
        calendar.is_trading_day.return_value = True

        detector = DataGapDetector(market_calendar=calendar)

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 20), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 1000},
            # Jan 21 is trading day but missing
            {'timestamp': datetime(2025, 1, 22), 'open': 101, 'high': 102, 'low': 100, 'close': 101, 'volume': 1500}
        ])

        gaps = detector.detect_gaps(df, '1d')

        # Should detect gap for trading day
        assert len(gaps) == 1


class TestGapReporting:
    """Test gap reporting"""

    def test_gap_report_statistics(self):
        """Test gap report generation"""
        detector = DataGapDetector()

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100},
            # Gap of 5 minutes
            {'timestamp': datetime(2025, 1, 1, 9, 36), 'open': 101, 'high': 103, 'low': 101, 'close': 102, 'volume': 200},
            # Gap of 3 minutes
            {'timestamp': datetime(2025, 1, 1, 9, 40), 'open': 102, 'high': 104, 'low': 102, 'close': 103, 'volume': 250}
        ])

        report = detector.get_gap_report(df, '1m')

        assert report.total_gaps == 2
        assert report.total_missing_rows == 8  # 5 + 3
        assert report.largest_gap_size == 5

    def test_gap_report_empty_data(self):
        """Test gap report on empty data"""
        detector = DataGapDetector()

        df = pd.DataFrame()

        report = detector.get_gap_report(df, '1m')

        assert report.total_gaps == 0
        assert report.total_missing_rows == 0

    def test_gap_report_by_type(self):
        """Test gap report categorizes by gap type"""
        detector = DataGapDetector()

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100},
            # Small gap (< 5 rows)
            {'timestamp': datetime(2025, 1, 1, 9, 33), 'open': 101, 'high': 102, 'low': 100, 'close': 101, 'volume': 150},
            # Large gap (>= 5 rows)
            {'timestamp': datetime(2025, 1, 1, 9, 40), 'open': 102, 'high': 104, 'low': 102, 'close': 103, 'volume': 250}
        ])

        report = detector.get_gap_report(df, '1m')

        assert report.small_gaps == 1  # 2-minute gap
        assert report.large_gaps == 1  # 6-minute gap
