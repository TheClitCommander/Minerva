#!/bin/bash

# Simple script to start the Minerva Think Tank server
# with all API keys configured

# Kill any existing server
pkill -f server.py || true
sleep 1

# Set API keys
export OPENAI_API_KEY="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"
export ANTHROPIC_API_KEY="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"
export MISTRAL_API_KEY="FtHMcuPu4HsbKHUk4mJUIFfG1g20xF42"
export HUGGINGFACE_API_KEY="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"
export COHERE_API_KEY="7WjdzEYrvdWQNP40s30WX69znXVgiuHrD7spOwB4"
export GEMINI_API_KEY="AIzaSyCWP63Cmx_inlEwlAC0-zpxkYCjYo3wA5k"
export FLASK_SECRET_KEY="minerva-think-tank-$(date +%s)"

# Create data directories
mkdir -p data/chat_history data/web_research_cache logs

# Activate virtual environment
source ./venv_minerva/bin/activate

# Start server
echo "Starting Minerva Think Tank server with all AI models..."
echo "Access at: http://localhost:5505/portal"

python server.py
