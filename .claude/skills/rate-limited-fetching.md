# Rate-Limited Data Fetching Skill

## When to Use

Use this skill when you need to:
- Fetch OHLCV data from Angel One API
- Batch process multiple symbols
- Handle API quota limits and rate limiting
- Minimize API calls through intelligent caching
- Implement retry logic for API failures

## Decision Tree

```
┌─────────────────────┐
│  Data Request       │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ Check Cache  │
    └──────┬───────┘
           │
      ┌────┴────┐
      │         │
      ▼         ▼
   Cache      Cache
   HIT        MISS
      │         │
      │         ▼
      │    ┌─────────────────┐
      │    │ Check Rate      │
      │    │ Limiter Tokens  │
      │    └────────┬────────┘
      │             │
      │      ┌──────┴──────┐
      │      │             │
      │      ▼             ▼
      │   Tokens        No Tokens
      │   Available     Available
      │      │             │
      │      ▼             ▼
      │   ┌──────┐      Wait for
      │   │ API  │      Refill
      │   │ Call │         │
      │   └───┬──┘         │
      │       │            │
      │   ┌───┴────────┐   │
      │   │            │   │
      │   ▼            ▼   │
      │ Success     Error  │
      │   │            │   │
      │   │            ▼   │
      │   │        ┌───────────┐
      │   │        │ 429 Error?│
      │   │        └─────┬─────┘
      │   │              │
      │   │         ┌────┴─────┐
      │   │         │          │
      │   │         ▼          ▼
      │   │     Exponential  Other
      │   │     Backoff      Error
      │   │     Retry          │
      │   │         │          │
      │   ▼         ▼          ▼
      │ ┌────────────────────────┐
      │ │  Cache Result          │
      │ └────────────────────────┘
      │              │
      └──────────────┼──────────────┐
                     │              │
                     ▼              │
              ┌─────────────┐       │
              │ Return Data │       │
              └─────────────┘       │
                                    │
                                    ▼
                             ┌──────────────┐
                             │ Log & Raise  │
                             └──────────────┘
```

## Tools Used

### 1. EnhancedSQLiteCacheTool
- **Purpose**: Persistent caching with TTL
- **Location**: `agents/data/tools/enhanced_sqlite_cache_tool.py`
- **Key Methods**:
  - `get_cached_ohlcv()` - Check cache
  - `cache_ohlcv()` - Store data
  - `is_cache_fresh()` - Validate freshness

### 2. ExponentialBackoffTool
- **Purpose**: Retry logic with circuit breaker
- **Location**: `agents/data/tools/exponential_backoff_tool.py`
- **Key Methods**:
  - `execute_with_retry()` - Wrap API calls
  - `should_retry()` - Determine retryability
  - `get_retry_stats()` - Monitor performance

### 3. RateLimiter (existing)
- **Purpose**: Token bucket rate limiting
- **Location**: `tools/rate_limiter.py`
- **Configuration**: 3 requests/second for Angel One

## Usage Examples

### Example 1: Basic Fetch with Caching

```python
from agents.data.angel_rate_limiter_agent import AngelOneRateLimiterAgent
from src.data.angel_one_client import AngelOneClient
from datetime import datetime, timedelta

# Setup
client = AngelOneClient()
client.authenticate()

agent = AngelOneRateLimiterAgent(client=client)

# Fetch (cache-first)
data = agent.fetch_with_cache(
    symbol="RELIANCE",
    exchange="NSE",
    interval="ONE_DAY",
    from_date=datetime.now() - timedelta(days=365),
    to_date=datetime.now()
)

# Result: DataFrame with OHLCV data
print(f"Fetched {len(data)} rows")

# Check if it was cached
stats = agent.get_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
```

### Example 2: Batch Fetch Multiple Symbols

```python
# Fetch multiple symbols efficiently
symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']

results = agent.fetch_batch(
    symbols=symbols,
    exchange="NSE",
    interval="ONE_DAY",
    from_date=datetime.now() - timedelta(days=365),
    to_date=datetime.now()
)

# Results: Dict mapping symbol -> DataFrame
for symbol, data in results.items():
    print(f"{symbol}: {len(data)} rows")

# Statistics
stats = agent.get_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"API calls: {stats['api_calls']}")
print(f"Efficiency: {(stats['cache_hits']/stats['total_requests']*100):.1f}% cached")
```

### Example 3: Nifty 50 Cache Warming

```python
# One-time operation to populate cache
from datetime import datetime

# Warm Nifty 50 cache (3 years of data)
warming_stats = agent.warm_nifty_50_cache(
    from_date=datetime(2021, 1, 1),
    to_date=datetime.now()
)

print(f"Cache warming complete:")
print(f"  Successful: {warming_stats['successful']}/50")
print(f"  Failed: {warming_stats['failed']}")
print(f"  Total rows cached: {warming_stats.get('total_rows', 'N/A')}")
print(f"  API calls made: {warming_stats['api_calls']}")
print(f"  Cache hits (reused): {warming_stats['cache_hits']}")

# Now subsequent backtests will be much faster!
```

