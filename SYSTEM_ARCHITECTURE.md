# 🏗️ System Architecture - Multi-Agent Backtest Optimization

**Version:** 1.0.0
**Last Updated:** November 21, 2025
**Status:** Production Ready

---

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKTEST WITH ANGEL                            │
│                    (Main Entry Point)                               │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ├─────────────────────────────────┐
                                 │                                 │
                                 ▼                                 ▼
        ┌────────────────────────────────────┐    ┌────────────────────────────┐
        │  PRIORITY 1: RATE LIMITING         │    │  PRIORITY 2: BSE FILTERING │
        │  AngelOneRateLimiterAgent          │    │  BSEFilteringAgent         │
        │  (90% API Reduction)               │    │  (70% Universe Reduction)  │
        └────────────────────────────────────┘    └────────────────────────────┘
                         │                                      │
          ┌──────────────┼──────────────┐                      │
          │              │              │                      │
          ▼              ▼              ▼                      ▼
    ┌─────────┐   ┌──────────┐   ┌──────────┐        ┌──────────────────┐
    │ Cache   │   │ Backoff  │   │  Nifty   │        │  Earnings        │
    │  Tool   │   │  Tool    │   │  Tool    │        │  Calendar        │
    └─────────┘   └──────────┘   └──────────┘        │  + Mapping       │
          │                                           └──────────────────┘
          │
          └───────────────────────┐
                                  │
                                  ▼
        ┌────────────────────────────────────────────────────┐
        │  PRIORITY 3: CACHE MANAGEMENT                      │
        │  HistoricalCacheManagerAgent                       │
        │  (Automated Maintenance)                           │
        └────────────────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Backfill │   │Increment │   │  Health  │
    │   Tool   │   │   Tool   │   │ Monitor  │
    └──────────┘   └──────────┘   └──────────┘
          │              │              │
          └──────────────┴──────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  SQLITE DATABASES                  │
        │  • angel_ohlcv_cache.db            │
        │  • earnings_calendar.db            │
        │  • bse_nse_mapping.db              │
        └────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

### Backtest Execution Flow

```
1. USER INITIATES BACKTEST
   │
   └─> backtest_with_angel.py
       │
       ├─> [OPTIONAL] BSEFilteringAgent.filter_universe_by_earnings()
       │   │
       │   ├─> BSEEarningsCalendarTool.fetch_earnings_calendar()
       │   │   │
       │   │   └─> BSE API (unofficial endpoint)
       │   │       └─> Returns announcements for next N days
       │   │
       │   ├─> StockFilterByEarningsTool.map_bse_to_nse()
       │   │   │
       │   │   └─> bse_nse_mapping.db
       │   │       └─> Maps BSE codes to NSE symbols
       │   │
       │   └─> Returns filtered universe (50 → 15 stocks)
       │
       └─> For each symbol in (filtered) universe:
           │
           └─> AngelOneRateLimiterAgent.fetch_with_cache()
               │
               ├─> EnhancedSQLiteCacheTool.get_cached_ohlcv()
               │   │
               │   ├─> [CACHE HIT] Returns cached data ✅
               │   │   └─> 90% of requests (after initial population)
               │   │
               │   └─> [CACHE MISS] Returns None
               │       │
               │       └─> ExponentialBackoffTool.execute_with_backoff()
               │           │
               │           ├─> Angel One API call
               │           │   │
               │           │   ├─> [SUCCESS] Returns data
               │           │   │   │
               │           │   │   └─> EnhancedSQLiteCacheTool.store_ohlcv()
               │           │   │       └─> Stores in angel_ohlcv_cache.db
               │           │   │
               │           │   └─> [FAILURE] Retry with exponential backoff
               │           │       └─> 1s → 2s → 4s → 8s → 16s → 32s (max)
               │           │
               │           └─> Circuit breaker trips after 5 consecutive failures
               │
               └─> Returns OHLCV data to backtest engine
```

