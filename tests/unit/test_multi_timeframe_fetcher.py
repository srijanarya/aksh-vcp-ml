"""
Tests for Multi-Timeframe Data Fetcher

TDD Approach: RED Phase - All tests will fail initially
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from src.data.multi_timeframe_fetcher import MultiTimeframeFetcher


class TestFetcherInitialization:
    """Test fetcher initialization"""

    def test_fetcher_initialization(self):
        """Test fetcher with default base interval"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source)
        assert fetcher.data_source == data_source
        assert fetcher.base_interval == "1m"

    def test_fetcher_with_base_interval(self):
        """Test fetcher with custom base interval"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source, base_interval="5m")
        assert fetcher.base_interval == "5m"


class TestSingleTimeframeFetch:
    """Test single timeframe fetching"""

    def test_fetch_single_timeframe(self):
        """Test fetching data for single timeframe"""
        data_source = Mock()

        mock_result = Mock()
        mock_result.data = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 105, 'low': 99, 'close': 103, 'volume': 1000}
        ])
        mock_result.success = True
        data_source.fetch_ohlcv.return_value = mock_result

        fetcher = MultiTimeframeFetcher(data_source)

        result = fetcher.fetch_multi_timeframe(
            'RELIANCE', 'NSE', ['1d'],
            datetime(2025, 1, 1), datetime(2025, 1, 2)
        )

        assert '1d' in result
        assert len(result['1d']) == 1
        assert result['1d'].iloc[0]['close'] == 103

    def test_fetch_nonexistent_symbol(self):
        """Test fetching data for non-existent symbol"""
        data_source = Mock()

        mock_result = Mock()
        mock_result.data = pd.DataFrame()
        mock_result.success = False
        mock_result.errors = ["Symbol not found"]
        data_source.fetch_ohlcv.return_value = mock_result

        fetcher = MultiTimeframeFetcher(data_source)

        result = fetcher.fetch_multi_timeframe(
            'INVALID', 'NSE', ['1d'],
            datetime(2025, 1, 1), datetime(2025, 1, 2)
        )

        assert '1d' in result
        assert len(result['1d']) == 0


class TestMultiTimeframeFetch:
    """Test multi-timeframe fetching"""

    def test_fetch_multiple_timeframes(self):
        """Test fetching data for multiple timeframes"""
        data_source = Mock()

        def mock_fetch(symbol, exchange, interval, from_date, to_date):
            mock_result = Mock()
            mock_result.success = True
            if interval == '1m':
                mock_result.data = pd.DataFrame([
                    {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100},
                    {'timestamp': datetime(2025, 1, 1, 9, 31), 'open': 100.5, 'high': 102, 'low': 100, 'close': 101, 'volume': 150}
                ])
            elif interval == '5m':
                mock_result.data = pd.DataFrame([
                    {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 102, 'low': 99, 'close': 101, 'volume': 250}
                ])
            return mock_result

        data_source.fetch_ohlcv.side_effect = mock_fetch

        fetcher = MultiTimeframeFetcher(data_source)

        result = fetcher.fetch_multi_timeframe(
            'RELIANCE', 'NSE', ['1m', '5m'],
            datetime(2025, 1, 1), datetime(2025, 1, 2)
        )

        assert '1m' in result
        assert '5m' in result
        assert len(result['1m']) == 2
        assert len(result['5m']) == 1

    def test_fetch_with_partial_failure(self):
        """Test fetching when one timeframe fails"""
        data_source = Mock()

        def mock_fetch(symbol, exchange, interval, from_date, to_date):
            mock_result = Mock()
            if interval == '1m':
                mock_result.success = True
                mock_result.data = pd.DataFrame([
                    {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100}
                ])
            else:
                mock_result.success = False
                mock_result.data = pd.DataFrame()
                mock_result.errors = ["Fetch failed"]
            return mock_result

        data_source.fetch_ohlcv.side_effect = mock_fetch

        fetcher = MultiTimeframeFetcher(data_source)

        result = fetcher.fetch_multi_timeframe(
            'RELIANCE', 'NSE', ['1m', '5m'],
            datetime(2025, 1, 1), datetime(2025, 1, 2)
        )

        assert '1m' in result
        assert '5m' in result
        assert len(result['1m']) == 1
        assert len(result['5m']) == 0

    def test_parallel_fetching(self):
        """Test that multiple intervals are fetched in parallel"""
        data_source = Mock()

        mock_result = Mock()
        mock_result.success = True
        mock_result.data = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100}
        ])
        data_source.fetch_ohlcv.return_value = mock_result

        fetcher = MultiTimeframeFetcher(data_source)

        result = fetcher.fetch_multi_timeframe(
            'RELIANCE', 'NSE', ['1m', '5m', '15m', '1h'],
            datetime(2025, 1, 1), datetime(2025, 1, 2)
        )

        # Should have called fetch for each interval
        assert data_source.fetch_ohlcv.call_count == 4
        assert len(result) == 4


class TestResampling:
    """Test timeframe resampling"""

    def test_resample_1m_to_5m(self):
        """Test resampling 1-minute data to 5-minute"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source)

        df_1m = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100},
            {'timestamp': datetime(2025, 1, 1, 9, 31), 'open': 100.5, 'high': 102, 'low': 100, 'close': 101, 'volume': 150},
            {'timestamp': datetime(2025, 1, 1, 9, 32), 'open': 101, 'high': 103, 'low': 101, 'close': 102, 'volume': 200},
            {'timestamp': datetime(2025, 1, 1, 9, 33), 'open': 102, 'high': 104, 'low': 101.5, 'close': 103, 'volume': 180},
            {'timestamp': datetime(2025, 1, 1, 9, 34), 'open': 103, 'high': 105, 'low': 102, 'close': 104, 'volume': 220}
        ])

        df_5m = fetcher.resample_timeframe(df_1m, '1m', '5m')

        assert len(df_5m) == 1
        assert df_5m.iloc[0]['open'] == 100  # First open
        assert df_5m.iloc[0]['high'] == 105  # Highest high
        assert df_5m.iloc[0]['low'] == 99    # Lowest low
        assert df_5m.iloc[0]['close'] == 104 # Last close
        assert df_5m.iloc[0]['volume'] == 850 # Sum of volume

    def test_resample_5m_to_1h(self):
        """Test resampling 5-minute data to 1-hour"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source)

        # Create 12 x 5-minute bars = 1 hour (starting at exactly 9:00 for clean hour boundary)
        df_5m = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 0) + timedelta(minutes=5*i),
             'open': 100 + i, 'high': 101 + i, 'low': 99 + i, 'close': 100.5 + i, 'volume': 100 + i*10}
            for i in range(12)
        ])

        df_1h = fetcher.resample_timeframe(df_5m, '5m', '1h')

        assert len(df_1h) == 1
        assert df_1h.iloc[0]['open'] == 100  # First open
        assert df_1h.iloc[0]['high'] == 112  # Highest high (101 + 11)
        assert df_1h.iloc[0]['low'] == 99    # Lowest low
        assert df_1h.iloc[0]['close'] == 111.5 # Last close (100.5 + 11)
        assert df_1h.iloc[0]['volume'] == 1860 # Sum of volumes

    def test_resample_preserves_ohlcv(self):
        """Test that resampling preserves OHLCV integrity"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source)

        df_1m = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000},
            {'timestamp': datetime(2025, 1, 1, 9, 31), 'open': 102, 'high': 108, 'low': 101, 'close': 106, 'volume': 1500}
        ])

        df_resampled = fetcher.resample_timeframe(df_1m, '1m', '5m')

        # Check OHLC relationships are valid
        assert df_resampled.iloc[0]['high'] >= df_resampled.iloc[0]['open']
        assert df_resampled.iloc[0]['high'] >= df_resampled.iloc[0]['close']
        assert df_resampled.iloc[0]['low'] <= df_resampled.iloc[0]['open']
        assert df_resampled.iloc[0]['low'] <= df_resampled.iloc[0]['close']


