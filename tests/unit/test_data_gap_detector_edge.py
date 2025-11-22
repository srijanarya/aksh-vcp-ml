"""
Edge cases for Data Gap Detector to reach higher coverage
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock
from src.data.data_gap_detector import DataGapDetector


class TestEdgeCases:
    """Test edge cases for coverage"""

    def test_detect_gaps_empty_dataframe(self):
        """Test gap detection on empty DataFrame"""
        detector = DataGapDetector()

        df_empty = pd.DataFrame()
        gaps = detector.detect_gaps(df_empty, '1m')

        assert len(gaps) == 0

    def test_detect_gaps_single_row(self):
        """Test gap detection on single-row DataFrame"""
        detector = DataGapDetector()

        df_single = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100}
        ])

        gaps = detector.detect_gaps(df_single, '1m')

        assert len(gaps) == 0

    def test_fill_gaps_empty_dataframe(self):
        """Test filling gaps on empty DataFrame"""
        detector = DataGapDetector()

        df_empty = pd.DataFrame()
        filled = detector.fill_gaps(df_empty, '1m', strategy='forward_fill')

        assert len(filled) == 0

    def test_fill_gaps_no_gaps(self):
        """Test filling when there are no gaps"""
        detector = DataGapDetector()

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30) + timedelta(minutes=i),
             'open': 100 + i, 'high': 101 + i, 'low': 99 + i, 'close': 100.5 + i, 'volume': 100}
            for i in range(3)
        ])

        filled = detector.fill_gaps(df, '1m', strategy='forward_fill')

        # Should return original data when no gaps
        assert len(filled) == 3

    def test_non_trading_gap_without_calendar(self):
        """Test non-trading gap detection without calendar"""
        detector = DataGapDetector()  # No calendar provided

        # The _is_non_trading_gap should return False without calendar
        is_non_trading = detector._is_non_trading_gap(
            datetime(2025, 1, 3),
            datetime(2025, 1, 6),
            '1d'
        )

        assert is_non_trading == False

    def test_non_trading_gap_intraday_interval(self):
        """Test non-trading gap check for intraday interval"""
        calendar = Mock()
        calendar.is_trading_day.return_value = False
        detector = DataGapDetector(market_calendar=calendar)

        # For intraday intervals, should always return False
        is_non_trading = detector._is_non_trading_gap(
            datetime(2025, 1, 1, 9, 30),
            datetime(2025, 1, 1, 10, 30),
            '1m'
        )

        assert is_non_trading == False
