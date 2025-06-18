#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}     Starting Minerva Persistent Server     ${NC}"
echo -e "${GREEN}======================================${NC}"

# Ensure the script works in the correct directory
cd "$(dirname "$0")"

# Create log directory if it doesn't exist
mkdir -p logs

# Kill any existing Minerva server instances
echo -e "${YELLOW}Stopping any existing Minerva server processes...${NC}"
pkill -f server.py || true
sleep 2  # Give the old process time to fully terminate

# Activate the virtual environment
echo -e "${YELLOW}Activating Python virtual environment...${NC}"
source ./venv_minerva/bin/activate

# Install dependencies if needed
if [ ! -d "./venv_minerva" ]; then
    echo -e "${YELLOW}No virtual environment found. Creating one...${NC}"
    python -m venv venv_minerva
    source ./venv_minerva/bin/activate
    pip install -r requirements.txt
fi

# Setup environment variables for the server
export FLASK_APP=server.py
export FLASK_ENV=development
export FLASK_DEBUG=1
export SOCKETIO_DEBUG=1

# Set dummy API keys if none are provided (will use enhanced simulation)
# This is safer than using invalid keys that might trigger API errors
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}No OpenAI API key found. Using enhanced simulation mode for OpenAI.${NC}"
    export OPENAI_API_KEY=""
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}No Anthropic API key found. Using enhanced simulation mode for Claude.${NC}"
    export ANTHROPIC_API_KEY=""
fi

if [ -z "$MISTRAL_API_KEY" ]; then
    echo -e "${YELLOW}No Mistral API key found. Using enhanced simulation mode for Mistral.${NC}"
    export MISTRAL_API_KEY=""
fi

# Generate timestamp for logging
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/minerva_server_${TIMESTAMP}.log"

# Create a symlink to the latest log
ln -sf "$LOG_FILE" logs/latest.log

echo -e "${BLUE}Starting Minerva server in persistent mode...${NC}"
echo -e "${BLUE}Server logs will be saved to: ${LOG_FILE}${NC}"
echo -e "${BLUE}Monitor logs with: tail -f ${LOG_FILE}${NC}"

# Start the server using nohup to keep it running after terminal closes
nohup python server.py > "$LOG_FILE" 2>&1 &
PID=$!

# Save PID to file for easier management
echo $PID > .minerva_server.pid

# Wait a moment for server to initialize
echo -e "${YELLOW}Waiting for server to initialize (5 seconds)...${NC}"
sleep 5

# Check if server is still running
if ps -p $PID > /dev/null; then
    echo -e "${GREEN}✅ Minerva server started successfully!${NC}"
    echo -e "${GREEN}---------------------------------------${NC}"
    echo -e "${GREEN}Access the Minerva Portal at:${NC}"
    echo -e "${GREEN}http://localhost:5505/portal${NC}"
    echo -e "${GREEN}---------------------------------------${NC}"
    echo -e "${YELLOW}Process ID: ${PID}${NC}"
    echo -e "${YELLOW}To view logs: tail -f ${LOG_FILE}${NC}"
    echo -e "${YELLOW}To stop the server: ./stop_server.sh or pkill -f server.py${NC}"
else
    echo -e "${RED}❌ Server failed to start or crashed immediately.${NC}"
    echo -e "${RED}Please check the logs for errors: ${LOG_FILE}${NC}"
    tail -n 20 "$LOG_FILE"
    exit 1
fi 