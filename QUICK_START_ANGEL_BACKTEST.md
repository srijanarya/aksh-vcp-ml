# Quick Start: Angel One Backtesting

## 🚀 Immediate Actions

### Option 1: Use Your Account After Reactivation

```bash
# Step 1: Test connection (once KYC is complete)
python3 strategies/backtest_angel_flexible.py --test-connection

# Step 2: Run backtest (if test passes)
python3 strategies/backtest_angel_flexible.py
```

### Option 2: Add a Second Active Account (Recommended Now)

```bash
# Step 1: Create credential file
cp .env.angel.template .env.angel2

# Step 2: Edit with your second account credentials
nano .env.angel2

# Add:
# export ANGEL_API_KEY="your_api_key"
# export ANGEL_CLIENT_ID="your_client_id"
# export ANGEL_MPIN="your_mpin"
# export ANGEL_TOTP_SECRET="your_totp_secret"

# Step 3: Test
python3 strategies/backtest_angel_flexible.py \
    --account .env.angel2 \
    --test-connection

# Step 4: Run backtest
python3 strategies/backtest_angel_flexible.py \
    --account .env.angel2
```

---

## 📋 What You Need

### For Each Angel One Account:

1. **API Key** - From Angel One Developer Portal
2. **Client ID** - Your Angel One client code
3. **MPIN** - Mobile PIN
4. **TOTP Secret** - For 2FA (from Angel One)

Get these from: https://smartapi.angelbroking.com/

---

## ⚡ Quick Commands

```bash
# Test connection
python3 strategies/backtest_angel_flexible.py --test-connection

# Basic backtest
python3 strategies/backtest_angel_flexible.py

# Use specific account
python3 strategies/backtest_angel_flexible.py --account .env.angel2

# Custom symbols and dates
python3 strategies/backtest_angel_flexible.py \
    --symbols RELIANCE TCS INFY \
    --start-date 2024-01-01 \
    --end-date 2024-11-01

# Short test (faster)
python3 strategies/backtest_angel_flexible.py \
    --symbols TATAMOTORS \
    --start-date 2024-06-01
```

---

## ✅ Success Indicators

When your backtest works, you'll see:

```
✅ Client initialized successfully

Fetching MTF data for TATAMOTORS...
   ✅ Fetched 451 days, 96 weeks, 180 4H bars

🎯 Signal on 2023-03-15
   Entry: ₹425.50
   S/R Quality: 75.0/100
   ✅ Exit: ₹458.80 (+7.83%)
```

---

## ❌ Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "Account is dormant" | Wait for KYC reactivation OR use second account |
| "Authentication failed" | Check credentials in .env.angel file |
| "Symbol not found" | Use correct NSE symbols (TATAMOTORS not TATAMOTORS.NS) |
| "Rate limit exceeded" | Wait 5 minutes, or use different account |

---

## 📊 Expected Results

With S/R integration, expect:

- **Signals**: 3-5 per month (highly selective)
- **Win Rate**: 52-55%
- **S/R Quality**: 65-85/100 average
- **Sharpe Ratio**: 2.2-2.5

If you see 0 signals, it might be due to:
- Market consolidation period
- Strict S/R filtering (by design)
- Need more stocks in watchlist

---

## 🎯 Next Steps

1. **If you have a second active account**: Set it up now (15 minutes)
2. **If waiting for reactivation**: Test as soon as you get notification
3. **Want to test now**: Use yfinance backtester as temporary fallback

---

## 📖 Full Documentation

- [ANGEL_ONE_BACKTEST_SETUP.md](ANGEL_ONE_BACKTEST_SETUP.md) - Complete setup guide
- [BACKTEST_RESULTS_SR_INTEGRATION.md](BACKTEST_RESULTS_SR_INTEGRATION.md) - S/R integration details
