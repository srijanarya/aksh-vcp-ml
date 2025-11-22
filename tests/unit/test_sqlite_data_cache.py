"""
Tests for SQLite Data Cache

TDD Approach: RED Phase - All tests will fail initially
"""

import pytest
import pandas as pd
import os
import sqlite3
from datetime import datetime, timedelta
from src.data.sqlite_data_cache import SQLiteDataCache


class TestCacheInitialization:
    """Test cache initialization"""

    def test_cache_initialization_default(self):
        """Test cache with default database path"""
        cache = SQLiteDataCache()
        assert cache.db_path is not None
        assert os.path.exists(cache.db_path)
        assert cache.ttl_seconds == 3600

    def test_cache_initialization_custom_path(self, tmp_path):
        """Test cache with custom database path"""
        db_path = str(tmp_path / "custom_cache.db")
        cache = SQLiteDataCache(db_path=db_path, ttl_seconds=7200)
        assert cache.db_path == db_path
        assert os.path.exists(db_path)
        assert cache.ttl_seconds == 7200


class TestDataStorage:
    """Test storing data in cache"""

    @pytest.fixture
    def cache(self, tmp_path):
        return SQLiteDataCache(db_path=str(tmp_path / "test_cache.db"))

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1, 9, 15),
                'open': 100,
                'high': 105,
                'low': 95,
                'close': 102,
                'volume': 1000
            },
            {
                'timestamp': datetime(2025, 1, 1, 9, 20),
                'open': 102,
                'high': 108,
                'low': 100,
                'close': 106,
                'volume': 1200
            }
        ])

    def test_cache_single_symbol_data(self, cache, sample_df):
        """Test caching data for single symbol"""
        cache.cache_data("RELIANCE", "NSE", "5m", sample_df)

        # Verify data was stored
        cached = cache.get_cached_data(
            "RELIANCE",
            "NSE",
            "5m",
            datetime(2025, 1, 1),
            datetime(2025, 1, 2)
        )

        assert cached is not None
        assert len(cached) == 2
        assert cached.iloc[0]['close'] == 102

    def test_cache_multiple_symbols(self, cache, sample_df):
        """Test caching data for multiple symbols"""
        cache.cache_data("RELIANCE", "NSE", "5m", sample_df)
        cache.cache_data("TCS", "NSE", "5m", sample_df)

        reliance_data = cache.get_cached_data("RELIANCE", "NSE", "5m", datetime(2025, 1, 1), datetime(2025, 1, 2))
        tcs_data = cache.get_cached_data("TCS", "NSE", "5m", datetime(2025, 1, 1), datetime(2025, 1, 2))

        assert reliance_data is not None
        assert tcs_data is not None
        assert len(reliance_data) == 2
        assert len(tcs_data) == 2

    def test_cache_overwrites_duplicate_timestamps(self, cache):
        """Test that caching same data twice updates instead of duplicating"""
        df1 = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 15), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

        df2 = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 15), 'open': 101, 'high': 106, 'low': 96, 'close': 103, 'volume': 1100}
        ])

        cache.cache_data("RELIANCE", "NSE", "5m", df1)
        cache.cache_data("RELIANCE", "NSE", "5m", df2)

        cached = cache.get_cached_data("RELIANCE", "NSE", "5m", datetime(2025, 1, 1), datetime(2025, 1, 2))

        # Should have only 1 row (updated)
        assert len(cached) == 1
        assert cached.iloc[0]['close'] == 103  # Updated value

    def test_bulk_insert_performance(self, cache):
        """Test bulk insert of large dataset"""
        # Create 1000 rows
        rows = [
            {
                'timestamp': datetime(2025, 1, 1) + timedelta(minutes=i*5),
                'open': 100 + i,
                'high': 105 + i,
                'low': 95 + i,
                'close': 102 + i,
                'volume': 1000 + i*10
            }
            for i in range(1000)
        ]
        df = pd.DataFrame(rows)

        cache.cache_data("RELIANCE", "NSE", "5m", df)

        cached = cache.get_cached_data("RELIANCE", "NSE", "5m", datetime(2025, 1, 1), datetime(2025, 1, 10))

        assert len(cached) == 1000


