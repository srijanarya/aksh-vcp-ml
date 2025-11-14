# Intelligent Earnings Collector - Deployment & Testing Guide

## ⚠️ Current Status

**What's Built**: ✅ Complete
- Intelligent earnings collector agent
- API endpoints
- Daily automation script
- Full documentation

**What's NOT Working**: ❌ Server Not Restarted
- New API endpoints not live on AWS yet
- Need to restart FastAPI server to load new routes

---

## 🚀 How to Deploy to AWS

### **Option 1: Restart the Server** (Recommended)

SSH into your AWS instance and restart the API:

```bash
# SSH to AWS
ssh your-aws-instance

# Navigate to VCP directory
cd /path/to/vcp

# Restart the FastAPI server
# If using systemd:
sudo systemctl restart vcp-api

# If using PM2:
pm2 restart vcp-api

# If running manually:
pkill -f "uvicorn api.main:app"
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

### **Option 2: Git Pull + Restart** (If AWS has git repo)

```bash
# SSH to AWS
ssh your-aws-instance

# Pull latest code
cd /path/to/vcp
git pull origin main

# Restart server
sudo systemctl restart vcp-api  # or pm2 restart
```

---

## 🧪 How to Test (After Restart)

### **Test 1: Check New Endpoints Are Live**

```bash
curl http://13.200.109.29:8001/api/intelligent-collector/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "intelligent-earnings-collector",
  "version": "1.0.0"
}
```

### **Test 2: See Data Gaps**

```bash
curl http://13.200.109.29:8001/api/intelligent-collector/gaps
```

**Expected**: List of companies missing earnings data

### **Test 3: Quick Collection Test**

```bash
curl -X POST http://13.200.109.29:8001/api/intelligent-collector/collect/quick
```

**Expected**: Processes 10 companies and returns stats

### **Test 4: View Swagger UI**

Open in browser:
```
http://13.200.109.29:8001/docs
```

Look for "Intelligent Collector" section.

---

## 📁 Files That Were Created/Modified

### **New Files Created**:

1. **`/vcp/agents/intelligent_earnings_collector.py`**
   - Core AI-powered collector
   - 3-phase strategy: Scrapers → Web Search → AI Inference
   - ~700 lines

2. **`/vcp/api/routers/intelligent_collector.py`**
   - FastAPI endpoints
   - `/gaps`, `/collect`, `/status`, `/health`
   - ~300 lines

3. **`/vcp/scripts/daily_earnings_gap_filler.py`**
   - Daily automation script
   - Cron-ready
   - ~150 lines

4. **`/docs/INTELLIGENT_EARNINGS_COLLECTOR.md`**
   - Complete documentation
   - ~500 lines

5. **`/Desktop/aksh/INTELLIGENT_EARNINGS_SYSTEM_SUMMARY.md`**
   - Executive summary
   - Quick reference guide

### **Modified Files**:

1. **`/vcp/api/main.py`** (Line 30, Line 227)
   - Added `intelligent_collector` import
   - Added router registration

2. **`/vcp/api/routers/earnings_calendar.py`** (Lines 229-402)
   - Fixed to show all 11,389 companies
   - Merges master list with database
   - Shows TBD for missing data

---

## 🎯 What the System Does

### **Phase 1**: Identify Gaps
- Loads master_stock_list.json (11,389 companies)
- Checks earnings_calendar.db (7,530 companies)
- Identifies 3,859 companies missing data

### **Phase 2**: Research Each Company
1. **Try BSE/NSE Scrapers** (Confidence: 95%)
   - Official data, highest trust

2. **Web Search via Perplexity AI** (Confidence: 75%)
   - Searches: moneycontrol.com, economictimes.com, etc.
   - AI parses results for dates

3. **Dexter AI Inference** (Confidence: 50-65%)
   - Analyzes historical patterns
   - Predicts based on sector norms

### **Phase 3**: Validate & Update
- Only accepts confidence ≥ 70%
- Validates date ranges
- Updates database automatically

---

## 💡 Manual Testing (Without API)

If you can't restart the AWS server right now, you can still test the core functionality directly:

### **Test the Collector Agent**

```bash
# SSH to AWS or run locally
cd /path/to/vcp

# Test with Python
python3 << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/path/to/vcp')

from agents.intelligent_earnings_collector import IntelligentEarningsCollector

async def test():
    collector = IntelligentEarningsCollector(
        enable_web_search=False,  # Disable for quick test
        enable_ai_inference=False
    )

    # Just identify gaps
    gaps = collector.identify_data_gaps()
    print(f"Found {len(gaps)} companies without earnings data")

    for gap in gaps[:5]:
        print(f"  - {gap.company_name} ({gap.code})")

asyncio.run(test())
EOF
```

---

## 🔑 Required API Keys

For full functionality, set these environment variables on AWS:

```bash
# Add to /etc/environment or ~/.bashrc
export PERPLEXITY_API_KEY="your-perplexity-key"
export OPENAI_API_KEY="your-openai-key"
# OR
export ANTHROPIC_API_KEY="your-anthropic-key"
```

**Without keys**: Only scrapers work (BSE/NSE official data)
**With keys**: Full AI-powered search works

---

## 📊 Expected Performance

### **With Just Scrapers** (No API keys):
- Success rate: 30-40%
- Speed: Fast (1-2 seconds per company)
- Cost: Free

### **With Web Search** (PERPLEXITY_API_KEY):
- Success rate: 50-70%
- Speed: Medium (5-10 seconds per company)
- Cost: ~$0.01 per company

### **With Full AI** (All keys):
- Success rate: 60-80%
- Speed: Slow (20-30 seconds per company)
- Cost: ~$0.02 per company

---

## ❓ Troubleshooting

### **"Connection refused" or 404 errors**

**Problem**: Server hasn't been restarted
**Solution**: Restart FastAPI server on AWS

### **"Module not found" errors**

**Problem**: Dependencies not installed
**Solution**:
```bash
cd /path/to/vcp
pip install -r requirements.txt
```

### **"No such table: earnings"**

**Problem**: Database doesn't have tables yet
**Solution**: Normal - tables created on first run

### **Web search returns no results**

**Problem**: PERPLEXITY_API_KEY not set
**Solution**:
```bash
export PERPLEXITY_API_KEY="your-key"
```

---

## 🎉 Next Steps

1. **Restart AWS server** to load new endpoints
2. **Test health endpoint** to confirm it's working
3. **Run quick collection** to test with 10 companies
4. **Set up cron job** for daily automation
5. **Monitor results** via API or logs

---

## 📞 Summary

**What you have**: Complete AI-powered earnings collection system

**What you need**: Restart the FastAPI server on AWS

**How to test after restart**:
```bash
# Health check
curl http://13.200.109.29:8001/api/intelligent-collector/health

# Quick test
curl -X POST http://13.200.109.29:8001/api/intelligent-collector/collect/quick

# View in browser
http://13.200.109.29:8001/docs
```

---

**Created**: 2025-11-09
**Status**: Code Complete, Pending Deployment
