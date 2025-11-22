#!/bin/bash
#
# AWS Dashboard Restart Script
# Diagnoses and restarts the VCP dashboard on AWS
#
# Usage: ./restart_aws_dashboard.sh
#

set -e  # Exit on error

# Configuration
AWS_HOST="13.200.109.29"
AWS_USER="ubuntu"
AWS_PORT="22"
AWS_KEY="$HOME/.ssh/lightsail.pem"
SSH_OPTS="-i $AWS_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🔧 AWS DASHBOARD RESTART SCRIPT${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

# Step 1: Check SSH connectivity
echo -e "${YELLOW}Step 1: Checking SSH connectivity...${NC}"
if ssh $SSH_OPTS -p "$AWS_PORT" "$AWS_USER@$AWS_HOST" "echo 'SSH OK'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "${RED}❌ Cannot SSH to server${NC}"
    echo -e "${YELLOW}Possible issues:${NC}"
    echo "  1. AWS instance is stopped - Check AWS console and start it"
    echo "  2. Security group doesn't allow your IP - Add your IP to security group"
    echo "  3. SSH key is incorrect - Check $AWS_KEY exists"
    echo "  4. Network connectivity issue - Check your internet"
    echo ""
    echo -e "${YELLOW}To check AWS instance status:${NC}"
    echo "  aws lightsail get-instance --instance-name your-instance-name"
    echo ""
    echo -e "${YELLOW}To start AWS instance:${NC}"
    echo "  aws lightsail start-instance --instance-name your-instance-name"
    exit 1
fi

echo ""

# Step 2: Check if FastAPI/Uvicorn is running
echo -e "${YELLOW}Step 2: Checking if web server is running...${NC}"
PROCESS_CHECK=$(ssh $SSH_OPTS -p "$AWS_PORT" "$AWS_USER@$AWS_HOST" "ps aux | grep -E '(uvicorn|fastapi|python.*main)' | grep -v grep" 2>/dev/null || echo "")

if [ -z "$PROCESS_CHECK" ]; then
    echo -e "${RED}❌ Web server is NOT running${NC}"
    WEB_SERVER_DOWN=true
else
    echo -e "${GREEN}✅ Web server process found:${NC}"
    echo "$PROCESS_CHECK"
    WEB_SERVER_DOWN=false
fi

echo ""

# Step 3: Check port 8001
echo -e "${YELLOW}Step 3: Checking if port 8001 is listening...${NC}"
PORT_CHECK=$(ssh $SSH_OPTS -p "$AWS_PORT" "$AWS_USER@$AWS_HOST" "lsof -i :8001 2>/dev/null || netstat -tuln | grep :8001" 2>/dev/null || echo "")

if [ -z "$PORT_CHECK" ]; then
    echo -e "${RED}❌ Port 8001 is NOT listening${NC}"
    PORT_DOWN=true
else
    echo -e "${GREEN}✅ Port 8001 is active${NC}"
    PORT_DOWN=false
fi

echo ""

# Step 4: Check application directory
echo -e "${YELLOW}Step 4: Checking application directory...${NC}"
APP_DIR_CHECK=$(ssh $SSH_OPTS -p "$AWS_PORT" "$AWS_USER@$AWS_HOST" "ls -la /home/ubuntu/vcp/main.py 2>/dev/null" || echo "NOT_FOUND")

if [[ "$APP_DIR_CHECK" == *"NOT_FOUND"* ]]; then
    echo -e "${RED}❌ Application not found at /home/ubuntu/vcp/${NC}"
    echo -e "${YELLOW}Please verify the correct application path${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Application directory exists${NC}"
fi

echo ""

# Step 5: Restart web server if needed
if [ "$WEB_SERVER_DOWN" = true ] || [ "$PORT_DOWN" = true ]; then
    echo -e "${YELLOW}Step 5: Restarting web server...${NC}"

    # Kill any existing processes
    echo "  Killing any existing processes..."
    ssh $SSH_OPTS -p "$AWS_PORT" "$AWS_USER@$AWS_HOST" "pkill -f uvicorn || true; pkill -f 'python.*main' || true" 2>/dev/null

    sleep 2

    # Start the server
    echo "  Starting FastAPI/Uvicorn server..."
    ssh $SSH_OPTS -p "$AWS_PORT" "$AWS_USER@$AWS_HOST" << 'ENDSSH'
cd /home/ubuntu/vcp

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start uvicorn in background
nohup uvicorn main:app --host 0.0.0.0 --port 8001 --reload > /home/ubuntu/vcp/logs/uvicorn.log 2>&1 &

# Get PID
echo $! > /home/ubuntu/vcp/uvicorn.pid

