#!/bin/bash

# Minimal Minerva Chat Server Runner
# This script runs a minimal version of the chat server without eventlet dependencies
# making it compatible with Python 3.13

echo -e "\n\033[1;36m=== Running Minimal Minerva Chat ===\033[0m\n"

# Kill any running server processes
pkill -f "python.*server.py" || true
sleep 1

# Ensure Python is available
if command -v python3 &>/dev/null; then
    PYTHON=python3
    echo "Using Python 3"
elif command -v python &>/dev/null; then
    PYTHON=python
    echo "Using Python"
else
    echo "Error: Python not found. Please install Python to run this server."
    exit 1
fi

# Create directories if they don't exist
mkdir -p web/static/js

# Set up environment (optional API keys)
export PYTHONUNBUFFERED=1
export OPENAI_API_KEY=${OPENAI_API_KEY:-"sk-dummy12345678901234567890"}
export ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-"sk-ant-dummy12345678901234567890"}
export MISTRAL_API_KEY=${MISTRAL_API_KEY:-"dummy12345678901234567890"}

# Run the server
echo -e "\n\033[1;32m=== Starting Minimal Chat Server ===\033[0m"
echo "Server will be available at: http://localhost:5505"
echo "Access the chat interface at: http://localhost:5505/chat"
echo "Press Ctrl+C to stop the server"
echo ""

$PYTHON minimal_chat_server.py

echo "Server stopped." 