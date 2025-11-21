# Daily Cache Maintenance Skill

**Agent:** HistoricalCacheManagerAgent
**Purpose:** Automated daily cache updates and health monitoring
**Priority:** 3
**Status:** Production Ready

---

## 🎯 What This Does

Keeps cache fresh with daily incremental updates (only latest data), preventing stale data and ensuring backtests always use current prices.

**Update Strategy:** Fetch only the last 1-2 days per symbol (minimal API calls)
**Frequency:** Daily after market close (5 PM IST)
**API Calls:** ~50 per day (one per symbol)

---

## 📋 Quick Start

### Setup Cron Job (Recommended)

```bash
# Edit crontab
crontab -e

# Add daily update (5 PM IST, Mon-Fri)
0 17 * * 1-5 cd /path/to/aksh && python3 agents/cache/scripts/daily_cache_update.py >> logs/daily_update.log 2>&1

# Add weekly cleanup (Sunday 2 AM)
0 2 * * 0 cd /path/to/aksh && python3 agents/cache/scripts/weekly_cache_cleanup.py >> logs/weekly_cleanup.log 2>&1
```

### Manual Run

```bash
# Run daily update
python3 agents/cache/scripts/daily_cache_update.py

# Check health after update
python3 agents/cache/scripts/cache_health_report.py
```

### Python API

```python
from agents.cache.historical_cache_manager_agent import HistoricalCacheManagerAgent
from agents.data.angel_rate_limiter_agent import AngelOneRateLimiterAgent

cache_manager = HistoricalCacheManagerAgent()

# Run automated maintenance (update + health check)
results = cache_manager.run_automated_maintenance(
    rate_limiter_agent=rate_limiter,
    mode="update_and_check"
)
```

---

## 🏗️ Maintenance Workflow

### Daily Maintenance (Automated)

```
5:00 PM IST
   ↓
Market Closes
   ↓
daily_cache_update.py runs
   ↓
For each symbol:
  - Check last cached date
  - Fetch only new data (1-2 days)
  - Update cache
   ↓
Run health check
   ↓
Log results
   ↓
Done (2-3 minutes)
```

### Weekly Maintenance (Automated)

```
Sunday 2:00 AM
   ↓
weekly_cache_cleanup.py runs
   ↓
Delete data older than 365 days
   ↓
VACUUM database
   ↓
Clean earnings cache (90 days)
   ↓
Done (1-2 minutes)
```

---

## 📊 Usage Examples

### Example 1: Automated Daily Update

```python
# This is what the cron job does
from agents.cache.historical_cache_manager_agent import HistoricalCacheManagerAgent
from agents.data.angel_rate_limiter_agent import AngelOneRateLimiterAgent
from src.data.angel_one_client import AngelOneClient

client = AngelOneClient()
client.authenticate()

rate_limiter = AngelOneRateLimiterAgent(client=client)
cache_manager = HistoricalCacheManagerAgent()

# Run daily maintenance
results = cache_manager.run_automated_maintenance(
    rate_limiter_agent=rate_limiter,
    mode="update_and_check"
)

# Log results
update = results['update']
health = results['health']

print(f"Updated: {update['symbols_updated']} symbols")
print(f"New rows: {update['new_rows_added']}")
print(f"Health: {health['status']}")
```

### Example 2: Update Specific Symbols

```python
# Update only Nifty 50
NIFTY_50 = ['RELIANCE', 'TCS', 'INFY', ...]

result = cache_manager.run_daily_update(
    rate_limiter_agent=rate_limiter,
    symbols=NIFTY_50
)

print(f"Updated {result['symbols_updated']} symbols")
```

### Example 3: Update All Cached Symbols

```python
# Automatically updates all symbols in cache
result = cache_manager.run_daily_update(
    rate_limiter_agent=rate_limiter,
    symbols=None  # None = all cached symbols
)
```

### Example 4: Manual Health Check

```python
# Check cache health anytime
health = cache_manager.run_health_check()

if health['status'] != 'HEALTHY':
    print(f"⚠️  Issues detected:")
    for issue in health['issues']:
        print(f"  - {issue}")

    print(f"\nRecommendations:")
    for rec in health['recommendations']:
        print(f"  💡 {rec}")
```

### Example 5: Check Update Status

```python
from agents.cache.tools.incremental_update_tool import IncrementalUpdateTool

update_tool = IncrementalUpdateTool()

# Check if symbol needs update
status = update_tool.get_update_status('RELIANCE')

print(f"Symbol: {status['symbol']}")
print(f"Last date: {status['last_date']}")
print(f"Days stale: {status['days_stale']}")
print(f"Needs update: {status['needs_update']}")
```

---

## ⚙️ Configuration

### Update Frequency

**Daily (Recommended):**
- Updates after market close
- Minimal API calls (~50)
- Fast execution (2-3 min)

```bash
# Cron: 5 PM IST Mon-Fri
0 17 * * 1-5 python3 agents/cache/scripts/daily_cache_update.py
```

**Manual (As Needed):**
- Run before backtests
- Run after data gaps detected

```bash
python3 agents/cache/scripts/daily_cache_update.py
```

### Cleanup Configuration

**Weekly (Recommended):**
```bash
# Keep 1 year of data
python3 agents/cache/scripts/weekly_cache_cleanup.py --keep-days 365
```

**Monthly (Conservative):**
```bash
# Keep 2 years of data
python3 agents/cache/scripts/weekly_cache_cleanup.py --keep-days 730
```

### Logging

```python
# Configure logging in script
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_cache_update.log'),
        logging.StreamHandler()
    ]
)
```

---

## 📈 Performance Metrics

### Daily Update Performance

