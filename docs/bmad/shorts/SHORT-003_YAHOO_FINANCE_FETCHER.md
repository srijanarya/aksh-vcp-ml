# SHORT-003: Yahoo Finance Historical Data Fetcher

**Parent**: FX-001 (Data Ingestion)
**Status**: 🟡 In Progress
**Estimated Effort**: 3-4 hours
**TDD Approach**: Red-Green-Refactor

---

## Objective

Implement Yahoo Finance OHLCV data fetcher as a fallback/backup source when Angel One API fails or for additional data verification.

## User Story

**AS A** portfolio manager
**I WANT** a reliable fallback data source
**SO THAT** I can continue operations even if Angel One API is down

## Acceptance Criteria

1. Fetch OHLCV data from Yahoo Finance (via yfinance library)
2. Support NSE/BSE symbols with proper suffix handling (.NS, .BO)
3. Return data in same DataFrame format as Angel One fetcher
4. Handle missing data gracefully
5. Cache responses
6. 100% test coverage

---

## Technical Specification

### Class Design

```python
class YahooFinanceFetcher:
    """
    Fetch historical OHLCV data from Yahoo Finance

    Backup source when Angel One unavailable
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        cache_ttl: int = 3600
    ):
        pass

    def fetch_ohlcv(
        self,
        symbol: str,
        exchange: str,
        from_date: datetime,
        to_date: datetime,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from Yahoo Finance

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            exchange: "NSE" or "BSE"
            from_date: Start date
            to_date: End date
            interval: "1m", "5m", "1h", "1d"

        Returns:
            DataFrame with: timestamp, open, high, low, close, volume
        """
```

---

## TDD Implementation Plan

### Phase 1: RED (Write 15 failing tests)

1. **TestYahooFetcherInitialization** (2 tests)
   - test_fetcher_initialization
   - test_fetcher_with_custom_cache

2. **TestSymbolConversion** (3 tests)
   - test_nse_symbol_conversion
   - test_bse_symbol_conversion
   - test_invalid_exchange_raises_error

3. **TestOHLCVFetching** (6 tests)
   - test_fetch_daily_data_success
   - test_fetch_intraday_data_success
   - test_fetch_invalid_symbol_returns_empty
   - test_fetch_with_date_range
   - test_data_schema_matches_angel_one
   - test_handles_yahoo_api_failure

4. **TestCaching** (2 tests)
   - test_cache_hit
   - test_cache_disabled

5. **TestDataTransformation** (2 tests)
   - test_transforms_to_standard_format
   - test_handles_missing_data

### Phase 2: GREEN (Implement)

### Phase 3: REFACTOR (Improve)

---

## Definition of Done

- ✅ All 15 tests passing
- ✅ 100% code coverage
- ✅ Can fetch data for NSE/BSE symbols
- ✅ Returns data in same format as Angel One
- ✅ Integrated and ready for use as fallback

---

**Created**: 2025-11-19
**Status**: In Progress
