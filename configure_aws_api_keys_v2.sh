#!/bin/bash
#
# Configure API Keys on AWS Instance - Enhanced Version
# This script extracts API keys from your local project and configures them on the AWS instance
#
# Features:
# - Dynamic .env file detection
# - Comprehensive error handling
# - Backup of existing configuration
# - Security improvements
# - Better validation
#

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# AWS Configuration
AWS_USER="ubuntu"
AWS_HOST="13.200.109.29"
SSH_KEY="$HOME/.ssh/lightsail.pem"
REMOTE_ENV_FILE="/home/ubuntu/vcp/.env"
REMOTE_BACKUP_DIR="/home/ubuntu/vcp/backups"

# Function to print colored output
print_status() {
    echo -e "${2}${1}${NC}"
}

# Function to find .env file
find_env_file() {
    # Check multiple possible locations
    local possible_paths=(
        "$PWD/.env"
        "$PWD/../vcp/.env"
        "/Users/srijan/Desktop/aksh/.env"
        "/Users/srijan/vcp/.env"
        "/Users/srijan/vcp_clean_test/vcp/.env"
        "$HOME/vcp/.env"
    )

    for path in "${possible_paths[@]}"; do
        if [ -f "$path" ]; then
            echo "$path"
            return 0
        fi
    done

    return 1
}

# Function to validate SSH connectivity
validate_ssh() {
    if [ ! -f "$SSH_KEY" ]; then
        print_status "❌ SSH key not found at $SSH_KEY" "$RED"
        print_status "Please ensure your Lightsail key is at: $SSH_KEY" "$YELLOW"
        return 1
    fi

    print_status "Testing SSH connection..." "$BLUE"
    if ssh -o ConnectTimeout=5 -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" "echo 'Connection successful'" &>/dev/null; then
        print_status "✓ SSH connection successful" "$GREEN"
        return 0
    else
        print_status "❌ Cannot connect to AWS instance" "$RED"
        return 1
    fi
}

# Function to extract API key safely
extract_key() {
    local key_name="$1"
    local file="$2"
    local value=$(grep "^${key_name}=" "$file" 2>/dev/null | cut -d'=' -f2- | tr -d '\n' | tr -d '"' | tr -d "'" || echo "")
    echo "$value"
}

# Function to mask API key for display
mask_key() {
    local key="$1"
    if [ -z "$key" ]; then
        echo "NOT_FOUND"
    else
        echo "${key:0:10}...${key: -4}"
    fi
}

echo "================================================================================"
echo -e "${BLUE}🔑 Enhanced API Key Configuration for AWS Instance${NC}"
echo "================================================================================"
echo ""

# Step 1: Find .env file
print_status "📋 Searching for .env file..." "$BLUE"
LOCAL_ENV_FILE=$(find_env_file)

if [ $? -ne 0 ]; then
    print_status "❌ No .env file found in common locations" "$RED"
    print_status "Please specify the path to your .env file:" "$YELLOW"
    read -r custom_path
    if [ -f "$custom_path" ]; then
        LOCAL_ENV_FILE="$custom_path"
    else
        print_status "❌ File not found: $custom_path" "$RED"
        exit 1
    fi
fi

print_status "✓ Found .env file: $LOCAL_ENV_FILE" "$GREEN"

# Step 2: Validate SSH connection
if ! validate_ssh; then
    exit 1
fi

# Step 3: Extract API keys
print_status "\n📋 Extracting API keys from local configuration..." "$BLUE"

OPENAI_KEY=$(extract_key "OPENAI_API_KEY" "$LOCAL_ENV_FILE")
ANTHROPIC_KEY=$(extract_key "ANTHROPIC_API_KEY" "$LOCAL_ENV_FILE")
DEEPSEEK_KEY=$(extract_key "DEEPSEEK_API_KEY" "$LOCAL_ENV_FILE")
PERPLEXITY_KEY=$(extract_key "PERPLEXITY_API_KEY" "$LOCAL_ENV_FILE")

