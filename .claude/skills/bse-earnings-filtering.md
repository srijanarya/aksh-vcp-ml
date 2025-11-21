# BSE Earnings Filtering Skill

**Agent:** BSEFilteringAgent
**Purpose:** Pre-filter stock universe using BSE earnings calendar to reduce API calls by 70%
**Priority:** 2
**Status:** Production Ready

---

## 🎯 What This Does

Reduces backtest universe by **70%** by only analyzing stocks with upcoming earnings announcements, dramatically reducing expensive OHLCV API calls.

**Before:** Backtest all 50 Nifty stocks = 500+ API calls
**After:** Backtest only 15 stocks with earnings = 150 API calls (70% reduction)

---

## 📋 Quick Start

### Step 1: Initialize Databases

```bash
python3 agents/filtering/scripts/init_earnings_db.py
```

### Step 2: Use in Backtest

```python
from agents.filtering.bse_filtering_agent import BSEFilteringAgent

# Initialize agent
agent = BSEFilteringAgent(default_lookforward_days=7)

# Initialize mappings (one-time)
agent.initialize_mappings()

# Filter universe
result = agent.filter_universe_by_earnings(
    original_universe=['RELIANCE', 'TCS', 'INFY', ...],
    lookforward_days=7
)

print(f"Filtered: {result['original_size']} → {result['filtered_size']} stocks")
```

### Step 3: Enable in Backtest

```python
# In backtest_with_angel.py
bt = AngelBacktester(
    enable_bse_filtering=True,  # Enable BSE filtering
    lookforward_days=7          # Look 7 days ahead
)
```

---

## 🏗️ Architecture

### Components

**1. BSEEarningsCalendarTool**
- Scrapes BSE API for earnings announcements
- Caches results in SQLite (24h TTL)
- Filters for earnings-related keywords
- Location: `agents/filtering/tools/bse_earnings_calendar_tool.py`

**2. StockFilterByEarningsTool**
- Maps BSE codes to NSE symbols
- Filters universe based on earnings whitelist
- Tracks mapping coverage
- Location: `agents/filtering/tools/stock_filter_by_earnings_tool.py`

**3. BSEFilteringAgent**
- Main coordinator
- Fetches earnings + filters universe
- Tracks performance metrics
- Location: `agents/filtering/bse_filtering_agent.py`

### Data Flow

```
BSE API
   ↓
BSEEarningsCalendarTool → earnings_calendar.db
   ↓
BSEFilteringAgent
   ↓
StockFilterByEarningsTool → bse_nse_mapping.db
   ↓
Filtered Universe (NSE symbols)
   ↓
Backtest Engine
```

---

## 📊 Usage Examples

### Example 1: Basic Filtering

```python
from agents.filtering.bse_filtering_agent import BSEFilteringAgent

agent = BSEFilteringAgent()
agent.initialize_mappings()

# Nifty 50 universe
nifty_50 = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', ...]

# Filter to stocks with earnings in next 7 days
result = agent.filter_universe_by_earnings(
    original_universe=nifty_50,
    lookforward_days=7
)

print(f"Original: {result['original_size']} stocks")
print(f"Filtered: {result['filtered_size']} stocks")
print(f"Reduction: {result['reduction_pct']:.1f}%")
```

### Example 2: Check Single Stock

```python
# Check if a stock should be analyzed
should_analyze = agent.should_analyze_stock(
    nse_symbol='RELIANCE',
    lookforward_days=7
)

if should_analyze:
    print("RELIANCE has earnings coming up - analyze it!")
else:
    print("RELIANCE has no earnings - skip it!")
```

### Example 3: Get Earnings Whitelist

```python
# Get list of all NSE symbols with upcoming earnings
whitelist = agent.get_earnings_whitelist(lookforward_days=7)

print(f"Stocks to analyze: {len(whitelist)}")
for symbol in whitelist:
    print(f"  - {symbol}")
```

### Example 4: Warm Earnings Cache

```python
# Pre-fetch 14 days of earnings data
agent.warm_earnings_cache(days_ahead=14)

# Now filtering will be instant (cache hit)
result = agent.filter_universe_by_earnings(
    original_universe=nifty_50,
    lookforward_days=7
)
```

