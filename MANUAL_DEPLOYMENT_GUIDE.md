# Manual Deployment Guide - AWS Lightsail

**Server Status:** ⚠️ Currently Unreachable (SSH timeout)
**Likely Issue:** Instance stopped or network issue

---

## 🚨 Current Situation

The AWS Lightsail server at `13.200.109.29` is **not responding** to SSH connections:
- Connection timeout on port 22
- Ping fails
- Multiple connection attempts failed

**This is NOT a code issue.** All dashboards are ready and tested. The server infrastructure needs attention.

---

## ✅ What You Need to Do

### Step 1: Access AWS Lightsail Console

1. **Open browser and go to:** https://lightsail.aws.amazon.com/
2. **Log in** with your AWS credentials
3. **Select your region** (where your instance is located)

### Step 2: Check Instance Status

You should see your instance in the dashboard. Check its status:

- **If status is "Stopped" (red/gray):**
  - ✅ This is the problem!
  - Click on the instance
  - Click the **"Start"** button
  - Wait 1-2 minutes for it to boot
  - Status should change to "Running" (green)

- **If status is "Running" (green) but still can't connect:**
  - Check Networking tab → Firewall rules
  - Ensure SSH (port 22) rule exists
  - Add rule if missing: Application=SSH, Protocol=TCP, Port=22

- **If instance doesn't exist:**
  - You may need to create a new instance
  - Or check if you're in the correct AWS region

### Step 3: Verify Instance is Running

Once instance shows "Running":
1. Note the **Public IP address** (should be 13.200.109.29)
2. If IP changed, update `deploy_dashboards.sh`:
   ```bash
   AWS_HOST="NEW_IP_ADDRESS"
   ```

### Step 4: Test Connection from Your Mac

Open Terminal and run:
```bash
cd /Users/srijan/Desktop/aksh
./diagnose_aws_connection.sh
```

You should see:
```
✅ SSH connection successful!
```

### Step 5: Deploy Dashboards

Once connection works, deploy with one command:
```bash
./deploy_dashboards.sh html
```

Expected output:
```
🚀 VCP DASHBOARD DEPLOYMENT SCRIPT
✅ Connected to 13.200.109.29
✅ Directories created
📤 Deploying production dashboards...
✅ Production dashboards deployed
🧪 Testing deployment...
✅ All health checks passed
```

---

## 🔄 Alternative: Manual File Upload via AWS Console

If SSH continues to fail, you can upload files manually through the browser:

### Step 1: Connect via Browser SSH

1. In AWS Lightsail console, click your instance
2. Click **"Connect using SSH"** button (browser-based terminal)
3. A browser terminal window opens

### Step 2: Create Directories

In the browser terminal, run:
```bash
mkdir -p /home/ubuntu/vcp/static/production
cd /home/ubuntu/vcp/static/production
```

### Step 3: Upload Files

You have two options:

**Option A: Use wget from GitHub** (if you push to GitHub first)
```bash
wget https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/dashboard-hub-FINAL.html
wget https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/comprehensive_earnings_calendar.html
wget https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/market_status_dashboard.html
wget https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/intelligence_dashboard.html
```

**Option B: Copy-paste file contents**
1. On your Mac, open each HTML file
2. Copy entire contents (Cmd+A, Cmd+C)
3. In browser terminal, create file:
   ```bash
   nano dashboard-hub-FINAL.html
   ```
4. Paste contents (Cmd+V)
5. Save (Ctrl+X, Y, Enter)
6. Repeat for all 4 dashboards

### Step 4: Verify Files

```bash
ls -lh
# Should show all 4 HTML files
```

### Step 5: Test Access

Open in browser:
- http://13.200.109.29:8001/static/production/dashboard-hub-FINAL.html

---

## 🆘 If AWS Instance Doesn't Exist

If your Lightsail instance was terminated, you'll need to:

### Option 1: Create New Lightsail Instance

1. **In AWS Lightsail, click "Create instance"**
2. **Select:**
   - Platform: Linux/Unix
   - Blueprint: Ubuntu 20.04 LTS
   - Instance plan: Choose your plan