# Additional keys that might be needed
ANGEL_API_KEY=$(extract_key "ANGEL_API_KEY" "$LOCAL_ENV_FILE")
ANGEL_SECRET=$(extract_key "ANGEL_SECRET" "$LOCAL_ENV_FILE")
TELEGRAM_BOT_TOKEN=$(extract_key "TELEGRAM_BOT_TOKEN" "$LOCAL_ENV_FILE")

# Display found keys (masked)
echo ""
print_status "Found API Keys:" "$BLUE"
print_status "  OpenAI:     $(mask_key "$OPENAI_KEY")" "$GREEN"
print_status "  Anthropic:  $(mask_key "$ANTHROPIC_KEY")" "$GREEN"
print_status "  DeepSeek:   $(mask_key "$DEEPSEEK_KEY")" "$GREEN"
print_status "  Perplexity: $(mask_key "$PERPLEXITY_KEY")" "$YELLOW"
print_status "  Angel API:  $(mask_key "$ANGEL_API_KEY")" "$YELLOW"
print_status "  Telegram:   $(mask_key "$TELEGRAM_BOT_TOKEN")" "$YELLOW"

# Step 4: Create backup on remote
print_status "\n🔄 Creating backup of existing configuration..." "$BLUE"

ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'EOFBACKUP'
    # Create backup directory if it doesn't exist
    mkdir -p /home/ubuntu/vcp/backups

    # Backup existing .env if it exists
    if [ -f /home/ubuntu/vcp/.env ]; then
        BACKUP_FILE="/home/ubuntu/vcp/backups/.env.$(date +%Y%m%d_%H%M%S)"
        cp /home/ubuntu/vcp/.env "$BACKUP_FILE"
        echo "Backup created: $BACKUP_FILE"
    else
        echo "No existing .env file to backup"
    fi
EOFBACKUP

# Step 5: Upload new configuration
print_status "\n🔄 Uploading .env file to AWS..." "$BLUE"

if scp -i "$SSH_KEY" "$LOCAL_ENV_FILE" "$AWS_USER@$AWS_HOST:$REMOTE_ENV_FILE" 2>/dev/null; then
    print_status "✓ .env file uploaded successfully" "$GREEN"
else
    print_status "❌ Failed to upload .env file" "$RED"
    exit 1
fi

# Step 6: Set proper permissions
print_status "\n🔒 Setting secure permissions on .env file..." "$BLUE"

ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'EOFPERMS'
    # Set restrictive permissions
    chmod 600 /home/ubuntu/vcp/.env

    # Ensure ubuntu user owns the file
    chown ubuntu:ubuntu /home/ubuntu/vcp/.env

    echo "Permissions set: 600 (read/write for owner only)"
EOFPERMS

# Step 7: Configure systemd service
print_status "\n🔧 Configuring systemd services..." "$BLUE"

ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'EOFSERVICE'
    # Function to update service file
    update_service() {
        local service_name=$1
        local service_file="/etc/systemd/system/${service_name}.service"

        if [ -f "$service_file" ]; then
            if ! grep -q "EnvironmentFile=" "$service_file"; then
                echo "Adding EnvironmentFile to $service_name..."
                sudo sed -i '/^\[Service\]/a EnvironmentFile=/home/ubuntu/vcp/.env' "$service_file"
            else
                echo "$service_name already has EnvironmentFile configured"
            fi
        else
            echo "Service $service_name not found, skipping..."
        fi
    }

    # Update multiple services if they exist
    update_service "vcp-api"
    update_service "vcp-ml-api"

    # Reload systemd
    sudo systemctl daemon-reload
EOFSERVICE

# Step 8: Restart services
print_status "\n🔄 Restarting services..." "$BLUE"

ssh -i "$SSH_KEY" "$AWS_USER@$AWS_HOST" << 'EOFRESTART'
    # Function to restart service if it exists
    restart_service() {
        local service_name=$1

        if systemctl list-units --all | grep -q "$service_name.service"; then
            echo "Restarting $service_name..."
            sudo systemctl restart "$service_name"
            sleep 3

            if systemctl is-active --quiet "$service_name"; then
                echo "✓ $service_name is running"
                sudo systemctl status "$service_name" --no-pager | head -10
            else
                echo "⚠ $service_name failed to start"
                sudo journalctl -u "$service_name" -n 20 --no-pager
            fi
        else
            echo "$service_name not found, skipping..."
        fi
        echo ""
    }

    # Restart services
    restart_service "vcp-api"
    restart_service "vcp-ml-api"
