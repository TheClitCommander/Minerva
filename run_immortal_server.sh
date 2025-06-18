#!/bin/bash

# Immortal Minerva Server launcher
# This script launches a server that CANNOT be killed by normal means

echo "==============================================="
echo "  IMMORTAL MINERVA SERVER LAUNCHER"
echo "==============================================="

# Clear Python cache to ensure fresh imports
echo "Clearing Python cache..."
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Make sure the script is executable
chmod +x forever_server.py

# Set dummy API keys if not already set
if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY="sk-dummy-key-1234567890"
    echo "✓ Using dummy OpenAI API key"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    export ANTHROPIC_API_KEY="sk-ant-dummy-key-1234567890"
    echo "✓ Using dummy Anthropic API key"
fi

if [ -z "$MISTRAL_API_KEY" ]; then
    export MISTRAL_API_KEY="dummy-key-1234567890"
    echo "✓ Using dummy Mistral API key"
fi

# Enable unbuffered Python output
export PYTHONUNBUFFERED=1

# Disable Python bytecode caching
export PYTHONDONTWRITEBYTECODE=1

# Important: Trap attempts to terminate this script
trap "echo '⚠️ Termination attempt detected, but server will continue running in background'" SIGINT SIGTERM

echo "Starting immortal Minerva server..."
echo "This server CANNOT be terminated by normal means"
echo "To ACTUALLY stop it, you must use: kill -9 <PID>"
echo "==============================================="

# The critical step: We run the server with nohup so it keeps running after terminal closes
# We redirect output to both a log file AND stdout with tee
nohup python3 forever_server.py > >(tee minerva_forever.log) 2>&1 &

# Get the PID of the background process
SERVER_PID=$!
echo "Server running with PID: $SERVER_PID"
echo "You can view logs with: tail -f minerva_forever.log"
echo "To ACTUALLY stop the server: kill -9 $SERVER_PID"

# Sleep to let it start
sleep 2
echo ""
echo "Last 10 lines of server log:"
tail -n 10 minerva_forever.log

echo ""
echo "✅ Server running in background"
echo "✅ Visit http://localhost:5505/portal"
echo ""
echo "This terminal is now free. The server will continue running forever." 