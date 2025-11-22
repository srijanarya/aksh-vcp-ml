#!/bin/bash
# Deploy Announcement Intelligence System + Dashboard to AWS LightSail

SERVER_IP="13.200.109.29"
USER="ubuntu"
KEY_PATH="~/.ssh/lightsail.pem"
REMOTE_DIR="/home/ubuntu/vcp-ml"

echo "🚀 Deploying Announcement Intelligence System + Dashboard to $SERVER_IP..."

# 1. Create directories
echo "📁 Creating directories..."
ssh -i $KEY_PATH $USER@$SERVER_IP "mkdir -p $REMOTE_DIR/src/intelligence $REMOTE_DIR/src/data $REMOTE_DIR/data/cache/pdfs"

# 2. Copy Files
echo "📤 Copying files..."
scp -i $KEY_PATH src/intelligence/*.py $USER@$SERVER_IP:$REMOTE_DIR/src/intelligence/
scp -i $KEY_PATH src/data/corporate_announcement_fetcher.py $USER@$SERVER_IP:$REMOTE_DIR/src/data/
scp -i $KEY_PATH src/data/announcement_db.py $USER@$SERVER_IP:$REMOTE_DIR/src/data/
scp -i $KEY_PATH run_announcement_intelligence.py $USER@$SERVER_IP:$REMOTE_DIR/
scp -i $KEY_PATH indian_pdf_extractor.py $USER@$SERVER_IP:$REMOTE_DIR/
scp -i $KEY_PATH serve_dashboard_prod.py $USER@$SERVER_IP:$REMOTE_DIR/
scp -i $KEY_PATH intelligence_dashboard.html $USER@$SERVER_IP:$REMOTE_DIR/
scp -i $KEY_PATH requirements_intelligence.txt $USER@$SERVER_IP:$REMOTE_DIR/ 2>/dev/null || echo "requirements_intelligence.txt not found, skipping"

# 3. Install Dependencies & Setup Services
echo "⚙️  Installing dependencies and setting up services..."
ssh -i $KEY_PATH $USER@$SERVER_IP << 'EOF'
    cd /home/ubuntu/vcp-ml
    
    # Install Python libs
    source venv/bin/activate
    pip install -q flask flask-cors gunicorn pdfplumber pytesseract pdf2image Pillow requests beautifulsoup4
    
    # Install System libs for OCR
    sudo apt-get update -qq
    sudo apt-get install -y -qq tesseract-ocr poppler-utils

    # Create/Update Announcement Intelligence Service
    sudo tee /etc/systemd/system/vcp-intelligence.service > /dev/null << EOL
[Unit]
Description=VCP Announcement Intelligence System
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

    # Create Dashboard Service
    sudo tee /etc/systemd/system/vcp-dashboard.service > /dev/null << EOL
[Unit]
Description=VCP Announcement Intelligence Dashboard
After=network.target vcp-intelligence.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/vcp-ml
ExecStart=/home/ubuntu/vcp-ml/venv/bin/gunicorn -w 2 -b 0.0.0.0:5001 serve_dashboard_prod:app
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/vcp-ml/dashboard.log
StandardError=append:/home/ubuntu/vcp-ml/dashboard.log

[Install]
WantedBy=multi-user.target
EOL

    # Reload and Start Services
    sudo systemctl daemon-reload
    sudo systemctl enable vcp-intelligence vcp-dashboard
    sudo systemctl restart vcp-intelligence
    sudo systemctl restart vcp-dashboard
    
    echo ""
    echo "✅ Services started!"
    echo ""
    echo "📊 Intelligence Service Status:"
    sudo systemctl status vcp-intelligence --no-pager -l
    echo ""
    echo "🌐 Dashboard Service Status:"
    sudo systemctl status vcp-dashboard --no-pager -l
    echo ""
    echo "🔥 Opening port 5001 in firewall..."
    sudo ufw allow 5001/tcp 2>/dev/null || echo "UFW not enabled or already configured"
EOF

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "📊 Access Dashboard: http://$SERVER_IP:5001"
echo "🔌 API Health: http://$SERVER_IP:5001/api/health"
echo ""
echo "📝 Check logs:"
echo "   Intelligence: ssh -i $KEY_PATH $USER@$SERVER_IP 'tail -f /home/ubuntu/vcp-ml/announcement_intelligence.log'"
echo "   Dashboard: ssh -i $KEY_PATH $USER@$SERVER_IP 'tail -f /home/ubuntu/vcp-ml/dashboard.log'"
echo ""
