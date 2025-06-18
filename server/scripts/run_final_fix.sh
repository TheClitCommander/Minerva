#!/bin/bash

# Run the 100% working Socket.IO server for Minerva
# Works with Python 3.13 by using threading instead of eventlet

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "=================================================="
echo "       100% WORKING SOCKET.IO SERVER       "
echo "=================================================="
echo -e "${NC}"

# Kill any running server processes
echo -e "${YELLOW}Stopping any running server processes...${NC}"
pkill -f "python.*server.py" 2>/dev/null || true
sleep 1

# Check for Python
if command -v python3 &>/dev/null; then
    PYTHON=python3
    echo -e "${GREEN}Using Python 3${NC}"
elif command -v python &>/dev/null; then
    PYTHON=python
    echo -e "${GREEN}Using Python${NC}"
else
    echo -e "${RED}Error: Python not found. Please install Python to run this server.${NC}"
    exit 1
fi

# Create virtual environment
VENV_DIR="venv_working"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating new virtual environment in $VENV_DIR...${NC}"
    $PYTHON -m venv $VENV_DIR || {
        echo -e "${RED}Failed to create virtual environment. Please install python3-venv package.${NC}"
        exit 1
    }
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate" || {
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
}

# Install dependencies with exact versions
echo -e "${YELLOW}Installing exact compatible versions of dependencies...${NC}"
pip install flask-socketio==5.3.6 \
    python-socketio==5.9.0 \
    python-engineio==4.7.1 \
    flask==3.1.0 \
    werkzeug==3.1.3 || {
    echo -e "${RED}Failed to install dependencies.${NC}"
    exit 1
}

# Create static directory
mkdir -p static/js

# Download Socket.IO client
if [ ! -f "static/js/socket.io.min.js" ]; then
    echo -e "${YELLOW}Downloading Socket.IO client v4.4.1...${NC}"
    curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o static/js/socket.io.min.js || {
        echo -e "${RED}Failed to download Socket.IO client. CDN fallback will be used.${NC}"
    }
fi

# Check if port 5505 is in use
if command -v nc &>/dev/null; then
    if nc -z localhost 5505 2>/dev/null; then
        echo -e "${RED}Warning: Port 5505 is already in use. The server may fail to start.${NC}"
        echo -e "${YELLOW}Try these commands to fix:${NC}"
        echo -e "  lsof -i :5505 (to see what's using the port)"
        echo -e "  kill -9 [PID] (to kill the process)"
    fi
fi

# Run the server
echo -e "${GREEN}Starting 100% working Socket.IO server...${NC}"
echo -e "${YELLOW}Server will be available at: http://localhost:5505${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo

$PYTHON final_fix_server.py 