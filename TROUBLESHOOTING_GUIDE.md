# 🔧 Troubleshooting Guide - Multi-Agent Backtest Optimization

**Version:** 1.0.0
**Last Updated:** November 21, 2025
**For System Version:** 1.0.0

---

## 📋 Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Priority 1 Issues (Rate Limiting)](#priority-1-issues-rate-limiting)
3. [Priority 2 Issues (BSE Filtering)](#priority-2-issues-bse-filtering)
4. [Priority 3 Issues (Cache Management)](#priority-3-issues-cache-management)
5. [Database Issues](#database-issues)
6. [API Issues](#api-issues)
7. [Test Failures](#test-failures)
8. [Performance Issues](#performance-issues)
9. [Integration Issues](#integration-issues)
10. [Advanced Debugging](#advanced-debugging)

---

## 🩺 Quick Diagnostics

### Run System Verification

```bash
python3 verify_system.py
```

This checks:
- ✅ All agents import successfully
- ✅ All databases exist and are accessible
- ✅ All scripts are present
- ✅ All documentation is available
- ✅ Backtest integration is complete
- ✅ All test files are present

### Check System Health

```bash
# Check cache health
python3 agents/cache/scripts/cache_health_report.py

# Check databases
ls -lh data/*.db

# Run all tests
python3 -m pytest tests/unit/agents/ -v
```

### Common Quick Fixes

```bash
# Reinitialize databases
python3 agents/data/scripts/init_cache_db.py
python3 agents/filtering/scripts/init_earnings_db.py

# Clear cache (nuclear option)
rm data/angel_ohlcv_cache.db
python3 agents/data/scripts/init_cache_db.py

# Clear checkpoints (restart backfill)
rm /tmp/backfill_checkpoint.json
```

---

## 🔴 Priority 1 Issues (Rate Limiting)

### Issue: Cache Not Working (0% Hit Rate)

**Symptoms:**
- Every API call goes to Angel One
- No performance improvement
- Cache hit rate shows 0%

**Diagnosis:**
```python
from agents.data.angel_rate_limiter_agent import AngelOneRateLimiterAgent

agent = AngelOneRateLimiterAgent(client=your_client)
stats = agent.get_statistics()
print(f"Cache hits: {stats['cache_hits']}")
print(f"Cache misses: {stats['cache_misses']}")
print(f"Hit rate: {stats['cache_hit_rate_pct']}%")
```

**Solutions:**

1. **Database doesn't exist**:
   ```bash
   ls -lh data/angel_ohlcv_cache.db
   # If not found:
   python3 agents/data/scripts/init_cache_db.py
   ```

2. **TTL expired (all data stale)**:
   ```python
   # Increase TTL in agent initialization
   agent = AngelOneRateLimiterAgent(
       client=client,
       cache_ttl_hours=48  # Default: 24
   )
   ```

3. **Database permissions**:
   ```bash
   chmod 644 data/angel_ohlcv_cache.db
   # Ensure directory is writable
   chmod 755 data/
   ```

4. **Cache lookup failing silently**:
   - Check logs for errors
   - Enable debug mode: `logging.basicConfig(level=logging.DEBUG)`
   - Verify symbol/exchange format matches cache keys

---

### Issue: Circuit Breaker Keeps Tripping

**Symptoms:**
- Error: "Circuit breaker is open"
- API calls fail after 5 consecutive errors
- System refuses to make API calls

**Diagnosis:**
```python
from agents.data.tools.exponential_backoff_tool import ExponentialBackoffTool

tool = ExponentialBackoffTool()
print(f"Circuit breaker open: {tool.circuit_breaker_open}")
print(f"Consecutive failures: {tool.consecutive_failures}")
```

**Solutions:**

1. **Angel One API is down**:
   ```bash
   # Test API connectivity
   curl -X POST https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword
   ```

2. **Invalid API credentials**:
   - Verify `.env.angel` has correct credentials
   - Test login manually
   - Check API key expiration

3. **Rate limit exceeded**:
   - Circuit breaker may open due to rate limiting
   - Wait 60 seconds for reset
   - Reduce request rate (increase `request_delay`)

4. **Reset circuit breaker manually**:
   ```python
   agent.backoff_tool.consecutive_failures = 0
   agent.backoff_tool.circuit_breaker_open = False
   agent.backoff_tool.circuit_breaker_opened_at = None
   ```

---

### Issue: Exponential Backoff Too Slow

**Symptoms:**
- Retries take too long (up to 32 seconds per retry)
- System feels sluggish

**Solutions:**

1. **Reduce max backoff**:
   ```python
   from agents.data.tools.exponential_backoff_tool import ExponentialBackoffTool

   tool = ExponentialBackoffTool(
       max_delay=10,  # Default: 32 seconds
       max_retries=3   # Default: 5
   )
   ```

2. **Disable backoff for development**:
   ```python
   # Directly call API without backoff
   data = client.fetch_ohlcv(...)
   ```

---

### Issue: Batch Fetching Fails

**Symptoms:**
- `fetch_batch()` returns incomplete results
- Some symbols missing from batch results

**Diagnosis:**
```python
results = agent.fetch_batch(symbols, ...)
print(f"Requested: {len(symbols)}")
print(f"Received: {len(results)}")
print(f"Missing: {set(symbols) - set(results.keys())}")
```

**Solutions:**

1. **Some symbols invalid**:
   - Check symbol format (NSE requires ".NS" suffix)
   - Verify symbols exist on exchange
   - Review error logs for failed symbols

2. **API timeout for some symbols**:
   - Increase timeout: `ExponentialBackoffTool(timeout=30)`
   - Reduce batch size
   - Retry failed symbols individually

3. **Partial cache hit**:
   - This is expected behavior
   - Only uncached symbols hit API
   - Check which symbols were cached vs API-fetched

---

## 🟡 Priority 2 Issues (BSE Filtering)

### Issue: BSE Scraping Returns Empty Results

**Symptoms:**
- `filter_universe_by_earnings()` returns original universe (no filtering)
- Warning: "No earnings announcements found"

**Diagnosis:**
```python
from agents.filtering.bse_filtering_agent import BSEFilteringAgent

agent = BSEFilteringAgent()
announcements = agent.earnings_tool.fetch_earnings_calendar(lookforward_days=7)
print(f"Announcements found: {len(announcements)}")
```

**Solutions:**

1. **No earnings in lookforward window**:
   - Increase `lookforward_days`: Try 14 or 30 days
   - Check actual BSE calendar manually
   - This is normal during quiet periods

2. **BSE API endpoint changed**:
   ```bash
   # Test BSE API directly
   curl -X POST https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w \
     -H "Content-Type: application/json" \
     -d '{"FromDate":"21/11/2024","ToDate":"28/11/2024","...}'
   ```
   - If endpoint changed, update URL in `bse_earnings_calendar_tool.py`

3. **Keyword filtering too strict**:
   ```python
   # Check what keywords are being filtered
   tool.earnings_keywords = [
       'result', 'earnings', 'financials',
       'dividend', 'profit', 'loss'
       # Add more if needed
   ]
   ```

4. **Date format mismatch**:
   - BSE expects DD/MM/YYYY
   - Verify date conversion in tool

---

### Issue: BSE-NSE Mapping Not Working

**Symptoms:**
- Warning: "BSE code XXX not found in mapping"
- Filtered universe smaller than expected

**Diagnosis:**
```bash
# Check mapping database
sqlite3 data/bse_nse_mapping.db "SELECT COUNT(*) FROM symbol_mappings;"
# Expected: 20+ (Nifty 50 has only ~20 mapped by default)
```

**Solutions:**

1. **Mapping database empty**:
   ```bash
   python3 agents/filtering/scripts/init_earnings_db.py
   ```

2. **Add missing mappings**:
   ```python
   from agents.filtering.tools.stock_filter_by_earnings_tool import StockFilterByEarningsTool

   tool = StockFilterByEarningsTool()
   tool.add_mapping(
       bse_code='500325',
       nse_symbol='RELIANCE',
       company_name='Reliance Industries Ltd'
   )
   ```

3. **Bulk import mappings**:
   ```python
   # Create CSV: bse_code,nse_symbol,company_name
   # Then import:
   import sqlite3
   import csv

   conn = sqlite3.connect('data/bse_nse_mapping.db')
   with open('mappings.csv') as f:
       reader = csv.DictReader(f)
       for row in reader:
           conn.execute("""
               INSERT OR REPLACE INTO symbol_mappings
               (bse_code, nse_symbol, company_name, last_updated)
               VALUES (?, ?, ?, datetime('now'))
           """, (row['bse_code'], row['nse_symbol'], row['company_name']))
   conn.commit()
   ```

---

### Issue: Universe Reduction Too Aggressive (0 stocks)

**Symptoms:**
- Filtered universe is empty
- Warning: "Filtered universe is empty"

**Solutions:**

1. **Increase lookforward window**:
   ```python
   result = agent.filter_universe_by_earnings(
       original_universe=symbols,
       lookforward_days=30  # Default: 7
   )
   ```

2. **Disable filtering temporarily**:
   ```python
   bt = AngelBacktester(
       enable_bse_filtering=False  # Disable filtering
   )
   ```

3. **Use whitelist mode**:
   ```python
   # Generate whitelist, don't filter
   result = agent.filter_universe_by_earnings(
       original_universe=symbols,
       return_whitelist_only=True  # Just get earnings symbols
   )
   print(f"Symbols with earnings: {result['filtered_universe']}")
   ```

---

## 🟢 Priority 3 Issues (Cache Management)

### Issue: Historical Backfill Stuck/Slow

**Symptoms:**
- Backfill seems frozen
- Progress not updating
- Takes hours to complete

**Diagnosis:**
```bash
# Check checkpoint
cat /tmp/backfill_checkpoint.json

# Monitor progress in separate terminal
watch -n 5 "cat /tmp/backfill_checkpoint.json | jq '.'"
```

**Solutions:**

1. **API rate limiting**:
   - This is normal for large backfills
   - Expect 1-2 hours for Nifty 50 (3 years)
   - Angel One has rate limits (~3 req/sec)

2. **Resume from checkpoint**:
   ```bash
   # If interrupted, resume
   python3 agents/cache/scripts/backfill_nifty50.py --resume
   ```

3. **Reduce scope**:
   ```bash
   # Backfill fewer years
   python3 agents/cache/scripts/backfill_nifty50.py --years 1

   # Or fewer symbols
   python3 -c "
   from agents.cache.historical_cache_manager_agent import HistoricalCacheManagerAgent
   agent = HistoricalCacheManagerAgent()
   agent.run_historical_backfill(
       symbols=['RELIANCE', 'TCS', 'INFY'],
       years=3
   )
   "
   ```

4. **Clear stuck checkpoint**:
   ```bash
   rm /tmp/backfill_checkpoint.json
   # Start fresh
   python3 agents/cache/scripts/backfill_nifty50.py
   ```

---

### Issue: Daily Updates Not Running

**Symptoms:**
- Cache becomes stale
- Recent data missing
- Cron job not executing

**Diagnosis:**
```bash
# Check cron jobs
crontab -l

# Check cron logs (macOS)
log show --predicate 'process == "cron"' --info --last 1d

# Check cron logs (Linux)
grep CRON /var/log/syslog
```

**Solutions:**

1. **Cron not configured**:
   ```bash
   crontab -e
   # Add:
   0 17 * * 1-5 cd /Users/srijan/Desktop/aksh && python3 agents/cache/scripts/daily_cache_update.py >> /tmp/cache_update.log 2>&1
   ```

2. **Python path issues in cron**:
   ```bash
   # Use absolute path to python
   which python3
   # Output: /usr/bin/python3 or /opt/homebrew/bin/python3

   # Update cron:
   0 17 * * 1-5 cd /Users/srijan/Desktop/aksh && /usr/bin/python3 agents/cache/scripts/daily_cache_update.py
   ```

3. **Environment variables not set**:
   ```bash
   # Add to cron:
   0 17 * * 1-5 cd /Users/srijan/Desktop/aksh && source .env.angel && python3 agents/cache/scripts/daily_cache_update.py
   ```

4. **Run manually to test**:
   ```bash
   python3 agents/cache/scripts/daily_cache_update.py
   # Check output for errors
   ```

---

### Issue: Cache Health Report Shows "CRITICAL"

**Symptoms:**
- Health status: CRITICAL
- Multiple issues reported

**Diagnosis:**
```bash
python3 agents/cache/scripts/cache_health_report.py
```

**Solutions based on issues:**

1. **Low freshness (<70%)**:
   ```bash
   # Run incremental update
   python3 agents/cache/scripts/daily_cache_update.py
   ```

2. **Data gaps detected**:
   ```bash
   # Re-backfill specific symbols
   python3 -c "
   from agents.cache.tools.historical_backfill_tool import HistoricalBackfillTool
   tool = HistoricalBackfillTool()
   tool.backfill_symbol('SYMBOL_WITH_GAPS', years=1)
   "
   ```

3. **Database too large**:
   ```bash
   # Run weekly cleanup
   python3 agents/cache/scripts/weekly_cache_cleanup.py
   ```

4. **Database corrupted**:
   ```bash
   # Check integrity
   sqlite3 data/angel_ohlcv_cache.db "PRAGMA integrity_check;"

   # If corrupted, reinitialize
   rm data/angel_ohlcv_cache.db
   python3 agents/data/scripts/init_cache_db.py
   python3 agents/cache/scripts/backfill_nifty50.py
   ```

---

## 💾 Database Issues

### Issue: Database Locked

**Symptoms:**
- Error: "database is locked"
- SQLite operational error

**Solutions:**

1. **Close other connections**:
   ```python
   # In your code, always use context managers
   with sqlite3.connect(db_path) as conn:
       # Do work
       pass  # Automatically closes
   ```

2. **Increase timeout**:
   ```python
   conn = sqlite3.connect(db_path, timeout=30)  # Default: 5
   ```

3. **Kill hanging processes**:
   ```bash
   # Find processes using database
   lsof data/angel_ohlcv_cache.db

   # Kill if needed
   kill -9 <PID>
   ```

---

### Issue: Database Corrupted

**Symptoms:**
- Error: "database disk image is malformed"
- Integrity check fails

**Diagnosis:**
```bash
sqlite3 data/angel_ohlcv_cache.db "PRAGMA integrity_check;"
```

**Solutions:**

1. **Attempt repair**:
   ```bash
   # Dump and restore
   sqlite3 data/angel_ohlcv_cache.db ".dump" > backup.sql
   rm data/angel_ohlcv_cache.db
   sqlite3 data/angel_ohlcv_cache.db < backup.sql
   ```

2. **Reinitialize** (last resort):
   ```bash
   rm data/angel_ohlcv_cache.db
   python3 agents/data/scripts/init_cache_db.py
   python3 agents/cache/scripts/backfill_nifty50.py --resume
   ```

---

### Issue: Database Growing Too Large

**Symptoms:**
- Database >1 GB
- Queries becoming slow

**Solutions:**

1. **Run weekly cleanup**:
   ```bash
   python3 agents/cache/scripts/weekly_cache_cleanup.py
   ```

2. **Reduce retention period**:
   ```python
   # Modify weekly_cache_cleanup.py
   retention_days = 365 * 3  # Keep only 3 years (default: 5)
   ```

3. **Manual vacuum**:
   ```bash
   sqlite3 data/angel_ohlcv_cache.db "VACUUM;"
   ```

---

## 🌐 API Issues

### Issue: Angel One API Authentication Fails

**Symptoms:**
- Error: "Invalid credentials"
- Login fails

**Solutions:**

1. **Verify credentials**:
   ```bash
   cat .env.angel
   # Should have:
   # ANGEL_CLIENT_ID=...
   # ANGEL_PASSWORD=...
   # ANGEL_API_KEY=...
   ```

2. **Test login manually**:
   ```python
   from SmartApi import SmartConnect

   client = SmartConnect(api_key="YOUR_KEY")
   data = client.generateSession("CLIENT_ID", "PASSWORD")
   print(data)
   ```

3. **API key expired**:
   - Generate new API key from Angel One dashboard
   - Update `.env.angel`

---

### Issue: Angel One Rate Limit Exceeded

**Symptoms:**
- Error: "Rate limit exceeded"
- HTTP 429 responses

**Solutions:**

1. **Rate limiter should handle this**:
   - Exponential backoff automatically slows down
   - Circuit breaker opens if persistent

2. **Manually increase delays**:
   ```python
   agent = AngelOneRateLimiterAgent(
       client=client,
       request_delay=1.0  # Default: 0.33 (3 req/sec)
   )
   ```

3. **Use cache aggressively**:
   - Increase TTL to avoid refetching
   - Run historical backfill to minimize API calls

---

### Issue: BSE API Returns Error

**Symptoms:**
- Error: "Failed to fetch BSE earnings"
- HTTP 500/503 responses

**Solutions:**

1. **BSE API is down**:
   - This is temporary, retry later
   - Use cached data if available

2. **Date range invalid**:
   ```python
   # BSE limits date range
   # Try smaller windows
   announcements = tool.fetch_earnings_calendar(
       from_date=datetime.now(),
       to_date=datetime.now() + timedelta(days=7)  # Max 7-14 days
   )
   ```

3. **Request format changed**:
   - BSE may update API
   - Check latest request format
   - Update `bse_earnings_calendar_tool.py` if needed

---

## 🧪 Test Failures

### Issue: Tests Failing After Update

**Symptoms:**
- Previously passing tests now fail
- Errors in test suite

**Solutions:**

1. **Clear test artifacts**:
   ```bash
   rm -rf .pytest_cache
   rm -rf __pycache__
   find . -name "*.pyc" -delete
   ```

2. **Update test dependencies**:
   ```bash
   pip install -r requirements-test.txt --upgrade
   ```

3. **Reset test databases**:
   ```bash
   # Tests use temp databases, but check:
   rm -rf /tmp/test_*.db
   ```

4. **Run tests with verbose output**:
   ```bash
   python3 -m pytest tests/unit/agents/ -vv --tb=long
   ```

---

### Issue: Integration Test Fails

**Symptoms:**
- Integration test skipped or fails
- Requires real API connection

**Solutions:**

1. **Integration test requires real API**:
   - This is expected to be skipped by default
   - To run: Set environment variable `RUN_INTEGRATION_TESTS=1`

   ```bash
   RUN_INTEGRATION_TESTS=1 python3 -m pytest tests/unit/agents/test_angel_rate_limiter_agent.py::test_real_api_integration -v
   ```

2. **Provide real credentials**:
   - Ensure `.env.angel` has valid credentials
   - Test credentials work with manual API call first

---

## ⚡ Performance Issues

### Issue: Backtest Running Slow Despite Caching

**Symptoms:**
- Backtest still takes 30+ minutes
- Cache hit rate is high but performance poor

**Solutions:**

1. **Check BSE filtering**:
   ```python
   # Ensure BSE filtering is enabled
   bt = AngelBacktester(enable_bse_filtering=True)
   ```

2. **Profile the bottleneck**:
   ```python
   import cProfile

   cProfile.run('bt.run_backtest(...)', 'profile_stats')

   # Analyze
   import pstats
   stats = pstats.Stats('profile_stats')
   stats.sort_stats('cumulative')
   stats.print_stats(20)
   ```

3. **Database query optimization**:
   ```bash
   # Check indexes exist
   sqlite3 data/angel_ohlcv_cache.db ".indexes"

   # If missing, reinitialize
   python3 agents/data/scripts/init_cache_db.py
   ```

4. **Reduce universe size**:
   - Use BSE filtering
   - Or manually filter to fewer symbols

---

### Issue: High Memory Usage

**Symptoms:**
- Python process using >1 GB RAM
- System becomes slow

**Solutions:**

1. **Reduce batch size**:
   ```python
   # In backfill
   tool = HistoricalBackfillTool(batch_size=5)  # Default: 10
   ```

2. **Process in chunks**:
   ```python
   # Instead of all Nifty 50 at once
   for chunk in chunks(NIFTY_50, size=10):
       results = agent.fetch_batch(chunk, ...)
       # Process results
   ```

3. **Clear cache periodically**:
   ```python
   import gc
   gc.collect()  # Force garbage collection
   ```

---

## 🔗 Integration Issues

### Issue: Backtest Not Using Rate Limiter

**Symptoms:**
- Every run makes full API calls
- No caching observed

**Solutions:**

1. **Check integration**:
   ```bash
   grep -n "AngelOneRateLimiterAgent" backtest_with_angel.py
   # Should show import and usage
   ```

2. **Verify agent initialization**:
   ```python
   # In backtest_with_angel.py __init__
   self.rate_limiter_agent = AngelOneRateLimiterAgent(
       client=self.client,
       cache_ttl_hours=24
   )
   ```

3. **Check fetch method**:
   ```python
   # Should use rate_limiter_agent.fetch_with_cache()
   # Not direct client.fetch_ohlcv()
   ```

---

### Issue: BSE Filtering Not Working

**Symptoms:**
- Universe not reduced
- All symbols processed

**Solutions:**

1. **Check if enabled**:
   ```python
   bt = AngelBacktester(
       enable_bse_filtering=True  # Must be True
   )
   ```

2. **Verify filtering logic**:
   ```python
   # In run_backtest(), should have:
   if self.enable_bse_filtering and self.bse_filter_agent:
       result = self.bse_filter_agent.filter_universe_by_earnings(...)
       symbols = result['filtered_universe']
   ```

---

## 🔬 Advanced Debugging

### Enable Debug Logging

```python
import logging

# Console logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# File logging
logging.basicConfig(
    level=logging.DEBUG,
    filename='debug.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Inspect Database Contents

```bash
# Count cached symbols
sqlite3 data/angel_ohlcv_cache.db "SELECT COUNT(DISTINCT symbol) FROM ohlcv_data;"

# Check date range
sqlite3 data/angel_ohlcv_cache.db "SELECT MIN(timestamp), MAX(timestamp) FROM ohlcv_data WHERE symbol='RELIANCE';"

# Check cache freshness
sqlite3 data/angel_ohlcv_cache.db "SELECT symbol, MAX(cached_at) FROM ohlcv_data GROUP BY symbol;"

# Check data gaps
sqlite3 data/angel_ohlcv_cache.db "
SELECT symbol, COUNT(*) as rows,
       MIN(timestamp) as first_date,
       MAX(timestamp) as last_date
FROM ohlcv_data
GROUP BY symbol;
"
```

### Test Individual Components

```python
# Test cache tool
from agents.data.tools.enhanced_sqlite_cache_tool import EnhancedSQLiteCacheTool
tool = EnhancedSQLiteCacheTool()
tool.store_ohlcv([...])  # Store test data
result = tool.get_cached_ohlcv(...)  # Retrieve
print(result)

# Test backoff tool
from agents.data.tools.exponential_backoff_tool import ExponentialBackoffTool
tool = ExponentialBackoffTool()
result = tool.execute_with_backoff(lambda: "test")
print(result)

# Test BSE scraping
from agents.filtering.tools.bse_earnings_calendar_tool import BSEEarningsCalendarTool
tool = BSEEarningsCalendarTool()
announcements = tool.fetch_earnings_calendar(7)
print(len(announcements))
```

### Network Debugging

```bash
# Test Angel One API
curl -X POST https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword \
  -H "Content-Type: application/json" \
  -d '{"clientcode":"YOUR_CLIENT_ID","password":"YOUR_PASSWORD"}'

# Test BSE API
curl -X POST https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w \
  -H "Content-Type: application/json" \
  -d '{"FromDate":"21/11/2024","ToDate":"28/11/2024","Pageno":"1","Flag":"1","strCat":"-1","strPrevDate":"21/11/2024","strScrip":""}'
```

---

## 📞 Still Having Issues?

### Collect Diagnostic Information

```bash
# System info
python3 --version
pip list | grep -E "(pytest|sqlite|requests)"

# Database info
ls -lh data/*.db
sqlite3 data/angel_ohlcv_cache.db "PRAGMA integrity_check;"

# Test results
python3 -m pytest tests/unit/agents/ -v > test_results.txt 2>&1

# Health report
python3 agents/cache/scripts/cache_health_report.py > health_report.txt
```

### Common Error Messages

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| "database is locked" | Multiple connections | Close other connections, increase timeout |
| "Circuit breaker is open" | API failures | Check API connectivity, wait 60s, reset |
| "Cache error. Falling back to API." | Cache tool error | Check database exists, verify permissions |
| "BSE scraping failed" | BSE API down | Use cached data, retry later |
| "No earnings announcements found" | No earnings in window | Increase lookforward_days |
| "Invalid credentials" | Angel One auth fail | Verify .env.angel credentials |
| "Rate limit exceeded" | Too many requests | Increase request_delay |

---

**Troubleshooting Guide Version**: 1.0.0
**Last Updated**: November 21, 2025
**For System Version**: 1.0.0
**Status**: Complete ✅
