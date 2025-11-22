# SHORT-006: SQLite Data Cache Implementation

**Parent**: FX-001 (Data Ingestion)
**Status**: ✅ Complete
**Estimated Effort**: 4-5 hours
**TDD Approach**: Red-Green-Refactor

---

## Objective

Implement persistent SQLite-based caching for OHLCV data to reduce API calls and improve performance.

## User Story

**AS A** portfolio manager
**I WANT** historical data cached locally
**SO THAT** I minimize API calls and get faster data retrieval

## Acceptance Criteria

1. Store OHLCV data in SQLite database
2. Cache data with TTL (configurable)
3. Query cached data by symbol, exchange, timeframe, date range
4. Automatically invalidate stale cache entries
5. Support bulk insert for efficient caching
6. Handle database migrations/schema updates
7. 100% test coverage

---

## Technical Specification

### Database Schema

```sql
CREATE TABLE ohlcv_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    interval TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, exchange, interval, timestamp)
);

CREATE INDEX idx_symbol_exchange_interval
ON ohlcv_data(symbol, exchange, interval);

CREATE INDEX idx_timestamp
ON ohlcv_data(timestamp);
```

### Class Design

```python
class SQLiteDataCache:
    """
    SQLite-based persistent cache for OHLCV data
    """

    def __init__(
        self,
        db_path: str = "/tmp/ohlcv_cache.db",
        ttl_seconds: int = 3600
    ):
        pass

    def get_cached_data(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        from_date: datetime,
        to_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve cached OHLCV data

        Returns None if data not in cache or stale
        """

    def cache_data(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        df: pd.DataFrame
    ):
        """Store OHLCV data in cache"""

    def invalidate_cache(
        self,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        before_date: Optional[datetime] = None
    ):
        """Invalidate cache entries based on filters"""

    def get_cache_stats(self) -> Dict:
        """Get cache statistics (hit rate, size, etc.)"""

    def cleanup_stale_entries(self):
        """Remove entries older than TTL"""
```

---

## TDD Implementation Plan

### Phase 1: RED (Write 16 failing tests)

1. **TestCacheInitialization** (2 tests)
   - test_cache_initialization_default
   - test_cache_initialization_custom_path

2. **TestDataStorage** (4 tests)
   - test_cache_single_symbol_data
   - test_cache_multiple_symbols
   - test_cache_overwrites_duplicate_timestamps
   - test_bulk_insert_performance

3. **TestDataRetrieval** (4 tests)
   - test_get_cached_data_exact_match
   - test_get_cached_data_partial_range
   - test_get_cached_data_no_match
   - test_get_stale_data_returns_none

4. **TestCacheInvalidation** (3 tests)
   - test_invalidate_by_symbol
   - test_invalidate_by_date
   - test_invalidate_all

5. **TestCacheManagement** (3 tests)
   - test_cleanup_stale_entries
   - test_get_cache_stats
   - test_database_schema_created

### Phase 2: GREEN (Implement)

### Phase 3: REFACTOR (Improve)

---

## Definition of Done

- ✅ All 19 tests passing (16 main + 3 edge cases)
- ✅ 100% code coverage
- ✅ SQLite database with proper indexes
- ✅ TTL-based cache invalidation
- ✅ Efficient bulk operations

---

**Created**: 2025-11-19
**Completed**: 2025-11-19
**Status**: Complete
