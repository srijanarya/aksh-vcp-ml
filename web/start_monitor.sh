#!/bin/bash

# Backtest Monitoring Dashboard Startup Script
# Starts the Flask API server and opens the dashboard

echo "🚀 Starting Backtest Monitoring Dashboard..."
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if log file exists
if [ ! -f "/tmp/smallcap_backtest.log" ]; then
    echo "⚠️  Warning: /tmp/smallcap_backtest.log not found"
    echo "   Make sure a backtest is running or has completed"
    echo ""
fi

# Check if Flask is already running on port 5001
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo "✓ API server already running on port 5001"
else
    echo "Starting API server..."
    cd "$SCRIPT_DIR/api"
    python3 backtest_progress.py > /dev/null 2>&1 &
    API_PID=$!
    echo "✓ API server started (PID: $API_PID)"

    # Wait for server to start
    sleep 2
fi

echo ""
echo "Dashboard URLs:"
echo "  - http://localhost:5001/backtest_monitor.html"
echo "  - http://127.0.0.1:5001/backtest_monitor.html"
echo ""
echo "API Endpoints:"
echo "  - http://localhost:5001/api/backtest/progress"
echo "  - http://localhost:5001/health"
echo ""

# Try to open in browser (macOS)
if command -v open &> /dev/null; then
    echo "Opening dashboard in browser..."
    open "file://$SCRIPT_DIR/backtest_monitor.html"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "file://$SCRIPT_DIR/backtest_monitor.html"
else
    echo "Please open the dashboard manually in your browser"
fi

echo ""
echo "To stop the API server:"
echo "  pkill -f backtest_progress"
echo ""
echo "Press Ctrl+C to exit (API will continue running in background)"
