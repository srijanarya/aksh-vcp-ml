# 📚 API Reference - Multi-Agent Backtest Optimization

**Version:** 1.0.0
**Last Updated:** November 21, 2025
**System Status:** Production Ready

---

## 📋 Table of Contents

1. [Priority 1: Rate Limiting System](#priority-1-rate-limiting-system)
2. [Priority 2: BSE Filtering System](#priority-2-bse-filtering-system)
3. [Priority 3: Cache Management System](#priority-3-cache-management-system)
4. [Automation Scripts](#automation-scripts)
5. [Database Schemas](#database-schemas)
6. [Common Patterns](#common-patterns)

---

## 🔵 Priority 1: Rate Limiting System

### AngelOneRateLimiterAgent

**Location**: `agents/data/angel_rate_limiter_agent.py`

Main coordinator for rate-limited API access with intelligent caching.

#### Constructor

```python
AngelOneRateLimiterAgent(
    client: SmartConnect,
    cache_db_path: str = "data/angel_ohlcv_cache.db",
    cache_ttl_hours: int = 24,
    request_delay: float = 0.33
)
```

**Parameters:**
- `client`: SmartConnect instance (Angel One client)
- `cache_db_path`: Path to SQLite cache database
- `cache_ttl_hours`: Cache time-to-live in hours
- `request_delay`: Delay between API requests (seconds)

**Example:**
```python
from SmartApi import SmartConnect
from agents.data.angel_rate_limiter_agent import AngelOneRateLimiterAgent

client = SmartConnect(api_key="YOUR_KEY")
client.generateSession("CLIENT_ID", "PASSWORD")

agent = AngelOneRateLimiterAgent(
    client=client,
    cache_ttl_hours=24,
    request_delay=0.33
)
```

---

#### fetch_with_cache()

Fetch OHLCV data with cache-first strategy.

```python
fetch_with_cache(
    symbol: str,
    exchange: str,
    interval: str,
    from_date: datetime,
    to_date: datetime,
    force_refresh: bool = False
) -> Optional[List[Dict]]
```

**Parameters:**
- `symbol`: Stock symbol (e.g., "RELIANCE")
- `exchange`: Exchange name (e.g., "NSE")
- `interval`: Timeframe (e.g., "ONE_DAY")
- `from_date`: Start date
- `to_date`: End date
- `force_refresh`: Skip cache, fetch from API

**Returns:**
- List of OHLCV dictionaries, or None if error

**Example:**
```python
from datetime import datetime

data = agent.fetch_with_cache(
    symbol="RELIANCE",
    exchange="NSE",
    interval="ONE_DAY",
    from_date=datetime(2024, 1, 1),
    to_date=datetime(2024, 11, 1),
    force_refresh=False
)

# data = [
#     {
#         'timestamp': '2024-01-01T09:15:00',
#         'open': 2500.0,
#         'high': 2550.0,
#         'low': 2480.0,
#         'close': 2520.0,
#         'volume': 1000000
#     },
#     ...
# ]
```

---

#### fetch_batch()

Fetch OHLCV data for multiple symbols in batch.

```python
fetch_batch(
    symbols: List[str],
    exchange: str,
    interval: str,
    from_date: datetime,
    to_date: datetime,
    force_refresh: bool = False
) -> Dict[str, Optional[List[Dict]]]
```

**Parameters:**
- `symbols`: List of stock symbols
- Other parameters same as `fetch_with_cache()`

**Returns:**
- Dictionary mapping symbol to OHLCV data

**Example:**
```python
results = agent.fetch_batch(
    symbols=["RELIANCE", "TCS", "INFY"],
    exchange="NSE",
    interval="ONE_DAY",
    from_date=datetime(2024, 1, 1),
    to_date=datetime(2024, 11, 1)
)

# results = {
#     'RELIANCE': [...],
#     'TCS': [...],
#     'INFY': [...]
# }
```

---

#### warm_nifty50_cache()

Pre-populate cache with Nifty 50 historical data.

```python
warm_nifty50_cache(
    interval: str = "ONE_DAY",
    from_date: datetime = None,
    to_date: datetime = None
) -> Dict[str, int]
```

**Parameters:**
- `interval`: Timeframe (default: "ONE_DAY")
- `from_date`: Start date (default: 1 year ago)
- `to_date`: End date (default: today)

**Returns:**
- Dictionary with success/failure counts

**Example:**
```python
result = agent.warm_nifty50_cache(
    interval="ONE_DAY",
    from_date=datetime(2023, 1, 1),
    to_date=datetime(2024, 11, 1)
)

# result = {
#     'total': 50,
#     'success': 48,
#     'failed': 2
# }
```

---

#### get_statistics()

Get cache and API call statistics.

```python
get_statistics() -> Dict[str, Any]
```

**Returns:**
- Dictionary with statistics

**Example:**
```python
stats = agent.get_statistics()

# stats = {
#     'cache_hits': 450,
#     'cache_misses': 50,
#     'api_calls': 50,
#     'cache_hit_rate_pct': 90.0
# }
```

---

### EnhancedSQLiteCacheTool

**Location**: `agents/data/tools/enhanced_sqlite_cache_tool.py`

SQLite-based caching with TTL expiration.

#### Constructor

```python
EnhancedSQLiteCacheTool(
    db_path: str = "data/angel_ohlcv_cache.db",
    ttl_hours: int = 24
)
```

---

#### get_cached_ohlcv()

Retrieve cached OHLCV data.

```python
get_cached_ohlcv(
    symbol: str,
    exchange: str,
    interval: str,
    from_date: datetime,
    to_date: datetime
) -> Optional[List[Dict]]
```

**Returns:**
- Cached data if available and fresh, None otherwise

---

#### store_ohlcv()

Store OHLCV data in cache.

```python
store_ohlcv(
    symbol: str,
    exchange: str,
    interval: str,
    data: List[Dict]
) -> bool
```

**Returns:**
- True if stored successfully, False otherwise

---

#### clear_expired()

Remove expired entries based on TTL.

```python
clear_expired() -> int
```

**Returns:**
- Number of entries deleted

---

### ExponentialBackoffTool

**Location**: `agents/data/tools/exponential_backoff_tool.py`

Retry logic with exponential backoff and circuit breaker.

#### Constructor

```python
ExponentialBackoffTool(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 32.0,
    circuit_breaker_threshold: int = 5,
    circuit_breaker_timeout: int = 60
)
```

---

#### execute_with_backoff()

Execute function with retry logic.

```python
execute_with_backoff(
    func: Callable,
    *args,
    **kwargs
) -> Any
```

**Raises:**
- `CircuitBreakerOpen`: If circuit breaker is open
- `MaxRetriesExceeded`: If max retries exceeded

**Example:**
```python
from agents.data.tools.exponential_backoff_tool import ExponentialBackoffTool

tool = ExponentialBackoffTool()

result = tool.execute_with_backoff(
    lambda: client.fetch_ohlcv(symbol, exchange, interval, from_date, to_date)
)
```

---

### NiftyIndexCacheTool

**Location**: `agents/data/tools/nifty_index_cache_tool.py`

Manage Nifty index constituent lists.

#### get_nifty50()

```python
get_nifty50() -> List[str]
```

**Returns:**
- List of Nifty 50 symbols

**Example:**
```python
from agents.data.tools.nifty_index_cache_tool import NiftyIndexCacheTool

tool = NiftyIndexCacheTool()
symbols = tool.get_nifty50()
# symbols = ['RELIANCE', 'TCS', 'INFY', ...]
```

---

## 🟡 Priority 2: BSE Filtering System

### BSEFilteringAgent

**Location**: `agents/filtering/bse_filtering_agent.py`

Main coordinator for BSE earnings-based filtering.

#### Constructor

```python
BSEFilteringAgent(
    earnings_db_path: str = "data/earnings_calendar.db",
    mapping_db_path: str = "data/bse_nse_mapping.db",
    default_lookforward_days: int = 7
)
```

---

#### filter_universe_by_earnings()

Filter stock universe by upcoming earnings.

```python
filter_universe_by_earnings(
    original_universe: List[str],
    lookforward_days: Optional[int] = None,
    force_refresh: bool = False
) -> Dict[str, Any]
```

**Parameters:**
- `original_universe`: List of NSE symbols to filter
- `lookforward_days`: Days to look ahead for earnings (default: 7)
- `force_refresh`: Bypass cache, fetch fresh data

**Returns:**
- Dictionary with filtering results

**Example:**
```python
from agents.filtering.bse_filtering_agent import BSEFilteringAgent

agent = BSEFilteringAgent()

result = agent.filter_universe_by_earnings(
    original_universe=['RELIANCE', 'TCS', 'INFY', 'HDFC', ...],  # 50 stocks
    lookforward_days=7,
    force_refresh=False
)

# result = {
#     'filtered_universe': ['RELIANCE', 'TCS', 'INFY'],  # 3 stocks
#     'original_size': 50,
#     'filtered_size': 3,
#     'reduction_pct': 94.0,
#     'announcements_found': 5,
#     'mapped_symbols': 3,
#     'unmapped_codes': ['500123', '532456']
# }

# Use filtered universe for backtest
symbols_to_backtest = result['filtered_universe']
```

---

#### get_upcoming_earnings()

Get upcoming earnings announcements.

```python
get_upcoming_earnings(
    lookforward_days: int = 7,
    force_refresh: bool = False
) -> List[Dict]
```

**Returns:**
- List of earnings announcement dictionaries

**Example:**
```python
announcements = agent.get_upcoming_earnings(lookforward_days=7)

# announcements = [
#     {
#         'bse_code': '500325',
#         'company_name': 'Reliance Industries',
#         'announcement_date': '2024-11-25',
#         'announcement_type': 'Result',
#         'subject': 'Financial Results for Q2 FY25'
#     },
#     ...
# ]
```

---

#### warm_earnings_cache()

Pre-populate earnings cache.

```python
warm_earnings_cache(
    lookforward_days: int = 14
) -> int
```

**Returns:**
- Number of announcements cached

---

### BSEEarningsCalendarTool

**Location**: `agents/filtering/tools/bse_earnings_calendar_tool.py`

Scrape BSE for earnings announcements.

#### fetch_earnings_calendar()

```python
fetch_earnings_calendar(
    lookforward_days: int = 7,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None
) -> List[Dict]
```

**Example:**
```python
from agents.filtering.tools.bse_earnings_calendar_tool import BSEEarningsCalendarTool

tool = BSEEarningsCalendarTool()
announcements = tool.fetch_earnings_calendar(lookforward_days=7)
```

---

### StockFilterByEarningsTool

**Location**: `agents/filtering/tools/stock_filter_by_earnings_tool.py`

Map BSE codes to NSE symbols and filter universe.

#### map_bse_to_nse()

```python
map_bse_to_nse(
    bse_codes: List[str]
) -> Dict[str, str]
```

**Returns:**
- Dictionary mapping BSE codes to NSE symbols

**Example:**
```python
from agents.filtering.tools.stock_filter_by_earnings_tool import StockFilterByEarningsTool

tool = StockFilterByEarningsTool()
mapping = tool.map_bse_to_nse(['500325', '532540'])

# mapping = {
#     '500325': 'RELIANCE',
#     '532540': 'TCS'
# }
```

---

#### filter_by_whitelist()

```python
filter_by_whitelist(
    original_universe: List[str],
    whitelist: List[str]
) -> List[str]
```

**Returns:**
- Filtered list of symbols

---

#### add_mapping()

```python
add_mapping(
    bse_code: str,
    nse_symbol: str,
    company_name: str
) -> bool
```

**Example:**
```python
tool.add_mapping(
    bse_code='500325',
    nse_symbol='RELIANCE',
    company_name='Reliance Industries Ltd'
)
```

---

## 🟢 Priority 3: Cache Management System

### HistoricalCacheManagerAgent

**Location**: `agents/cache/historical_cache_manager_agent.py`

Unified interface for cache lifecycle management.

#### Constructor

```python
HistoricalCacheManagerAgent(
    cache_db_path: str = "data/angel_ohlcv_cache.db",
    checkpoint_file: str = "/tmp/backfill_checkpoint.json"
)
```

---

#### run_historical_backfill()

One-time historical data backfill.

```python
run_historical_backfill(
    symbols: List[str],
    years: int = 3,
    interval: str = "ONE_DAY",
    batch_size: int = 10,
    resume: bool = True
) -> Dict[str, Any]
```

**Parameters:**
- `symbols`: List of symbols to backfill
- `years`: Years of historical data
- `interval`: Timeframe
- `batch_size`: Symbols per batch
- `resume`: Resume from checkpoint if exists

**Returns:**
- Dictionary with backfill results

**Example:**
```python
from agents.cache.historical_cache_manager_agent import HistoricalCacheManagerAgent

agent = HistoricalCacheManagerAgent()

result = agent.run_historical_backfill(
    symbols=['RELIANCE', 'TCS', 'INFY'],
    years=3,
    batch_size=10,
    resume=True
)

# result = {
#     'total_symbols': 3,
#     'completed': 3,
#     'failed': 0,
#     'duration_seconds': 1200,
#     'api_calls': 300
# }
```

---

#### run_daily_update()

Incremental daily cache update.

```python
run_daily_update(
    exchange: str = "NSE",
    interval: str = "ONE_DAY",
    lookback_days: int = 3
) -> Dict[str, Any]
```

**Returns:**
- Dictionary with update results

**Example:**
```python
result = agent.run_daily_update()

# result = {
#     'symbols_updated': 48,
#     'symbols_failed': 2,
#     'api_calls': 48,
#     'duration_seconds': 60
# }
```

---

#### run_weekly_cleanup()

Weekly maintenance and cleanup.

```python
run_weekly_cleanup(
    retention_days: int = 1825  # 5 years
) -> Dict[str, Any]
```

**Returns:**
- Dictionary with cleanup results

**Example:**
```python
result = agent.run_weekly_cleanup(retention_days=1825)

# result = {
#     'rows_deleted': 150000,
#     'database_size_before_mb': 120.5,
#     'database_size_after_mb': 85.3,
#     'space_reclaimed_mb': 35.2
# }
```

---

#### generate_health_report()

Generate comprehensive cache health report.

```python
generate_health_report() -> Dict[str, Any]
```

**Returns:**
- Dictionary with health metrics

**Example:**
```python
report = agent.generate_health_report()

# report = {
#     'status': 'HEALTHY',  # HEALTHY/WARNING/CRITICAL
#     'coverage': {
#         'total_symbols': 50,
#         'coverage_pct': 96.0
#     },
#     'freshness': {
#         'fresh_symbols': 48,
#         'stale_symbols': 2,
#         'freshness_rate': 96.0
#     },
#     'quality': {
#         'symbols_with_gaps': 0,
#         'duplicate_rows': 0
#     },
#     'database': {
#         'size_mb': 85.3,
#         'row_count': 125000
#     },
#     'issues': [],
#     'recommendations': ['Run daily updates regularly']
# }
```

---

### HistoricalBackfillTool

**Location**: `agents/cache/tools/historical_backfill_tool.py`

One-time historical backfill with resume capability.

#### backfill_symbols()

```python
backfill_symbols(
    symbols: List[str],
    years: int = 3,
    interval: str = "ONE_DAY",
    resume: bool = True
) -> Dict[str, Any]
```

---

#### get_progress()

```python
get_progress() -> Dict[str, Any]
```

**Returns:**
- Current backfill progress

**Example:**
```python
from agents.cache.tools.historical_backfill_tool import HistoricalBackfillTool

tool = HistoricalBackfillTool()
progress = tool.get_progress()

# progress = {
#     'total_symbols': 50,
#     'completed': 35,
#     'failed': 2,
#     'remaining': 13,
#     'progress_pct': 74.0
# }
```

---

### IncrementalUpdateTool

**Location**: `agents/cache/tools/incremental_update_tool.py`

Daily incremental cache updates.

#### update_all_symbols()

```python
update_all_symbols(
    exchange: str = "NSE",
    interval: str = "ONE_DAY",
    lookback_days: int = 3
) -> Dict[str, Any]
```

---

#### get_update_status()

```python
get_update_status(
    symbol: str,
    exchange: str = "NSE",
    interval: str = "ONE_DAY"
) -> Dict[str, Any]
```

**Example:**
```python
from agents.cache.tools.incremental_update_tool import IncrementalUpdateTool

tool = IncrementalUpdateTool()
status = tool.get_update_status('RELIANCE')

# status = {
#     'symbol': 'RELIANCE',
#     'has_data': True,
#     'last_cached_date': '2024-11-20',
#     'days_stale': 1,
#     'needs_update': True
# }
```

---

### CacheHealthMonitorTool

**Location**: `agents/cache/tools/cache_health_monitor_tool.py`

Monitor cache health and generate reports.

#### generate_health_report()

```python
generate_health_report() -> Dict[str, Any]
```

---

#### check_symbol_health()

```python
check_symbol_health(
    symbol: str,
    exchange: str = "NSE",
    interval: str = "ONE_DAY"
) -> Dict[str, Any]
```

**Example:**
```python
from agents.cache.tools.cache_health_monitor_tool import CacheHealthMonitorTool

tool = CacheHealthMonitorTool()
health = tool.check_symbol_health('RELIANCE')

# health = {
#     'symbol': 'RELIANCE',
#     'status': 'HEALTHY',  # HEALTHY/STALE/NO_DATA
#     'row_count': 750,
#     'date_range': {'first': '2022-01-01', 'last': '2024-11-20'},
#     'is_fresh': True,
#     'has_gaps': False
# }
```

---

## 🤖 Automation Scripts

### init_cache_db.py

Initialize cache database.

```bash
python3 agents/data/scripts/init_cache_db.py
```

**Output:**
- Creates `data/angel_ohlcv_cache.db`
- Initializes schema and indexes

---

### init_earnings_db.py

Initialize earnings and mapping databases.

```bash
python3 agents/filtering/scripts/init_earnings_db.py
```

**Output:**
- Creates `data/earnings_calendar.db`
- Creates `data/bse_nse_mapping.db`
- Loads Nifty 50 mappings

---

### backfill_nifty50.py

Automated Nifty 50 historical backfill.

```bash
python3 agents/cache/scripts/backfill_nifty50.py [options]
```

**Options:**
- `--years N`: Years of history (default: 3)
- `--resume`: Resume from checkpoint
- `--batch-size N`: Symbols per batch (default: 10)

**Example:**
```bash
python3 agents/cache/scripts/backfill_nifty50.py --years 3 --resume
```

---

### daily_cache_update.py

Daily incremental cache update.

```bash
python3 agents/cache/scripts/daily_cache_update.py
```

**Cron:** `0 17 * * 1-5` (5 PM IST, Mon-Fri)

---

### weekly_cache_cleanup.py

Weekly maintenance and cleanup.

```bash
python3 agents/cache/scripts/weekly_cache_cleanup.py
```

**Cron:** `0 2 * * 0` (Sunday 2 AM)

---

### cache_health_report.py

Generate cache health report.

```bash
python3 agents/cache/scripts/cache_health_report.py
```

**Output:** Text report to stdout

---

## 💾 Database Schemas

### angel_ohlcv_cache.db

```sql
CREATE TABLE ohlcv_data (
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    interval TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    cached_at TEXT NOT NULL,
    PRIMARY KEY (symbol, exchange, interval, timestamp)
);
```

---

### earnings_calendar.db

```sql
CREATE TABLE earnings_announcements (
    bse_code TEXT NOT NULL,
    company_name TEXT,
    announcement_date TEXT NOT NULL,
    announcement_type TEXT,
    subject TEXT,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (bse_code, announcement_date, subject)
);
```

---

### bse_nse_mapping.db

```sql
CREATE TABLE symbol_mappings (
    bse_code TEXT PRIMARY KEY,
    nse_symbol TEXT NOT NULL,
    company_name TEXT,
    last_updated TEXT NOT NULL
);
```

---

## 🔄 Common Patterns

### Basic Backtest with All Optimizations

```python
from backtest_with_angel import AngelBacktester
from datetime import datetime

# Create backtester with all features enabled
bt = AngelBacktester(
    enable_bse_filtering=True,  # 70% universe reduction
    lookforward_days=7          # Earnings in next 7 days
)

# Run backtest
signals = bt.run_backtest(
    symbols=NIFTY_50,
    start_date=datetime(2022, 1, 1),
    end_date=datetime(2024, 11, 1)
)

# First run: ~300 API calls (populating cache)
# Second run: ~15 API calls (95% reduction!)
```

---

### Manual Cache Warming

```python
from agents.data.angel_rate_limiter_agent import AngelOneRateLimiterAgent
from datetime import datetime

agent = AngelOneRateLimiterAgent(client=client)

# Warm Nifty 50 cache
result = agent.warm_nifty50_cache(
    interval="ONE_DAY",
    from_date=datetime(2022, 1, 1),
    to_date=datetime(2024, 11, 1)
)

print(f"Success: {result['success']}/{result['total']}")
```

---

### Custom Universe Filtering

```python
from agents.filtering.bse_filtering_agent import BSEFilteringAgent

agent = BSEFilteringAgent()

# Get symbols with earnings in next 14 days
result = agent.filter_universe_by_earnings(
    original_universe=MY_WATCHLIST,
    lookforward_days=14,
    force_refresh=True
)

filtered_symbols = result['filtered_universe']
print(f"Filtered: {result['original_size']} → {result['filtered_size']}")
```

---

### One-Time Historical Backfill

```python
from agents.cache.historical_cache_manager_agent import HistoricalCacheManagerAgent

agent = HistoricalCacheManagerAgent()

# Backfill with resume capability
result = agent.run_historical_backfill(
    symbols=NIFTY_50,
    years=3,
    batch_size=10,
    resume=True  # Resume if interrupted
)

print(f"Completed: {result['completed']}/{result['total_symbols']}")
```

---

### Daily Maintenance

```python
from agents.cache.historical_cache_manager_agent import HistoricalCacheManagerAgent

agent = HistoricalCacheManagerAgent()

# Run daily update
result = agent.run_daily_update()
print(f"Updated: {result['symbols_updated']} symbols")

# Generate health report
health = agent.generate_health_report()
print(f"Status: {health['status']}")
```

---

**API Reference Version**: 1.0.0
**Last Updated**: November 21, 2025
**System Version**: 1.0.0
**Status**: Complete ✅
