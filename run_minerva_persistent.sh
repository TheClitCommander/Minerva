#!/bin/bash

# Ensure the script works in the correct directory
cd "$(dirname "$0")"

# Create log directory if it doesn't exist
mkdir -p logs

# Kill any existing Minerva server instances
echo "Stopping any existing Minerva server processes..."
pkill -f server.py || true
sleep 2  # Give the old process time to fully terminate

# Install all dependencies first
echo "Checking dependencies..."
./start_minerva_portal.sh setup

# Add Socket.IO debug logging env var if needed
export SOCKETIO_DEBUG=1

# Start the server in the background using nohup with the current date in the log filename
LOG_FILE="logs/minerva_server_$(date +%Y%m%d_%H%M%S).log"
echo "Starting Minerva server in persistent mode..."
echo "The server will continue to run even if you close this terminal."
echo "To stop the server, run: pkill -f server.py"
echo "---------------------------------------"
echo "Access the Minerva Portal at:"
echo "http://localhost:5505/portal"
echo "---------------------------------------"

# Use a symlink for the latest log for easy access
ln -sf "$LOG_FILE" logs/latest.log

# Run with nohup to keep it running after terminal closes
# Binding explicitly to 0.0.0.0 makes it accessible on all interfaces
nohup python server.py --host 0.0.0.0 > "$LOG_FILE" 2>&1 &
PID=$!

# Save PID to file for easier management
echo $PID > .minerva_server.pid

# Print the process ID for reference
echo "Server started with PID: $PID"
echo "Log file: $LOG_FILE"
echo "Monitor logs with: tail -f $LOG_FILE"
echo "Waiting for server to initialize (5 seconds)..."

# Short pause to give server time to start and detect any immediate errors
sleep 5

# Check if process is still running after the sleep
if ps -p $PID > /dev/null; then
    echo "✅ Server started successfully and is running."
    echo "Logs are being written to: $LOG_FILE"
    echo "To monitor logs: tail -f $LOG_FILE"
else
    echo "❌ ERROR: Server failed to start or exited immediately."
    echo "Check the log file for details: $LOG_FILE"
    cat "$LOG_FILE"
    exit 1
fi 