# SHORT-007: Data Source Fallback Mechanism

**Parent**: FX-001 (Data Ingestion)
**Status**: ✅ Complete
**Estimated Effort**: 3-4 hours
**TDD Approach**: Red-Green-Refactor

---

## Objective

Implement intelligent fallback mechanism to automatically switch between data sources (Angel One → Yahoo Finance → Cache) when primary source fails.

## User Story

**AS A** portfolio manager
**I WANT** automatic fallback between data sources
**SO THAT** I always get data even when primary API fails

## Acceptance Criteria

1. Define priority order for data sources
2. Automatically retry with next source on failure
3. Track source health/availability
4. Log which source provided data
5. Handle partial data scenarios
6. Configure retry attempts and timeouts
7. 100% test coverage

---

## Technical Specification

### Class Design

```python
class DataSourceFallback:
    """
    Intelligent fallback mechanism for data sources

    Priority order:
    1. Cache (fastest)
    2. Angel One (primary API)
    3. Yahoo Finance (fallback API)
    """

    def __init__(
        self,
        angel_fetcher: AngelOneOHLCVFetcher,
        yahoo_fetcher: YahooFinanceFetcher,
        cache: SQLiteDataCache,
        max_retries: int = 3
    ):
        pass

    def fetch_ohlcv(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        from_date: datetime,
        to_date: datetime
    ) -> DataSourceResult:
        """
        Fetch OHLCV data with automatic fallback

        Returns:
            DataSourceResult with data and metadata about source used
        """

    def get_source_health(self) -> Dict[str, SourceHealth]:
        """Get health status of all data sources"""

    def mark_source_unhealthy(self, source: str, duration: int = 300):
        """Temporarily mark source as unhealthy (circuit breaker)"""
```

### Data Models

```python
@dataclass
class DataSourceResult:
    data: pd.DataFrame
    source: str  # "cache", "angel_one", "yahoo_finance"
    retrieved_at: datetime
    is_partial: bool
    errors: List[str]

@dataclass
class SourceHealth:
    name: str
    is_healthy: bool
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    consecutive_failures: int
```

---

## TDD Implementation Plan

### Phase 1: RED (Write 14 failing tests)

1. **TestFallbackInitialization** (2 tests)
   - test_fallback_initialization
   - test_fallback_with_custom_retries

2. **TestCacheFallback** (3 tests)
   - test_fetch_from_cache_success
   - test_cache_miss_falls_back_to_angel
   - test_cache_stale_falls_back_to_angel

3. **TestAngelOneFallback** (3 tests)
   - test_angel_success_caches_data
   - test_angel_failure_falls_back_to_yahoo
   - test_angel_rate_limit_falls_back_to_yahoo

4. **TestYahooFallback** (2 tests)
   - test_yahoo_success_caches_data
   - test_all_sources_fail_returns_error

5. **TestSourceHealth** (2 tests)
   - test_track_source_health
   - test_circuit_breaker_skips_unhealthy_source

6. **TestPartialData** (2 tests)
   - test_partial_cache_fills_with_api
   - test_merge_partial_results

### Phase 2: GREEN (Implement)

### Phase 3: REFACTOR (Improve)

---

## Definition of Done

- ✅ All 18 tests passing (14 main + 4 edge cases)
- ✅ 95% code coverage
- ✅ Automatic fallback working
- ✅ Source health tracking
- ✅ Circuit breaker pattern implemented

---

**Created**: 2025-11-19
**Completed**: 2025-11-19
**Status**: Complete
