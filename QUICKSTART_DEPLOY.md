# 🚀 Quick Start - Deploy Your Dashboards

**Your dashboards are ready to deploy!** Follow these simple steps.

---

## ✅ Pre-Flight Check

Your dashboards have been:
- ✅ Consolidated (70+ → 16 dashboards)
- ✅ Organized (production/ and development/ folders)
- ✅ Built successfully (React app compiled)
- ✅ Documented (4 comprehensive docs)

**Status:** 100% READY TO DEPLOY

---

## 🚀 Deployment Options

### Option 1: Automated Deployment (Recommended)

I've created a deployment script for you: **[deploy_dashboards.sh](deploy_dashboards.sh)**

```bash
# Make sure you're in the aksh directory
cd /Users/srijan/Desktop/aksh

# Deploy everything (HTML + React)
./deploy_dashboards.sh all

# Or deploy just HTML dashboards
./deploy_dashboards.sh html

# Or deploy just React app
./deploy_dashboards.sh react
```

**Before running:** Edit `deploy_dashboards.sh` and update:
- `AWS_USER` (line 14) - Your AWS username (currently set to "ubuntu")
- `AWS_BASE_PATH` (line 16) - Path where dashboards should be deployed

### Option 2: Manual Deployment

If you prefer manual control:

```bash
# 1. Connect to your AWS server
ssh ubuntu@13.200.109.29

# 2. Create directories (on AWS server)
mkdir -p /path/to/frontend/production
mkdir -p /path/to/frontend/development
mkdir -p /path/to/frontend/react-app

# 3. Exit SSH, then deploy from your local machine

# Deploy HTML dashboards
cd /Users/srijan/vcp_clean_test/vcp/frontend
scp production/*.html ubuntu@13.200.109.29:/path/to/frontend/production/
scp development/*.html ubuntu@13.200.109.29:/path/to/frontend/development/
scp index.html ubuntu@13.200.109.29:/path/to/frontend/

# Deploy React app
scp -r react-app/dist/* ubuntu@13.200.109.29:/path/to/frontend/react-app/

# Done!
```

Replace `/path/to/frontend/` with your actual static files path on AWS.

---

## 🔍 Finding Your Static Files Path

Your FastAPI backend serves static files. To find where:

```bash
# SSH into your AWS server
ssh ubuntu@13.200.109.29

# Look for the FastAPI app configuration
grep -r "StaticFiles\|mount" ~/vcp/*.py | grep static

# This will show you the static files directory path
```

Common paths:
- `/home/ubuntu/vcp/frontend`
- `/home/ubuntu/vcp/static`
- `/var/www/vcp/static`

---

## 🧪 Testing After Deployment

### Test HTML Dashboards

```bash
# Test Dashboard Hub
curl -I http://13.200.109.29:8001/static/production/dashboard-hub.html

# Test Earnings Calendar
curl -I http://13.200.109.29:8001/static/production/earnings-calendar.html

# Test Blockbuster Scanner
curl -I http://13.200.109.29:8001/static/production/blockbuster-scanner.html

# Test Alerts Dashboard
curl -I http://13.200.109.29:8001/static/production/alerts-dashboard.html
```

All should return `HTTP/1.1 200 OK`

### Test React App

```bash
# Test React app
curl -I http://13.200.109.29:8001/static/react-app/index.html

# Should return HTTP/1.1 200 OK
```

### Test in Browser

Open in your browser:
- Dashboard Hub: http://13.200.109.29:8001/static/production/dashboard-hub.html
- React App: http://13.200.109.29:8001/static/react-app/index.html

---

## 📋 What's Being Deployed

### Production HTML Dashboards (4 files)
Located in: `production/`

1. **dashboard-hub.html** - Central navigation hub
2. **earnings-calendar.html** - 5,535 companies earnings tracker
3. **blockbuster-scanner.html** - VCP pattern scanner (realtime)
4. **alerts-dashboard.html** - Real-time BSE/NSE alerts

