#!/bin/bash

# Kill any existing server processes
pkill -f server.py

# Clear the terminal
clear

# Print header
echo "========================================"
echo "  STARTING MINERVA SERVER (SIMPLIFIED)  "
echo "========================================"

# Set API keys directly
export OPENAI_API_KEY="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"
export ANTHROPIC_API_KEY="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"
export MISTRAL_API_KEY="FtHMcuPu4HsbKHUk4mJUIFfG1g20xF42"
export HUGGINGFACE_API_KEY="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"
export FLASK_SECRET_KEY="minerva-secure-key-$(date +%s)"

# Activate the virtual environment
source ./venv_minerva/bin/activate

# Ensure data directories exist
mkdir -p data/chat_history data/web_research_cache logs

# Run the server directly (not in background)
echo "Starting server on http://localhost:5505/portal"
echo "Press Ctrl+C to stop the server"
echo ""

# Execute Python directly without nohup or background
python server.py 