### Cache Maintenance Flow

```
DAILY MAINTENANCE (Cron: 5 PM IST, Mon-Fri)
│
└─> daily_cache_update.py
    │
    └─> HistoricalCacheManagerAgent.run_daily_update()
        │
        └─> IncrementalUpdateTool.update_all_symbols()
            │
            ├─> For each cached symbol:
            │   │
            │   ├─> Get last cached date
            │   │
            │   ├─> Fetch only data since last date
            │   │   └─> Minimal API calls (~50 for Nifty 50)
            │   │
            │   └─> Append to cache
            │
            └─> Returns update statistics


WEEKLY MAINTENANCE (Cron: Sunday 2 AM)
│
└─> weekly_cache_cleanup.py
    │
    └─> HistoricalCacheManagerAgent.run_weekly_cleanup()
        │
        ├─> Delete data older than retention period (default: 5 years)
        │
        ├─> VACUUM database (reclaim space)
        │
        └─> Generate health report
            │
            └─> CacheHealthMonitorTool.generate_health_report()
                │
                ├─> Check coverage (what's cached)
                ├─> Check freshness (how recent)
                ├─> Check quality (data gaps)
                └─> Check database (size, performance)
```

---

## 🗄️ Database Schema

### angel_ohlcv_cache.db

```sql
-- OHLCV data cache
CREATE TABLE ohlcv_data (
    symbol TEXT NOT NULL,           -- Stock symbol (e.g., 'RELIANCE')
    exchange TEXT NOT NULL,         -- Exchange (e.g., 'NSE')
    interval TEXT NOT NULL,         -- Timeframe (e.g., 'ONE_DAY')
    timestamp TEXT NOT NULL,        -- ISO format datetime
    open REAL NOT NULL,             -- Opening price
    high REAL NOT NULL,             -- Highest price
    low REAL NOT NULL,              -- Lowest price
    close REAL NOT NULL,            -- Closing price
    volume INTEGER NOT NULL,        -- Trading volume
    cached_at TEXT NOT NULL,        -- When cached (for TTL)
    PRIMARY KEY (symbol, exchange, interval, timestamp)
);

CREATE INDEX idx_symbol_exchange_interval
    ON ohlcv_data(symbol, exchange, interval);
CREATE INDEX idx_timestamp
    ON ohlcv_data(timestamp);
CREATE INDEX idx_cached_at
    ON ohlcv_data(cached_at);
```

### earnings_calendar.db

```sql
-- BSE earnings announcements
CREATE TABLE earnings_announcements (
    bse_code TEXT NOT NULL,         -- BSE stock code
    company_name TEXT,              -- Full company name
    announcement_date TEXT NOT NULL,-- Announcement date (ISO format)
    announcement_type TEXT,         -- Type of announcement
    subject TEXT,                   -- Announcement subject
    fetched_at TEXT NOT NULL,       -- When fetched (for TTL)
    PRIMARY KEY (bse_code, announcement_date, subject)
);

CREATE INDEX idx_announcement_date
    ON earnings_announcements(announcement_date);
CREATE INDEX idx_bse_code
    ON earnings_announcements(bse_code);
CREATE INDEX idx_fetched_at
    ON earnings_announcements(fetched_at);
```

### bse_nse_mapping.db

```sql
-- BSE to NSE symbol mappings
CREATE TABLE symbol_mappings (
    bse_code TEXT PRIMARY KEY,      -- BSE stock code (e.g., '500325')
    nse_symbol TEXT NOT NULL,       -- NSE symbol (e.g., 'RELIANCE')
    company_name TEXT,              -- Full company name
    last_updated TEXT NOT NULL      -- Last verification date
);

CREATE INDEX idx_nse_symbol
    ON symbol_mappings(nse_symbol);
```

---

## 🔧 Component Details

### Priority 1: Rate Limiting System