### Development Dashboards (2 files)
Located in: `development/`

1. **dexter_chat.html** - Dexter AI research agent
2. **vikram-agent.html** - Vikram hedge fund AI

### React Application (1 app, 11 pages)
Located in: `react-app/dist/`

**Pages:**
1. Home (/) - Dashboard hub
2. Earnings Calendar (/earnings)
3. Blockbuster Scanner (/blockbuster)
4. Announcements Screener (/announcements) - 4,203+ alerts
5. Alerts Dashboard (/alerts)
6. Telegram Alerts (/telegram)
7. Historical Alerts (/historical)
8. System Health (/health)
9. Data Viewer (/data-viewer)
10. LLM Training (/llm-training)
11. Intelligent Collector (/collector)

**Total Size:** ~850 KB (250 KB gzipped)

---

## 🔧 Troubleshooting

### "Permission denied" error
```bash
# Add your SSH key to AWS
ssh-copy-id ubuntu@13.200.109.29

# Or specify key explicitly
scp -i ~/.ssh/your-key.pem files ubuntu@13.200.109.29:/path/
```

### "Connection refused"
- Check AWS security group allows SSH (port 22) from your IP
- Verify EC2 instance is running
- Check if username is correct (might be `ec2-user`, `admin`, or `ubuntu`)

### "404 Not Found" after deployment
- Verify static files path in FastAPI configuration
- Check file permissions: `chmod 644 *.html` on AWS server
- Restart FastAPI backend: `systemctl restart vcp-api` (or your service name)

### React app shows blank page
- Check browser console for errors
- Verify all files in `dist/` were copied (not just index.html)
- Check `dist/assets/` folder was copied
- Ensure correct base path in React router

---

## 🎯 After Deployment Checklist

- [ ] Test all 4 production HTML dashboards load
- [ ] Test React app home page loads
- [ ] Test at least 3 React app pages (click navigation)
- [ ] Test API endpoints work (check data loads)
- [ ] Test on mobile device (responsive design)
- [ ] Update Dashboard Hub links to point to new locations
- [ ] Add dashboards to your bookmarks/favorites
- [ ] Share URLs with your team/users

---

## 📱 Access Your Dashboards

After successful deployment, access at:

**Production Dashboards:**
- http://13.200.109.29:8001/static/production/dashboard-hub.html
- http://13.200.109.29:8001/static/production/earnings-calendar.html
- http://13.200.109.29:8001/static/production/blockbuster-scanner.html
- http://13.200.109.29:8001/static/production/alerts-dashboard.html

**React Application:**
- http://13.200.109.29:8001/static/react-app/index.html

**Development Dashboards:**
- http://13.200.109.29:8001/static/development/dexter_chat.html
- http://13.200.109.29:8001/static/development/vikram-agent.html

---

## 🔄 Updating Dashboards Later

When you make changes to dashboards:

```bash
# Re-build React app (if changed)
cd /Users/srijan/vcp_clean_test/vcp/frontend/react-app
npm run build

# Re-deploy using the script
cd /Users/srijan/Desktop/aksh
./deploy_dashboards.sh all
```

---

## 🎉 Success!

Once deployed, your MVP is **LIVE** and ready for users!

**Next steps:**
1. Test all dashboards work correctly
2. Add authentication for sensitive dashboards
3. Set up custom domain (optional)
4. Configure HTTPS/SSL (recommended)
5. Set up monitoring/analytics

---

**Questions?** Check the comprehensive docs:
- [README.md](/Users/srijan/vcp_clean_test/vcp/frontend/README.md)
- [DEPLOYMENT_READY.md](/Users/srijan/vcp_clean_test/vcp/frontend/DEPLOYMENT_READY.md)
- [CONSOLIDATION_SUMMARY.md](/Users/srijan/vcp_clean_test/vcp/frontend/CONSOLIDATION_SUMMARY.md)

**Ready to deploy?** Run: `./deploy_dashboards.sh all`