### Example 5: Add Custom BSE-NSE Mappings

```python
from agents.filtering.tools.stock_filter_by_earnings_tool import StockFilterByEarningsTool

filter_tool = StockFilterByEarningsTool()

# Add single mapping
filter_tool.add_mapping(
    bse_code='500325',
    nse_symbol='RELIANCE',
    company_name='Reliance Industries'
)

# Add bulk mappings
mappings = [
    {'bse_code': '532540', 'nse_symbol': 'TCS'},
    {'bse_code': '500209', 'nse_symbol': 'INFY'},
]
filter_tool.add_mappings_bulk(mappings)
```

---

## 🎓 Decision Tree

```
START
  │
  ├─ Need 70% universe reduction? → YES
  │    │
  │    ├─ Initialize databases
  │    │   python3 agents/filtering/scripts/init_earnings_db.py
  │    │
  │    ├─ Add BSE-NSE mappings (if not Nifty 50)
  │    │   agent.initialize_mappings()
  │    │
  │    ├─ Enable in backtest
  │    │   bt = AngelBacktester(enable_bse_filtering=True)
  │    │
  │    └─ Run backtest
  │        Stocks filtered automatically!
  │
  └─ Don't need filtering? → NO
       │
       └─ Use backtest without BSE filtering
           bt = AngelBacktester(enable_bse_filtering=False)
```

---

## ⚙️ Configuration

### Lookforward Window

**7 days (default):** Conservative, only earnings very soon
**14 days:** Moderate, captures more stocks
**30 days:** Aggressive, minimal filtering

```python
# Configure at agent level
agent = BSEFilteringAgent(default_lookforward_days=14)

# Or per-call
result = agent.filter_universe_by_earnings(
    original_universe=symbols,
    lookforward_days=14  # Override default
)
```

### Cache TTL

```python
# Earnings cache: 24 hours (in tool)
earnings_tool = BSEEarningsCalendarTool(db_path="data/earnings_calendar.db")

# Force refresh if needed
agent.filter_universe_by_earnings(..., force_refresh=True)
```

### Database Paths

```python
agent = BSEFilteringAgent(
    earnings_db_path="data/earnings_calendar.db",
    mapping_db_path="data/bse_nse_mapping.db"
)
```

---

## 📈 Performance Metrics

### Expected Reductions

| Lookforward Window | Expected Reduction | Use Case |
|-------------------|-------------------|----------|
| 7 days | 60-80% | Earnings-focused backtest |
| 14 days | 40-60% | Balanced approach |
| 30 days | 20-40% | Broad coverage |

### Actual Performance

```python
# Get agent statistics
stats = agent.get_stats()

print(f"Total runs: {stats['total_runs']}")
print(f"Average reduction: {stats['average_reduction']:.1f}%")
print(f"Total BSE announcements: {stats['total_bse_announcements']}")
```

---

## 🔧 Troubleshooting

### Issue: No Stocks Filtered

**Symptom:** Filter returns original universe (0% reduction)

**Solutions:**
1. Check if BSE has earnings data for the period
2. Verify BSE-NSE mappings exist
3. Increase lookforward_days
4. Force refresh cache: `force_refresh=True`

```python
# Debug: Check BSE announcements
bse_codes = agent.earnings_tool.get_stocks_with_upcoming_earnings(days_ahead=7)
print(f"BSE codes with earnings: {len(bse_codes)}")

# Debug: Check mappings
coverage = agent.filter_tool.get_mapping_coverage()
print(f"Mappings available: {coverage['total_mappings']}")
```

### Issue: BSE API Fails

**Symptom:** No earnings data fetched from BSE

**Solutions:**
1. Check internet connection
2. Verify BSE website is accessible
3. Check rate limiting (0.5s between requests)
4. Review BSE API URL changes