#### AngelOneRateLimiterAgent
**Location**: `agents/data/angel_rate_limiter_agent.py`
**Purpose**: Main coordinator for rate-limited API access with caching
**Key Methods**:
- `fetch_with_cache()` - Cache-first data retrieval
- `fetch_batch()` - Batch fetching for multiple symbols
- `warm_nifty50_cache()` - Pre-populate cache with Nifty 50 data
- `get_statistics()` - Cache hit rate and API call statistics

**Dependencies**:
- EnhancedSQLiteCacheTool
- ExponentialBackoffTool
- NiftyIndexCacheTool

#### EnhancedSQLiteCacheTool
**Location**: `agents/data/tools/enhanced_sqlite_cache_tool.py`
**Purpose**: SQLite-based caching with TTL expiration
**Key Features**:
- TTL-based expiration (24h default)
- Partial date range matching
- Bulk insert operations
- Automatic schema initialization

#### ExponentialBackoffTool
**Location**: `agents/data/tools/exponential_backoff_tool.py`
**Purpose**: Retry logic with exponential backoff and circuit breaker
**Key Features**:
- Exponential backoff: 1s → 2s → 4s → 8s → 16s → 32s (max)
- Jitter to prevent thundering herd
- Circuit breaker (opens after 5 consecutive failures)
- Automatic recovery

#### NiftyIndexCacheTool
**Location**: `agents/data/tools/nifty_index_cache_tool.py`
**Purpose**: Manage Nifty index constituent lists
**Key Features**:
- Hardcoded Nifty 50/100/200/500 lists
- Quick access to popular indices
- No external dependencies

---

### Priority 2: BSE Filtering System

#### BSEFilteringAgent
**Location**: `agents/filtering/bse_filtering_agent.py`
**Purpose**: Filter stock universe using BSE earnings calendar
**Key Methods**:
- `filter_universe_by_earnings()` - Main filtering method
- `get_upcoming_earnings()` - Fetch earnings announcements
- `warm_earnings_cache()` - Pre-populate earnings cache

**Dependencies**:
- BSEEarningsCalendarTool
- StockFilterByEarningsTool

#### BSEEarningsCalendarTool
**Location**: `agents/filtering/tools/bse_earnings_calendar_tool.py`
**Purpose**: Scrape BSE for earnings announcements
**Key Features**:
- Reverse-engineered BSE API (unofficial)
- Keyword filtering (earnings-related only)
- 24h cache TTL
- Configurable lookforward window

**BSE API Endpoint** (unofficial):
```
https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w
```

#### StockFilterByEarningsTool
**Location**: `agents/filtering/tools/stock_filter_by_earnings_tool.py`
**Purpose**: Map BSE codes to NSE symbols and filter universe
**Key Features**:
- BSE-NSE symbol mapping database
- Whitelist generation from earnings
- Coverage tracking (mapped vs unmapped)
- Statistics reporting

---

### Priority 3: Cache Management System

#### HistoricalCacheManagerAgent
**Location**: `agents/cache/historical_cache_manager_agent.py`
**Purpose**: Unified interface for cache lifecycle management
**Key Methods**:
- `run_historical_backfill()` - One-time backfill
- `run_daily_update()` - Incremental updates
- `run_weekly_cleanup()` - Maintenance and cleanup
- `generate_health_report()` - Health monitoring

**Dependencies**:
- HistoricalBackfillTool
- IncrementalUpdateTool
- CacheHealthMonitorTool

#### HistoricalBackfillTool
**Location**: `agents/cache/tools/historical_backfill_tool.py`
**Purpose**: One-time historical data backfill with resume capability
**Key Features**:
- Checkpoint-based resume (survives interruptions)
- Batch processing (10 symbols at a time)
- Progress tracking
- Configurable years of history

**Checkpoint Format**:
```json
{
    "timestamp": "2024-11-21T14:30:00",
    "remaining_symbols": ["TCS", "INFY", ...],
    "completed": 35,
    "failed": 2,
    "failed_symbols": ["BADSTOCK1", "BADSTOCK2"]
}
```