EOFRESTART

# Step 9: Validate configuration
print_status "\n🧪 Validating API configuration..." "$BLUE"

# Test endpoints
print_status "Testing API endpoints..." "$BLUE"

# Test main API
if curl -s -o /dev/null -w "%{http_code}" "http://${AWS_HOST}:8001/health" | grep -q "200"; then
    print_status "✓ Main API (port 8001) is responding" "$GREEN"
else
    print_status "⚠ Main API (port 8001) is not responding" "$YELLOW"
fi

# Test ML API
if curl -s -o /dev/null -w "%{http_code}" "http://${AWS_HOST}:8002/health" | grep -q "200"; then
    print_status "✓ ML API (port 8002) is responding" "$GREEN"
else
    print_status "⚠ ML API (port 8002) is not responding" "$YELLOW"
fi

echo ""
echo "================================================================================"
print_status "✅ API Key Configuration Complete!" "$GREEN"
echo "================================================================================"
echo ""

# Summary
print_status "Configuration Summary:" "$BLUE"
echo "┌─────────────────────────────────────────────────┐"
echo "│ Service          │ Status                       │"
echo "├─────────────────────────────────────────────────┤"
printf "│ %-16s │ %-28s │\n" "OpenAI API" "$([ -n "$OPENAI_KEY" ] && echo "✓ Configured" || echo "❌ Missing")"
printf "│ %-16s │ %-28s │\n" "Anthropic API" "$([ -n "$ANTHROPIC_KEY" ] && echo "✓ Configured" || echo "❌ Missing")"
printf "│ %-16s │ %-28s │\n" "DeepSeek API" "$([ -n "$DEEPSEEK_KEY" ] && echo "✓ Configured" || echo "❌ Missing")"
printf "│ %-16s │ %-28s │\n" "Perplexity API" "$([ -n "$PERPLEXITY_KEY" ] && echo "✓ Configured" || echo "⚠ Optional")"
printf "│ %-16s │ %-28s │\n" "Angel One API" "$([ -n "$ANGEL_API_KEY" ] && echo "✓ Configured" || echo "⚠ Optional")"
printf "│ %-16s │ %-28s │\n" "Telegram Bot" "$([ -n "$TELEGRAM_BOT_TOKEN" ] && echo "✓ Configured" || echo "⚠ Optional")"
echo "└─────────────────────────────────────────────────┘"

echo ""
print_status "🚀 Test Commands:" "$BLUE"
echo ""
echo "1. Test Health Check:"
echo "   curl http://${AWS_HOST}:8001/health"
echo ""
echo "2. Test Intelligent Collector (Quick):"
echo "   curl -X POST http://${AWS_HOST}:8001/api/intelligent-collector/collect/quick"
echo ""
echo "3. Test Full Collection (50 companies):"
echo "   curl -X POST http://${AWS_HOST}:8001/api/intelligent-collector/collect \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"max_companies\": 50, \"priority_filter\": \"high\", \"enable_ai_inference\": true}'"
echo ""
echo "4. View Earnings Calendar:"
echo "   curl http://${AWS_HOST}:8001/api/earnings/calendar/public?filter=all"
echo ""
echo "5. Test ML Prediction API:"
echo "   curl http://${AWS_HOST}:8002/health"
echo ""

# Rollback instructions
print_status "🔄 Rollback Instructions (if needed):" "$YELLOW"
echo "   ssh -i $SSH_KEY $AWS_USER@$AWS_HOST"
echo "   cd /home/ubuntu/vcp/backups"
echo "   ls -la  # Find your backup file"
echo "   cp .env.TIMESTAMP /home/ubuntu/vcp/.env"
echo "   sudo systemctl restart vcp-api vcp-ml-api"
echo ""
echo "================================================================================"