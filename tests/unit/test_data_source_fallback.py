"""
Tests for Data Source Fallback Mechanism

TDD Approach: RED Phase - All tests will fail initially
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, MagicMock
from src.data.data_source_fallback import (
    DataSourceFallback,
    DataSourceResult,
    SourceHealth
)


class TestFallbackInitialization:
    """Test fallback mechanism initialization"""

    def test_fallback_initialization(self):
        """Test fallback with default parameters"""
        angel_fetcher = Mock()
        yahoo_fetcher = Mock()
        cache = Mock()

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=yahoo_fetcher,
            cache=cache
        )

        assert fallback.angel_fetcher == angel_fetcher
        assert fallback.yahoo_fetcher == yahoo_fetcher
        assert fallback.cache == cache
        assert fallback.max_retries == 3

    def test_fallback_with_custom_retries(self):
        """Test fallback with custom retry count"""
        fallback = DataSourceFallback(
            angel_fetcher=Mock(),
            yahoo_fetcher=Mock(),
            cache=Mock(),
            max_retries=5
        )

        assert fallback.max_retries == 5


class TestCacheFallback:
    """Test cache fallback behavior"""

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

    def test_fetch_from_cache_success(self, sample_df):
        """Test successful fetch from cache (no API calls)"""
        # Cache data that covers the requested range
        cache_df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000},
            {'timestamp': datetime(2025, 1, 2), 'open': 102, 'high': 108, 'low': 100, 'close': 106, 'volume': 1200},
        ])

        cache = Mock()
        cache.get_cached_data.return_value = cache_df

        fallback = DataSourceFallback(
            angel_fetcher=Mock(),
            yahoo_fetcher=Mock(),
            cache=cache
        )

        result = fallback.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="1d",
            from_date=datetime(2025, 1, 1),
            to_date=datetime(2025, 1, 2)
        )

        assert isinstance(result, DataSourceResult)
        assert result.source == "cache"
        assert len(result.data) == 2
        assert result.is_partial is False

    def test_cache_miss_falls_back_to_angel(self, sample_df):
        """Test cache miss triggers Angel One fetch"""
        cache = Mock()
        cache.get_cached_data.return_value = None

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.return_value = sample_df

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=Mock(),
            cache=cache
        )

        result = fallback.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="1d",
            from_date=datetime(2025, 1, 1),
            to_date=datetime(2025, 1, 2)
        )

        assert result.source == "angel_one"
        assert len(result.data) == 1

        # Verify Angel One was called
        angel_fetcher.fetch_ohlcv.assert_called_once()

        # Verify data was cached
        cache.cache_data.assert_called_once()

    def test_cache_stale_falls_back_to_angel(self, sample_df):
        """Test stale cache (None) triggers API fetch"""
        cache = Mock()
        cache.get_cached_data.return_value = None  # Stale/expired

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.return_value = sample_df

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=Mock(),
            cache=cache
        )

        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        assert result.source == "angel_one"


class TestAngelOneFallback:
    """Test Angel One fallback behavior"""

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

    def test_angel_success_caches_data(self, sample_df):
        """Test successful Angel One fetch caches data"""
        cache = Mock()
        cache.get_cached_data.return_value = None

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.return_value = sample_df

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=Mock(),
            cache=cache
        )

        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        # Verify data was cached
        cache.cache_data.assert_called_once_with("RELIANCE", "NSE", "1d", sample_df)

    def test_angel_failure_falls_back_to_yahoo(self, sample_df):
        """Test Angel One failure triggers Yahoo Finance fallback"""
        cache = Mock()
        cache.get_cached_data.return_value = None

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.side_effect = Exception("Angel One API error")

        yahoo_fetcher = Mock()
        yahoo_fetcher.fetch_ohlcv.return_value = sample_df

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=yahoo_fetcher,
            cache=cache
        )

        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        assert result.source == "yahoo_finance"
        assert len(result.data) == 1

        # Verify Yahoo was called
        yahoo_fetcher.fetch_ohlcv.assert_called_once()

    def test_angel_rate_limit_falls_back_to_yahoo(self, sample_df):
        """Test Angel One rate limit triggers Yahoo fallback"""
        cache = Mock()
        cache.get_cached_data.return_value = None

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.side_effect = Exception("429 Too Many Requests")

        yahoo_fetcher = Mock()
        yahoo_fetcher.fetch_ohlcv.return_value = sample_df

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=yahoo_fetcher,
            cache=cache
        )

        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        assert result.source == "yahoo_finance"


class TestYahooFallback:
    """Test Yahoo Finance fallback behavior"""

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

    def test_yahoo_success_caches_data(self, sample_df):
        """Test successful Yahoo fetch caches data"""
        cache = Mock()
        cache.get_cached_data.return_value = None

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.side_effect = Exception("Angel error")

        yahoo_fetcher = Mock()
        yahoo_fetcher.fetch_ohlcv.return_value = sample_df

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=yahoo_fetcher,
            cache=cache
        )

        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        # Verify data was cached
        cache.cache_data.assert_called_once_with("RELIANCE", "NSE", "1d", sample_df)

    def test_all_sources_fail_returns_error(self):
        """Test all sources failing returns result with errors"""
        cache = Mock()
        cache.get_cached_data.return_value = None

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.side_effect = Exception("Angel error")

        yahoo_fetcher = Mock()
        yahoo_fetcher.fetch_ohlcv.side_effect = Exception("Yahoo error")

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=yahoo_fetcher,
            cache=cache
        )

        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        assert result.source == "none"
        assert result.data.empty
        assert len(result.errors) > 0


class TestSourceHealth:
    """Test source health tracking"""

    def test_track_source_health(self):
        """Test source health is tracked correctly"""
        cache = Mock()
        cache.get_cached_data.return_value = None

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.side_effect = Exception("Angel error")

        yahoo_fetcher = Mock()
        yahoo_fetcher.fetch_ohlcv.return_value = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=yahoo_fetcher,
            cache=cache
        )

        # Trigger fallback
        fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        # Check health
        health = fallback.get_source_health()

        assert "angel_one" in health
        assert "yahoo_finance" in health

        # Angel One should be unhealthy after failure
        assert health["angel_one"].consecutive_failures >= 1

        # Yahoo should be healthy after success
        assert health["yahoo_finance"].is_healthy is True

    def test_circuit_breaker_skips_unhealthy_source(self):
        """Test circuit breaker skips unhealthy source"""
        cache = Mock()
        cache.get_cached_data.return_value = None

        angel_fetcher = Mock()
        yahoo_fetcher = Mock()
        yahoo_fetcher.fetch_ohlcv.return_value = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=yahoo_fetcher,
            cache=cache
        )

        # Mark Angel One as unhealthy
        fallback.mark_source_unhealthy("angel_one", duration=300)

        # Fetch data
        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        # Should skip Angel One and go directly to Yahoo
        angel_fetcher.fetch_ohlcv.assert_not_called()
        yahoo_fetcher.fetch_ohlcv.assert_called_once()
        assert result.source == "yahoo_finance"


class TestPartialData:
    """Test handling of partial data scenarios"""

    def test_partial_cache_fills_with_api(self):
        """Test partial cache data is filled with API data"""
        # Cache has Jan 1-5
        cached_df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, i), 'open': 100+i, 'high': 105+i, 'low': 95+i, 'close': 102+i, 'volume': 1000}
            for i in range(1, 6)
        ])

        # API has Jan 6-10
        api_df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, i), 'open': 100+i, 'high': 105+i, 'low': 95+i, 'close': 102+i, 'volume': 1000}
            for i in range(6, 11)
        ])

        cache = Mock()
        cache.get_cached_data.return_value = cached_df

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.return_value = api_df

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=Mock(),
            cache=cache
        )

        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 10))

        # Should have combined data
        assert len(result.data) == 10
        assert result.is_partial is False

    def test_merge_partial_results(self):
        """Test merging partial results from multiple sources"""
        # Implementation detail test - verify merge logic
        cache = Mock()
        cache.get_cached_data.return_value = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.return_value = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 2), 'open': 102, 'high': 108, 'low': 100, 'close': 106, 'volume': 1200}
        ])

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=Mock(),
            cache=cache
        )

        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 3))

        # Should merge cache + API data
        assert len(result.data) >= 2