#### IncrementalUpdateTool
**Location**: `agents/cache/tools/incremental_update_tool.py`
**Purpose**: Daily incremental cache updates
**Key Features**:
- Fetches only data since last cached date
- Minimal API calls (~50 for Nifty 50)
- Automatic staleness detection
- Configurable lookback (default: 3 days)

#### CacheHealthMonitorTool
**Location**: `agents/cache/tools/cache_health_monitor_tool.py`
**Purpose**: Monitor cache health and generate reports
**Key Metrics**:
- **Coverage**: What symbols are cached
- **Freshness**: How recent is the data (threshold: 1 day)
- **Quality**: Data gaps, duplicates, errors
- **Database**: Size, performance, fragmentation

**Health Status**:
- `HEALTHY`: >90% fresh, no gaps
- `WARNING`: 70-90% fresh, minor gaps
- `CRITICAL`: <70% fresh, significant gaps

---

## 🤖 Automation Scripts

### init_cache_db.py
**Location**: `agents/data/scripts/init_cache_db.py`
**Purpose**: Initialize cache database
**Usage**: `python3 agents/data/scripts/init_cache_db.py`
**Output**: Creates `data/angel_ohlcv_cache.db`

### init_earnings_db.py
**Location**: `agents/filtering/scripts/init_earnings_db.py`
**Purpose**: Initialize earnings and mapping databases
**Usage**: `python3 agents/filtering/scripts/init_earnings_db.py`
**Output**:
- `data/earnings_calendar.db`
- `data/bse_nse_mapping.db` (with Nifty 50 mappings)

### backfill_nifty50.py
**Location**: `agents/cache/scripts/backfill_nifty50.py`
**Purpose**: Automated Nifty 50 historical backfill
**Usage**:
```bash
python3 agents/cache/scripts/backfill_nifty50.py --years 3 --resume
```
**Options**:
- `--years N`: Years of history (default: 3)
- `--resume`: Resume from checkpoint if exists
- `--batch-size N`: Symbols per batch (default: 10)

### daily_cache_update.py
**Location**: `agents/cache/scripts/daily_cache_update.py`
**Purpose**: Daily incremental cache update
**Usage**: `python3 agents/cache/scripts/daily_cache_update.py`
**Cron**: `0 17 * * 1-5` (5 PM IST, Mon-Fri)
**API Calls**: ~50 (one per Nifty 50 symbol)

### weekly_cache_cleanup.py
**Location**: `agents/cache/scripts/weekly_cache_cleanup.py`
**Purpose**: Weekly maintenance and cleanup
**Usage**: `python3 agents/cache/scripts/weekly_cache_cleanup.py`
**Cron**: `0 2 * * 0` (Sunday 2 AM)
**Actions**:
- Delete data older than retention period (5 years)
- VACUUM database (reclaim space)
- Generate health report

### cache_health_report.py
**Location**: `agents/cache/scripts/cache_health_report.py`
**Purpose**: Generate comprehensive health report
**Usage**: `python3 agents/cache/scripts/cache_health_report.py`
**Output**: Text report to stdout

---

## 📊 Performance Characteristics

### API Call Reduction

| Scenario | API Calls | Cache Hits | Time |
|----------|-----------|------------|------|
| **First backtest (cold cache)** | ~300 | 0% | ~30 min |
| **Second backtest (warm cache)** | ~15 | ~95% | ~3 min |
| **With historical backfill** | ~0 | ~100% | <1 min |

### Cache Hit Rate Over Time

```
Day 1 (Initial Run):
└─> Cache Hit Rate: 0% (cold start)
    API Calls: 300 (populating cache)

Day 2-7 (Same backtest period):
└─> Cache Hit Rate: 90-95% (warm cache)
    API Calls: 15-30 (only latest day)

After Historical Backfill:
└─> Cache Hit Rate: 100% (all historical data cached)
    API Calls: 0 (for historical period)

Daily Incremental Updates:
└─> API Calls: ~50/day (Nifty 50)
    Keeps cache fresh automatically
```

