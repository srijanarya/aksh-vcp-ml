"""
Edge cases for SQLite Data Cache to reach 100% coverage
"""

import pytest
import pandas as pd
import sqlite3
from datetime import datetime
from src.data.sqlite_data_cache import SQLiteDataCache


class TestEdgeCases:
    """Test edge cases for 100% coverage"""

    def test_get_cached_data_exception(self, tmp_path):
        """Test retrieving data when database error occurs"""
        cache = SQLiteDataCache(db_path=str(tmp_path / "test_cache.db"))

        # Corrupt the database to trigger exception
        conn = sqlite3.connect(cache.db_path)
        conn.execute("DROP TABLE ohlcv_data")
        conn.close()

        # Should return None on error
        result = cache.get_cached_data(
            "RELIANCE",
            "NSE",
            "5m",
            datetime(2025, 1, 1),
            datetime(2025, 1, 2)
        )

        assert result is None

    def test_cache_data_exception(self, tmp_path):
        """Test caching data when database error occurs"""
        cache = SQLiteDataCache(db_path=str(tmp_path / "test_cache.db"))

        # Corrupt the database to trigger exception
        conn = sqlite3.connect(cache.db_path)
        conn.execute("DROP TABLE ohlcv_data")
        conn.close()

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

        # Should not raise exception, just log error
        cache.cache_data("RELIANCE", "NSE", "5m", df)

    def test_invalidate_cache_symbol_and_exchange(self, tmp_path):
        """Test invalidating cache with both symbol and exchange filters"""
        cache = SQLiteDataCache(db_path=str(tmp_path / "test_cache.db"))

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000}
        ])

        cache.cache_data("RELIANCE", "NSE", "5m", df)
        cache.cache_data("RELIANCE", "BSE", "5m", df)
        cache.cache_data("TCS", "NSE", "5m", df)

        # Invalidate only RELIANCE on NSE
        cache.invalidate_cache(symbol="RELIANCE", exchange="NSE")

        # Check that only RELIANCE-NSE was invalidated
        reliance_nse = cache.get_cached_data("RELIANCE", "NSE", "5m", datetime(2025, 1, 1), datetime(2025, 1, 2))
        reliance_bse = cache.get_cached_data("RELIANCE", "BSE", "5m", datetime(2025, 1, 1), datetime(2025, 1, 2))
        tcs_nse = cache.get_cached_data("TCS", "NSE", "5m", datetime(2025, 1, 1), datetime(2025, 1, 2))

        assert reliance_nse is None  # Invalidated
        assert reliance_bse is not None  # Still cached
        assert tcs_nse is not None  # Still cached
