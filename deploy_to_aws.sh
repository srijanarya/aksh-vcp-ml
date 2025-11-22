#!/bin/bash

# AWS Connection Details
HOST="13.200.109.29"
USER="ubuntu"
KEY="~/.ssh/lightsail.pem"
REMOTE_DIR="/home/ubuntu/vcp-ml"

echo "🚀 Starting Deployment to $HOST..."

# 1. Sync Agents and Tools
echo "📦 Syncing agents and tools..."
rsync -avz -e "ssh -i $KEY" --progress \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    agents/ \
    $USER@$HOST:$REMOTE_DIR/agents/

rsync -avz -e "ssh -i $KEY" --progress \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    tools/ \
    $USER@$HOST:$REMOTE_DIR/tools/

    skills/ \
    $USER@$HOST:$REMOTE_DIR/skills/

# Sync Models
echo "📦 Syncing models..."
rsync -avz -e "ssh -i $KEY" --progress \
    models/ \
    $USER@$HOST:$REMOTE_DIR/models/

# Sync Historical Financials DB
echo "📦 Syncing historical financials..."
scp -i $KEY data/historical_financials.db $USER@$HOST:$REMOTE_DIR/data/

# 2. Sync New API Extension
echo "📦 Syncing API extension..."
scp -i $KEY ml_api_extension.py $USER@$HOST:$REMOTE_DIR/

# 3. Install Dependencies on Server (pypdf)
echo "🔧 Installing dependencies on server..."
ssh -i $KEY $USER@$HOST << 'EOF'
    source vcp-ml/venv/bin/activate
    pip install pypdf
    
    # Check if simple_ml_api.py exists and needs patching
    if [ -f "vcp-ml/simple_ml_api.py" ]; then
        echo "Checking if API needs patching..."
        if ! grep -q "ml_api_extension" "vcp-ml/simple_ml_api.py"; then
            echo "Patching simple_ml_api.py to include earnings router..."
            # Append import and include_router
            sed -i '/from fastapi import FastAPI/a from ml_api_extension import router as earnings_router' vcp-ml/simple_ml_api.py
            sed -i '/app = FastAPI()/a app.include_router(earnings_router, prefix="/api/v1")' vcp-ml/simple_ml_api.py
        fi
    fi
    
    # Restart Service
    echo "🔄 Restarting vcp-ml-api service..."
    sudo systemctl restart vcp-ml-api
    
    # Check Status
    sleep 2
    sudo systemctl status vcp-ml-api --no-pager | head -n 10
EOF

echo "✅ Deployment Complete!"
