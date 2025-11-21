# Angel One Backtesting Setup Guide

## Overview

This guide helps you set up and use the flexible Angel One backtester with support for multiple accounts.

---

## Quick Start

### 1. Test Your Current Account Connection

```bash
# Test the primary account
python3 strategies/backtest_angel_flexible.py --test-connection

# Test a specific account
python3 strategies/backtest_angel_flexible.py \
    --account /Users/srijan/vcp_clean_test/vcp/.env.angel \
    --test-connection
```

**Expected Output (Success)**:
```
🔌 Testing Angel One Connection
======================================================================

Loading credentials from: /path/to/.env.angel
Client ID: S692691
Authenticating...
✅ Authentication successful!
Session token: abcd1234...
✅ Connection test PASSED
```

**Expected Output (Dormant Account)**:
```
❌ Connection test FAILED: Your demat account is dormant

Possible issues:
1. Account is dormant (complete KYC reactivation)
2. Incorrect credentials in .env.angel
3. Network/API issues
```

### 2. Run Backtest (Once Account is Active)

```bash
# Basic backtest with default settings
python3 strategies/backtest_angel_flexible.py

# Custom parameters
python3 strategies/backtest_angel_flexible.py \
    --symbols TATAMOTORS SAIL VEDL ADANIPORTS \
    --start-date 2023-01-01 \
    --end-date 2024-11-01 \
    --capital 100000
```

---

## Setting Up Multiple Accounts

### Why Use Multiple Accounts?

- **Backup**: If one account is dormant, use another
- **API Limits**: Distribute requests across accounts
- **Testing**: Test with different account setups
- **Data Access**: Some accounts may have better data access

### Adding Additional Accounts

**Step 1**: Copy the template

```bash
cp .env.angel.template .env.angel2
```

**Step 2**: Edit with your credentials

```bash
# Open in your editor
nano .env.angel2

# Add your credentials
export ANGEL_API_KEY="your_second_account_api_key"
export ANGEL_CLIENT_ID="your_second_account_client_id"
export ANGEL_MPIN="your_second_account_mpin"
export ANGEL_TOTP_SECRET="your_second_account_totp_secret"
```

**Step 3**: Test the new account

```bash
python3 strategies/backtest_angel_flexible.py \
    --account .env.angel2 \
    --test-connection
```

**Step 4**: Use it for backtesting

```bash
python3 strategies/backtest_angel_flexible.py \
    --account .env.angel2
```

---

## Account Locations

The backtester automatically searches these locations:

1. `/Users/srijan/Desktop/aksh/.env.angel` (primary - aksh project)
2. `/Users/srijan/vcp_clean_test/vcp/.env.angel` (secondary - vcp project)
3. `./.env.angel` (current directory)

You can also specify a custom path:

```bash
python3 strategies/backtest_angel_flexible.py \
    --account /path/to/your/.env.angel3
```

---

## Current Account Status

### Account 1 (Primary)
- **Location**: `/Users/srijan/vcp_clean_test/vcp/.env.angel`
- **Client ID**: S692691
- **Status**: ⏳ Dormant (KYC reactivation in progress)
- **Action**: Wait for reactivation

### Adding Account 2 (If Available)

If you have a second Angel One account that's active:

```bash
# Create credentials file
nano /Users/srijan/Desktop/aksh/.env.angel2

# Add credentials for your second account

# Test it
python3 strategies/backtest_angel_flexible.py \
    --account /Users/srijan/Desktop/aksh/.env.angel2 \
    --test-connection
```

---

## Usage Examples

### Test Connection Before Backtest

Always test connection first to avoid wasting time:

```bash
# Test
python3 strategies/backtest_angel_flexible.py --test-connection

# If successful, run backtest
python3 strategies/backtest_angel_flexible.py
```

### Backtest Specific Symbols

```bash
python3 strategies/backtest_angel_flexible.py \
    --symbols RELIANCE TCS INFY HDFCBANK
```

### Short Date Range (Faster)

```bash
python3 strategies/backtest_angel_flexible.py \
    --start-date 2024-01-01 \
    --end-date 2024-11-01
```

### Different Capital

```bash
python3 strategies/backtest_angel_flexible.py \
    --capital 500000
```

### Combine All Options

```bash
python3 strategies/backtest_angel_flexible.py \
    --account .env.angel2 \
    --symbols TATAMOTORS SAIL VEDL \
    --start-date 2023-06-01 \
    --end-date 2024-11-01 \
    --capital 200000
```

---

## Troubleshooting

### Issue: "Account is dormant"

**Solution**:
1. Complete KYC reactivation (in progress)
2. Use an alternate active account
3. Wait for reactivation notification from Angel One

**Temporary Workaround**:
```bash
# Use a different account
python3 strategies/backtest_angel_flexible.py \
    --account /path/to/active/account/.env.angel2
```

### Issue: "Authentication failed"

**Possible Causes**:
1. Incorrect credentials in .env.angel file
2. TOTP secret expired or incorrect
3. Network issues

**Solution**:
```bash
# Verify credentials format
cat .env.angel

# Should look like:
# export ANGEL_API_KEY="..."
# export ANGEL_CLIENT_ID="..."
# export ANGEL_MPIN="..."
# export ANGEL_TOTP_SECRET="..."

# Test connection
python3 strategies/backtest_angel_flexible.py --test-connection
```

### Issue: "Symbol not found"

**Cause**: Symbol name might be incorrect or not listed on NSE