| Metric | Nifty 50 | Notes |
|--------|----------|-------|
| Symbols updated | 50 | All Nifty 50 |
| New rows added | 50 | One day per symbol |
| API calls | 50 | One per symbol |
| Duration | 2-3 min | Very fast |
| Cache hit rate | 0% | Force refresh for latest |

### Weekly Cleanup Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Rows deleted | Varies | Depends on age |
| Database size before | ~200 MB | 5 years data |
| Database size after | ~50 MB | 1 year data |
| Duration | 1-2 min | VACUUM included |

### Cache Freshness

- **Without daily updates:** Data becomes stale after 1 day
- **With daily updates:** Always current (updated daily)
- **Stale threshold:** 2 days (configurable)

---

## 🔧 Troubleshooting

### Issue: Daily Update Fails

**Symptom:** Cron job fails, no updates

**Solutions:**
```bash
# Check logs
tail -f logs/daily_cache_update.log

# Test authentication
python3 -c "
from src.data.angel_one_client import AngelOneClient
client = AngelOneClient()
print('Auth:', client.authenticate())
"

# Run manually to see errors
python3 agents/cache/scripts/daily_cache_update.py
```

### Issue: High API Call Count

**Symptom:** Daily update uses >100 API calls

**Cause:** Cache doesn't have recent data

**Solution:**
```python
# Check last cached dates
from agents.cache.tools.incremental_update_tool import IncrementalUpdateTool

tool = IncrementalUpdateTool()
for symbol in ['RELIANCE', 'TCS', 'INFY']:
    status = tool.get_update_status(symbol)
    print(f"{symbol}: {status['days_stale']} days stale")

# If many symbols are very stale, run backfill
# agents/cache/scripts/backfill_nifty50.py --years 1
```

### Issue: Cron Job Not Running

**Symptom:** No daily updates happening

**Diagnosis:**
```bash
# Check cron is configured
crontab -l

# Check cron logs
grep CRON /var/log/syslog  # Linux
# or
grep cron /var/log/system.log  # macOS

# Test cron job manually
cd /path/to/aksh && python3 agents/cache/scripts/daily_cache_update.py
```

### Issue: Health Check Shows Warnings

**Symptom:** Health status is WARNING or CRITICAL

**Solutions:**
```python
health = cache_manager.run_health_check()

# Check specific issues
for issue in health['issues']:
    print(f"Issue: {issue}")

# Follow recommendations
for rec in health['recommendations']:
    print(f"Action: {rec}")

# Common fixes:
# - Run backfill for gaps
# - Run daily update for staleness
# - Run cleanup for size
```

---

## 🎯 Best Practices

### 1. Setup Automated Updates Immediately

```bash
# Don't rely on manual updates - automate from day 1
crontab -e

# Add both daily and weekly jobs
0 17 * * 1-5 cd /path/to/aksh && python3 agents/cache/scripts/daily_cache_update.py
0 2 * * 0 cd /path/to/aksh && python3 agents/cache/scripts/weekly_cache_cleanup.py
```

### 2. Monitor Logs Weekly

```bash
# Check for failures
grep -i error logs/daily_cache_update.log

# Check update success
grep -i "UPDATE COMPLETE" logs/daily_cache_update.log | tail -7
```

### 3. Run Health Checks Weekly

```bash
# Generate weekly health report
python3 agents/cache/scripts/cache_health_report.py \
    --output reports/health_$(date +%Y%m%d).txt
```

### 4. Keep Logs Organized

```bash
# Log rotation (keep last 30 days)
find logs/ -name "*.log" -mtime +30 -delete
```

### 5. Backup Before Major Operations

```bash
# Backup before cleanup
cp data/angel_ohlcv_cache.db backups/cache_$(date +%Y%m%d).db
python3 agents/cache/scripts/weekly_cache_cleanup.py
```

---

## 📊 Monitoring Checklist

### Daily Checks (Automated)

- ✅ Daily update runs successfully
- ✅ All symbols updated
- ✅ No authentication failures
- ✅ Logs written correctly

### Weekly Checks (Manual)

- ✅ Run health report
- ✅ Review any issues
- ✅ Check database size
- ✅ Verify freshness >90%

### Monthly Checks (Manual)

- ✅ Review failed symbols (if any)
- ✅ Check data gaps
- ✅ Verify cron jobs running
- ✅ Rotate logs

---

## 💡 Tips

1. **Set and forget** - Automate everything with cron
2. **Check logs weekly** - Catch issues early
3. **Run health checks** - Monthly verification
4. **Keep 1 year** - Good balance of history and size
5. **Backup before cleanup** - Safety first

---

## 🔗 Related

- **Priority 1:** [Rate Limited Fetching](rate-limited-fetching.md)
- **Priority 2:** [BSE Earnings Filtering](bse-earnings-filtering.md)
- **Historical Backfill:** [Historical Cache Backfill](historical-backfill.md)

---

## 📝 Cron Examples

### Complete Crontab Setup

```bash
# Edit crontab
crontab -e

# Add these lines:

# Daily cache update (5 PM IST, Mon-Fri)
0 17 * * 1-5 cd /Users/srijan/Desktop/aksh && /usr/bin/python3 agents/cache/scripts/daily_cache_update.py >> logs/daily_update.log 2>&1

# Weekly cleanup (Sunday 2 AM)
0 2 * * 0 cd /Users/srijan/Desktop/aksh && /usr/bin/python3 agents/cache/scripts/weekly_cache_cleanup.py --keep-days 365 >> logs/weekly_cleanup.log 2>&1

# Weekly health report (Sunday 3 AM)
0 3 * * 0 cd /Users/srijan/Desktop/aksh && /usr/bin/python3 agents/cache/scripts/cache_health_report.py --output reports/health_$(date +\%Y\%m\%d).txt
```

---

**Created:** November 21, 2025
**Version:** 1.0
**Status:** Production Ready
