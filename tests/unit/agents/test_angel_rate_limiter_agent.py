"""
Unit Tests for Angel One Rate Limiter Agent

Tests the cache-first data fetching strategy with rate limiting and exponential backoff.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.data.angel_rate_limiter_agent import AngelOneRateLimiterAgent


class TestAngelRateLimiterAgentInitialization:
    """Test agent initialization"""

    def test_initialization_without_client(self):
        """Test agent can be initialized without client"""
        agent = AngelOneRateLimiterAgent(client=None)

        assert agent.client is None
        assert agent.cache_tool is not None
        assert agent.backoff_tool is not None
        assert agent.nifty_tool is not None
        assert agent.ohlcv_fetcher is None  # No client, so no fetcher

    def test_initialization_with_mock_client(self):
        """Test agent initializes with mock client"""
        mock_client = Mock()
        mock_client.is_authenticated = True

        with patch('agents.data.angel_rate_limiter_agent.AngelOneOHLCVFetcher'):
            agent = AngelOneRateLimiterAgent(client=mock_client)

            assert agent.client is mock_client
            assert agent.cache_tool is not None

    def test_custom_cache_ttl(self):
        """Test agent respects custom cache TTL"""
        agent = AngelOneRateLimiterAgent(client=None, cache_ttl_hours=12)

        assert agent.cache_tool.ttl_hours == 12

    def test_custom_max_retries(self):
        """Test agent respects custom max retries"""
        agent = AngelOneRateLimiterAgent(client=None, max_retries=3)

        assert agent.max_retries == 3


class TestStatisticsTracking:
    """Test statistics tracking functionality"""

    def test_initial_stats(self):
        """Test initial statistics are zero"""
        agent = AngelOneRateLimiterAgent(client=None)
        stats = agent.get_stats()

        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        assert stats['api_calls'] == 0
        assert stats['failed_api_calls'] == 0
        assert stats['total_requests'] == 0
        assert stats['cache_hit_rate'] == 0

    def test_stats_reset(self):
        """Test statistics can be reset"""
        agent = AngelOneRateLimiterAgent(client=None)

        # Manually set some stats
        agent.stats['cache_hits'] = 10
        agent.stats['api_calls'] = 5

        # Reset
        agent.reset_stats()

        # Verify reset
        stats = agent.get_stats()
        assert stats['cache_hits'] == 0
        assert stats['api_calls'] == 0


class TestCacheInteraction:
    """Test cache tool interaction"""

    def test_cache_hit_increments_stats(self):
        """Test cache hit increments cache_hits stat"""
        agent = AngelOneRateLimiterAgent(client=None)

        # Mock cache tool to return data
        mock_data = pd.DataFrame({
            'timestamp': [datetime.now()],
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [102],
            'volume': [1000000]
        })

        agent.cache_tool.get_cached_ohlcv = Mock(return_value=mock_data)

        # Fetch (should hit cache)
        result = agent.fetch_with_cache(
            symbol='TEST',
            exchange='NSE',
            interval='ONE_DAY',
            from_date=datetime.now() - timedelta(days=30),
            to_date=datetime.now()
        )

        # Verify
        assert result is not None
        assert agent.stats['cache_hits'] == 1
        assert agent.stats['cache_misses'] == 0

    def test_cache_miss_increments_stats(self):
        """Test cache miss increments cache_misses stat"""
        agent = AngelOneRateLimiterAgent(client=None)

        # Mock cache miss
        agent.cache_tool.get_cached_ohlcv = Mock(return_value=None)

        # Fetch (should miss cache, but fail due to no fetcher)
        result = agent.fetch_with_cache(
            symbol='TEST',
            exchange='NSE',
            interval='ONE_DAY',
            from_date=datetime.now() - timedelta(days=30),
            to_date=datetime.now()
        )

        # Verify
        assert result is None  # Failed due to no fetcher
        assert agent.stats['cache_misses'] == 1


class TestForceRefresh:
    """Test force refresh functionality"""

    def test_force_refresh_bypasses_cache(self):
        """Test force_refresh=True bypasses cache"""
        agent = AngelOneRateLimiterAgent(client=None)

        # Mock cache to return data
        mock_data = pd.DataFrame({'timestamp': [datetime.now()]})
        agent.cache_tool.get_cached_ohlcv = Mock(return_value=mock_data)

        # Fetch with force_refresh (should NOT call cache)
        result = agent.fetch_with_cache(
            symbol='TEST',
            exchange='NSE',
            interval='ONE_DAY',
            from_date=datetime.now() - timedelta(days=30),
            to_date=datetime.now(),
            force_refresh=True
        )

        # Verify cache was NOT called
        agent.cache_tool.get_cached_ohlcv.assert_not_called()


class TestBatchFetching:
    """Test batch fetching functionality"""

    def test_fetch_batch_returns_dict(self):
        """Test fetch_batch returns dictionary"""
        agent = AngelOneRateLimiterAgent(client=None)

        # Mock successful cache hits
        mock_data = pd.DataFrame({
            'timestamp': [datetime.now()],
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [102],
            'volume': [1000000]
        })

        agent.cache_tool.get_cached_ohlcv = Mock(return_value=mock_data)

        # Fetch batch
        symbols = ['SYM1', 'SYM2', 'SYM3']
        results = agent.fetch_batch(symbols=symbols)

        # Verify
        assert isinstance(results, dict)
        assert len(results) == 3
        assert all(symbol in results for symbol in symbols)

    def test_fetch_batch_handles_failures(self):
        """Test fetch_batch handles individual failures gracefully"""
        agent = AngelOneRateLimiterAgent(client=None)

        # Mock: first returns data, second returns None, third returns data
        call_count = [0]

        def mock_fetch(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                return None  # Fail second call
            return pd.DataFrame({'timestamp': [datetime.now()]})

        agent.cache_tool.get_cached_ohlcv = Mock(side_effect=mock_fetch)

        # Fetch batch
        results = agent.fetch_batch(symbols=['SYM1', 'SYM2', 'SYM3'])

        # Verify: should have 2 results (SYM2 failed)
        assert len(results) == 2


class TestNifty50CacheWarming:
    """Test Nifty 50 cache warming"""

    def test_warm_nifty_50_returns_stats(self):
        """Test warm_nifty_50_cache returns statistics"""
        agent = AngelOneRateLimiterAgent(client=None)

        # Mock cache hits for all 50
        mock_data = pd.DataFrame({'timestamp': [datetime.now()]})
        agent.cache_tool.get_cached_ohlcv = Mock(return_value=mock_data)

        # Warm cache
        stats = agent.warm_nifty_50_cache()

        # Verify
        assert 'total_symbols' in stats
        assert 'successful' in stats
        assert 'failed' in stats
        assert stats['total_symbols'] == 50

    def test_warm_nifty_50_uses_nifty_tool(self):
        """Test warming uses Nifty tool for constituent list"""
        agent = AngelOneRateLimiterAgent(client=None)

        # Mock
        agent.nifty_tool.get_nifty_50_constituents = Mock(return_value=['SYM1', 'SYM2'])
        agent.cache_tool.get_cached_ohlcv = Mock(return_value=pd.DataFrame({'timestamp': [datetime.now()]}))

        # Warm
        stats = agent.warm_nifty_50_cache()

        # Verify nifty tool was called
        agent.nifty_tool.get_nifty_50_constituents.assert_called_once()
        assert stats['total_symbols'] == 2  # Only 2 mocked symbols


class TestErrorHandling:
    """Test error handling"""

    def test_handles_cache_tool_errors(self):
        """Test agent handles cache tool errors gracefully"""
        agent = AngelOneRateLimiterAgent(client=None)

        # Mock cache to raise exception
        agent.cache_tool.get_cached_ohlcv = Mock(side_effect=Exception("Cache error"))

        # Should not crash, should return None
        result = agent.fetch_with_cache(
            symbol='TEST',
            exchange='NSE',
            interval='ONE_DAY',
            from_date=datetime.now() - timedelta(days=30),
            to_date=datetime.now()
        )

        # Agent should handle error and try API (which will also fail due to no client)
        # Result should be None, not an exception
        assert result is None

    def test_handles_empty_symbol_list(self):
        """Test batch fetch handles empty symbol list"""
        agent = AngelOneRateLimiterAgent(client=None)

        results = agent.fetch_batch(symbols=[])

        assert results == {}


class TestCacheHitRateCalculation:
    """Test cache hit rate calculation"""

    def test_cache_hit_rate_with_hits(self):
        """Test cache hit rate is calculated correctly"""
        agent = AngelOneRateLimiterAgent(client=None)

        # Simulate 8 hits, 2 misses
        agent.stats['cache_hits'] = 8
        agent.stats['cache_misses'] = 2

        stats = agent.get_stats()

        assert stats['total_requests'] == 10
        assert stats['cache_hit_rate'] == 80.0

    def test_cache_hit_rate_with_zero_requests(self):
        """Test cache hit rate is 0 with no requests"""
        agent = AngelOneRateLimiterAgent(client=None)

        stats = agent.get_stats()

        assert stats['cache_hit_rate'] == 0


# Integration-style test (requires actual components)
@pytest.mark.skip(reason="Requires Angel One credentials and real API")
class TestIntegration:
    """Integration tests (skipped in CI)"""

    def test_real_fetch_with_caching(self):
        """Test real API fetch with caching"""
        from src.data.angel_one_client import AngelOneClient

        client = AngelOneClient()
        if not client.authenticate():
            pytest.skip("Authentication failed")

        agent = AngelOneRateLimiterAgent(client=client)

        # First fetch (cache miss)
        data1 = agent.fetch_with_cache(
            symbol='RELIANCE',
            exchange='NSE',
            interval='ONE_DAY',
            from_date=datetime.now() - timedelta(days=30),
            to_date=datetime.now()
        )

        # Second fetch (cache hit)
        data2 = agent.fetch_with_cache(
            symbol='RELIANCE',
            exchange='NSE',
            interval='ONE_DAY',
            from_date=datetime.now() - timedelta(days=30),
            to_date=datetime.now()
        )

        # Verify
        assert data1 is not None
        assert data2 is not None
        assert len(data1) == len(data2)

        # Check stats
        stats = agent.get_stats()
        assert stats['cache_hits'] == 1
        assert stats['api_calls'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
