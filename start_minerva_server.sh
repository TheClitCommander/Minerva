#!/bin/bash

# Minerva Server Startup Script with Robust Error Handling
# This script starts the Minerva server with extensive error checking
# and environment setup to ensure reliable operation

# Terminal colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}     Minerva AI Server Startup     ${NC}"
echo -e "${BLUE}========================================${NC}"

# Change to script directory for consistent operation
cd "$(dirname "$0")"

# Kill any existing Minerva processes to avoid port conflicts
pkill -f server.py || true
echo -e "${GREEN}✓ Cleared any existing Minerva server processes${NC}"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found! Please install Python 3.8 or newer${NC}"
    exit 1
fi

python_version=$(python3 --version | cut -d ' ' -f 2)
echo -e "${GREEN}✓ Using Python version: ${python_version}${NC}"

# Verify virtual environment
if [ ! -d "./venv_minerva" ]; then
    echo -e "${YELLOW}! Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv_minerva
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to create virtual environment. Check Python installation.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source ./venv_minerva/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to activate virtual environment.${NC}"
    exit 1
fi

# Install or update critical dependencies
echo -e "${BLUE}Installing/updating critical dependencies...${NC}"

# Install eventlet for WebSocket support
echo -e "${BLUE}Installing eventlet for WebSocket support...${NC}"
pip install --quiet eventlet flask flask-socketio flask-cors python-dotenv

# Check if dependencies installed correctly
if ! python3 -c "import eventlet, flask, flask_socketio" 2>/dev/null; then
    echo -e "${RED}✗ Failed to install or import critical dependencies.${NC}"
    echo -e "${YELLOW}Try running: pip install eventlet flask flask-socketio flask-cors python-dotenv${NC}"
    exit 1
fi

# Set API keys from environment if available, or use placeholders for testing
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}! No OpenAI API key found in environment. Server will use fallback models.${NC}"
    # export OPENAI_API_KEY="sk-dummy-for-testing-only"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}! No Anthropic API key found in environment. Claude models will be unavailable.${NC}"
    # export ANTHROPIC_API_KEY="sk-ant-dummy-for-testing-only"
fi

if [ -z "$MISTRAL_API_KEY" ]; then
    echo -e "${YELLOW}! No Mistral API key found in environment. Mistral models will be unavailable.${NC}"
    # export MISTRAL_API_KEY="dummy-for-testing-only"
fi

if [ -z "$HUGGINGFACE_API_KEY" ]; then
    echo -e "${YELLOW}! No HuggingFace API key found in environment. HuggingFace models will be unavailable.${NC}"
    # export HUGGINGFACE_API_KEY="hf-dummy-for-testing-only"
fi

# Try to create required directories
mkdir -p logs
mkdir -p data/chat_history
mkdir -p data/web_research_cache

# Set environmental variables
export FLASK_DEBUG=0
export PYTHONUNBUFFERED=1  # Ensure Python doesn't buffer output

# Run a quick pre-flight check to verify the server can start
echo -e "${BLUE}Running server pre-flight check...${NC}"
python3 -c "
import sys
import os
import importlib.util

# Check for critical modules
modules_to_check = ['flask', 'flask_socketio', 'eventlet']
missing_modules = []

for module in modules_to_check:
    if importlib.util.find_spec(module) is None:
        missing_modules.append(module)

if missing_modules:
    print(f'❌ Missing critical modules: {missing_modules}')
    sys.exit(1)

# Check if server.py exists
if not os.path.exists('server.py'):
    print('❌ server.py not found in current directory')
    sys.exit(1)

# Check for web/multi_ai_coordinator.py
if not os.path.exists('web/multi_ai_coordinator.py'):
    print('❌ web/multi_ai_coordinator.py not found')
    sys.exit(1)

# Try importing MultiAICoordinator
try:
    sys.path.insert(0, '.')
    from web.multi_ai_coordinator import coordinator, MultiAICoordinator
    print(f'✅ Successfully imported coordinator with {len(coordinator.available_models)} models')
except Exception as e:
    print(f'⚠️ Warning: Could not import coordinator: {e}')

print('✅ Pre-flight check completed successfully')
"

# Check if the pre-flight script succeeded
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Server pre-flight check failed. See errors above.${NC}"
    exit 1
fi

# Start the server
echo -e "${GREEN}Starting Minerva server on port 5505...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Run with error handling
python3 server.py 2>&1 | tee -a logs/server-$(date +%Y%m%d-%H%M%S).log

# Check if server exited with an error
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo -e "${RED}✗ Server exited with an error. Check logs for details.${NC}"
    exit 1
fi

echo -e "${GREEN}Server shut down gracefully.${NC}" 