```python
# Test BSE API directly
from agents.filtering.tools.bse_earnings_calendar_tool import BSEEarningsCalendarTool

tool = BSEEarningsCalendarTool()
announcements = tool.fetch_bse_announcements(
    from_date=datetime.now(),
    to_date=datetime.now() + timedelta(days=7),
    force_refresh=True
)

print(f"Fetched: {len(announcements)} announcements")
```

### Issue: High Unmapped Codes

**Symptom:** Many BSE codes can't be mapped to NSE

**Solution:** Add missing BSE-NSE mappings

```python
# Check unmapped codes
filter_result = agent.filter_universe_by_earnings(...)
print(f"Unmapped codes: {filter_result['unmapped_codes']}")

# Add mappings for your universe
filter_tool = agent.filter_tool
filter_tool.add_mapping(bse_code='XXX', nse_symbol='YYY')
```

### Issue: Database Locked

**Symptom:** "database is locked" error

**Solution:**
```bash
# Close other processes using the database
lsof data/earnings_calendar.db
lsof data/bse_nse_mapping.db

# Kill processes if needed
```

---

## 🎯 Best Practices

### 1. Initialize Mappings Once

```python
# First time setup
agent.initialize_mappings()

# Check coverage
coverage = agent.filter_tool.get_mapping_coverage()
print(f"Mappings: {coverage['total_mappings']}")
```

### 2. Warm Cache Before Large Backtests

```python
# Before running Nifty 50 backtest
agent.warm_earnings_cache(days_ahead=14)

# Now filtering is instant
result = agent.filter_universe_by_earnings(...)
```

### 3. Choose Appropriate Lookforward Window

- **7 days:** High-conviction earnings plays
- **14 days:** Balanced (recommended)
- **30 days:** Broad coverage

### 4. Monitor Filtering Efficiency

```python
result = agent.filter_universe_by_earnings(...)

if result['reduction_pct'] < 50:
    print("⚠️  Low filtering efficiency")
    print("   Consider increasing lookforward_days")
```

### 5. Cleanup Old Data Regularly

```python
# Weekly cleanup (keep 90 days)
agent.cleanup_old_data(days_to_keep=90)
```

---

## 📚 Integration Guide

### Integrate with Backtest

**Step 1:** Modify `__init__`

```python
class AngelBacktester:
    def __init__(self, enable_bse_filtering=False):
        # ... existing code ...

        if enable_bse_filtering:
            self.bse_filter_agent = BSEFilteringAgent()
```

**Step 2:** Add Filtering in `run_backtest`

```python
def run_backtest(self, symbols, start_date, end_date):
    if self.enable_bse_filtering:
        filter_result = self.bse_filter_agent.filter_universe_by_earnings(
            original_universe=symbols
        )
        symbols = filter_result['filtered_universe']

    # ... rest of backtest ...
```

**Step 3:** Enable When Running

```python
bt = AngelBacktester(enable_bse_filtering=True)
signals = bt.run_backtest(symbols=NIFTY_50, ...)
```

---

## 🧪 Testing

### Run Demo

```bash
# Test BSE filtering agent
python3 agents/filtering/bse_filtering_agent.py
```

### Run Unit Tests

```bash
# Full test suite
python3 -m pytest tests/unit/agents/filtering/ -v
```

---

## 📊 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Universe reduction | >70% | `result['reduction_pct']` |
| BSE data freshness | <24h | Check `scraped_at` |
| Mapping coverage | >80% | `get_mapping_coverage()` |
| Cache hit rate | >50% | Check logs |

---

## 💡 Tips

1. **Start with 7 days lookforward** - More conservative
2. **Warm cache daily** - Run cron job to fetch BSE data
3. **Add mappings incrementally** - As you discover unmapped codes
4. **Monitor BSE API changes** - Endpoints may change
5. **Combine with Rate Limiter** - Priority 1 + Priority 2 = 90% + 70% savings!

---

## 🔗 Related

- **Priority 1:** [Rate Limited Fetching](rate-limited-fetching.md)
- **Priority 3:** [Historical Cache Management](historical-backfill.md)
- **Priority 4:** [TradingView Visualization](tradingview-visualization.md)

---

**Created:** November 21, 2025
**Version:** 1.0
**Status:** Production Ready
