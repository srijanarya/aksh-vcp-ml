# Dashboard Quick Reference Guide

**Last Updated:** November 21, 2025

---

## 📊 Available Dashboards

### 1. Dashboard Hub (Navigation)
**URL:** http://13.200.109.29:8001/static/production/dashboard-hub-FINAL.html
**Purpose:** Central navigation to all dashboards
**Features:**
- Live status indicators
- Dashboard descriptions
- Quick access links

---

### 2. Earnings Calendar
**URL:** http://13.200.109.29:8001/static/production/comprehensive_earnings_calendar.html
**Purpose:** View upcoming BSE earnings announcements

**Features:**
- ✅ **CSV Export** - Download earnings data as CSV
- ✅ **Excel Export** - Download earnings data as Excel
- ✅ **Auto-Refresh** - Refresh every 5 minutes automatically
- ✅ **Search & Filter** - Find specific companies or dates
- ✅ **Sortable Columns** - Click headers to sort

**How to Use:**
1. Open the dashboard
2. Browse upcoming earnings (sorted by date)
3. Use search box to filter companies
4. Click **"📥 Download CSV"** to export data
5. Enable **"Auto-refresh (5 min)"** for live updates

**Export Filename Format:** `bse_upcoming_earnings_2025-11-21.csv`

---

### 3. Market Status Dashboard
**URL:** http://13.200.109.29:8001/static/production/market_status_dashboard.html
**Purpose:** Real-time market analysis and stock performance

**Features:**
- ✅ **Market Phase Indicator** - Bullish/Bearish/Sideways
- ✅ **Key Metrics** - Stocks analyzed, data confidence, trend
- ✅ **Top Stocks** - Performance scores and price changes
- ✅ **Auto-Refresh** - 5-minute intervals
- ✅ **Technical Scores** - Pattern strength visualization
- ✅ **Data Confidence** - Quality indicators

**Stock Coverage:**
- TCS (Tata Consultancy Services)
- RELIANCE (Reliance Industries)
- INFY (Infosys Limited)
- HDFCBANK (HDFC Bank Limited)
- ICICIBANK (ICICI Bank Limited)
- BAJFINANCE (Bajaj Finance Limited)

**How to Use:**
1. View market phase at top (BULLISH/BEARISH/SIDEWAYS)
2. Check key metrics grid
3. Scroll to see individual stock cards
4. View technical scores (pattern strength)
5. Check data confidence scores (data quality)
6. Enable auto-refresh for live updates

---

### 4. Intelligence Dashboard
**URL:** http://13.200.109.29:8001/static/production/intelligence_dashboard.html
**Purpose:** AI-powered BSE announcement analysis

**Features:**
- ✅ **Announcement Feed** - Real-time BSE announcements
- ✅ **Category Breakdown** - EARNINGS, GENERAL, PROMOTER_ACTION
- ✅ **Extraction Status** - Success/failed/skipped indicators
- ✅ **Manual Refresh** - Update data on demand
- ✅ **Statistics** - Total announcements, successful extractions

**Categories:**
- **EARNINGS** - Financial results announcements
- **GENERAL** - General corporate announcements
- **PROMOTER_ACTION** - Promoter shareholding changes

**How to Use:**
1. View total announcements and extraction stats
2. Check category breakdown percentages
3. Browse recent announcements table
4. Click **"🔄 Refresh Data"** to update
5. Review extraction status for each announcement

---

## 🔄 Auto-Refresh Feature

### Dashboards with Auto-Refresh:
- ✅ Earnings Calendar
- ✅ Market Status Dashboard

### How It Works:
1. Check the **"Auto-refresh (5 min)"** checkbox
2. Dashboard automatically reloads every 5 minutes
3. Preference is saved in browser (persists across visits)
4. Uncheck to disable auto-refresh

### Manual Refresh:
- All dashboards have **"🔄 Refresh Now"** button
- Click anytime for immediate update
- Shows "⏳ Refreshing..." during reload

---

## 📥 CSV/Excel Export

### Available On:
- ✅ Earnings Calendar Dashboard

### Export Options:
1. **CSV Format**
   - Click **"📥 Download CSV"**
   - Opens in Excel, Google Sheets, Numbers
   - Filename: `bse_upcoming_earnings_YYYY-MM-DD.csv`

2. **Excel Format**
   - Click **"📊 Download Excel"**
   - Native .xlsx format
   - Filename: `bse_upcoming_earnings_YYYY-MM-DD.xlsx`

### What Gets Exported:
- Company names
- Stock symbols
- Earnings announcement dates
- Earnings amounts
- All visible columns

### Export Tips:
- Apply filters before exporting (only visible rows exported)
- Use search to filter companies
- Sort columns before export
- Filename automatically includes current date

---

## 🎨 Dashboard Design

