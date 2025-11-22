"""
Edge cases for Data Source Fallback to reach 100% coverage
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock
from src.data.data_source_fallback import DataSourceFallback


class TestEdgeCases:
    """Test edge cases for 100% coverage"""

    def test_empty_angel_data_falls_back_to_yahoo(self):
        """Test empty Angel One response triggers Yahoo fallback"""
        cache = Mock()
        cache.get_cached_data.return_value = None

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.return_value = pd.DataFrame()  # Empty

        yahoo_fetcher = Mock()
        yahoo_fetcher.fetch_ohlcv.return_value = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=yahoo_fetcher,
            cache=cache
        )

        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        assert result.source == "yahoo_finance"

    def test_empty_yahoo_data_returns_none_source(self):
        """Test empty Yahoo response after Angel failure"""
        cache = Mock()
        cache.get_cached_data.return_value = None

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.side_effect = Exception("Angel error")

        yahoo_fetcher = Mock()
        yahoo_fetcher.fetch_ohlcv.return_value = pd.DataFrame()  # Empty

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=yahoo_fetcher,
            cache=cache
        )

        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        assert result.source == "none"
        assert result.data.empty

    def test_circuit_breaker_expires_and_resets(self):
        """Test circuit breaker expiration resets health"""
        import time
        from datetime import timedelta

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

        # Mark unhealthy with 1 second duration
        fallback.mark_source_unhealthy("angel_one", duration=1)

        # Should skip Angel One initially
        health = fallback.get_source_health()
        assert health["angel_one"].is_healthy is False

        # Wait for circuit breaker to expire
        time.sleep(2)

        # Fetch should reset circuit breaker
        result = fallback.fetch_ohlcv("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        # Check health updated (circuit breaker expired)
        health_after = fallback.get_source_health()
        assert health_after["angel_one"].unhealthy_until is None

    def test_interval_conversion(self):
        """Test interval conversion for Yahoo Finance"""
        cache = Mock()
        cache.get_cached_data.return_value = None

        angel_fetcher = Mock()
        angel_fetcher.fetch_ohlcv.side_effect = Exception("Error")

        yahoo_fetcher = Mock()
        yahoo_fetcher.fetch_ohlcv.return_value = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

        fallback = DataSourceFallback(
            angel_fetcher=angel_fetcher,
            yahoo_fetcher=yahoo_fetcher,
            cache=cache
        )

        # Test with Angel One format interval
        fallback.fetch_ohlcv("RELIANCE", "NSE", "ONE_DAY", datetime(2025, 1, 1), datetime(2025, 1, 2))

        # Verify Yahoo was called with converted interval
        yahoo_fetcher.fetch_ohlcv.assert_called_once()
        call_kwargs = yahoo_fetcher.fetch_ohlcv.call_args[1]
        assert call_kwargs['interval'] == "1d"
