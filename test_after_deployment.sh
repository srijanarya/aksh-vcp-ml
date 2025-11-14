#!/bin/bash
#
# Comprehensive Test Script for Intelligent Earnings Collector
# Run this AFTER deploying to AWS to verify everything works
#
# Usage: ./test_after_deployment.sh

AWS_URL="http://13.200.109.29:8001"

echo "================================================================================"
echo "🧪 TESTING INTELLIGENT EARNINGS COLLECTOR ON AWS"
echo "================================================================================"
echo ""

# Test 1: Health Check
echo "📋 Test 1: Health Check"
echo "   Endpoint: GET /api/intelligent-collector/health"
echo "   Testing..."
HEALTH=$(curl -s "$AWS_URL/api/intelligent-collector/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✅ PASS: Service is healthy"
    echo "   Response: $HEALTH"
else
    echo "   ❌ FAIL: Service not responding or unhealthy"
    echo "   Response: $HEALTH"
fi
echo ""

# Test 2: Data Gaps
echo "📋 Test 2: Identify Data Gaps"
echo "   Endpoint: GET /api/intelligent-collector/gaps"
echo "   Testing..."
GAPS=$(curl -s "$AWS_URL/api/intelligent-collector/gaps")
if echo "$GAPS" | grep -q "total_gaps"; then
    echo "   ✅ PASS: Gaps endpoint working"
    TOTAL=$(echo "$GAPS" | grep -o '"total_gaps":[0-9]*' | grep -o '[0-9]*')
    echo "   Total companies missing data: $TOTAL"
else
    echo "   ❌ FAIL: Gaps endpoint not working"
    echo "   Response: $GAPS"
fi
echo ""

# Test 3: Calendar API (Phase 1 fix)
echo "📋 Test 3: Earnings Calendar (Phase 1 Fix)"
echo "   Endpoint: GET /api/earnings/calendar/public?filter=all"
echo "   Testing..."
CALENDAR=$(curl -s "$AWS_URL/api/earnings/calendar/public?filter=all")
if echo "$CALENDAR" | grep -q "total_available"; then
    echo "   ✅ PASS: Calendar endpoint working"
    TOTAL=$(echo "$CALENDAR" | grep -o '"total_available":[0-9]*' | grep -o '[0-9]*')
    WITH_DATES=$(echo "$CALENDAR" | grep -o '"with_dates":[0-9]*' | grep -o '[0-9]*')
    WITHOUT=$(echo "$CALENDAR" | grep -o '"without_dates":[0-9]*' | grep -o '[0-9]*')
    echo "   Total companies: $TOTAL"
    echo "   With earnings: $WITH_DATES"
    echo "   Without earnings: $WITHOUT"
else
    echo "   ❌ FAIL: Calendar endpoint not working"
    echo "   Response: $CALENDAR"
fi
echo ""

# Test 4: Quick Collection (if you want to run it)
echo "📋 Test 4: Quick Collection Test (Optional)"
echo "   Endpoint: POST /api/intelligent-collector/collect/quick"
echo "   This will process 10 companies - takes ~1-2 minutes"
read -p "   Run quick collection test? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Running quick collection..."
    QUICK=$(curl -s -X POST "$AWS_URL/api/intelligent-collector/collect/quick")
    if echo "$QUICK" | grep -q "success"; then
        echo "   ✅ PASS: Quick collection completed"
        echo "   Response: $QUICK"
    else
        echo "   ❌ FAIL: Quick collection failed"
        echo "   Response: $QUICK"
    fi
else
    echo "   ⏭️  SKIPPED: Quick collection test"
fi
echo ""

# Test 5: Swagger UI
echo "📋 Test 5: Swagger UI Documentation"
echo "   URL: $AWS_URL/docs"
echo "   Open this in your browser to see all endpoints"
echo ""

echo "================================================================================"
echo "✅ TESTING COMPLETE"
echo "================================================================================"
echo ""
echo "📊 Summary:"
echo "   - If all tests passed, the system is deployed successfully"
echo "   - If any failed, check the deployment guide"
echo ""
echo "📚 Next Steps:"
echo "   1. Open $AWS_URL/docs in browser"
echo "   2. Test endpoints interactively in Swagger UI"
echo "   3. Set up daily automation with cron"
echo ""
echo "================================================================================"