class TestConsistencyValidation:
    """Test cross-timeframe consistency validation"""

    def test_validate_consistent_data(self):
        """Test validation passes for consistent data"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source)

        timeframe_data = {
            '1m': pd.DataFrame([
                {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100},
                {'timestamp': datetime(2025, 1, 1, 9, 31), 'open': 100.5, 'high': 102, 'low': 100, 'close': 101, 'volume': 150}
            ]),
            '5m': pd.DataFrame([
                {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 102, 'low': 99, 'close': 101, 'volume': 250}
            ])
        }

        issues = fetcher.validate_consistency(timeframe_data)
        assert len(issues) == 0

    def test_detect_inconsistency(self):
        """Test detection of inconsistent data"""
        data_source = Mock()
        fetcher = MultiTimeframeFetcher(data_source)

        timeframe_data = {
            '1m': pd.DataFrame([
                {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100},
                {'timestamp': datetime(2025, 1, 1, 9, 31), 'open': 100.5, 'high': 102, 'low': 100, 'close': 101, 'volume': 150}
            ]),
            '5m': pd.DataFrame([
                # Inconsistent: 5m high should be max of 1m highs (102), but shows 110
                {'timestamp': datetime(2025, 1, 1, 9, 30), 'open': 100, 'high': 110, 'low': 99, 'close': 101, 'volume': 250}
            ])
        }

        issues = fetcher.validate_consistency(timeframe_data)
        assert len(issues) > 0
        assert any('high' in issue.lower() for issue in issues)
