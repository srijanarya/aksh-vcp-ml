# Next Steps Guide - Testing & Integration

## 🎯 Immediate Actions

### 1. Test with Real BSE/NSE PDF (YOU DO THIS)

Since I can't access your Gmail, you need to:

1. **Open Gmail** and search for: `from:bse AND (pdf OR attachment)`
2. **Find a recent earnings announcement** with a PDF link
3. **Copy the PDF URL** (usually looks like: `https://www.bseindia.com/xml-data/corpfiling/AttachLive/...pdf`)
4. **Test it on AWS**:

```bash
ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29

# Replace XXXXX with BSE code and REAL_PDF_URL with actual URL
curl -X POST http://localhost:8002/api/v1/analyze-earnings \
  -H "Content-Type: application/json" \
  -d '{
    "bse_code": "XXXXX",
    "pdf_url": "REAL_PDF_URL",
    "subject": "Financial Results"
  }'
```

**Expected Result**: Should return JSON with extracted financials and blockbuster classification

**If it fails**: The PDF format might be different - we may need to adjust the regex patterns in `IndianPDFExtractor`

---

### 2. Angel One API Integration (I CAN HELP WITH THIS)

You mentioned you have Angel One API credentials. Here's how to set them up:

#### Step A: Create `.env.angel` File

Create this file in the project root:

```bash
cd /Users/srijan/Desktop/aksh
cat > .env.angel << 'EOF'
export ANGEL_API_KEY="yip3kpG2"
export ANGEL_CLIENT_ID="S692691"
export ANGEL_MPIN="8383"
export ANGEL_TOTP_SECRET="X7TPG2AANT6UYOVJVKCQIR2CMM="
EOF
```

#### Step B: Test Authentication Locally

```bash
cd /Users/srijan/Desktop/aksh
python3 << 'PYTHON'
from src.data.angel_one_client import AngelOneClient
from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
from datetime import datetime, timedelta

# Authenticate
client = AngelOneClient.from_env_file('.env.angel')
success = client.authenticate()

if success:
    print("✅ Authentication successful!")
    
    # Test fetching OHLCV data
    fetcher = AngelOneOHLCVFetcher(client)
    
    # Fetch Reliance daily data for last 30 days
    to_date = datetime.now()
    from_date = to_date - timedelta(days=30)
    
    df = fetcher.fetch_ohlcv(
        symbol="RELIANCE",
        exchange="NSE",
        interval="ONE_DAY",
        from_date=from_date,
        to_date=to_date
    )
    
    print(f"Fetched {len(df)} candles")
    print(df.head())
else:
    print("❌ Authentication failed")
PYTHON
```

#### Step C: Integrate into ML Data Collector

I can modify `ml_data_collector.py` to use Angel One for historical data fetching to fix your "insufficient data" warnings.

**Do you want me to proceed with this integration?**

---

### 3. Dashboard Clarification

You mentioned getting `{"detail":"Not Found"}` on the earnings calendar. Let me clarify:

**VCP System Dashboards (AWS - Port 8001)**:
- Earnings Calendar: `http://13.200.109.29:8001/static/earnings_calendar_public.html`
- Blockbuster Scanner: `http://13.200.109.29:8001/static/blockbuster.html`
- Alerts: `http://13.200.109.29:8001/alerts-dashboard`

**BMAD System (Local - Port 8080)**:
- Different system entirely
- For backtesting/paper trading

**NEW ML API (AWS - Port 8002)**:
- Earnings Analysis: `POST http://13.200.109.29:8002/api/v1/analyze-earnings`
- Health: `GET http://13.200.109.29:8002/health`
- Note: Port 8002 is NOT publicly accessible yet (need to open in AWS security group)

If you're getting 404 errors, make sure you're using the correct port and URL path.

---

## 🔍 Quick Diagnostics

If something isn't working:

### Check Service Status
```bash
ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29
sudo systemctl status vcp-ml-api
```

### View Recent Logs
```bash
ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29
sudo journalctl -u vcp-ml-api -n 100 --no-pager
```

### Test Health Endpoint
```bash
ssh -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29
curl http://localhost:8002/health
```

---

## ✅ What to Tell Me

**For me to continue effectively, please tell me:**

1. ✅ "Test the Angel One integration" - I'll integrate historical data fetching
2. ✅ "Here's a PDF URL: [URL]" - I'll test it on the server for you
3. ✅ "The dashboard at [URL] shows [issue]" - I'll investigate
4. ✅ "All working, move to [next priority]" - I'll proceed

**Current Status**: Deployment complete and working with mock data. Ready for real-world testing.