3. **Create instance**
4. **Download SSH key** (save as `~/.ssh/lightsail-new.pem`)
5. **Note the public IP**
6. **Update deploy script:**
   ```bash
   AWS_HOST="NEW_IP_ADDRESS"
   AWS_KEY="$HOME/.ssh/lightsail-new.pem"
   ```
7. **Install web server on new instance:**
   ```bash
   sudo apt update
   sudo apt install nginx -y
   sudo systemctl start nginx
   ```
8. **Deploy dashboards**

### Option 2: Deploy to Alternative Platform

**GitHub Pages (Free):**
```bash
cd /Users/srijan/Desktop/aksh
git checkout -b gh-pages
cp dashboard-hub-FINAL.html index.html
git add *.html
git commit -m "Deploy dashboards"
git push origin gh-pages
```
Enable in repo settings → Pages

**Netlify (Free):**
```bash
npm install -g netlify-cli
cd /Users/srijan/Desktop/aksh
netlify deploy --prod
```

**Vercel (Free):**
```bash
npm install -g vercel
cd /Users/srijan/Desktop/aksh
vercel --prod
```

---

## 📋 Files Ready for Deployment

All files are in `/Users/srijan/Desktop/aksh/`:

```
dashboard-hub-FINAL.html (21.9 KB)
comprehensive_earnings_calendar.html (18.0 KB)
market_status_dashboard.html (17.5 KB)
intelligence_dashboard.html (15.6 KB)
```

---

## ✅ Post-Deployment Checklist

Once deployed, verify:

- [ ] Dashboard Hub loads: http://13.200.109.29:8001/static/production/dashboard-hub-FINAL.html
- [ ] Earnings Calendar loads and CSV export works
- [ ] Market Status Dashboard displays stock cards
- [ ] Intelligence Dashboard loads
- [ ] Auto-refresh toggle saves preference
- [ ] No JavaScript errors (F12 → Console)

---

## 🔍 Troubleshooting AWS Connection

### Check Instance State
```bash
# From AWS Console:
# Instance → Details → State should be "Running"
```

### Check Firewall Rules
```bash
# From AWS Console:
# Instance → Networking → Firewall
# Should have: SSH (TCP, 22), HTTP (TCP, 80), Custom (TCP, 8001)
```

### Check SSH Key
```bash
# On your Mac:
ls -la ~/.ssh/lightsail.pem
# Should show: -r-------- (permissions 400)

# Fix if needed:
chmod 400 ~/.ssh/lightsail.pem
```

### Test Connection
```bash
# Verbose SSH test:
ssh -vvv -i ~/.ssh/lightsail.pem ubuntu@13.200.109.29
```

---

## 📞 What to Check First

1. ✅ **AWS Console** - Is instance running?
2. ✅ **Firewall** - Is SSH allowed?
3. ✅ **IP Address** - Did it change?
4. ✅ **SSH Key** - Correct permissions?
5. ✅ **Network** - Can you access other sites?

---

## 🎯 Quick Actions

### If Instance is Stopped:
```bash
# Start it in AWS Console → Click "Start"
```

### If SSH Key Missing:
```bash
# Download from AWS Console → Instance → Connect → Download key
```

### If Firewall Blocking:
```bash
# Add rule in AWS Console → Networking → Add rule → SSH
```

---

## 💡 Why This Happened

Common reasons AWS instances become unreachable:
1. **Instance auto-stopped** (to save costs)
2. **IP address changed** (if instance was stopped/started)
3. **Firewall rule removed** (accidental deletion)
4. **SSH key lost/changed**
5. **Instance terminated** (if on free tier and expired)

---

## 🚀 Summary

**Problem:** AWS server not responding
**Solution:** Start instance in AWS Console
**Deploy:** `./deploy_dashboards.sh html`
**Time:** < 5 minutes once server running

---

## 📚 Related Documentation

- [START_HERE_DEPLOYMENT.md](START_HERE_DEPLOYMENT.md) - Quick start
- [DEPLOYMENT_READINESS_REPORT.md](DEPLOYMENT_READINESS_REPORT.md) - Full deployment guide
- [README_DEPLOYMENT.md](README_DEPLOYMENT.md) - Deployment instructions

---

**The code is 100% ready. You just need to get the AWS instance running, then deployment is one command away!**

**Status:** ✅ CODE READY | ⏳ NEED AWS ACCESS
