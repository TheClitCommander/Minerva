#!/bin/bash

# ======================================================
# Socket.IO Debug Server - Python 3.13 Compatible
# - Uses threading instead of eventlet
# - Auto-installs dependencies in venv
# - Works with all browsers
# ======================================================

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Title Banner
echo -e "${BLUE}"
echo "======================================================="
echo "       Socket.IO Debug Server - Starting Up            "
echo "======================================================="
echo -e "${NC}"

# Kill any running server processes
echo -e "${YELLOW}Stopping any running server processes...${NC}"
pkill -f "python.*server.py" 2>/dev/null || true
sleep 1

# Create virtual environment if it doesn't exist
VENV_DIR="venv_debug"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment in $VENV_DIR...${NC}"
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

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install flask flask-socketio python-socketio || {
    echo -e "${RED}Failed to install dependencies.${NC}"
    exit 1
}

# Create static directories
echo -e "${YELLOW}Setting up static directories...${NC}"
mkdir -p static/js
mkdir -p web/static/js

# Download Socket.IO client if needed
if [ ! -f "static/js/socket.io.min.js" ]; then
    echo -e "${YELLOW}Downloading Socket.IO client v4.4.1...${NC}"
    curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o static/js/socket.io.min.js || {
        echo -e "${RED}Failed to download Socket.IO client. CDN fallback will be used.${NC}"
    }
    
    # Copy to web directory as well
    cp static/js/socket.io.min.js web/static/js/ 2>/dev/null || true
fi

# Run the server
echo -e "${GREEN}Starting debug server...${NC}"
echo -e "${YELLOW}Server will be available at: http://localhost:5505/debug${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo

python threading_server.py || {
    echo -e "${RED}Server exited with an error.${NC}"
    exit 1
}

echo -e "${GREEN}Server shutdown successfully.${NC}" 