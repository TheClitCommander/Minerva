#!/bin/bash

# Kill any existing server
pkill -f "python.*server.py" 2>/dev/null || true

# Clear the Python cache to ensure fresh imports
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Set API keys (not actually used by standalone server, but included for completeness)
export OPENAI_API_KEY="sk-dummy-key-12345"
export ANTHROPIC_API_KEY="sk-ant-dummy-key-12345"
export MISTRAL_API_KEY="dummy-key-12345"

# Make sure output is not buffered
export PYTHONUNBUFFERED=1

echo "Starting standalone Minerva server..."
echo "This server WILL provide real responses."
echo "================================================="

# Run our standalone server
python standalone_server.py 