### Color Scheme:
- **Primary Gradient:** Purple (#667eea) to Violet (#764ba2)
- **Background:** Dark navy gradient
- **Success:** Green (#10b981)
- **Error:** Red (#ef4444)
- **Warning:** Orange (#f59e0b)

### UI Components:
- **Glassmorphic Cards** - Semi-transparent with blur effect
- **Gradient Buttons** - Hover effects with shadow
- **Progress Bars** - Smooth animated fills
- **Responsive Grid** - Adapts to screen size

### Browser Support:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari (with -webkit- prefixes)
- ✅ Mobile browsers (iOS/Android)
- ❌ Internet Explorer (not supported)

---

## 🚀 Deployment

### Quick Deploy:
```bash
cd /Users/srijan/Desktop/aksh
./deploy_dashboards.sh html
```

### What Gets Deployed:
1. Dashboard Hub (dashboard-hub-FINAL.html)
2. Earnings Calendar (comprehensive_earnings_calendar.html)
3. Market Status (market_status_dashboard.html)
4. Intelligence Dashboard (intelligence_dashboard.html)

### Deployment Target:
- **Server:** AWS Lightsail (13.200.109.29)
- **Port:** 8001
- **Path:** /home/ubuntu/vcp/static/production/
- **Access:** HTTP (not HTTPS)

### Verify Deployment:
```bash
# Test each dashboard
curl -I http://13.200.109.29:8001/static/production/dashboard-hub-FINAL.html
curl -I http://13.200.109.29:8001/static/production/comprehensive_earnings_calendar.html
curl -I http://13.200.109.29:8001/static/production/market_status_dashboard.html
curl -I http://13.200.109.29:8001/static/production/intelligence_dashboard.html
```

Expected response: `HTTP/1.1 200 OK`

---

## 🔧 Troubleshooting

### Dashboard Not Loading
**Problem:** Dashboard shows blank page or 404 error
**Solutions:**
1. Check AWS server is running
2. Verify URL is correct (check for typos)
3. Try clearing browser cache (Ctrl+Shift+R)
4. Check browser console for errors (F12 → Console)

### CSV Export Not Working
**Problem:** Export button doesn't download file
**Solutions:**
1. Check browser popup blocker settings
2. Verify DataTables Buttons libraries loaded (check Network tab)
3. Try different browser
4. Check browser download settings

### Auto-Refresh Not Working
**Problem:** Dashboard doesn't refresh automatically
**Solutions:**
1. Verify checkbox is checked
2. Check browser console for errors
3. Clear localStorage: `localStorage.clear()`
4. Disable browser extensions that might block timers
5. Try manual refresh button first

### Data Not Updating
**Problem:** Dashboard shows old data
**Solutions:**
1. Click manual refresh button
2. Clear browser cache
3. Check if backend service is running
4. Verify data source APIs are accessible

### Slow Performance
**Problem:** Dashboard loads slowly
**Solutions:**
1. Check internet connection
2. Disable auto-refresh temporarily
3. Clear browser cache and cookies
4. Close other browser tabs
5. Check server load (AWS metrics)

---

## 📱 Mobile Access

All dashboards are mobile-responsive:

### Portrait Mode:
- Cards stack vertically
- Tables scroll horizontally
- Buttons remain full-width

### Landscape Mode:
- Grid layouts activate
- Tables show more columns
- Side-by-side card arrangement

### Touch Gestures:
- Tap to interact with buttons
- Swipe to scroll tables
- Pinch to zoom (if needed)

---

## 🔐 Security Notes

### Current Setup:
- ⚠️ **No authentication** - Dashboards are publicly accessible
- ⚠️ **HTTP only** - Not encrypted (no HTTPS)
- ⚠️ **No rate limiting** - Unlimited requests allowed

### Recommendations for Production:
1. Add authentication (Basic Auth, OAuth, etc.)
2. Enable HTTPS with SSL certificate
3. Implement rate limiting
4. Add CORS headers
5. Use API keys for backend calls

---

## 📚 Related Documentation

- [DASHBOARD_ENHANCEMENTS_COMPLETE.md](DASHBOARD_ENHANCEMENTS_COMPLETE.md) - Full technical documentation
- [README.md](README.md) - System overview
- [deploy_dashboards.sh](deploy_dashboards.sh) - Deployment script
- [QUICK_START.md](QUICK_START.md) - Getting started guide

---

## 💡 Tips & Best Practices

### For Daily Use:
1. **Bookmark Dashboard Hub** - Central access to all dashboards
2. **Enable Auto-Refresh** - For dashboards you monitor frequently
3. **Export Data Regularly** - Daily/weekly earnings exports for analysis
4. **Check Data Confidence** - Higher scores = more reliable data
5. **Monitor Technical Scores** - Identify high-confidence opportunities

### For Analysis:
1. **Export to Excel** - Easier to manipulate and analyze
2. **Use Filters** - Focus on specific sectors or date ranges
3. **Sort by Confidence** - Prioritize high-quality signals
4. **Cross-Reference** - Compare earnings calendar with market status
5. **Track Trends** - Note recurring patterns in announcements

### For Performance:
1. **Disable Auto-Refresh** - When not actively monitoring
2. **Close Unused Tabs** - Reduces browser memory usage
3. **Clear Cache Weekly** - Prevents stale data issues
4. **Use Chrome/Firefox** - Best performance and compatibility
5. **Check Mobile First** - If desktop is slow

---

## ❓ FAQ

**Q: How often is data updated?**
A: BSE data updates in real-time. Enable auto-refresh for 5-minute intervals.

**Q: Can I change the refresh interval?**
A: Currently fixed at 5 minutes. Contact admin to customize.

**Q: Why is auto-refresh disabled by default?**
A: To reduce server load and give users control over refreshes.

**Q: Can I access dashboards offline?**
A: No, dashboards require internet connection to load data.

**Q: Is historical data available?**
A: Earnings calendar shows upcoming announcements only. Historical data in backend.

**Q: Can I customize the dashboard appearance?**
A: Currently no user customization. Contact admin for theme changes.

**Q: What browsers are supported?**
A: Chrome, Firefox, Safari, Edge (latest versions). Not IE.

**Q: Is there a mobile app?**
A: No dedicated app. Use mobile browser - dashboards are responsive.

**Q: How do I report bugs?**
A: Contact system administrator or check GitHub issues.

**Q: Where is data sourced from?**
A: BSE API, NSE data, Yahoo Finance. Multi-source validation.

---

**Version:** 1.0
**Created:** November 21, 2025
**Author:** Claude Code (AI Assistant)
**Support:** Check DASHBOARD_ENHANCEMENTS_COMPLETE.md for detailed documentation
