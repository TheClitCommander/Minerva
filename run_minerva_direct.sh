#!/bin/bash

# Minerva Direct Server - Reliable Chat Server
# This script runs a direct, self-contained Minerva server that:
# - Ignores SIGTERM signals
# - Handles all Socket.IO client versions 
# - Provides simulated responses when API keys aren't available

echo "====================================="
echo "   MINERVA DIRECT SERVER LAUNCHER    "
echo "====================================="

# Kill any existing processes (safely)
echo "Stopping any existing server processes..."
pkill -f "python.*server.py" 2>/dev/null || true
sleep 1

# Clear Python cache
echo "Cleaning Python cache..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Make sure server script is executable
chmod +x minerva_direct_server.py

# Prevent Python from creating new bytecode
export PYTHONDONTWRITEBYTECODE=1

# Make Python output unbuffered for real-time logs
export PYTHONUNBUFFERED=1

# Set dummy API keys if not already set
if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY="sk-dummy-key-123456789"
    echo "⚠️ Using dummy OpenAI API key (simulation mode)"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    export ANTHROPIC_API_KEY="sk-ant-dummy-key-123456789" 
    echo "⚠️ Using dummy Anthropic API key (simulation mode)"
fi

if [ -z "$MISTRAL_API_KEY" ]; then
    export MISTRAL_API_KEY="dummy-key-123456789"
    echo "⚠️ Using dummy Mistral API key (simulation mode)"
fi

echo "====================================="
echo "Starting Minerva Direct Server..."
echo "This server CANNOT be killed by SIGTERM"
echo "Access the portal at: http://localhost:5505/portal"
echo "====================================="

# RUN THE SERVER directly - it now handles its own signal processing
# No need for nohup or background process
python3 minerva_direct_server.py 