#!/bin/bash

# ===================================================
# Minerva Think Tank - Server Startup Script
# ===================================================

# Add color to the output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Minerva Think Tank Server Startup  ${NC}"
echo -e "${GREEN}======================================${NC}"

# Kill any existing Minerva processes
pkill -f server.py || true
sleep 1

# Set up API keys
echo -e "${BLUE}Setting up AI model API keys...${NC}"

# Primary API keys
export OPENAI_API_KEY="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"
export ANTHROPIC_API_KEY="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"
export MISTRAL_API_KEY="FtHMcuPu4HsbKHUk4mJUIFfG1g20xF42"
export HUGGINGFACE_API_KEY="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"
export COHERE_API_KEY="7WjdzEYrvdWQNP40s30WX69znXVgiuHrD7spOwB4"
export GEMINI_API_KEY="AIzaSyCWP63Cmx_inlEwlAC0-zpxkYCjYo3wA5k"

# Set Flask environment
export FLASK_APP=server.py
export FLASK_ENV=development
export FLASK_SECRET_KEY="minerva-think-tank-$(date +%s)"

# Ensure data directories exist
mkdir -p data/chat_history data/web_research_cache logs

# Activate virtual environment
echo -e "${BLUE}Activating Python virtual environment...${NC}"
source ./venv_minerva/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Run a quick pre-check
echo -e "${BLUE}Running pre-flight check...${NC}"
python -c '
import sys
sys.path.append(".")
try:
    from web.multi_ai_coordinator import coordinator
    print("✅ Coordinator loaded with %d models: %s" % (
        len(coordinator.available_models),
        ", ".join(coordinator.available_models.keys())
    ))
except Exception as e:
    print("❌ Error loading coordinator: %s" % str(e))
    sys.exit(1)
'

# Check if preflight was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Pre-flight check failed. Not starting server.${NC}"
    exit 1
fi

echo -e "${GREEN}All systems go! Starting server...${NC}"
echo -e "${YELLOW}Access at: http://localhost:5505/portal${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Start the server
python server.py 