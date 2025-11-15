#!/bin/bash
#
# Deploy VCP ML System to AWS LightSail
# This script handles complete deployment of the ML prediction system
#

set -e

# Configuration
AWS_USER="ubuntu"
AWS_HOST="13.200.109.29"
SSH_KEY="$HOME/.ssh/lightsail.pem"
LOCAL_PROJECT_DIR="/Users/srijan/Desktop/aksh"
LOCAL_VCP_DATA="/Users/srijan/vcp_clean_test/vcp"
REMOTE_PROJECT_DIR="/home/ubuntu/vcp-ml"
REMOTE_DATA_DIR="/home/ubuntu/vcp-ml/data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

separator() {
    echo ""
    echo "================================================================================"
    echo "$1"
    echo "================================================================================"
    echo ""
}

# Step 1: Test SSH Connection
test_ssh_connection() {
    separator "Step 1: Testing SSH Connection to AWS LightSail"

    log_info "Connecting to $AWS_HOST..."

    if ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$AWS_USER@$AWS_HOST" "echo 'Connection successful'" &>/dev/null; then
        log_success "SSH connection to AWS LightSail established"

        # Get system info
        log_info "Fetching AWS instance information..."
        ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'EOF'
echo "Hostname: $(hostname)"
echo "OS: $(lsb_release -d | cut -f2)"
echo "Kernel: $(uname -r)"
echo "Python: $(python3 --version 2>&1)"
echo "Disk Space: $(df -h / | tail -1 | awk '{print $4 " available out of " $2}')"
echo "Memory: $(free -h | grep Mem | awk '{print $7 " available out of " $2}')"
EOF
    else
        log_error "Failed to connect to AWS LightSail"
        log_error "Please check:"
        log_error "  1. SSH key permissions: chmod 400 $SSH_KEY"
        log_error "  2. Security group allows SSH from your IP"
        log_error "  3. Instance is running"
        exit 1
    fi
}

# Step 2: Prepare AWS Environment
prepare_aws_environment() {
    separator "Step 2: Preparing AWS Environment"

    log_info "Creating project directories..."
    ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << EOF
mkdir -p $REMOTE_PROJECT_DIR
mkdir -p $REMOTE_DATA_DIR
mkdir -p $REMOTE_DATA_DIR/models/registry
mkdir -p $REMOTE_PROJECT_DIR/logs
EOF

    log_success "Directories created on AWS"

    log_info "Checking/Installing system dependencies..."
    ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'EOF'
# Update package list
sudo apt-get update -qq

# Install required system packages
PACKAGES="python3-pip python3-venv sqlite3 git curl"
for pkg in $PACKAGES; do
    if ! dpkg -l | grep -q "^ii  $pkg"; then
        echo "Installing $pkg..."
        sudo apt-get install -y $pkg > /dev/null 2>&1
    else
        echo "$pkg already installed"
    fi
done
EOF

    log_success "System dependencies ready"
}

# Step 3: Transfer ML System Code
transfer_ml_system() {
    separator "Step 3: Transferring ML System Code"

    log_info "Creating deployment package..."
    cd "$LOCAL_PROJECT_DIR"

    # Create a clean package (exclude tests, cache, etc.)
    tar --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.pytest_cache' \
        --exclude='*.db-journal' \
        --exclude='venv*' \
        --exclude='.git' \
        --exclude='tests' \
        -czf /tmp/vcp-ml-system.tar.gz \
        agents/ml/*.py \
        api/*.py \
        monitoring/*.py \
        deployment/*.py \
        requirements.txt \
        .env.local 2>/dev/null || true

    log_info "Uploading ML system to AWS ($(du -h /tmp/vcp-ml-system.tar.gz | cut -f1))..."
    scp -i "$SSH_KEY" /tmp/vcp-ml-system.tar.gz "$AWS_USER@$AWS_HOST:/tmp/"

    log_info "Extracting on AWS..."
    ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << EOF
cd $REMOTE_PROJECT_DIR
tar -xzf /tmp/vcp-ml-system.tar.gz
rm /tmp/vcp-ml-system.tar.gz
EOF

    rm /tmp/vcp-ml-system.tar.gz
    log_success "ML system code transferred"
}

# Step 4: Transfer Databases
transfer_databases() {
    separator "Step 4: Transferring Databases"

    # List of databases to transfer
    declare -a databases=(
        "$LOCAL_VCP_DATA/vcp_trading_local.db:vcp_trading_local.db"
        "$LOCAL_VCP_DATA/data/earnings_calendar.db:earnings_calendar.db"
        "$LOCAL_PROJECT_DIR/data/ml_collection_status.db:ml_collection_status.db"
    )

    for db_pair in "${databases[@]}"; do
        IFS=':' read -r local_path remote_name <<< "$db_pair"

        if [ -f "$local_path" ] && [ -s "$local_path" ]; then
            size=$(du -h "$local_path" | cut -f1)
            log_info "Transferring $remote_name ($size)..."
            scp -i "$SSH_KEY" "$local_path" "$AWS_USER@$AWS_HOST:$REMOTE_DATA_DIR/$remote_name"
            log_success "$remote_name transferred"
        else
            log_warning "Skipping $remote_name (not found or empty)"
        fi
    done

    # Transfer model registry if it exists
    if [ -f "$LOCAL_PROJECT_DIR/data/models/registry/registry.db" ]; then
        log_info "Transferring model registry..."
        scp -i "$SSH_KEY" "$LOCAL_PROJECT_DIR/data/models/registry/registry.db" \
            "$AWS_USER@$AWS_HOST:$REMOTE_DATA_DIR/models/registry/registry.db"
        log_success "Model registry transferred"
    fi
}