class TestDataRetrieval:
    """Test retrieving data from cache"""

    @pytest.fixture
    def cache_with_data(self, tmp_path):
        cache = SQLiteDataCache(db_path=str(tmp_path / "test_cache.db"), ttl_seconds=3600)

        # Cache some data
        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1, 9, 15), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000},
            {'timestamp': datetime(2025, 1, 1, 9, 20), 'open': 102, 'high': 108, 'low': 100, 'close': 106, 'volume': 1200},
            {'timestamp': datetime(2025, 1, 2, 9, 15), 'open': 106, 'high': 112, 'low': 104, 'close': 110, 'volume': 1100},
        ])
        cache.cache_data("RELIANCE", "NSE", "5m", df)

        return cache

    def test_get_cached_data_exact_match(self, cache_with_data):
        """Test retrieving exact date range"""
        cached = cache_with_data.get_cached_data(
            "RELIANCE",
            "NSE",
            "5m",
            datetime(2025, 1, 1),
            datetime(2025, 1, 3)
        )

        assert cached is not None
        assert len(cached) == 3

    def test_get_cached_data_partial_range(self, cache_with_data):
        """Test retrieving partial date range"""
        cached = cache_with_data.get_cached_data(
            "RELIANCE",
            "NSE",
            "5m",
            datetime(2025, 1, 1, 9, 0),
            datetime(2025, 1, 1, 10, 0)
        )

        assert cached is not None
        assert len(cached) == 2  # Only Jan 1 data

    def test_get_cached_data_no_match(self, cache_with_data):
        """Test retrieving non-existent data"""
        cached = cache_with_data.get_cached_data(
            "TCS",  # Different symbol
            "NSE",
            "5m",
            datetime(2025, 1, 1),
            datetime(2025, 1, 2)
        )

        assert cached is None

    def test_get_stale_data_returns_none(self, tmp_path):
        """Test that stale data returns None"""
        cache = SQLiteDataCache(db_path=str(tmp_path / "test_cache.db"), ttl_seconds=1)

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

        cache.cache_data("RELIANCE", "NSE", "1d", df)

        # Wait for TTL to expire
        import time
        time.sleep(2)

        cached = cache.get_cached_data("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 2))

        assert cached is None  # Stale data should not be returned


class TestCacheInvalidation:
    """Test cache invalidation"""

    @pytest.fixture
    def cache_with_data(self, tmp_path):
        cache = SQLiteDataCache(db_path=str(tmp_path / "test_cache.db"))

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000},
            {'timestamp': datetime(2025, 1, 2), 'open': 102, 'high': 108, 'low': 100, 'close': 106, 'volume': 1200},
        ])

        cache.cache_data("RELIANCE", "NSE", "1d", df)
        cache.cache_data("TCS", "NSE", "1d", df)

        return cache

    def test_invalidate_by_symbol(self, cache_with_data):
        """Test invalidating cache for specific symbol"""
        cache_with_data.invalidate_cache(symbol="RELIANCE")

        reliance_data = cache_with_data.get_cached_data("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 3))
        tcs_data = cache_with_data.get_cached_data("TCS", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 3))

        assert reliance_data is None  # Invalidated
        assert tcs_data is not None  # Still cached

    def test_invalidate_by_date(self, cache_with_data):
        """Test invalidating cache before specific date"""
        cache_with_data.invalidate_cache(before_date=datetime(2025, 1, 1, 12, 0))

        # Manually check database
        conn = sqlite3.connect(cache_with_data.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ohlcv_data WHERE timestamp < ?", (datetime(2025, 1, 1, 12, 0),))
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 0  # Data before Jan 1 12:00 should be deleted

    def test_invalidate_all(self, cache_with_data):
        """Test invalidating entire cache"""
        cache_with_data.invalidate_cache()

        reliance_data = cache_with_data.get_cached_data("RELIANCE", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 3))
        tcs_data = cache_with_data.get_cached_data("TCS", "NSE", "1d", datetime(2025, 1, 1), datetime(2025, 1, 3))

        assert reliance_data is None
        assert tcs_data is None


class TestCacheManagement:
    """Test cache management operations"""

    @pytest.fixture
    def cache(self, tmp_path):
        return SQLiteDataCache(db_path=str(tmp_path / "test_cache.db"), ttl_seconds=2)

    def test_cleanup_stale_entries(self, cache):
        """Test cleaning up stale cache entries"""
        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

        cache.cache_data("RELIANCE", "NSE", "1d", df)

        # Wait for TTL to expire
        import time
        time.sleep(3)

        # Run cleanup
        cache.cleanup_stale_entries()

        # Manually check database
        conn = sqlite3.connect(cache.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ohlcv_data")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 0  # All stale entries cleaned up

    def test_get_cache_stats(self, cache):
        """Test getting cache statistics"""
        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, i), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
            for i in range(1, 11)
        ])

        cache.cache_data("RELIANCE", "NSE", "1d", df)
        cache.cache_data("TCS", "NSE", "1d", df)

        stats = cache.get_cache_stats()

        assert stats['total_rows'] == 20
        assert stats['unique_symbols'] == 2
        assert 'db_size_kb' in stats

    def test_database_schema_created(self, cache):
        """Test that database schema is created properly"""
        conn = sqlite3.connect(cache.db_path)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ohlcv_data'")
        assert cursor.fetchone() is not None

        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ohlcv_data'")
        indexes = cursor.fetchall()
        assert len(indexes) >= 2  # At least 2 indexes

        conn.close()