### Storage Requirements

| Database | Initial Size | After Backfill (3 years, Nifty 50) | Growth Rate |
|----------|--------------|-------------------------------------|-------------|
| `angel_ohlcv_cache.db` | 32 KB | ~50-100 MB | ~1 MB/symbol/year |
| `earnings_calendar.db` | 1.7 MB | ~2-3 MB | ~100 KB/month |
| `bse_nse_mapping.db` | 16 KB | ~20 KB | Minimal |
| **Total** | ~1.8 MB | ~55-105 MB | ~50 MB/year |

---

## 🔒 Error Handling Strategy

### Cache Tool Errors
```python
try:
    cached_data = cache_tool.get_cached_ohlcv(...)
except Exception as e:
    logger.warning(f"Cache error: {e}. Falling back to API.")
    # Graceful degradation to API
```

### API Errors
```python
# Exponential backoff with circuit breaker
try:
    data = backoff_tool.execute_with_backoff(api_call)
except CircuitBreakerOpen:
    logger.error("Circuit breaker open. API unavailable.")
    raise
except MaxRetriesExceeded:
    logger.error("Max retries exceeded. API call failed.")
    raise
```

### Database Errors
```python
# Automatic retry with connection pooling
try:
    conn = sqlite3.connect(db_path, timeout=10)
except sqlite3.OperationalError as e:
    logger.error(f"Database locked: {e}. Retrying...")
    time.sleep(1)
    conn = sqlite3.connect(db_path, timeout=10)
```

### BSE Scraping Errors
```python
# Fallback to cached data if available
try:
    data = scrape_bse_earnings()
except (RequestException, JSONDecodeError) as e:
    logger.warning(f"BSE scraping failed: {e}. Using cached data.")
    data = get_cached_earnings()
```

---

## 🧪 Testing Architecture

### Test Structure

```
tests/unit/agents/
├── test_angel_rate_limiter_agent.py     (17 tests)
│   ├── TestInitialization (4 tests)
│   ├── TestStatisticsTracking (2 tests)
│   ├── TestCacheInteraction (2 tests)
│   ├── TestForceRefresh (1 test)
│   ├── TestBatchFetching (2 tests)
│   ├── TestNifty50CacheWarming (2 tests)
│   ├── TestErrorHandling (2 tests)
│   └── TestCacheHitRateCalculation (2 tests)
│
├── filtering/
│   └── test_bse_filtering_agent.py      (20 tests)
│       ├── TestBSEEarningsCalendarTool (5 tests)
│       ├── TestStockFilterByEarningsTool (9 tests)
│       └── TestBSEFilteringAgent (6 tests)
│
└── cache/
    └── test_cache_tools.py              (21 tests)
        ├── TestHistoricalBackfillTool (6 tests)
        ├── TestIncrementalUpdateTool (6 tests)
        └── TestCacheHealthMonitorTool (9 tests)
```

### Mocking Strategy

**Angel One API Calls**:
```python
@patch('agents.data.angel_rate_limiter_agent.AngelOneClient')
def test_fetch_with_cache(mock_client):
    mock_client.fetch_ohlcv.return_value = mock_ohlcv_data
    # Test logic
```

**Database Connections**:
```python
@pytest.fixture
def tmp_cache_db(tmp_path):
    return tmp_path / "test_cache.db"
```

**BSE API Responses**:
```python
@patch('requests.post')
def test_bse_scraping(mock_post):
    mock_post.return_value.json.return_value = mock_earnings_data
    # Test logic
```

---

## 📖 Documentation Structure

### User Documentation
- **QUICK_START.md**: 5-minute setup guide
- **IMPLEMENTATION_COMPLETE.md**: Complete system overview
- **SESSION_COMPLETE_NOV_21.md**: Session report and achievements
- **SYSTEM_ARCHITECTURE.md**: This file (technical architecture)

