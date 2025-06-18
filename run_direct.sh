#!/bin/bash

# Kill existing servers
pkill -f "python.*server.py" 2>/dev/null || true
pkill -f "python.*chat_directly.py" 2>/dev/null || true

# Make sure our script is executable
chmod +x chat_directly.py

# Enable unbuffered Python output
export PYTHONUNBUFFERED=1

echo "Starting direct chat server..."
echo "Connect to http://localhost:5505/portal in your browser"
echo "This server BLOCKS all SIGTERM signals so it won't randomly terminate"
echo "============================================================="

# Run our standalone server
python3 chat_directly.py 