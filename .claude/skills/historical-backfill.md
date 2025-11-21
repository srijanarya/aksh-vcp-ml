# Historical Cache Backfill Skill

**Agent:** HistoricalCacheManagerAgent
**Purpose:** One-time population of cache with years of historical OHLCV data
**Priority:** 3
**Status:** Production Ready

---

## 🎯 What This Does

Populates cache with 3-5 years of historical data in a single run, enabling instant backtests on subsequent runs without API calls for historical data.

**Before:** Every backtest fetches 3 years × 50 stocks = 150+ API calls
**After:** First backtest populates cache, subsequent backtests use cached data (0 API calls for historical)

---

## 📋 Quick Start

### Step 1: One-Time Backfill

```bash
# Backfill Nifty 50 with 3 years of data
python3 agents/cache/scripts/backfill_nifty50.py --years 3 --resume

# This takes 1-2 hours but only needs to run once
```

### Step 2: Setup Daily Updates

```bash
# Add to crontab (run at 5 PM IST after market close)
0 17 * * 1-5 cd /path/to/aksh && python3 agents/cache/scripts/daily_cache_update.py
```

### Step 3: Verify Cache

```bash
# Check cache health
python3 agents/cache/scripts/cache_health_report.py
```

---

## 🏗️ Architecture

### Components

**1. HistoricalBackfillTool**
- One-time backfill with resume capability
- Batch processing (10 symbols at a time)
- Progress checkpoints
- Error recovery
- Location: `agents/cache/tools/historical_backfill_tool.py`

**2. IncrementalUpdateTool**
- Daily incremental updates (only latest data)
- Minimal API calls (1 per symbol per day)
- Automatic staleness detection
- Location: `agents/cache/tools/incremental_update_tool.py`

**3. CacheHealthMonitorTool**
- Coverage metrics
- Freshness tracking
- Data quality checks
- Health reports
- Location: `agents/cache/tools/cache_health_monitor_tool.py`

**4. HistoricalCacheManagerAgent**
- Main coordinator
- Unified interface
- Automated maintenance
- Location: `agents/cache/historical_cache_manager_agent.py`

### Data Flow

```
One-Time Backfill
   ↓
HistoricalBackfillTool → Cache DB (3-5 years)
   ↓
Daily Updates
   ↓
IncrementalUpdateTool → Add latest day
   ↓
Health Monitoring
   ↓
CacheHealthMonitorTool → Reports
```

---

## 📊 Usage Examples

### Example 1: Initial Backfill (Nifty 50)

```python
from agents.cache.historical_cache_manager_agent import HistoricalCacheManagerAgent
from agents.data.angel_rate_limiter_agent import AngelOneRateLimiterAgent
from src.data.angel_one_client import AngelOneClient

# Initialize
client = AngelOneClient()
client.authenticate()

rate_limiter = AngelOneRateLimiterAgent(client=client)
cache_manager = HistoricalCacheManagerAgent(backfill_batch_size=10)

# Backfill Nifty 50 (3 years)
NIFTY_50 = ['RELIANCE', 'TCS', 'INFY', ...]  # All 50 symbols

result = cache_manager.run_initial_backfill(
    rate_limiter_agent=rate_limiter,
    symbols=NIFTY_50,
    years_back=3,
    resume=True  # Resume if interrupted
)

print(f"Backfilled {result['rows_cached']} rows")
```

### Example 2: Daily Incremental Update

```python
# Run daily after market close
result = cache_manager.run_daily_update(
    rate_limiter_agent=rate_limiter,
    symbols=None  # Update all cached symbols
)

print(f"Updated: {result['symbols_updated']} symbols")
print(f"New rows: {result['new_rows_added']}")
print(f"API calls: {result['api_calls_made']}")
```

### Example 3: Check Cache Health

```python
health = cache_manager.run_health_check()

print(f"Status: {health['status']}")  # HEALTHY, WARNING, CRITICAL
print(f"Symbols: {health['metrics']['coverage']['total_symbols']}")
print(f"Freshness: {health['metrics']['freshness']['freshness_rate']:.1f}%")

# Check recommendations
for rec in health['recommendations']:
    print(f"  💡 {rec}")
```

### Example 4: Automated Maintenance

```python
# Run both update + health check
results = cache_manager.run_automated_maintenance(
    rate_limiter_agent=rate_limiter,
    mode="update_and_check"
)

# Perfect for daily cron job
```

### Example 5: Resume Interrupted Backfill

```python
# If backfill was interrupted, simply run again with resume=True
result = cache_manager.run_initial_backfill(
    rate_limiter_agent=rate_limiter,
    symbols=NIFTY_50,
    years_back=3,
    resume=True  # Picks up where it left off
)
```

---

## 🎓 Decision Tree

```
START
  │
  ├─ Need historical data in cache? → YES
  │    │
  │    ├─ First time setup?
  │    │   YES: Run backfill_nifty50.py (1-2 hours, one-time)
  │    │   NO: Already have cache
  │    │
  │    ├─ Setup daily updates
  │    │   Add daily_cache_update.py to cron (5 PM IST)
  │    │
  │    ├─ Setup weekly cleanup
  │    │   Add weekly_cache_cleanup.py to cron (Sunday 2 AM)
  │    │
  │    └─ Monitor health
  │        Run cache_health_report.py weekly
  │
  └─ Don't need historical cache? → NO
       │
       └─ Use real-time fetching only
           (slower but no setup needed)
```

---

## ⚙️ Configuration

### Backfill Parameters

