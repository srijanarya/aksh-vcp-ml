# SHORT-002: Angel One OHLCV Data Fetcher

**Parent**: FX-001 (Data Ingestion)
**Status**: 🟡 Ready for Implementation
**Estimated Effort**: 4-6 hours
**TDD Approach**: Red-Green-Refactor

---

## Objective

Implement OHLCV (Open, High, Low, Close, Volume) historical data fetcher from Angel One SmartAPI with comprehensive test coverage.

## User Story

**AS A** portfolio manager
**I WANT** to fetch reliable historical OHLCV data from Angel One
**SO THAT** I can backtest strategies and calculate technical indicators

## Acceptance Criteria

### Functional Requirements

1. **Historical Data Fetching**
   - Fetch OHLCV data for any NSE/BSE symbol
   - Support multiple timeframes: 1min, 5min, 15min, 1hour, 1day
   - Date range support (from_date, to_date)
   - Automatic pagination for large datasets

2. **Data Quality**
   - Validate OHLC relationships (High ≥ Close ≥ Low, High ≥ Open ≥ Low)
   - Detect and flag missing data gaps
   - Handle corporate actions (splits, bonuses) via adjustment flags
   - Return pandas DataFrame with standardized schema

3. **Error Handling**
   - Handle invalid symbols gracefully
   - Retry on rate limits (429) with exponential backoff
   - Handle token expiry and auto-refresh
   - Clear error messages for debugging

4. **Performance**
   - Cache responses locally (configurable TTL)
   - Batch requests when possible
   - Rate limiting (3 requests/second as per Angel One limits)

### Non-Functional Requirements

- **Test Coverage**: 100% (critical component)
- **Response Time**: < 2 seconds for 1 year daily data
- **Reliability**: Automatic retry on transient failures
- **Maintainability**: Clean separation of API logic and data transformation

---

## Technical Specification

### File Structure

```
src/data/
  angel_one_client.py       # Existing auth client
  angel_one_ohlcv.py         # NEW: OHLCV fetcher

tests/unit/
  test_angel_one_auth.py    # Existing (21 tests)
  test_angel_one_ohlcv.py    # NEW: OHLCV tests
```

### Class Design

```python
class AngelOneOHLCVFetcher:
    """
    Fetch historical OHLCV data from Angel One SmartAPI

    Attributes:
        client: AngelOneClient (authenticated)
        cache_dir: Path to cache directory
        rate_limiter: RateLimiter (3 req/sec)
    """

    def __init__(
        self,
        client: AngelOneClient,
        cache_dir: Optional[str] = None,
        cache_ttl: int = 3600,  # 1 hour default
    ):
        """Initialize OHLCV fetcher"""

    def fetch_ohlcv(
        self,
        symbol: str,
        exchange: str,  # "NSE" or "BSE"
        interval: str,  # "ONE_DAY", "ONE_HOUR", "FIVE_MINUTE"
        from_date: datetime,
        to_date: datetime,
        token: Optional[str] = None,  # Angel One symbol token
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data

        Returns:
            DataFrame with columns:
            - timestamp (datetime)
            - open (float)
            - high (float)
            - low (float)
            - close (float)
            - volume (int)

        Raises:
            ValueError: Invalid symbol or date range
            AuthenticationError: Client not authenticated
            RateLimitError: Rate limit exceeded
            DataQualityError: Invalid OHLC data received
        """

    def get_symbol_token(
        self,
        symbol: str,
        exchange: str
    ) -> str:
        """
        Get Angel One symbol token (required for API calls)

        Example: "RELIANCE" on NSE → "2885"
        """

    def validate_ohlc(
        self,
        df: pd.DataFrame
    ) -> Tuple[bool, List[str]]:
        """
        Validate OHLC data quality

        Returns:
            (is_valid, error_messages)
        """
```

### Angel One API Integration

**API Endpoint**: `getCandleData`

**Request Format**:
```python
{
    "exchange": "NSE",
    "symboltoken": "2885",  # Token for RELIANCE
    "interval": "ONE_DAY",
    "fromdate": "2023-01-01 09:15",
    "todate": "2024-01-01 15:30"
}
```

**Response Format**:
```python
{
    "status": true,
    "message": "SUCCESS",
    "data": [
        ["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000],
        # [timestamp, open, high, low, close, volume]
    ]
}
```

### Data Validation Rules

1. **OHLC Relationships**:
   - `high >= max(open, close)`
   - `low <= min(open, close)`
   - All values > 0

2. **Volume Validation**:
   - Volume >= 0 (can be 0 for illiquid stocks)

3. **Timestamp Validation**:
   - Timestamps in chronological order
   - No duplicates
   - Within market hours (9:15 AM - 3:30 PM IST)

4. **Gap Detection**:
   - Flag missing dates (exclude weekends/holidays)
   - Warn on large price jumps (> 20% in 1 day)

---

## TDD Implementation Plan

### Phase 1: RED (Write Failing Tests) - 1 hour

**Test File**: `tests/unit/test_angel_one_ohlcv.py`

#### Test Classes:

1. **TestOHLCVFetcherInitialization** (3 tests)
   - test_fetcher_initialization_with_authenticated_client
   - test_fetcher_initialization_with_unauthenticated_client_raises_error
   - test_fetcher_initialization_with_custom_cache_settings

2. **TestSymbolTokenLookup** (4 tests)
   - test_get_symbol_token_for_nse_stock
   - test_get_symbol_token_for_bse_stock
   - test_get_symbol_token_invalid_symbol_raises_error
   - test_get_symbol_token_caching