### Skill Guides (.claude/skills/)
- **rate-limited-fetching.md**: Priority 1 usage with examples
- **bse-earnings-filtering.md**: Priority 2 usage and integration
- **historical-backfill.md**: Priority 3 backfill guide
- **daily-cache-maintenance.md**: Priority 3 maintenance guide

### Code Examples
- **examples/rate_limiter_demo.py**: Interactive demonstration
- **examples/backtest_integration_example.py**: Integration tutorial

### Verification
- **verify_system.py**: System health check script

---

## 🚀 Deployment Checklist

### Initial Setup
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Initialize cache DB: `python3 agents/data/scripts/init_cache_db.py`
- [ ] Initialize earnings DB: `python3 agents/filtering/scripts/init_earnings_db.py`
- [ ] Run tests: `python3 -m pytest tests/unit/agents/ -v`
- [ ] Verify system: `python3 verify_system.py`

### Optional: Historical Backfill
- [ ] Run backfill: `python3 agents/cache/scripts/backfill_nifty50.py --years 3 --resume`
- [ ] Monitor progress: Check logs for completion
- [ ] Verify health: `python3 agents/cache/scripts/cache_health_report.py`

### Optional: Automated Maintenance
- [ ] Edit crontab: `crontab -e`
- [ ] Add daily update job: `0 17 * * 1-5 cd /path/to/aksh && python3 agents/cache/scripts/daily_cache_update.py`
- [ ] Add weekly cleanup job: `0 2 * * 0 cd /path/to/aksh && python3 agents/cache/scripts/weekly_cache_cleanup.py`
- [ ] Test cron jobs: Run scripts manually first

### Production Use
- [ ] Run optimized backtest: `python3 backtest_with_angel.py`
- [ ] Monitor cache hit rate: Check agent statistics
- [ ] Review health reports: Weekly checks recommended

---

## 🔍 Monitoring and Observability

### Key Metrics to Track

**Cache Performance**:
- Cache hit rate (target: >90%)
- API call count (target: <20/backtest)
- Cache size (monitor growth)

**Data Quality**:
- Data gaps (target: 0)
- Stale symbols (target: <5%)
- Failed API calls (monitor rate)

**System Health**:
- Database size (monitor growth)
- Query performance (should be <100ms)
- Cron job success rate (target: 100%)

### Logging

**Log Levels**:
- `INFO`: Normal operations, cache hits, successful API calls
- `WARNING`: Cache misses, API retries, non-critical errors
- `ERROR`: API failures, database errors, critical issues

**Log Locations**:
- Console output (default)
- Configure file logging as needed

---

## 🔮 Future Enhancements

### Priority 4: TradingView Integration
- Lightweight-charts integration
- Technical indicator visualization
- Chart rendering for pattern analysis

### Advanced Features
- Multi-broker support (Zerodha, Upstox, etc.)
- Advanced filtering (technical + fundamental)
- Real-time data streaming
- WebSocket integration for live data

### Performance Optimization
- Redis caching layer (if needed)
- Parallel API calls with asyncio
- Database partitioning for large datasets

---

## 📞 Support and Troubleshooting

### Common Issues

**Cache Not Working**:
1. Check database exists: `ls -lh data/angel_ohlcv_cache.db`
2. Verify permissions: Database must be writable
3. Check TTL settings: Default 24h, may need adjustment

**BSE Scraping Fails**:
1. Verify BSE API endpoint is accessible
2. Check user-agent headers
3. Review rate limiting (wait 0.5s between requests)

**Tests Failing**:
1. Ensure temp directories are writable
2. Check mock data format matches real API responses
3. Verify pytest version: `pytest --version`

### Debug Mode

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

**Architecture Documentation Version**: 1.0.0
**Last Updated**: November 21, 2025
**Maintainer**: Multi-Agent System (Anthropic Claude)
**Status**: Production Ready ✅
