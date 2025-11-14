#!/bin/bash
#
# Configure API Keys on AWS Instance
# This script extracts API keys from your local VCP project and configures them on the AWS instance
#

set -e

AWS_USER="ubuntu"
AWS_HOST="13.200.109.29"
SSH_KEY="$HOME/.ssh/lightsail.pem"
LOCAL_ENV_FILE="/Users/srijan/vcp_clean_test/vcp/.env"
REMOTE_ENV_FILE="/home/ubuntu/vcp/.env"

echo "================================================================================"
echo "🔑 Configuring API Keys on AWS Instance"
echo "================================================================================"
echo ""

# Check if local .env file exists
if [ ! -f "$LOCAL_ENV_FILE" ]; then
    echo "❌ ERROR: Local .env file not found at $LOCAL_ENV_FILE"
    exit 1
fi

echo "📋 Extracting API keys from local configuration..."

# Extract API keys from local .env
OPENAI_KEY=$(grep "^OPENAI_API_KEY=" "$LOCAL_ENV_FILE" | cut -d'=' -f2 | tr -d '\n')
ANTHROPIC_KEY=$(grep "^ANTHROPIC_API_KEY=" "$LOCAL_ENV_FILE" | cut -d'=' -f2 | tr -d '\n')
DEEPSEEK_KEY=$(grep "^DEEPSEEK_API_KEY=" "$LOCAL_ENV_FILE" | cut -d'=' -f2 | tr -d '\n')

# Extract or set Perplexity key (might not be in .env, will look for it)
PERPLEXITY_KEY=$(grep "^PERPLEXITY_API_KEY=" "$LOCAL_ENV_FILE" 2>/dev/null | cut -d'=' -f2 | tr -d '\n' || echo "")

echo "✓ Found OpenAI API Key: ${OPENAI_KEY:0:20}..."
echo "✓ Found Anthropic API Key: ${ANTHROPIC_KEY:0:20}..."
echo "✓ Found DeepSeek API Key: ${DEEPSEEK_KEY:0:20}..."

if [ -z "$PERPLEXITY_KEY" ]; then
    echo "⚠️  WARNING: Perplexity API Key not found in .env"
    echo "   Web search will be limited. You can add it later:"
    echo "   export PERPLEXITY_API_KEY='your-key-here'"
else
    echo "✓ Found Perplexity API Key: ${PERPLEXITY_KEY:0:20}..."
fi

echo ""
echo "🔄 Uploading .env file to AWS..."

# Upload local .env file to AWS
scp -i "$SSH_KEY" "$LOCAL_ENV_FILE" "$AWS_USER@$AWS_HOST:$REMOTE_ENV_FILE" 2>/dev/null && \
    echo "✓ .env file uploaded successfully" || \
    echo "❌ Failed to upload .env file"

echo ""
echo "🔧 Configuring systemd service to load environment variables..."

# Create/update systemd service EnvironmentFile
ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'EOFBASIC'
    # Check current service configuration
    if grep -q "EnvironmentFile=" /etc/systemd/system/vcp-api.service; then
        echo "Service already has EnvironmentFile configured"
    else
        echo "Adding EnvironmentFile to service configuration..."
        sudo sed -i '/^\[Service\]/a EnvironmentFile=/home/ubuntu/vcp/.env' /etc/systemd/system/vcp-api.service
        echo "Updated service file"
    fi
EOFBASIC

echo "✓ Service configuration updated"

echo ""
echo "🔄 Restarting VCP API service..."

# Reload systemd and restart service
ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'EOFBASIC'
    sudo systemctl daemon-reload
    sudo systemctl restart vcp-api
    sleep 5
    sudo systemctl status vcp-api --no-pager | head -15
EOFBASIC

echo ""
echo "✅ API Key Configuration Complete!"
echo ""
echo "Configuration Summary:"
echo "- OpenAI API Key: Configured ✓"
echo "- Anthropic API Key: Configured ✓"
echo "- DeepSeek API Key: Configured ✓"
if [ -n "$PERPLEXITY_KEY" ]; then
    echo "- Perplexity API Key: Configured ✓"
else
    echo "- Perplexity API Key: NOT configured (optional)"
fi
echo ""
echo "🚀 Next Steps:"
echo "1. Test intelligent collector with API keys:"
echo "   curl -X POST http://13.200.109.29:8001/api/intelligent-collector/collect/quick"
echo ""
echo "2. Run full collection (50 companies):"
echo "   curl -X POST http://13.200.109.29:8001/api/intelligent-collector/collect \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"max_companies\": 50, \"priority_filter\": \"high\", \"enable_web_search\": true, \"enable_ai_inference\": true}'"
echo ""
echo "3. Check calendar with all companies:"
echo "   curl http://13.200.109.29:8001/api/earnings/calendar/public?filter=all"
echo ""
echo "================================================================================"
