#!/bin/bash
#
# AWS Lightsail Connection Diagnostic Script
# Helps identify why SSH connection to AWS server is failing
#

set +e  # Don't exit on errors - we're diagnosing

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🔍 AWS LIGHTSAIL CONNECTION DIAGNOSTIC${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

# Configuration
AWS_HOST="13.200.109.29"
AWS_USER="ubuntu"
AWS_PORT="22"
AWS_KEY="$HOME/.ssh/lightsail.pem"

echo -e "${YELLOW}Testing connection to: ${AWS_USER}@${AWS_HOST}:${AWS_PORT}${NC}"
echo ""

# Test 1: Check SSH key exists
echo -e "${BLUE}Test 1: SSH Key${NC}"
echo "-----------------------------------"
if [ -f "$AWS_KEY" ]; then
    echo -e "${GREEN}✅ SSH key exists: $AWS_KEY${NC}"

    # Check permissions
    PERMS=$(stat -f %A "$AWS_KEY" 2>/dev/null || stat -c %a "$AWS_KEY" 2>/dev/null)
    if [ "$PERMS" = "400" ] || [ "$PERMS" = "600" ]; then
        echo -e "${GREEN}✅ SSH key permissions correct: $PERMS${NC}"
    else
        echo -e "${YELLOW}⚠️  SSH key permissions: $PERMS (should be 400 or 600)${NC}"
        echo -e "${YELLOW}   Fix with: chmod 400 $AWS_KEY${NC}"
    fi
else
    echo -e "${RED}❌ SSH key NOT found: $AWS_KEY${NC}"
    echo -e "${YELLOW}   Expected location: ~/.ssh/lightsail.pem${NC}"
    echo -e "${YELLOW}   Download from AWS Lightsail console${NC}"
fi
echo ""

# Test 2: Check network connectivity
echo -e "${BLUE}Test 2: Network Connectivity${NC}"
echo "-----------------------------------"
echo -n "Pinging $AWS_HOST... "
if ping -c 3 -W 3 "$AWS_HOST" &>/dev/null; then
    echo -e "${GREEN}✅ Host is reachable${NC}"
else
    echo -e "${RED}❌ Host is NOT reachable (ping failed)${NC}"
    echo -e "${YELLOW}   Possible causes:${NC}"
    echo "   - Instance is stopped"
    echo "   - Firewall blocking ICMP"
    echo "   - Network routing issue"
fi
echo ""

# Test 3: Check SSH port
echo -e "${BLUE}Test 3: SSH Port${NC}"
echo "-----------------------------------"
echo -n "Testing SSH port 22... "
if nc -z -w 5 "$AWS_HOST" 22 &>/dev/null; then
    echo -e "${GREEN}✅ Port 22 is open${NC}"
else
    echo -e "${RED}❌ Port 22 is NOT open or not responding${NC}"
    echo -e "${YELLOW}   Possible causes:${NC}"
    echo "   - Instance is stopped"
    echo "   - Security group blocking SSH"
    echo "   - SSH service not running"
fi
echo ""

# Test 4: Try SSH connection
echo -e "${BLUE}Test 4: SSH Connection${NC}"
echo "-----------------------------------"
echo "Attempting SSH connection (10 second timeout)..."

ssh -i "$AWS_KEY" \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -p "$AWS_PORT" \
    "$AWS_USER@$AWS_HOST" \
    "echo 'Successfully connected!'" 2>&1 | grep -v "Warning:"

SSH_EXIT=$?

if [ $SSH_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ SSH connection successful!${NC}"
else
    echo -e "${RED}❌ SSH connection failed (exit code: $SSH_EXIT)${NC}"
    echo ""
    echo -e "${YELLOW}Common SSH error codes:${NC}"
    echo "   255 = Connection timeout or refused"
    echo "   1 = Authentication failed"
    echo "   other = Various SSH errors"
fi
echo ""

# Test 5: Check if server might be at different IP
echo -e "${BLUE}Test 5: DNS/IP Check${NC}"
echo "-----------------------------------"
echo -n "Resolving hostname... "
if host "$AWS_HOST" &>/dev/null; then
    RESOLVED_IP=$(host "$AWS_HOST" | grep "has address" | awk '{print $4}')
    if [ ! -z "$RESOLVED_IP" ]; then
        echo -e "${GREEN}✅ Resolves to: $RESOLVED_IP${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No DNS record (using direct IP)${NC}"
fi
echo ""

# Summary and Recommendations
echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}📋 DIAGNOSTIC SUMMARY${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

if [ $SSH_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ CONNECTION SUCCESSFUL!${NC}"
    echo ""
    echo "Your server is accessible. You can now deploy dashboards:"
    echo ""
    echo -e "${YELLOW}   ./deploy_dashboards.sh html${NC}"
    echo ""
else
    echo -e "${RED}❌ CONNECTION FAILED${NC}"
    echo ""
    echo -e "${YELLOW}Recommended Actions (in order):${NC}"
    echo ""
    echo "1. Check AWS Lightsail Console"
    echo "   → https://lightsail.aws.amazon.com/"
    echo "   → Verify instance is 'Running' (not stopped)"
    echo ""
    echo "2. Check Instance Networking"
    echo "   → Go to instance → Networking tab"
    echo "   → Ensure SSH (port 22) firewall rule exists"
    echo "   → Rule should allow: Application=SSH, Protocol=TCP, Port=22"
    echo ""
    echo "3. Verify Instance Details"
    echo "   → Check public IP hasn't changed"
    echo "   → Current expected IP: $AWS_HOST"
    echo ""
    echo "4. Try Lightsail Browser-Based SSH"
    echo "   → Click instance → Connect using SSH"
    echo "   → If this works, it's a local SSH config issue"
    echo ""
    echo "5. Check Your Internet Connection"
    echo "   → Ensure you can access other websites"
    echo "   → Try from different network if possible"
    echo ""
    echo "6. Alternative: Redeploy to New Instance"
    echo "   → Create new Lightsail instance"
    echo "   → Update AWS_HOST in deploy_dashboards.sh"
    echo "   → Download new SSH key"
    echo ""
fi

echo -e "${BLUE}================================================================================${NC}"
echo ""

# Provide helpful commands
echo -e "${YELLOW}Useful Commands:${NC}"
echo ""
echo "Test SSH manually:"
echo "   ssh -i $AWS_KEY $AWS_USER@$AWS_HOST"
echo ""
echo "Fix SSH key permissions:"
echo "   chmod 400 $AWS_KEY"
echo ""
echo "Deploy when ready:"
echo "   ./deploy_dashboards.sh html"
echo ""
echo "View deployment script:"
echo "   cat deploy_dashboards.sh"
echo ""

echo -e "${BLUE}================================================================================${NC}"
