#!/bin/bash
#
# Deploy Blockbuster Scanner to AWS
#

HOST="13.200.109.29"
USER="ubuntu"
KEY="~/.ssh/lightsail.pem"
REMOTE_DIR="/home/ubuntu/vcp-ml"

echo "🚀 Deploying Blockbuster Scanner to AWS..."

# 1. Sync tools and agents
echo "📦 Syncing files..."
rsync -avz -e "ssh -i $KEY" tools/screener_client.py $USER@$HOST:$REMOTE_DIR/tools/
rsync -avz -e "ssh -i $KEY" agents/ml/blockbuster_detector.py $USER@$HOST:$REMOTE_DIR/agents/ml/
rsync -avz -e "ssh -i $KEY" scan_blockbusters.py $USER@$HOST:$REMOTE_DIR/

# 2. Install dependencies
echo "🔧 Installing dependencies..."
ssh -i $KEY $USER@$HOST << 'EOF'
    cd vcp-ml
    source venv/bin/activate
    pip install beautifulsoup4 requests pandas python-dotenv -q
    
    # Make script executable
    chmod +x scan_blockbusters.py
    
    echo "✅ Dependencies installed"
EOF

# 3. Test the scanner
echo ""
echo "🧪 Testing blockbuster scanner..."
ssh -i $KEY $USER@$HOST << 'EOF'
    cd vcp-ml
    source venv/bin/activate
    
    # Load Telegram credentials
    if [ -f /home/ubuntu/vcp/.env.bot ]; then
        export $(cat /home/ubuntu/vcp/.env.bot | xargs)
    fi
    
    # Set Chat ID found locally
    export TELEGRAM_CHAT_ID="@AIFinanceNews2024"
    
    # Persist Chat ID if not set
    if ! grep -q "TELEGRAM_CHAT_ID" ~/.bashrc; then
        echo 'export TELEGRAM_CHAT_ID="@AIFinanceNews2024"' >> ~/.bashrc
    fi
    
    # Test run (last 30 days, more likely to find results)
    python3 scan_blockbusters.py --days 30 --db /home/ubuntu/vcp/data/earnings_calendar.db
EOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Configuration:"
echo "   Bot Token: (from .env.bot)"
echo "   Chat ID: @AIFinanceNews2024"
echo ""
echo "4. Set up daily cron job:"
echo "   crontab -e"
echo "   Add: 0 19 * * * cd /home/ubuntu/vcp-ml && source venv/bin/activate && python3 scan_blockbusters.py --days 1"
echo "   (Runs daily at 7PM)"
