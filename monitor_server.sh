#!/bin/bash

# Monitor script for detecting what's killing the Minerva server
echo "=============================="
echo "  MINERVA SERVER WATCHDOG"
echo "=============================="
echo "This script monitors for processes killing your server"
echo

# Find the PID of the server
SERVER_PID=$(pgrep -f "python3 -B minerva_chat_server.py" || echo "NOT_RUNNING")

if [ "$SERVER_PID" == "NOT_RUNNING" ]; then
    echo "⚠️ Server not running! Start it with ./run_chat_server.sh first."
    exit 1
fi

echo "✅ Found server running with PID: $SERVER_PID"
echo

# Set up a monitoring loop
echo "🔍 Starting server monitoring..."
echo "Press Ctrl+C to stop monitoring"
echo

# Function to get parent process name
get_parent_name() {
    ps -p $1 -o comm= 2>/dev/null || echo "unknown"
}

# Function to check port 5505
check_port() {
    lsof -i:5505 | grep LISTEN >/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Port 5505 is active"
    else
        echo "❌ Port 5505 is NOT active!"
    fi
}

# Start monitoring loop
while true; do
    echo "-----------------------------"
    echo "Timestamp: $(date)"
    
    # Check if server is still running
    if ps -p $SERVER_PID >/dev/null 2>&1; then
        echo "✅ Server process $SERVER_PID is running"
        
        # Get parent process info
        PPID=$(ps -o ppid= -p $SERVER_PID | tr -d ' ')
        PARENT_CMD=$(ps -p $PPID -o command= 2>/dev/null || echo "unknown")
        echo "   Parent: $PPID ($PARENT_CMD)"
        
        # Check port status
        check_port
        
        # Check for any processes that might be trying to kill Python
        KILLERS=$(ps aux | grep -v grep | grep -E "pkill|kill.*python|kill.*server" | awk '{print $2 " " $11 " " $12}')
        if [ -n "$KILLERS" ]; then
            echo "⚠️ Potential killer processes detected:"
            echo "$KILLERS"
        fi
    else
        echo "❌ SERVER PROCESS IS GONE!"
        echo "Last 10 lines of server log:"
        tail -n 10 minerva_server.log
        
        # Try to find what killed it in the logs
        echo "Checking system logs for what killed PID $SERVER_PID..."
        grep -a "kill.*$SERVER_PID" /var/log/system.log 2>/dev/null || echo "No direct kill evidence found in system logs"
        
        # Break the loop
        break
    fi
    
    sleep 5
done

echo
echo "🚨 Server monitoring terminated!"
echo "Check minerva_server.log for more details on what happened." 