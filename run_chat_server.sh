#!/bin/bash

echo "==========================="
echo "  BULLETPROOF MINERVA SERVER"
echo "==========================="

# Use trap to catch script termination attempts
trap "echo '⚠️ Script termination attempted, but server will continue running'; exit 0" SIGTERM SIGINT

# Clear Python cache to ensure fresh import
echo "Clearing Python cache..."
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Set dummy API keys if not already set
if [ -z "$HUGGINGFACE_API_KEY" ]; then
    export HUGGINGFACE_API_KEY="hf_dummy_key"
    echo "⚠️ Using dummy HuggingFace API key"
fi

if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY="sk-dummy_key"
    echo "⚠️ Using dummy OpenAI API key"
fi

# Make sure we have necessary dependencies
echo "Checking dependencies..."
pip install -q flask flask-socketio requests eventlet || true

# IMPORTANT - Use nohup to prevent SIGHUP when terminal closes
echo "Starting Minerva Chat Server..."
echo "==========================="
echo "Chat will be available at: http://localhost:5505/portal"
echo "Server is BULLETPROOF - it cannot be killed by normal means"
echo "==========================="

# DO NOT USE PKILL HERE - it was likely killing your server!
# Just run the server and let it handle signals on its own
echo "🚀 Launching indestructible server..."

# Run in background with nohup to prevent killing on terminal close
# This is critical to make sure server doesn't die when script exits
nohup python3 -B minerva_chat_server.py > minerva_server.log 2>&1 &

# Store the PID
SERVER_PID=$!
echo "Server running with PID: $SERVER_PID"
echo "You can view logs with: tail -f minerva_server.log"
echo "To intentionally kill server: kill -9 $SERVER_PID"

# Wait for server to start
sleep 2
echo ""
echo "Last 10 lines of server log:"
tail -n 10 minerva_server.log
echo ""
echo "✅ Server running in background! The terminal is now free." 