3. **TestOHLCVFetching** (8 tests)
   - test_fetch_daily_ohlcv_success
   - test_fetch_intraday_5min_ohlcv_success
   - test_fetch_with_date_range
   - test_fetch_invalid_symbol_raises_error
   - test_fetch_invalid_date_range_raises_error
   - test_fetch_unauthenticated_raises_error
   - test_fetch_rate_limit_retry
   - test_fetch_token_expiry_auto_refresh

4. **TestDataValidation** (6 tests)
   - test_validate_ohlc_valid_data
   - test_validate_ohlc_invalid_high_low_relationship
   - test_validate_ohlc_negative_prices
   - test_validate_ohlc_missing_columns
   - test_detect_data_gaps
   - test_detect_large_price_jumps

5. **TestCaching** (4 tests)
   - test_cache_hit_avoids_api_call
   - test_cache_miss_makes_api_call
   - test_cache_ttl_expiry
   - test_cache_disabled

6. **TestRateLimiting** (3 tests)
   - test_rate_limiter_respects_3_req_per_second
   - test_rate_limiter_429_triggers_backoff
   - test_rate_limiter_concurrent_requests

**Total Tests**: 28 tests (all failing initially)

### Phase 2: GREEN (Make Tests Pass) - 3 hours

#### Step 1: Basic Structure (30 min)
- Create `angel_one_ohlcv.py`
- Implement `__init__` method
- Pass initialization tests

#### Step 2: Symbol Token Lookup (45 min)
- Implement `get_symbol_token()`
- Use Angel One master symbol list API
- Cache token mappings
- Pass symbol token tests

#### Step 3: Core OHLCV Fetching (90 min)
- Implement `fetch_ohlcv()`
- Handle API request/response
- Transform to pandas DataFrame
- Pass fetching tests

#### Step 4: Data Validation (30 min)
- Implement `validate_ohlc()`
- Add OHLC relationship checks
- Gap detection logic
- Pass validation tests

#### Step 5: Caching & Rate Limiting (30 min)
- Implement cache layer
- Add rate limiter
- Handle retries
- Pass caching/rate limiting tests

### Phase 3: REFACTOR (Improve Code) - 1 hour

#### Code Quality Improvements:
1. Extract constants (API URLs, rate limits)
2. Add comprehensive docstrings
3. Improve error messages
4. Add type hints
5. Performance optimization

#### Documentation:
- Usage examples in docstrings
- Integration guide for next SHORT tasks
- Cache configuration guide

---

## Test Coverage Target

**Goal**: 100% code coverage

**Critical Paths** (must be tested):
- Authentication flow
- API request/response handling
- Data validation
- Error handling
- Rate limiting
- Caching

---

## Dependencies

### Required Packages:
```txt
smartapi-python==1.3.0  # Already installed
pandas==2.1.4           # Already installed
requests==2.31.0        # Already installed
```

### New Imports:
```python
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import pandas as pd
from functools import lru_cache
import hashlib
import json
```

---

## Integration with Existing Code

### Usage Example:

```python
from src.data.angel_one_client import AngelOneClient
from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

# Step 1: Authenticate
client = AngelOneClient.from_env_file(".env.angel")
client.authenticate()

# Step 2: Initialize OHLCV fetcher
fetcher = AngelOneOHLCVFetcher(
    client=client,
    cache_dir="/tmp/ohlcv_cache",
    cache_ttl=3600
)

# Step 3: Fetch data
df = fetcher.fetch_ohlcv(
    symbol="RELIANCE",
    exchange="NSE",
    interval="ONE_DAY",
    from_date=datetime(2023, 1, 1),
    to_date=datetime(2024, 1, 1)
)

# Step 4: Validate
is_valid, errors = fetcher.validate_ohlc(df)
if not is_valid:
    print(f"Data quality issues: {errors}")
else:
    print(f"Fetched {len(df)} candles")
    print(df.head())
```

---

## Angel One API Rate Limits

- **Historical Data**: 3 requests/second
- **Daily Limit**: 10,000 requests/day
- **Rate Limit Response**: HTTP 429 with `Retry-After` header

**Mitigation Strategy**:
1. Token bucket algorithm (3 tokens/sec)
2. Exponential backoff on 429
3. Cache aggressively

---

## Definition of Done

- ✅ All 28 tests passing
- ✅ 100% code coverage
- ✅ Can fetch daily OHLCV for any NSE/BSE symbol
- ✅ Can fetch 5-min intraday data
- ✅ Data validation works correctly
- ✅ Rate limiting respects Angel One limits
- ✅ Caching reduces redundant API calls
- ✅ Documentation complete
- ✅ Integrated with AngelOneClient from SHORT-001

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Angel One API changes | Medium | High | Version pin smartapi-python, add integration tests |
| Rate limit issues | High | Medium | Implement token bucket, cache aggressively |
| Data quality issues | Medium | High | Strict validation, flag suspicious data |
| Cache invalidation bugs | Low | Medium | Clear TTL logic, add cache tests |

---

## Next Steps

After SHORT-002 completion:
- **SHORT-003**: Yahoo Finance Historical Data Fetcher (fallback source)
- **SHORT-004**: OHLCV Data Validator (unified validation layer)
- **SHORT-005**: Corporate Action Handler

---

**Created**: 2025-11-19
**Status**: Ready for TDD Implementation
**Estimated Completion**: 4-6 hours
