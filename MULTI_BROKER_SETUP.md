# Multi-Broker Backtesting Setup

## Overview

The multi-broker backtesting system automatically discovers and uses any of your broker accounts with intelligent fallback. It supports:

- **Angel One** (multiple accounts)
- **Zerodha** (multiple accounts)
- **Upstox** (multiple accounts)
- **Yahoo Finance** (free fallback)

### Key Features

✅ **Automatic Account Discovery** - Finds all configured broker accounts
✅ **Health Monitoring** - Tests which accounts are active
✅ **Intelligent Fallback** - Cache → Primary Broker → Alternate Broker → Yahoo
✅ **Multi-Account Support** - Use multiple accounts per broker
✅ **Full S/R Integration** - Complete support & resistance analysis

---

## Quick Start

### 1. List Available Brokers

```bash
python3 strategies/backtest_multi_broker.py --list-brokers
```

**Expected Output**:
```
📋 DISCOVERED BROKER ACCOUNTS
======================================================================

Found 3 broker account(s):

1. angel (angel_one)
   Path: /Users/srijan/vcp_clean_test/vcp/.env.angel
   Status: ⏳ UNTESTED

2. angel2 (angel_one)
   Path: /Users/srijan/Desktop/aksh/.env.angel2
   Status: ⏳ UNTESTED

3. zerodha1 (zerodha)
   Path: /Users/srijan/Desktop/aksh/.env.zerodha1
   Status: ⏳ UNTESTED
```

### 2. Test All Broker Connections

```bash
python3 strategies/backtest_multi_broker.py --test-all
```

**Expected Output**:
```
🔌 TESTING ALL BROKER ACCOUNTS
======================================================================

🔌 Testing angel (angel_one)...
   ✅ angel: Connected successfully

🔌 Testing angel2 (angel_one)...
   ❌ angel2: Your demat account is dormant

🔌 Testing zerodha1 (zerodha)...
   ⚠️  zerodha integration pending

======================================================================
✅ 1/3 accounts active
======================================================================
```

### 3. Run Backtest (Auto-Select Best Broker)

```bash
# Automatically uses best available account
python3 strategies/backtest_multi_broker.py
```

### 4. Run Backtest (Specific Broker)

```bash
# Use specific account
python3 strategies/backtest_multi_broker.py --broker angel2

# If that account is inactive, falls back to best available
```

---

## Setting Up Multiple Broker Accounts

### Angel One Accounts

You can have multiple Angel One accounts (e.g., personal, family members):

**Account 1 (Primary)**:
```bash
# Already exists at /Users/srijan/vcp_clean_test/vcp/.env.angel
```

**Account 2**:
```bash
# Create new credentials file
cp .env.angel.template .env.angel2

# Edit with second account credentials
nano .env.angel2

# Add:
export ANGEL_API_KEY="account2_api_key"
export ANGEL_CLIENT_ID="account2_client_id"
export ANGEL_MPIN="account2_mpin"
export ANGEL_TOTP_SECRET="account2_totp_secret"

# Test it
python3 strategies/backtest_multi_broker.py --test-all
```

**Account 3**:
```bash
cp .env.angel.template .env.angel3
nano .env.angel3
# Add third account credentials
```

### Zerodha Accounts

```bash
# Create Zerodha credentials file
nano .env.zerodha1

# Add (format will depend on Zerodha API):
export ZERODHA_API_KEY="your_api_key"
export ZERODHA_API_SECRET="your_api_secret"
export ZERODHA_USER_ID="your_user_id"
export ZERODHA_PASSWORD="your_password"
export ZERODHA_TOTP="your_totp_secret"
```

### Upstox Accounts

```bash
# Create Upstox credentials file
nano .env.upstox1

# Add:
export UPSTOX_API_KEY="your_api_key"
export UPSTOX_API_SECRET="your_api_secret"
export UPSTOX_ACCESS_TOKEN="your_access_token"
```

---

## File Naming Convention

The system automatically discovers credentials files following this pattern:

| Broker | File Names |
|--------|-----------|
| Angel One | `.env.angel`, `.env.angel1`, `.env.angel2`, `.env.angel3` |
| Zerodha | `.env.zerodha`, `.env.zerodha1`, `.env.zerodha2` |
| Upstox | `.env.upstox`, `.env.upstox1`, `.env.upstox2` |

