"""
Edge cases for Multi-Timeframe Fetcher to reach higher coverage
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock
from src.data.multi_timeframe_fetcher import MultiTimeframeFetcher


class TestEdgeCases:
    """Test edge cases for coverage"""

    def test_fetch_with_exception(self):
        """Test handling of exceptions during fetch"""
        data_source = Mock()
        data_source.fetch_ohlcv.side_effect = Exception("Network error")

        fetcher = MultiTimeframeFetcher(data_source)

        result = fetcher.fetch_multi_timeframe(
            'RELIANCE', 'NSE', ['1d'],
            datetime(2025, 1, 1), datetime(2025, 1, 2)
        )

        # Should return empty DataFrame for failed interval
        assert '1d' in result
        assert len(result['1d']) == 0

    def test_resample_empty_dataframe(self):
        """Test resampling empty DataFrame"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source)

        df_empty = pd.DataFrame()
        df_resampled = fetcher.resample_timeframe(df_empty, '1m', '5m')

        assert len(df_resampled) == 0

    def test_validate_consistency_single_interval(self):
        """Test validation with only one interval"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source)

        timeframe_data = {
            '1m': pd.DataFrame([
                {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100}
            ])
        }

        issues = fetcher.validate_consistency(timeframe_data)
        # Should return empty list since there's nothing to compare
        assert len(issues) == 0

    def test_validate_consistency_with_empty_dataframes(self):
        """Test validation with empty DataFrames"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source)

        timeframe_data = {
            '1m': pd.DataFrame(),
            '5m': pd.DataFrame()
        }

        issues = fetcher.validate_consistency(timeframe_data)
        # Should handle empty DataFrames gracefully
        assert isinstance(issues, list)

    def test_compare_dataframes_different_lengths(self):
        """Test comparison of DataFrames with different lengths"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source)

        df1 = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100}
        ])

        df2 = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100},
            {'timestamp': datetime(2025, 1, 1, 9, 35), 'open': 100.5, 'high': 102, 'low': 100, 'close': 101, 'volume': 150}
        ])

        issues = fetcher._compare_dataframes(df1, df2, "test")

        # Should detect different lengths
        assert len(issues) > 0
        assert "different number of rows" in issues[0].lower()

    def test_compare_dataframes_low_mismatch(self):
        """Test comparison detecting low price mismatch"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source)

        df1 = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100}
        ])

        df2 = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 90, 'close': 100.5, 'volume': 100}
        ])

        issues = fetcher._compare_dataframes(df1, df2, "test")

        # Should detect low mismatch
        assert len(issues) > 0
        assert any("low mismatch" in issue.lower() for issue in issues)