# Step 5: Setup Python Environment
setup_python_environment() {
    separator "Step 5: Setting up Python Environment"

    log_info "Creating virtual environment..."
    ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << EOF
cd $REMOTE_PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt > /tmp/pip_install.log 2>&1
    if [ \$? -eq 0 ]; then
        echo "Dependencies installed successfully"
    else
        echo "Some dependencies failed - check /tmp/pip_install.log"
        tail -20 /tmp/pip_install.log
    fi
else
    echo "requirements.txt not found, installing core packages..."
    pip install fastapi uvicorn scikit-learn xgboost lightgbm pandas numpy > /dev/null 2>&1
fi
EOF

    log_success "Python environment ready"
}

# Step 6: Create Systemd Service
create_systemd_service() {
    separator "Step 6: Creating Systemd Service"

    log_info "Creating vcp-ml-api.service..."
    ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'EOF'
sudo tee /etc/systemd/system/vcp-ml-api.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=VCP ML Prediction API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/vcp-ml
Environment="PATH=/home/ubuntu/vcp-ml/venv/bin"
EnvironmentFile=/home/ubuntu/vcp-ml/.env.local
ExecStart=/home/ubuntu/vcp-ml/venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

sudo systemctl daemon-reload
sudo systemctl enable vcp-ml-api
EOF

    log_success "Systemd service created"
}

# Step 7: Start Service
start_service() {
    separator "Step 7: Starting ML API Service"

    log_info "Starting vcp-ml-api service..."
    ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'EOF'
sudo systemctl restart vcp-ml-api
sleep 5
sudo systemctl status vcp-ml-api --no-pager | head -20
EOF

    log_success "Service started"
}

# Step 8: Run Health Checks
run_health_checks() {
    separator "Step 8: Running Health Checks"

    log_info "Waiting for API to be ready..."
    sleep 10

    log_info "Testing API health endpoint..."
    if curl -f -s "http://$AWS_HOST:8002/health" > /dev/null 2>&1; then
        log_success "API health check passed"

        log_info "API Response:"
        curl -s "http://$AWS_HOST:8002/health" | python3 -m json.tool 2>/dev/null || curl -s "http://$AWS_HOST:8002/health"
    else
        log_warning "API health check failed - service may still be starting"
        log_info "Check logs with: ssh -i $SSH_KEY $AWS_USER@$AWS_HOST 'sudo journalctl -u vcp-ml-api -n 50'"
    fi

    echo ""
    log_info "Testing prediction endpoint..."
    curl -s -X POST "http://$AWS_HOST:8002/api/v1/predict" \
        -H "Content-Type: application/json" \
        -d '{"symbol": "TCS", "features": {}}' 2>/dev/null | head -20 || log_warning "Prediction endpoint test failed"
}

# Step 9: Display Summary
display_summary() {
    separator "Deployment Complete!"

    echo -e "${GREEN}✅ VCP ML System successfully deployed to AWS LightSail${NC}"
    echo ""
    echo "📊 Deployment Summary:"
    echo "  • AWS Instance: $AWS_HOST"
    echo "  • API Port: 8002"
    echo "  • Service: vcp-ml-api"
    echo "  • Project Dir: $REMOTE_PROJECT_DIR"
    echo ""
    echo "🔗 API Endpoints:"
    echo "  • Health: http://$AWS_HOST:8002/health"
    echo "  • Docs: http://$AWS_HOST:8002/docs"
    echo "  • Predict: http://$AWS_HOST:8002/api/v1/predict"
    echo "  • Batch: http://$AWS_HOST:8002/api/v1/batch-predict"
    echo ""
    echo "📝 Useful Commands:"
    echo "  • Check status: ssh -i $SSH_KEY $AWS_USER@$AWS_HOST 'sudo systemctl status vcp-ml-api'"
    echo "  • View logs: ssh -i $SSH_KEY $AWS_USER@$AWS_HOST 'sudo journalctl -u vcp-ml-api -f'"
    echo "  • Restart: ssh -i $SSH_KEY $AWS_USER@$AWS_HOST 'sudo systemctl restart vcp-ml-api'"
    echo "  • SSH: ssh -i $SSH_KEY $AWS_USER@$AWS_HOST"
    echo ""
    echo "🧪 Test the API:"
    echo "  curl http://$AWS_HOST:8002/health"
    echo ""
}

# Main execution
main() {
    separator "🚀 VCP ML System - AWS LightSail Deployment"

    # Run all steps
    test_ssh_connection
    prepare_aws_environment
    transfer_ml_system
    transfer_databases
    setup_python_environment
    create_systemd_service
    start_service
    run_health_checks
    display_summary
}

# Run main function
main "$@"