```python
cache_manager = HistoricalCacheManagerAgent(
    backfill_batch_size=10,  # Symbols per batch
    incremental_lookback_days=2  # Safety margin for updates
)

# Run backfill
result = cache_manager.run_initial_backfill(
    rate_limiter_agent=rate_limiter,
    symbols=symbols,
    years_back=3,  # 1-5 years recommended
    exchange="NSE",
    interval="ONE_DAY",
    resume=True  # Resume from checkpoint
)
```

### Update Frequency

**Daily (Recommended):**
```bash
# Cron: 5 PM IST Mon-Fri
0 17 * * 1-5 python3 agents/cache/scripts/daily_cache_update.py
```

**Weekly Cleanup:**
```bash
# Cron: 2 AM Sunday
0 2 * * 0 python3 agents/cache/scripts/weekly_cache_cleanup.py --keep-days 365
```

---

## 📈 Performance Metrics

### Backfill Performance

| Metric | Nifty 50 (3 years) | Notes |
|--------|-------------------|-------|
| Total API calls | ~500 | One-time cost |
| Duration | 60-90 minutes | Depends on rate limits |
| Rows cached | ~37,500 | 50 stocks × 750 days |
| Database size | ~15-20 MB | Compressed |

### Daily Update Performance

| Metric | Value | Notes |
|--------|-------|-------|
| API calls | 50 | One per symbol |
| Duration | 2-3 minutes | Very fast |
| New rows | 50 | One day per symbol |
| Frequency | Daily | After market close |

### Cache Efficiency

- **First backtest:** Uses cache, 0 API calls for historical
- **Subsequent backtests:** Uses cache, 0 API calls
- **Overall savings:** 100% for historical data

---

## 🔧 Troubleshooting

### Issue: Backfill Interrupted

**Symptom:** Backfill stops mid-way

**Solution:** Resume from checkpoint
```bash
# Simply run again with --resume flag
python3 agents/cache/scripts/backfill_nifty50.py --resume

# Checkpoint file: data/backfill_checkpoint.json
```

### Issue: Low Cache Hit Rate

**Symptom:** Health report shows low freshness

**Solution:** Run daily update
```python
cache_manager.run_daily_update(rate_limiter_agent)
```

### Issue: Data Gaps Detected

**Symptom:** Health report shows symbols with gaps

**Solution:** Re-backfill affected symbols
```python
# Get symbols with gaps from health report
health = cache_manager.run_health_check()
gap_symbols = [s['symbol'] for s in health['metrics']['quality']['gap_details']]

# Re-backfill
cache_manager.run_initial_backfill(
    rate_limiter_agent=rate_limiter,
    symbols=gap_symbols,
    years_back=3
)
```

### Issue: Database Too Large

**Symptom:** Database >500 MB

**Solution:** Run cleanup
```bash
# Keep only 1 year
python3 agents/cache/scripts/weekly_cache_cleanup.py --keep-days 365
```

---

## 🎯 Best Practices

### 1. Run Backfill During Off-Hours

```bash
# Schedule overnight to avoid interfering with trading hours
nohup python3 agents/cache/scripts/backfill_nifty50.py --years 3 &
```

### 2. Monitor Progress

```python
# Check checkpoint file
import json
with open('data/backfill_checkpoint.json') as f:
    checkpoint = json.load(f)

print(f"Completed: {checkpoint['completed']}")
print(f"Remaining: {len(checkpoint['remaining_symbols'])}")
```

### 3. Setup Automated Daily Updates

```bash
# Add to crontab for automatic maintenance
crontab -e

# Add line:
0 17 * * 1-5 cd /path/to/aksh && python3 agents/cache/scripts/daily_cache_update.py >> logs/daily_update.log 2>&1
```

### 4. Regular Health Checks

```bash
# Weekly health report
python3 agents/cache/scripts/cache_health_report.py --output reports/cache_health_$(date +%Y%m%d).txt
```

### 5. Backup Before Cleanup

```bash
# Backup before weekly cleanup
cp data/angel_ohlcv_cache.db data/backups/cache_$(date +%Y%m%d).db
python3 agents/cache/scripts/weekly_cache_cleanup.py
```

---

## 📚 Scripts Reference

### backfill_nifty50.py

One-time Nifty 50 backfill

```bash
python3 agents/cache/scripts/backfill_nifty50.py --years 3 --resume
```

Options:
- `--years`: Years of historical data (default: 3)
- `--resume`: Resume from checkpoint
- `--batch-size`: Batch size (default: 10)

### daily_cache_update.py

Daily incremental update

```bash
python3 agents/cache/scripts/daily_cache_update.py
```

Perfect for cron jobs. Updates all cached symbols.

### weekly_cache_cleanup.py

Weekly database cleanup

```bash
python3 agents/cache/scripts/weekly_cache_cleanup.py --keep-days 365
```

Options:
- `--keep-days`: Days of data to keep (default: 365)

### cache_health_report.py

Generate health report

```bash
python3 agents/cache/scripts/cache_health_report.py --output report.txt
```

Options:
- `--output`: Output file (default: stdout)

---

## 💡 Tips

1. **Start with 3 years** - Good balance between history and time
2. **Use resume capability** - Interruptions are handled gracefully
3. **Setup cron jobs** - Automated maintenance prevents staleness
4. **Monitor health weekly** - Catch issues early
5. **Combine with Priority 1** - Rate limiting + caching = 90%+ savings

---

## 🔗 Related

- **Priority 1:** [Rate Limited Fetching](rate-limited-fetching.md)
- **Priority 2:** [BSE Earnings Filtering](bse-earnings-filtering.md)
- **Priority 4:** [TradingView Visualization](tradingview-visualization.md)

---

**Created:** November 21, 2025
**Version:** 1.0
**Status:** Production Ready