echo "Server started with PID: $(cat /home/ubuntu/vcp/uvicorn.pid)"
ENDSSH

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Web server restart command sent${NC}"
    else
        echo -e "${RED}❌ Failed to restart web server${NC}"
        exit 1
    fi

    # Wait for server to start
    echo "  Waiting for server to start..."
    sleep 5

else
    echo -e "${GREEN}Step 5: Web server is already running${NC}"
fi

echo ""

# Step 6: Test dashboard access
echo -e "${YELLOW}Step 6: Testing dashboard access...${NC}"

# Wait a bit more for server to be fully ready
sleep 3

# Test via curl from local machine
echo "  Testing from local machine..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "http://$AWS_HOST:8001/static/production/dashboard-hub-FINAL.html" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Dashboard is accessible (HTTP $HTTP_CODE)${NC}"
elif [ "$HTTP_CODE" = "000" ]; then
    echo -e "${RED}❌ Cannot connect to dashboard (Connection timeout/refused)${NC}"
    echo -e "${YELLOW}Checking from AWS server itself...${NC}"

    # Test from AWS server itself
    SERVER_TEST=$(ssh $SSH_OPTS -p "$AWS_PORT" "$AWS_USER@$AWS_HOST" "curl -s -o /dev/null -w '%{http_code}' http://localhost:8001/static/production/dashboard-hub-FINAL.html 2>/dev/null" || echo "000")

    if [ "$SERVER_TEST" = "200" ]; then
        echo -e "${YELLOW}⚠️  Server responds locally but not externally${NC}"
        echo -e "${YELLOW}Issue: Security group firewall is blocking port 8001${NC}"
        echo ""
        echo -e "${YELLOW}To fix:${NC}"
        echo "  1. Go to AWS Lightsail console"
        echo "  2. Click on your instance"
        echo "  3. Go to 'Networking' tab"
        echo "  4. Add firewall rule: Custom TCP, Port 8001, Source: Anywhere"
        echo ""
    else
        echo -e "${RED}❌ Server not responding even locally (HTTP $SERVER_TEST)${NC}"
        echo -e "${YELLOW}Checking server logs...${NC}"
        ssh $SSH_OPTS -p "$AWS_PORT" "$AWS_USER@$AWS_HOST" "tail -20 /home/ubuntu/vcp/logs/uvicorn.log 2>/dev/null || echo 'No logs found'"
    fi
else
    echo -e "${RED}❌ Dashboard returned HTTP $HTTP_CODE${NC}"
fi

echo ""

# Step 7: Display server info
echo -e "${YELLOW}Step 7: Server information...${NC}"
ssh $SSH_OPTS -p "$AWS_PORT" "$AWS_USER@$AWS_HOST" << 'ENDSSH'
echo "Current processes:"
ps aux | grep -E '(uvicorn|python.*main)' | grep -v grep || echo "No web server process found"

echo ""
echo "Port status:"
lsof -i :8001 2>/dev/null || netstat -tuln | grep :8001 || echo "Port 8001 not listening"

echo ""
echo "Recent logs (last 10 lines):"
tail -10 /home/ubuntu/vcp/logs/uvicorn.log 2>/dev/null || echo "No logs available"
ENDSSH

echo ""

# Final summary
echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}📋 SUMMARY${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Dashboard is WORKING${NC}"
    echo ""
    echo "Access your dashboard at:"
    echo "  🌐 http://$AWS_HOST:8001/static/production/dashboard-hub-FINAL.html"
    echo "  🌐 http://$AWS_HOST:8001/static/production/comprehensive_earnings_calendar.html"
    echo "  🌐 http://$AWS_HOST:8001/static/production/intelligence_dashboard.html"
    echo ""
else
    echo -e "${RED}❌ Dashboard is NOT working${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"

    if [ "$WEB_SERVER_DOWN" = true ]; then
        echo "  1. Web server was restarted - wait 30 seconds and try again"
        echo "  2. Check logs: ssh $SSH_OPTS ubuntu@$AWS_HOST 'tail -f /home/ubuntu/vcp/logs/uvicorn.log'"
    fi

    echo "  3. Check security group allows port 8001 from your IP"
    echo "  4. Verify main.py exists and has no errors"
    echo "  5. Check Python dependencies are installed"
    echo ""
    echo -e "${YELLOW}Manual restart commands:${NC}"
    echo "  ssh $SSH_OPTS ubuntu@$AWS_HOST"
    echo "  cd /home/ubuntu/vcp"
    echo "  pkill -f uvicorn"
    echo "  nohup uvicorn main:app --host 0.0.0.0 --port 8001 &"
fi

echo ""
echo -e "${BLUE}================================================================================${NC}"