### Example 4: Force Refresh (Bypass Cache)

```python
# Force fetch from API (ignore cache)
data = agent.fetch_with_cache(
    symbol="RELIANCE",
    exchange="NSE",
    interval="ONE_DAY",
    from_date=datetime.now() - timedelta(days=30),
    to_date=datetime.now(),
    force_refresh=True  # ← Bypass cache
)

# Use case: When you need guaranteed fresh data
```

### Example 5: Integration with Backtest

```python
# In backtest_with_angel.py

class AngelOneBacktester:
    def __init__(self, client, ...):
        # Replace direct OHLCV fetcher with rate limiter agent
        from agents.data.angel_rate_limiter_agent import AngelOneRateLimiterAgent
        self.rate_limiter_agent = AngelOneRateLimiterAgent(client=client)

    def fetch_angel_data(self, symbol, start_date, end_date):
        # Use rate limiter instead of direct fetch
        daily = self.rate_limiter_agent.fetch_with_cache(
            symbol=symbol,
            exchange="NSE",
            interval="ONE_DAY",
            from_date=start_date,
            to_date=end_date
        )

        # Rest of method unchanged
        if daily is None or daily.empty:
            logger.warning(f"No data for {symbol}")
            return None

        return daily
```

## Best Practices

### 1. Always Check Statistics

```python
# After batch operations, check performance
stats = agent.get_stats()

if stats['cache_hit_rate'] < 80:
    logger.warning("Low cache hit rate - consider warming cache")

if stats['failed_api_calls'] > 0:
    logger.warning(f"{stats['failed_api_calls']} API calls failed - check connectivity")
```

### 2. Warm Cache Before Large Operations

```python
# Don't do this:
for symbol in nifty_50:
    backtest(symbol)  # Cold cache = slow

# Do this instead:
agent.warm_nifty_50_cache()  # One-time warm-up
for symbol in nifty_50:
    backtest(symbol)  # Hot cache = fast
```

### 3. Handle Errors Gracefully

```python
try:
    data = agent.fetch_with_cache(...)
    if data is None:
        logger.error(f"Failed to fetch {symbol}")
        continue  # Skip this symbol
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Decide: retry, skip, or fail?
```

### 4. Monitor Cache Health

```python
from agents.data.tools.enhanced_sqlite_cache_tool import EnhancedSQLiteCacheTool

cache = EnhancedSQLiteCacheTool()
health = cache.get_coverage_stats()

print(f"Cache coverage: {health['cache_hit_rate']:.1f}%")
print(f"Database size: {health['db_size_mb']:.2f} MB")
print(f"Stale symbols: {health['stale_symbols']}")

# Cleanup if needed
if health['stale_symbols'] > 10:
    deleted = cache.cleanup_stale_entries()
    print(f"Cleaned up {deleted} stale entries")
```

## Performance Targets

| Metric | Target | How to Achieve |
|--------|--------|----------------|
| **Cache hit rate** | >90% | Warm cache before backtests |
| **API call reduction** | 90% | Use cache-first strategy |
| **Backtest speed** | <5 min for Nifty 50 | Pre-populate cache |
| **Error rate** | <1% | Exponential backoff on retries |

## Troubleshooting

### Problem: Low cache hit rate

**Symptoms:** `cache_hit_rate < 50%`

**Solutions:**
1. Check if cache was warmed up
2. Verify TTL is appropriate (default: 24h)
3. Check date ranges match previous fetches

### Problem: API rate limit errors

**Symptoms:** "429 Too Many Requests" or "Access denied"

**Solutions:**
1. Exponential backoff is automatic - wait it out
2. Check rate limiter configuration (should be 3 req/sec)
3. Consider multi-account rotation (future enhancement)

### Problem: Cache returns stale data

**Symptoms:** Data doesn't include recent days

**Solutions:**
```python
# Force refresh latest data
data = agent.fetch_with_cache(..., force_refresh=True)

# Or reduce TTL
agent = AngelOneRateLimiterAgent(client=client, cache_ttl_hours=6)
```

### Problem: Circuit breaker opens

**Symptoms:** `CircuitBreakerOpen` exception

**Solutions:**
1. Wait 60 seconds (circuit breaker timeout)
2. Check Angel One API status
3. Verify credentials in `.env.angel`
4. Review logs for repeated errors

## Related Skills

- **BSE Earnings Filtering** - Pre-filter stocks before fetching
- **Historical Backfill** - One-time cache population
- **Daily Cache Maintenance** - Automated cache updates

## References

- **Agent**: [angel_rate_limiter_agent.py](../agents/data/angel_rate_limiter_agent.py)
- **Tools**: [agents/data/tools/](../agents/data/tools/)
- **Tests**: [tests/unit/agents/test_angel_rate_limiter_agent.py](../tests/unit/agents/)
- **Status**: [BACKTEST_OPTIMIZATION_STATUS.md](../BACKTEST_OPTIMIZATION_STATUS.md)

---

**Last Updated:** November 21, 2025
**Skill Version:** 1.0
**Status:** Production Ready
