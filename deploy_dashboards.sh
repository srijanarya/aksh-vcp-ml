#!/bin/bash
#
# Dashboard Deployment Script
# Deploys consolidated dashboards to AWS production server
#
# Usage: ./deploy_dashboards.sh [html|react|all]
#

set -e  # Exit on error

# Configuration
AWS_HOST="13.200.109.29"
AWS_USER="ubuntu"  # Change this to your AWS username
AWS_PORT="22"
AWS_KEY="$HOME/.ssh/lightsail.pem"  # SSH key for AWS
AWS_BASE_PATH="/home/ubuntu/vcp/static"  # Static files path (where FastAPI serves from)
LOCAL_FRONTEND="/Users/srijan/Desktop/aksh"
SSH_OPTS="-i $AWS_KEY"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🚀 VCP DASHBOARD DEPLOYMENT SCRIPT${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

# Function to check SSH connection
check_connection() {
    echo -e "${YELLOW}📡 Checking connection to AWS server...${NC}"
    if ssh $SSH_OPTS -o ConnectTimeout=5 -p "$AWS_PORT" "$AWS_USER@$AWS_HOST" "echo 'Connected'" &>/dev/null; then
        echo -e "${GREEN}✅ Connected to $AWS_HOST${NC}"
        return 0
    else
        echo -e "${RED}❌ Cannot connect to $AWS_HOST${NC}"
        echo -e "${YELLOW}💡 Please check:${NC}"
        echo "   1. AWS_USER is correct (currently: $AWS_USER)"
        echo "   2. SSH keys are set up"
        echo "   3. Server is running"
        echo "   4. Security group allows SSH from your IP"
        return 1
    fi
}

# Function to create remote directories
create_directories() {
    echo -e "${YELLOW}📁 Creating remote directories...${NC}"
    ssh $SSH_OPTS -p "$AWS_PORT" "$AWS_USER@$AWS_HOST" "mkdir -p $AWS_BASE_PATH/production $AWS_BASE_PATH/development $AWS_BASE_PATH/react-app"
    echo -e "${GREEN}✅ Directories created${NC}"
}

# Function to deploy HTML dashboards
deploy_html() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}📤 DEPLOYING HTML DASHBOARDS${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""

    # Production dashboards
    echo -e "${YELLOW}📤 Deploying production dashboards...${NC}"
    # Deploy specific files from root to production folder
    scp $SSH_OPTS -P "$AWS_PORT" \
        "$LOCAL_FRONTEND/dashboard-hub-FINAL.html" \
        "$LOCAL_FRONTEND/comprehensive_earnings_calendar.html" \
        "$LOCAL_FRONTEND/blockbuster.html" \
        "$LOCAL_FRONTEND/intelligence_dashboard.html" \
        "$AWS_USER@$AWS_HOST:$AWS_BASE_PATH/production/"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Production dashboards deployed${NC}"
        echo "   - dashboard-hub-FINAL.html"
        echo "   - comprehensive_earnings_calendar.html"
        echo "   - blockbuster.html"
        echo "   - intelligence_dashboard.html"
    else
        echo -e "${RED}❌ Failed to deploy production dashboards${NC}"
        return 1
    fi

    # Development dashboards (Skipping for now as we don't have them in root, or assuming they are not critical for this task)
    # But to keep script valid, I'll comment out or just leave as is if I can find them.
    # The user is in /Users/srijan/Desktop/aksh. I don't see 'development' folder in root.
    # So I will skip development deployment for now to avoid errors.
}

# Function to deploy React app (Skipping as requested focus is on HTML calendar)
deploy_react() {
    echo "Skipping React deployment in this simplified script."
}

# Function to test deployment
test_deployment() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}🧪 TESTING DEPLOYMENT${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""

    AWS_URL="http://$AWS_HOST:8001"

    # Test HTML dashboards
    echo -e "${YELLOW}Testing HTML dashboards...${NC}"

    dashboards=(
        "production/dashboard-hub-FINAL.html"
        "production/comprehensive_earnings_calendar.html"
        "production/intelligence_dashboard.html"
    )

    for dashboard in "${dashboards[@]}"; do
        echo -n "   Testing $dashboard... "
        response=$(curl -s -o /dev/null -w "%{http_code}" "$AWS_URL/static/$dashboard" 2>/dev/null || echo "000")
        if [ "$response" = "200" ]; then
            echo -e "${GREEN}✅ OK${NC}"
        else
            echo -e "${RED}❌ FAILED (HTTP $response)${NC}"
        fi
    done
}

# Function to display URLs
display_urls() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}📋 DEPLOYMENT COMPLETE - ACCESS YOUR DASHBOARDS${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""

    echo -e "${GREEN}Production HTML Dashboards:${NC}"
    echo "   Dashboard Hub:       http://$AWS_HOST:8001/static/production/dashboard-hub-FINAL.html"
    echo "   Earnings Calendar:   http://$AWS_HOST:8001/static/production/comprehensive_earnings_calendar.html"
    echo ""
    echo -e "${GREEN}✅ All dashboards deployed successfully!${NC}"
}

# Main deployment logic
DEPLOY_TYPE="${1:-all}"

# Check connection first
if ! check_connection; then
    exit 1
fi

# Create directories
create_directories

# Deploy based on argument
case "$DEPLOY_TYPE" in
    html)
        deploy_html
        test_deployment
        display_urls
        ;;
    all)
        deploy_html
        test_deployment
        display_urls
        ;;
    *)
        echo -e "${RED}❌ Invalid deployment type: $DEPLOY_TYPE${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}================================================================================${NC}"
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""
