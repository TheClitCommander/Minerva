#!/bin/bash

# Test script for Minerva server with debugging output
echo "========================================"
echo "Testing Minerva Server"
echo "========================================"

# Activate virtual environment
source ./venv_minerva/bin/activate

# Set environmental variables
export FLASK_DEBUG=true
export PYTHONUNBUFFERED=1

# Export dummy API keys for testing
export OPENAI_API_KEY="sk-dummy-key-for-testing-only"
export ANTHROPIC_API_KEY="sk-ant-dummy-key-for-testing-only"
export MISTRAL_API_KEY="dummy-key-for-testing-only"
export HUGGINGFACE_API_KEY="hf-dummy-key-for-testing-only"

# Run the server in debug mode
echo "Starting server in debug mode..."
python server.py 