**Search Locations**:
1. `/Users/srijan/Desktop/aksh/` (aksh project)
2. `/Users/srijan/vcp_clean_test/vcp/` (vcp project)
3. `~/.broker_credentials/` (dedicated credentials folder)

---

## Usage Examples

### Example 1: Auto-Select Best Broker

```bash
# System tests all brokers and uses first active one
python3 strategies/backtest_multi_broker.py

# Output shows which broker is being used:
# ✅ Selected broker: angel (angel_one)
# ✅ Data sources ready: Cache → Angel One → Yahoo Finance
```

### Example 2: Prefer Specific Broker

```bash
# Try to use angel2, fall back if inactive
python3 strategies/backtest_multi_broker.py --broker angel2

# If angel2 is inactive:
# ⚠️  Preferred broker 'angel2' not available
# ✅ Selected broker: angel (angel_one)
```

### Example 3: Custom Parameters

```bash
python3 strategies/backtest_multi_broker.py \
    --broker angel \
    --symbols RELIANCE TCS INFY HDFCBANK \
    --start-date 2023-06-01 \
    --end-date 2024-11-01 \
    --capital 500000
```

### Example 4: Yahoo Finance Fallback

```bash
# If NO broker accounts are active, automatically uses Yahoo Finance
python3 strategies/backtest_multi_broker.py

# Output:
# ⚠️  No broker accounts available
# ✅ Using Yahoo Finance (free data source)
```

---

## Data Source Priority

The system uses intelligent fallback with this priority:

```
1. SQLite Cache (fastest, 24h TTL)
   ↓ (if cache miss or stale)
2. Primary Broker (Angel One, Zerodha, etc.)
   ↓ (if broker fails)
3. Alternate Broker Account (if available)
   ↓ (if all brokers fail)
4. Yahoo Finance (free, always available)
```

### Example Flow:

```
Fetching TATAMOTORS data...
1. Check cache → MISS (no cached data)
2. Try Angel One (angel) → SUCCESS ✅
   Data source: angel_one

Fetching SAIL data...
1. Check cache → HIT ✅
   Data source: cache

Fetching VEDL data...
1. Check cache → MISS
2. Try Angel One (angel) → FAIL (rate limit)
3. Try Angel One (angel2) → FAIL (dormant)
4. Try Yahoo Finance → SUCCESS ✅
   Data source: yahoo_finance
```

---

## Current Setup Status

### Your Broker Accounts

Based on what we know:

| Account | Broker | Status | Action Needed |
|---------|--------|--------|---------------|
| angel | Angel One | ⏳ Dormant | Wait for KYC reactivation |
| angel2 | Angel One | ❓ Unknown | Set up if you have 2nd account |
| angel3 | Angel One | ❓ Unknown | Set up if you have 3rd account |

### Recommended Actions

**Option 1: Have Additional Angel One Accounts?**

If you have other Angel One accounts (family members, etc.):

```bash
# Set them up now
cp .env.angel.template .env.angel2
nano .env.angel2  # Add credentials

# Test
python3 strategies/backtest_multi_broker.py --test-all

# Use for backtest
python3 strategies/backtest_multi_broker.py --broker angel2
```

**Option 2: Have Zerodha/Upstox Accounts?**

```bash
# Create credentials file
nano .env.zerodha1
# or
nano .env.upstox1

# Add credentials (we'll need to implement the API integration)

# For now, the system will show:
# ⚠️  zerodha integration pending
```

**Option 3: Use Yahoo Finance (Works Now)**

```bash
# No setup needed, works immediately
python3 strategies/backtest_multi_broker.py

# If no broker accounts active, uses Yahoo automatically
```

---

## Expected Backtest Output

When everything is working:

```
======================================================================
🚀 MULTI-BROKER BACKTESTER WITH S/R
======================================================================
Period: 2023-01-01 to 2024-11-01
Capital: ₹100,000
======================================================================

======================================================================
🚀 INITIALIZING DATA SOURCES
======================================================================

Testing broker accounts...

🔌 Testing angel (angel_one)...
   ✅ angel: Connected successfully

======================================================================
✅ 1/1 accounts active
======================================================================

✅ Selected broker: angel (angel_one)
✅ Data sources ready: Cache → Angel One → Yahoo Finance

======================================================================
📊 Backtesting TATAMOTORS
======================================================================

Fetching MTF data for TATAMOTORS...
   Data source: angel_one
   ✅ Fetched 451 days, 96 weeks, 180 4H bars

Walking forward through 451 days...

🎯 Signal on 2023-03-15
   Entry: ₹425.50, S/R Quality: 75.0/100
   ✅ Exit: ₹458.80 (+7.83%)

📊 TATAMOTORS: 3 signals

... [more symbols] ...

======================================================================
📊 BACKTEST RESULTS
======================================================================

Data Source: angel (angel_one)

💰 Performance:
   Trades: 12
   Win Rate: 58.3%
   Avg Return: 1.85%
   Sharpe: 2.35
   Max DD: 4.2%
   Final Capital: ₹122,200
   Total Return: 22.2%

📊 S/R Metrics:
   Avg S/R Quality: 72.5/100
   Avg Confluences: 4.8

======================================================================
```

