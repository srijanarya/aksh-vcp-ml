#!/bin/bash
# Service management script for Announcement Intelligence System

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$SCRIPT_DIR/announcement_service.pid"
LOG_FILE="$SCRIPT_DIR/announcement_intelligence.log"
PYTHON_SCRIPT="$SCRIPT_DIR/run_announcement_intelligence.py"

case "$1" in
    start)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "❌ Service is already running (PID: $PID)"
                exit 1
            else
                echo "⚠️  Removing stale PID file"
                rm "$PID_FILE"
            fi
        fi
        
        echo "🚀 Starting Announcement Intelligence Service..."
        nohup python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "✅ Service started (PID: $(cat $PID_FILE))"
        echo "📝 Logs: tail -f $LOG_FILE"
        ;;
    
    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "❌ Service is not running (no PID file)"
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "🛑 Stopping Announcement Intelligence Service (PID: $PID)..."
            kill $PID
            rm "$PID_FILE"
            echo "✅ Service stopped"
        else
            echo "❌ Process not found (PID: $PID)"
            rm "$PID_FILE"
        fi
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "✅ Service is running (PID: $PID)"
                echo "📊 Recent activity:"
                tail -n 5 "$LOG_FILE"
            else
                echo "❌ Service is not running (stale PID file)"
            fi
        else
            echo "❌ Service is not running"
        fi
        ;;
    
    logs)
        tail -f "$LOG_FILE"
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