**Solution**:
```bash
# Use correct NSE symbols (without .NS suffix)
python3 strategies/backtest_angel_flexible.py \
    --symbols TATAMOTORS  # Correct

# Not: TATAMOTORS.NS (remove .NS)
```

### Issue: "Rate limit exceeded"

**Cause**: Too many API requests

**Solution**:
- Wait 5 minutes and retry
- Use longer check intervals (script checks every 5 days)
- Spread backtests across multiple accounts
- Use caching (automatically enabled, 24h TTL)

---

## Expected Backtest Output

When everything works correctly:

```
======================================================================
🚀 ANGEL ONE MULTI-ACCOUNT BACKTESTER
✨ WITH S/R INTEGRATION
======================================================================
Account: /Users/srijan/Desktop/aksh/.env.angel
Initial Capital: ₹100,000
Period: 2023-01-01 to 2024-11-01
S/R Min Quality: 60/100
======================================================================

Initializing Angel One client...
✅ Client initialized successfully

======================================================================
📊 Backtesting TATAMOTORS
======================================================================

Fetching MTF data for TATAMOTORS...
   ✅ Fetched 451 days, 96 weeks, 180 4H bars

Walking forward through 451 days...

🎯 Signal on 2023-03-15
   Entry: ₹425.50
   Stop: ₹412.30
   Target: ₹458.80
   S/R Quality: 75.0/100
   Confluences: 5
   ✅ Exit: ₹458.80 (+7.83%)
   Days held: 12, R: 2.52R

... [more trades] ...

📊 TATAMOTORS Summary: 3 signals, 3 trades

======================================================================
📊 BACKTEST RESULTS
======================================================================

💰 Performance Summary:
   Total Trades: 12
   Winners: 7
   Losers: 5
   Win Rate: 58.3%
   Avg Return/Trade: 1.85%
   Avg Winner: 6.2%
   Avg Loser: -2.1%
   Avg R Multiple: 1.45R
   Sharpe Ratio: 2.35
   Max Drawdown: 4.2%
   Final Capital: ₹122,200
   Total Return: 22.2%

📊 S/R Metrics:
   Avg S/R Quality: 72.5/100
   Avg Confluences: 4.8

📋 Trade Details:
======================================================================
✅ #1 TATAMOTORS: 2023-03-15 → ₹425.50 → ₹458.80 (+7.83%) [TARGET] S/R:75
✅ #2 SAIL: 2023-04-20 → ₹95.20 → ₹102.30 (+7.46%) [TARGET] S/R:68
...
```

---

## What Happens Next?

### 1. Once Your Account is Reactivated

You'll receive notification from Angel One. Then:

```bash
# Test connection
python3 strategies/backtest_angel_flexible.py --test-connection

# If successful, run full backtest
python3 strategies/backtest_angel_flexible.py
```

### 2. If You Have Multiple Accounts

**Scenario**: Account 1 is dormant, but you have Account 2 active

```bash
# Set up Account 2
cp .env.angel.template .env.angel2
nano .env.angel2  # Add Account 2 credentials

# Test Account 2
python3 strategies/backtest_angel_flexible.py \
    --account .env.angel2 \
    --test-connection

# Use Account 2 for backtest
python3 strategies/backtest_angel_flexible.py \
    --account .env.angel2
```

### 3. Alternative: Use yfinance (Temporary)

While waiting for Angel One reactivation:

```bash
# Use the optimized yfinance backtester (slower but works)
python3 strategies/backtest_mtf_optimized.py
```

---

## Files Reference

### Backtesting Scripts

- **`backtest_angel_flexible.py`** - Multi-account Angel One backtester (NEW)
- `backtest_mtf_angel.py` - Original Angel One backtester (single account)
- `backtest_mtf_optimized.py` - yfinance-based backtester (fallback)
- `backtest_mtf_with_sr.py` - Original real-strategy backtester (very slow)

### Configuration Files

- `.env.angel.template` - Template for Angel One credentials
- `.env.angel` - Primary account (if exists)
- `.env.angel2`, `.env.angel3`, etc. - Additional accounts

### Documentation

- `ANGEL_ONE_BACKTEST_SETUP.md` - This file
- `BACKTEST_RESULTS_SR_INTEGRATION.md` - Complete S/R integration analysis
- `BACKTEST_SR_SUMMARY.md` - Original backtest summary

---

## Security Notes

**IMPORTANT**: Keep your `.env.angel` files secure!

```bash
# Set proper permissions
chmod 600 .env.angel*

# Never commit to git
echo ".env.angel*" >> .gitignore

# Verify not tracked
git status | grep .env.angel  # Should return nothing
```

---

## Next Steps

1. **Wait for KYC Reactivation** (primary account)
   - You mentioned it's in progress
   - Test immediately after reactivation

2. **Add Alternate Account** (if available)
   - Copy `.env.angel.template` to `.env.angel2`
   - Add your second account credentials
   - Test and use for backtesting

3. **Run Backtest**
   - Test connection first
   - Run full backtest on 2023-2024 data
   - Compare results with expectations

4. **Validate S/R Integration**
   - Check if S/R quality scores are realistic (60-85/100)
   - Verify signals have good confluences (4+)
   - Compare win rate with expected 52-55%

---

**Contact**: If you have issues, check the error messages from `--test-connection` first. Most issues are:
1. Dormant account (wait for reactivation)
2. Incorrect credentials (check .env.angel format)
3. Network issues (check internet connection)

**Last Updated**: November 19, 2024
