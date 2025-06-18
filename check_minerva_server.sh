#!/bin/bash

# Change to the script directory
cd "$(dirname "$0")"

# Check if PID file exists
if [ -f .minerva_server.pid ]; then
    PID=$(cat .minerva_server.pid)
    if ps -p $PID > /dev/null; then
        echo "✅ Minerva server is running with PID: $PID"
        
        # Get uptime of the process
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            START_TIME=$(ps -p $PID -o lstart= 2>/dev/null)
            if [ ! -z "$START_TIME" ]; then
                echo "   Started: $START_TIME"
                
                # Calculate rough uptime
                START_SECONDS=$(date -j -f "%a %b %d %T %Y" "$(echo $START_TIME)" +%s 2>/dev/null)
                NOW_SECONDS=$(date +%s)
                UPTIME_SECONDS=$((NOW_SECONDS - START_SECONDS))
                
                DAYS=$((UPTIME_SECONDS / 86400))
                HOURS=$(( (UPTIME_SECONDS % 86400) / 3600 ))
                MINUTES=$(( (UPTIME_SECONDS % 3600) / 60 ))
                SECONDS=$((UPTIME_SECONDS % 60))
                
                echo "   Uptime: ${DAYS}d ${HOURS}h ${MINUTES}m ${SECONDS}s"
            fi
        else
            # Linux
            START_TIME=$(ps -p $PID -o lstart= 2>/dev/null)
            echo "   Started: $START_TIME"
        fi
        
        # Show latest log file if available
        if [ -f logs/latest.log ]; then
            echo "   Log file: $(pwd)/logs/latest.log"
            echo ""
            echo "Last 5 log entries:"
            tail -n 5 logs/latest.log
        fi
        
        echo ""
        echo "Access the Minerva Portal at: http://localhost:5505/portal"
        echo "To monitor logs: tail -f logs/latest.log"
        echo "To stop the server: pkill -f server.py"
    else
        echo "❌ Minerva server is not running, but PID file exists."
        echo "   PID file contains: $PID"
        echo "   The server might have crashed or been terminated."
        echo "   Run './run_minerva_persistent.sh' to restart it."
        
        # Check if the log file exists
        if [ -f logs/latest.log ]; then
            echo ""
            echo "Last 10 log entries before termination:"
            tail -n 10 logs/latest.log
        fi
    fi
else
    echo "❌ Minerva server is not running (no PID file found)."
    echo "   Run './run_minerva_persistent.sh' to start it."
    
    # Check if there are any Python processes running server.py
    SERVER_PIDS=$(pgrep -f "python.*server.py")
    if [ ! -z "$SERVER_PIDS" ]; then
        echo ""
        echo "⚠️  Warning: Found server.py processes without PID file:"
        echo "$SERVER_PIDS"
        echo "   You may want to clean these up with: pkill -f server.py"
    fi
fi 