#!/bin/bash
# Enhanced Script to set up and run Minerva with real AI models
# This script handles API key configuration, dependency installation, and server startup

set -e  # Exit on any error

# Color formatting for messages
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${BLUE}\n===============================================${NC}"
echo -e "${GREEN}🚀 MINERVA AI - REAL MODEL INTEGRATION LAUNCHER 🚀${NC}"
echo -e "${BLUE}===============================================${NC}"

# Create logs directory if it doesn't exist
mkdir -p logs

# Load API keys from .env file if it exists
if [ -f ".env" ]; then
    echo -e "${GREEN}Loading API keys from .env file...${NC}"
    source .env
fi

# Check if API keys are set, prompt if not
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️ OpenAI API key not found in environment${NC}"
    echo -e "${YELLOW}⚠️ GPT-4 will use simulated responses${NC}"
    # Uncomment to prompt for API key
    # read -p "Enter your OpenAI API key (or press enter to skip): " OPENAI_API_KEY
    # if [ ! -z "$OPENAI_API_KEY" ]; then
    #     export OPENAI_API_KEY
    #     echo -e "${GREEN}✅ OpenAI API key set${NC}"
    # fi
else
    echo -e "${GREEN}✅ OpenAI API key found in environment${NC}"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠️ Anthropic API key not found in environment${NC}"
    echo -e "${YELLOW}⚠️ Claude-3 will use simulated responses${NC}"
    # Uncomment to prompt for API key
    # read -p "Enter your Anthropic API key (or press enter to skip): " ANTHROPIC_API_KEY
    # if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    #     export ANTHROPIC_API_KEY
    #     echo -e "${GREEN}✅ Anthropic API key set${NC}"
    # fi
else
    echo -e "${GREEN}✅ Anthropic API key found in environment${NC}"
fi

# Use minerva_env if it exists, otherwise use venv
if [ -d "minerva_env" ]; then
    VENV_DIR="minerva_env"
else
    VENV_DIR="venv"
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${BLUE}Creating virtual environment...${NC}"
        python3 -m venv $VENV_DIR
    fi
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment from $VENV_DIR...${NC}"
source $VENV_DIR/bin/activate

# Install required packages
echo -e "${BLUE}Ensuring all required packages are installed...${NC}"
pip install -q flask==2.2.5 werkzeug==2.2.3 python-socketio==5.10.0 python-engineio==4.8.0 flask-socketio==5.3.6 openai==1.12.0 anthropic python-dotenv

# Check if we have the validation components needed for the enhanced logging system
DEPENDENCIES_OK=true
python -c "import web.validator" &>/dev/null || DEPENDENCIES_OK=false
python -c "import web.route_request" &>/dev/null || DEPENDENCIES_OK=false

if [ "$DEPENDENCIES_OK" = false ]; then
    echo -e "${YELLOW}⚠️ Some Minerva dependencies couldn't be imported${NC}"
    echo -e "${YELLOW}⚠️ The system may fall back to simpler processing${NC}"
fi

# Run pre-flight checks for the coordinator
echo -e "${BLUE}Running pre-flight checks for AI models...${NC}"
python -c "from web.multi_ai_coordinator import MultiAICoordinator; print('✅ Coordinator imported successfully')" || (
    echo -e "${RED}❌ Failed to import MultiAICoordinator${NC}"
    echo -e "${RED}❌ Check your installation and try again${NC}"
    exit 1
)

# Run the enhanced WebSocket server
echo -e "${GREEN}\n🚀 Starting Minerva with real AI models...${NC}"
echo -e "${BLUE}Check logs/websocket_server.log for detailed logs${NC}"
python enhanced_standalone_websocket.py

# Deactivate virtual environment when done
deactivate
