#!/bin/bash

# ======================================================
# Python 3.13 Compatible Minerva Server
# - Forces threading mode instead of eventlet
# - Ensures Socket.IO compatibility
# ======================================================

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "======================================================="
echo "       Minerva Server - Python 3.13 Compatible         "
echo "======================================================="
echo -e "${NC}"

# Kill any existing server processes
echo -e "${YELLOW}Stopping any running server processes...${NC}"
pkill -f "python.*server.py" 2>/dev/null || true
sleep 1

# Ensure server.py exists
if [ ! -f "server.py" ]; then
    echo -e "${RED}Error: server.py not found in current directory.${NC}"
    exit 1
fi

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}Using $PYTHON_VERSION${NC}"

# Create the Socket.IO client in proper location
mkdir -p web/static/js 
mkdir -p static/js
echo -e "${YELLOW}Downloading Socket.IO v4.4.1 client...${NC}"
curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o web/static/js/socket.io.min.js
cp web/static/js/socket.io.min.js static/js/socket.io.min.js

# Set environment variables
export DEBUG_MODE=1
export OPENAI_API_KEY=${OPENAI_API_KEY:-"sk-dummy-key-12345"}
export ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-"sk-ant-dummy-key12345"}
export FLASK_DEBUG=1

# Run server with Python 3.13 compatibility
echo -e "${GREEN}Starting Minerva server...${NC}"
echo -e "${YELLOW}Server will be available at: http://localhost:5505/portal${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo

python3 server.py

echo -e "${GREEN}Server shutdown.${NC}" 