#!/bin/bash

# Kill any existing Minerva processes first
pkill -f server.py || true
sleep 1

# Set the real API keys - REPLACE WITH YOUR ACTUAL KEYS
export OPENAI_API_KEY="your-openai-api-key-here"
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
export MISTRAL_API_KEY="your-mistral-api-key-here"

# Additional API keys (not currently used but available for future implementation)
export HUGGINGFACE_API_KEY="your-huggingface-api-key-here"
export COHERE_API_KEY="your-cohere-api-key-here"
export GEMINI_API_KEY="your-gemini-api-key-here"

# Set Flask environment
export FLASK_APP=server.py
export FLASK_ENV=development

# Activate the virtual environment
source ./venv_minerva/bin/activate

# Run the server
echo "Starting Minerva server with real API keys..."
python server.py

# If you want to run it in the background, use this instead:
# nohup python server.py > minerva_server.log 2>&1 & 