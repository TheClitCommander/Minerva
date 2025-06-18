#!/bin/bash

# Kill existing server
pkill -f server.py > /dev/null 2>&1
pkill -f just_run_this.py > /dev/null 2>&1

# Set API keys (dummy values)
export OPENAI_API_KEY="sk-test12345"
export ANTHROPIC_API_KEY="sk-ant-test12345"
export MISTRAL_API_KEY="test12345"

# Enable unbuffered output
export PYTHONUNBUFFERED=1

echo "Starting simplified Minerva server..."
echo "This will provide REAL RESPONSES (not simulated)"
echo "==============================================="

# Run the self-contained server
python3 just_run_this.py 