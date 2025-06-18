#!/bin/bash

# ===================================================
# Minerva Think Tank - Full AI Model Setup
# ===================================================
# This script sets up all available AI models 
# in the Minerva Think Tank with real API keys

# Add color to the output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Starting Minerva Think Tank Server  ${NC}"
echo -e "${GREEN}======================================${NC}"

# Kill any existing Minerva processes first
pkill -f server.py || true
sleep 1

# Set up data directories
mkdir -p data/chat_history data/web_research_cache logs

# Create a log file
LOG_FILE="logs/think_tank_$(date +%Y%m%d_%H%M%S).log"
ln -sf "$LOG_FILE" logs/latest.log

# Set the real API keys for all services
echo -e "${BLUE}Setting up AI model API keys...${NC}"

# Primary API keys
export OPENAI_API_KEY="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"
export ANTHROPIC_API_KEY="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"
export MISTRAL_API_KEY="FtHMcuPu4HsbKHUk4mJUIFfG1g20xF42"

# Additional API keys
export HUGGINGFACE_API_KEY="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"
export COHERE_API_KEY="7WjdzEYrvdWQNP40s30WX69znXVgiuHrD7spOwB4"
export GEMINI_API_KEY="AIzaSyCWP63Cmx_inlEwlAC0-zpxkYCjYo3wA5k"

# Alternative/backup OpenAI key (comment out if causing issues)
# export OPENAI_API_KEY="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"

# Alternative/backup Cohere key
export COHERE_TRIAL_KEY="XDy2GA3TRNp1HMEpH4laK3wc8qRxu0s2ghRlrJoD"

# Set Flask environment
export FLASK_APP=server.py
export FLASK_ENV=development

# Create Flask secret key if it doesn't exist
if [ -z "$FLASK_SECRET_KEY" ]; then
    export FLASK_SECRET_KEY="minerva-think-tank-$(date +%s)"
fi

# Activate the virtual environment
echo -e "${BLUE}Activating Python virtual environment...${NC}"
if [ -d "./venv_minerva" ]; then
    source ./venv_minerva/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Please run setup_minerva.sh first to create the virtual environment"
    exit 1
fi

# Preload coordinator to ensure it's initialized correctly
echo -e "${BLUE}Pre-initializing AI coordinator...${NC}"
python -c "
import sys
sys.path.append('.')
try:
    from web.multi_ai_coordinator import coordinator
    print('✅ Successfully pre-loaded coordinator with %d models' % len(coordinator.available_models))
    if len(coordinator.available_models) < 2:
        print('⚠️  Only %d models available - check API keys' % len(coordinator.available_models))
    else:
        print('Available models: %s' % ', '.join(coordinator.available_models.keys()))
except Exception as e:
    print('❌ Error pre-loading coordinator: %s' % str(e))
"

# Run the server
echo -e "${BLUE}Starting Minerva server...${NC}"
echo -e "${YELLOW}Log file: ${LOG_FILE}${NC}"
python server.py | tee -a "$LOG_FILE"

# If you want to run it in the background, use this instead:
# nohup python server.py > "$LOG_FILE" 2>&1 &
# echo -e "${GREEN}✅ Minerva Think Tank running in background${NC}"
# echo -e "${YELLOW}View logs with: tail -f ${LOG_FILE}${NC}"
# echo -e "${GREEN}Access at: http://localhost:5505/portal${NC}" 