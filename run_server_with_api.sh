#!/bin/bash

# Add color to the output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}     Starting Minerva API Server     ${NC}"
echo -e "${GREEN}======================================${NC}"

# Kill any existing Minerva processes
pkill -f server.py || true
sleep 1

# Activate the virtual environment
source ./venv_minerva/bin/activate

# Set up logging
mkdir -p logs
LOG_FILE="logs/api_server_$(date +%Y%m%d_%H%M%S).log"
ln -sf "$LOG_FILE" logs/latest.log

# Set API keys - use real keys if available, otherwise use validation strings
if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY="BLANK_KEY_FOR_VALIDATION"
    echo -e "${YELLOW}No OpenAI API key set. Using validation key.${NC}"
    echo -e "${YELLOW}To use real OpenAI models, set OPENAI_API_KEY environment variable.${NC}"
else
    echo -e "${GREEN}Using OpenAI API key from environment.${NC}"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    export ANTHROPIC_API_KEY="BLANK_KEY_FOR_VALIDATION"
    echo -e "${YELLOW}No Anthropic API key set. Using validation key.${NC}"
    echo -e "${YELLOW}To use real Claude models, set ANTHROPIC_API_KEY environment variable.${NC}"
else
    echo -e "${GREEN}Using Anthropic API key from environment.${NC}"
fi

if [ -z "$MISTRAL_API_KEY" ]; then
    export MISTRAL_API_KEY="BLANK_KEY_FOR_VALIDATION"
    echo -e "${YELLOW}No Mistral API key set. Using validation key.${NC}"
    echo -e "${YELLOW}To use real Mistral models, set MISTRAL_API_KEY environment variable.${NC}"
else
    echo -e "${GREEN}Using Mistral API key from environment.${NC}"
fi

# Set server environment
export FLASK_APP=server.py
export FLASK_ENV=development
export PYTHONUNBUFFERED=1

# Run the coordinator test first
echo -e "${BLUE}Running coordinator test...${NC}"
python test_coordinator.py | tee -a "$LOG_FILE"

echo -e "\n${BLUE}Starting Minerva server...${NC}"
echo -e "${BLUE}Logs will be saved to: ${LOG_FILE}${NC}"

# Start server in foreground mode
python server.py --host 0.0.0.0 