---

## Troubleshooting

### Issue: "No broker accounts found"

**Cause**: No `.env.angel*` or `.env.zerodha*` files exist

**Solution**:
```bash
# Create first account
cp .env.angel.template .env.angel
nano .env.angel

# Add credentials

# Verify
python3 strategies/backtest_multi_broker.py --list-brokers
```

### Issue: "0/3 accounts active"

**Cause**: All broker accounts failed authentication

**Solutions**:
1. Check credentials in each `.env.*` file
2. Verify accounts are not dormant
3. Test each account individually
4. Use Yahoo Finance fallback temporarily

```bash
# The system will automatically fall back to Yahoo
python3 strategies/backtest_multi_broker.py
```

### Issue: "Preferred broker 'angel2' not available"

**Cause**: Specified broker account doesn't exist or is inactive

**Solution**: System auto-falls back to best available broker

```bash
# Check which brokers are available
python3 strategies/backtest_multi_broker.py --list-brokers

# Use an active one
python3 strategies/backtest_multi_broker.py --broker angel
```

---

## Advantages of Multi-Broker Setup

### 1. Redundancy
- If one account is dormant, others work
- Automatic failover
- No manual intervention needed

### 2. Rate Limit Distribution
- Distribute API calls across accounts
- Avoid hitting single account limits
- Faster backtesting

### 3. Data Quality
- Compare data across brokers
- Detect discrepancies
- Validate data integrity

### 4. Cost Optimization
- Use free Yahoo when possible (cached data)
- Reserve paid API calls for critical needs
- Optimize API usage

### 5. Flexibility
- Easy to add new accounts
- Easy to switch between brokers
- Test different data sources

---

## Next Steps

### Immediate (Today)

1. **List your current brokers**:
   ```bash
   python3 strategies/backtest_multi_broker.py --list-brokers
   ```

2. **Test all connections**:
   ```bash
   python3 strategies/backtest_multi_broker.py --test-all
   ```

3. **Add additional accounts** (if you have them):
   ```bash
   cp .env.angel.template .env.angel2
   nano .env.angel2  # Add credentials
   ```

### Short Term (This Week)

1. **Run backtest with available brokers**:
   ```bash
   python3 strategies/backtest_multi_broker.py
   ```

2. **Compare results** across different data sources

3. **Monitor which brokers are working** best

### Long Term (Next Month)

1. **Reactivate dormant accounts** (Angel One KYC)

2. **Add more broker integrations**:
   - Implement Zerodha API
   - Implement Upstox API
   - Add more data sources

3. **Optimize data fetching**:
   - Tune cache TTL
   - Implement smart prefetching
   - Add data quality metrics

---

## Files Reference

### Backtesting Scripts
- **`backtest_multi_broker.py`** - Multi-broker system (NEW - Use This!)
- `backtest_angel_flexible.py` - Angel One only (multiple accounts)
- `backtest_mtf_angel.py` - Angel One single account
- `backtest_mtf_optimized.py` - Yahoo Finance only

### Configuration Templates
- `.env.angel.template` - Angel One credentials template
- `.env.zerodha.template` - Zerodha credentials template (create if needed)
- `.env.upstox.template` - Upstox credentials template (create if needed)

### Infrastructure
- `src/data/data_source_fallback.py` - Intelligent fallback mechanism
- `src/data/angel_one_ohlcv.py` - Angel One data fetcher
- `src/data/yahoo_finance_fetcher.py` - Yahoo Finance fetcher
- `src/data/sqlite_data_cache.py` - Local data cache

---

**Last Updated**: November 19, 2024
**Status**: Multi-broker system ready - Add your accounts and test!
**Recommendation**: Start with available accounts, add more as they become active
