#!/bin/bash

# Ultra minimal diagnostic script for Socket.IO + Python 3.13
# - Creates clean venv
# - Installs only what's needed
# - Runs minimal test server

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=================================================="
echo "     Socket.IO Diagnostic - Python 3.13 Fix       "
echo "=================================================="
echo -e "${NC}"

# Kill any running server processes
echo -e "${YELLOW}Stopping any running server processes...${NC}"
pkill -f "python.*server.py" 2>/dev/null || true
sleep 1

# Create virtual environment if it doesn't exist
VENV_DIR="venv_diagnostic"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating clean virtual environment in $VENV_DIR...${NC}"
    python3 -m venv $VENV_DIR || {
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

# Verify Python version
PYTHON_VERSION=$(python --version)
echo -e "${GREEN}Using $PYTHON_VERSION${NC}"

# Install specific compatible dependencies
echo -e "${YELLOW}Installing precise compatible versions of dependencies...${NC}"
pip install flask==3.1.0 \
    flask-socketio==5.3.6 \
    python-socketio==5.9.0 \
    python-engineio==4.7.1 || {
    echo -e "${RED}Failed to install dependencies.${NC}"
    exit 1
}

# Create static directories
echo -e "${YELLOW}Setting up static directories...${NC}"
mkdir -p static/js

# Download Socket.IO client
if [ ! -f "static/js/socket.io.min.js" ]; then
    echo -e "${YELLOW}Downloading Socket.IO client v4.4.1...${NC}"
    curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o static/js/socket.io.min.js || {
        echo -e "${RED}Failed to download Socket.IO client. CDN fallback will be used.${NC}"
    }
fi

# Check if port 5505 is in use
if nc -z localhost 5505 2>/dev/null; then
    echo -e "${RED}Warning: Port 5505 is already in use. The server may fail to start.${NC}"
    echo -e "${YELLOW}Try: lsof -i :5505${NC} to see what's using the port."
    echo -e "${YELLOW}Try: kill -9 [PID]${NC} to kill the process."
    
    # Ask if user wants to continue anyway
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Exiting.${NC}"
        exit 1
    fi
fi

# Run the server
echo -e "${GREEN}Starting diagnostic server...${NC}"
echo -e "${YELLOW}Open http://localhost:5505/ in your browser${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop server${NC}"
echo ""

python debug_socketio.py || {
    echo -e "${RED}Server exited with an error.${NC}"
    exit 1
} 