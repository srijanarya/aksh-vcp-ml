#!/bin/bash
# Complete Deployment of Real-Time Announcement Intelligence System to AWS
# This script:
# 1. Deploys the intelligence collection service
# 2. Deploys the dashboard API server
# 3. Configures nginx to serve the dashboard on port 8001 with API proxy
# 4. Ensures real-time updates are working

set -e  # Exit on error

SERVER_IP="13.200.109.29"
USER="ubuntu"
KEY_PATH="$HOME/.ssh/lightsail.pem"
REMOTE_DIR="/home/ubuntu/vcp-ml"
STATIC_DIR="/home/ubuntu/vcp/static/production"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🚀 DEPLOYING REAL-TIME ANNOUNCEMENT INTELLIGENCE SYSTEM${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

# Check local database has recent data
echo -e "${YELLOW}📊 Checking local data freshness...${NC}"
LOCAL_DB="data/announcement_intelligence.db"
if [ -f "$LOCAL_DB" ]; then
    latest=$(sqlite3 "$LOCAL_DB" "SELECT MAX(timestamp) FROM announcements;" 2>/dev/null || echo "N/A")
    count=$(sqlite3 "$LOCAL_DB" "SELECT COUNT(*) FROM announcements;" 2>/dev/null || echo "0")
    echo -e "${GREEN}   ✅ Local DB: $count announcements, latest: $latest${NC}"
else
    echo -e "${RED}   ❌ Local database not found at $LOCAL_DB${NC}"
    exit 1
fi

# 1. Copy Files
echo ""
echo -e "${YELLOW}📤 Step 1: Copying files to AWS...${NC}"
ssh -i "$KEY_PATH" "$USER@$SERVER_IP" "mkdir -p $REMOTE_DIR/src/intelligence $REMOTE_DIR/src/data $REMOTE_DIR/data"

scp -i "$KEY_PATH" src/intelligence/*.py "$USER@$SERVER_IP:$REMOTE_DIR/src/intelligence/"
scp -i "$KEY_PATH" src/data/corporate_announcement_fetcher.py "$USER@$SERVER_IP:$REMOTE_DIR/src/data/"
scp -i "$KEY_PATH" src/data/announcement_db.py "$USER@$SERVER_IP:$REMOTE_DIR/src/data/"
scp -i "$KEY_PATH" run_announcement_intelligence.py "$USER@$SERVER_IP:$REMOTE_DIR/"
scp -i "$KEY_PATH" indian_pdf_extractor.py "$USER@$SERVER_IP:$REMOTE_DIR/"
scp -i "$KEY_PATH" serve_dashboard_prod.py "$USER@$SERVER_IP:$REMOTE_DIR/"
scp -i "$KEY_PATH" intelligence_dashboard.html "$USER@$SERVER_IP:$REMOTE_DIR/"
scp -i "$KEY_PATH" requirements_intelligence.txt "$USER@$SERVER_IP:$REMOTE_DIR/" 2>/dev/null || true

# Copy database to bootstrap
scp -i "$KEY_PATH" "$LOCAL_DB" "$USER@$SERVER_IP:$REMOTE_DIR/data/"

echo -e "${GREEN}   ✅ Files copied${NC}"

# 2. Install Dependencies & Setup Services
echo ""
echo -e "${YELLOW}⚙️  Step 2: Installing dependencies and configuring services...${NC}"
ssh -i "$KEY_PATH" "$USER@$SERVER_IP" bash << 'EOF'
    set -e
    cd /home/ubuntu/vcp-ml

    # Activate venv or create it
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate

    # Install Python libs
    echo "📦 Installing Python packages..."
    pip install -q flask flask-cors gunicorn pdfplumber pytesseract pdf2image Pillow requests beautifulsoup4

    # Install System libs for OCR
    echo "📦 Installing system packages..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq tesseract-ocr poppler-utils nginx

    # Create Intelligence Collection Service
    echo "🔧 Creating intelligence collection service..."
    sudo tee /etc/systemd/system/vcp-intelligence.service > /dev/null << 'EOL'
[Unit]
Description=VCP Announcement Intelligence Collection Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/vcp-ml
ExecStart=/home/ubuntu/vcp-ml/venv/bin/python3 run_announcement_intelligence.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/vcp-ml/announcement_intelligence.log
StandardError=append:/home/ubuntu/vcp-ml/announcement_intelligence.log

[Install]
WantedBy=multi-user.target
EOL

    # Create Dashboard API Service (runs on port 5001)
    echo "🔧 Creating dashboard API service..."
    sudo tee /etc/systemd/system/vcp-dashboard-api.service > /dev/null << 'EOL'
[Unit]
Description=VCP Announcement Intelligence Dashboard API
After=network.target vcp-intelligence.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/vcp-ml
ExecStart=/home/ubuntu/vcp-ml/venv/bin/gunicorn -w 2 -b 127.0.0.1:5001 serve_dashboard_prod:app
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/vcp-ml/dashboard_api.log
StandardError=append:/home/ubuntu/vcp-ml/dashboard_api.log

[Install]
WantedBy=multi-user.target
EOL

    # Reload and enable services
    sudo systemctl daemon-reload
    sudo systemctl enable vcp-intelligence vcp-dashboard-api

    echo "✅ Services configured"
EOF

echo -e "${GREEN}   ✅ Dependencies installed and services configured${NC}"

# 3. Configure Nginx
echo ""
echo -e "${YELLOW}🌐 Step 3: Configuring Nginx for integrated access...${NC}"
ssh -i "$KEY_PATH" "$USER@$SERVER_IP" bash << 'EOF'
    set -e

    # Create nginx config that serves both static dashboards AND intelligence API
    sudo tee /etc/nginx/sites-available/vcp-dashboards > /dev/null << 'NGINX_CONF'
server {
    listen 8001;
    server_name _;

    # Serve static dashboards
    location /static/ {
        alias /home/ubuntu/vcp/static/;
        autoindex on;
        try_files $uri $uri/ =404;
    }

    # Proxy intelligence dashboard API
    location /api/ {
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # CORS headers for cross-origin requests
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
    }

    # Root redirects to dashboard hub
    location = / {
        return 301 /static/production/dashboard-hub-FINAL.html;
    }
}
NGINX_CONF

    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/vcp-dashboards /etc/nginx/sites-enabled/

    # Test and reload nginx
    echo "🧪 Testing nginx configuration..."
    sudo nginx -t

    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx

    echo "✅ Nginx configured and reloaded"
EOF

echo -e "${GREEN}   ✅ Nginx configured${NC}"

# 4. Copy dashboard to static directory
echo ""
echo -e "${YELLOW}📋 Step 4: Deploying dashboard to static directory...${NC}"
ssh -i "$KEY_PATH" "$USER@$SERVER_IP" "mkdir -p $STATIC_DIR"
scp -i "$KEY_PATH" intelligence_dashboard.html "$USER@$SERVER_IP:$STATIC_DIR/"
echo -e "${GREEN}   ✅ Dashboard deployed${NC}"

# 5. Start/Restart Services
echo ""
echo -e "${YELLOW}🚀 Step 5: Starting services...${NC}"
ssh -i "$KEY_PATH" "$USER@$SERVER_IP" bash << 'EOF'
    set -e

    echo "🔄 Restarting intelligence collection service..."
    sudo systemctl restart vcp-intelligence
    sleep 2

    echo "🔄 Restarting dashboard API service..."
    sudo systemctl restart vcp-dashboard-api
    sleep 2

    echo ""
    echo "📊 Intelligence Collection Service Status:"
    sudo systemctl status vcp-intelligence --no-pager -l | head -20

    echo ""
    echo "📊 Dashboard API Service Status:"
    sudo systemctl status vcp-dashboard-api --no-pager -l | head -20
EOF

echo -e "${GREEN}   ✅ Services started${NC}"

# 6. Verify Deployment
echo ""
echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🧪 VERIFYING DEPLOYMENT${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

echo -e "${YELLOW}Testing endpoints...${NC}"

# Test API health
echo -n "   API Health Check: "
response=$(curl -s -o /dev/null -w "%{http_code}" "http://$SERVER_IP:8001/api/health" 2>/dev/null || echo "000")
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED (HTTP $response)${NC}"
fi

# Test API announcements endpoint
echo -n "   API Announcements: "
response=$(curl -s -o /dev/null -w "%{http_code}" "http://$SERVER_IP:8001/api/announcements" 2>/dev/null || echo "000")
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ OK${NC}"
    # Get announcement count
    count=$(curl -s "http://$SERVER_IP:8001/api/health" 2>/dev/null | grep -o '"announcement_count":[0-9]*' | grep -o '[0-9]*' || echo "?")
    echo -e "${GREEN}      Database has $count announcements${NC}"
else
    echo -e "${RED}❌ FAILED (HTTP $response)${NC}"
fi

# Test dashboard
echo -n "   Intelligence Dashboard: "
response=$(curl -s -o /dev/null -w "%{http_code}" "http://$SERVER_IP:8001/static/production/intelligence_dashboard.html" 2>/dev/null || echo "000")
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED (HTTP $response)${NC}"
fi

# 7. Display Access Info
echo ""
echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🎉 DEPLOYMENT COMPLETE - REAL-TIME INTELLIGENCE ACTIVE${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

echo -e "${GREEN}📊 Access Your Real-Time Intelligence Dashboard:${NC}"
echo "   Dashboard: http://$SERVER_IP:8001/static/production/intelligence_dashboard.html"
echo ""

echo -e "${GREEN}🔌 API Endpoints:${NC}"
echo "   Health:        http://$SERVER_IP:8001/api/health"
echo "   Announcements: http://$SERVER_IP:8001/api/announcements"
echo ""

echo -e "${GREEN}📝 Monitor Logs:${NC}"
echo "   Intelligence Service: ssh -i $KEY_PATH $USER@$SERVER_IP 'tail -f /home/ubuntu/vcp-ml/announcement_intelligence.log'"
echo "   Dashboard API:        ssh -i $KEY_PATH $USER@$SERVER_IP 'tail -f /home/ubuntu/vcp-ml/dashboard_api.log'"
echo ""

echo -e "${YELLOW}💡 The dashboard auto-refreshes every 30 seconds with real-time data!${NC}"
echo ""
