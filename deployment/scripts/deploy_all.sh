#!/bin/bash
# Complete autonomous deployment: Staging → Smoke Tests → Production
#
# This script executes the full deployment pipeline:
# 1. Pre-deployment validation
# 2. Deploy to staging
# 3. Run smoke tests
# 4. Deploy to production (if staging passes)
# 5. Monitor production deployment
#
# Author: VCP Financial Research Team
# Created: 2025-11-14

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "                    VCP ML PLATFORM - FULL DEPLOYMENT                          "
echo "================================================================================"
echo ""

# Step 1: Pre-deployment validation
echo -e "${BLUE}📋 STEP 1: PRE-DEPLOYMENT VALIDATION${NC}"
echo "--------------------------------------------------------------------------------"
python3 deployment/agents/pre_deployment_validator.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Pre-deployment validation failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Pre-deployment validation passed${NC}"
echo ""

# Step 2: Deploy to staging
echo -e "${BLUE}🔧 STEP 2: DEPLOYING TO STAGING${NC}"
echo "--------------------------------------------------------------------------------"
python3 deployment/scripts/deploy_staging.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Staging deployment failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Staging deployment successful${NC}"
echo ""

# Step 3: Run smoke tests on staging
echo -e "${BLUE}🧪 STEP 3: RUNNING SMOKE TESTS ON STAGING${NC}"
echo "--------------------------------------------------------------------------------"
python3 deployment/agents/smoke_test_runner.py http://localhost:8001
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Smoke tests failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Smoke tests passed${NC}"
echo ""

# Step 4: Deploy to production (with confirmation)
echo -e "${BLUE}🎯 STEP 4: DEPLOYING TO PRODUCTION${NC}"
echo "--------------------------------------------------------------------------------"
echo -e "${YELLOW}⚠️  WARNING: This will deploy to PRODUCTION${NC}"
read -p "Continue with production deployment? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Production deployment cancelled"
    exit 0
fi

python3 deployment/scripts/deploy_production.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Production deployment failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Production deployment successful${NC}"
echo ""

# Step 5: Monitor production deployment
echo -e "${BLUE}👀 STEP 5: MONITORING PRODUCTION DEPLOYMENT${NC}"
echo "--------------------------------------------------------------------------------"
echo "Monitoring for 5 minutes (300 seconds)..."
python3 deployment/agents/deployment_monitor.py http://localhost:8000 300
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Production monitoring detected issues${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Production monitoring passed${NC}"
echo ""

# Deployment complete
echo "================================================================================"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "================================================================================"
echo ""
echo "Environment URLs:"
echo "  Staging:    http://localhost:8001"
echo "  Production: http://localhost:8000"
echo ""
echo "Health Checks:"
echo "  Staging:    http://localhost:8001/api/v1/health"
echo "  Production: http://localhost:8000/api/v1/health"
echo ""
echo "Documentation:"
echo "  Staging:    http://localhost:8001/docs"
echo "  Production: http://localhost:8000/docs"
echo ""
echo "Deployment complete at: $(date)"
echo ""
