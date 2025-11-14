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
LOCAL_FRONTEND="/Users/srijan/vcp_clean_test/vcp/frontend"
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
    scp $SSH_OPTS -P "$AWS_PORT" "$LOCAL_FRONTEND/production"/*.html "$AWS_USER@$AWS_HOST:$AWS_BASE_PATH/production/"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Production dashboards deployed${NC}"
        echo "   - dashboard-hub.html"
        echo "   - earnings-calendar.html"
        echo "   - blockbuster-scanner.html"
        echo "   - alerts-dashboard.html"
    else
        echo -e "${RED}❌ Failed to deploy production dashboards${NC}"
        return 1
    fi

    # Development dashboards
    echo ""
    echo -e "${YELLOW}📤 Deploying development dashboards...${NC}"
    scp $SSH_OPTS -P "$AWS_PORT" "$LOCAL_FRONTEND/development"/*.html "$AWS_USER@$AWS_HOST:$AWS_BASE_PATH/development/"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Development dashboards deployed${NC}"
        echo "   - dexter_chat.html"
        echo "   - vikram-agent.html"
    else
        echo -e "${RED}❌ Failed to deploy development dashboards${NC}"
        return 1
    fi

    # Main index
    echo ""
    echo -e "${YELLOW}📤 Deploying main index.html...${NC}"
    scp $SSH_OPTS -P "$AWS_PORT" "$LOCAL_FRONTEND/index.html" "$AWS_USER@$AWS_HOST:$AWS_BASE_PATH/"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Main index deployed${NC}"
    else
        echo -e "${RED}❌ Failed to deploy index.html${NC}"
        return 1
    fi
}

# Function to deploy React app
deploy_react() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}⚛️  DEPLOYING REACT APPLICATION${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""

    # Check if build exists
    if [ ! -d "$LOCAL_FRONTEND/react-app/dist" ]; then
        echo -e "${RED}❌ React app not built yet!${NC}"
        echo -e "${YELLOW}💡 Building React app first...${NC}"
        cd "$LOCAL_FRONTEND/react-app"
        npm run build
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Build failed${NC}"
            return 1
        fi
    fi

    echo -e "${YELLOW}📤 Deploying React app dist/ folder...${NC}"
    scp -r $SSH_OPTS -P "$AWS_PORT" "$LOCAL_FRONTEND/react-app/dist"/* "$AWS_USER@$AWS_HOST:$AWS_BASE_PATH/react-app/"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ React app deployed${NC}"
        echo "   Location: $AWS_BASE_PATH/react-app/"
        echo "   Pages: 11 (Home, Earnings, Blockbuster, Announcements, etc.)"
    else
        echo -e "${RED}❌ Failed to deploy React app${NC}"
        return 1
    fi
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
        "production/dashboard-hub.html"
        "production/earnings-calendar.html"
        "production/blockbuster-scanner.html"
        "production/alerts-dashboard.html"
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

    # Test React app
    echo ""
    echo -e "${YELLOW}Testing React app...${NC}"
    echo -n "   Testing react-app/index.html... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$AWS_URL/static/react-app/index.html" 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ OK${NC}"
    else
        echo -e "${RED}❌ FAILED (HTTP $response)${NC}"
    fi
}

# Function to display URLs
display_urls() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}📋 DEPLOYMENT COMPLETE - ACCESS YOUR DASHBOARDS${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""

    echo -e "${GREEN}Production HTML Dashboards:${NC}"
    echo "   Dashboard Hub:       http://$AWS_HOST:8001/static/production/dashboard-hub.html"
    echo "   Earnings Calendar:   http://$AWS_HOST:8001/static/production/earnings-calendar.html"
    echo "   Blockbuster Scanner: http://$AWS_HOST:8001/static/production/blockbuster-scanner.html"
    echo "   Alerts Dashboard:    http://$AWS_HOST:8001/static/production/alerts-dashboard.html"
    echo ""

    echo -e "${YELLOW}Development Dashboards:${NC}"
    echo "   Dexter AI Agent:     http://$AWS_HOST:8001/static/development/dexter_chat.html"
    echo "   Vikram AI Agent:     http://$AWS_HOST:8001/static/development/vikram-agent.html"
    echo ""

    echo -e "${BLUE}React Application:${NC}"
    echo "   React App (Home):    http://$AWS_HOST:8001/static/react-app/index.html"
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
    react)
        deploy_react
        test_deployment
        display_urls
        ;;
    all)
        deploy_html
        deploy_react
        test_deployment
        display_urls
        ;;
    *)
        echo -e "${RED}❌ Invalid deployment type: $DEPLOY_TYPE${NC}"
        echo "Usage: $0 [html|react|all]"
        echo "  html  - Deploy only HTML dashboards"
        echo "  react - Deploy only React application"
        echo "  all   - Deploy everything (default)"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}================================================================================${NC}"
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""
