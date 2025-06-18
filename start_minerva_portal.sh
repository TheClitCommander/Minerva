#!/bin/bash

# ======================================
# Minerva Portal Server with Think Tank
# ======================================
# This script starts the Minerva Portal with all AI models configured

# Add color to the output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}     Starting Minerva Think Tank     ${NC}"
echo -e "${GREEN}======================================${NC}"

# Set up the API keys for all models in the Think Tank
export OPENAI_API_KEY="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"
export ANTHROPIC_API_KEY="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"
export MISTRAL_API_KEY="FtHMcuPu4HsbKHUk4mJUIFfG1g20xF42"
export HUGGINGFACE_API_KEY="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"
export COHERE_API_KEY="7WjdzEYrvdWQNP40s30WX69znXVgiuHrD7spOwB4"
export GEMINI_API_KEY="AIzaSyCWP63Cmx_inlEwlAC0-zpxkYCjYo3wA5k"
export FLASK_SECRET_KEY="minerva-think-tank-$(date +%s)"

# Check for existing virtual environment
if [ -d "./venv_minerva" ]; then
    echo -e "${BLUE}Using existing virtual environment${NC}"
    source ./venv_minerva/bin/activate
else
    echo -e "${RED}Error: Virtual environment not found. Please run setup_minerva first.${NC}"
    exit 1
fi

# Install dependencies for Minerva server
echo -e "${BLUE}Installing dependencies for Minerva server...${NC}"
echo "Using existing virtual environment in venv_minerva..."

# Install/upgrade eventlet for WebSocket support
echo "Installing/upgrading eventlet for WebSocket support..."
pip install -U eventlet

# Install/upgrade Flask-SocketIO 
echo "Installing/upgrading Flask-SocketIO..."
pip install -U flask-socketio

# Install/upgrade other dependencies
echo "Installing/upgrading other dependencies..."
pip install -U flask flask-cors markdown python-dotenv

# Attempt to install optional AI packages
echo "Attempting to install optional AI packages (will skip if not available)..."
pip install -q openai anthropic mistralai 2>/dev/null || true
pip install -q -U --upgrade-strategy eager cohere google-generativeai 2>/dev/null || true

echo "Dependencies installation complete!"
echo "You can now run ./start_minerva_portal.sh to start the server"

# Start Minerva server
echo -e "${BLUE}Starting Minerva server on port 5505...${NC}"

# Check if port 5505 is in use
PID=$(lsof -ti:5505)
if [ -n "$PID" ]; then
    echo "Port 5505 is already in use by process $PID"
    read -p "Do you want to kill this process? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Killing process $PID..."
        kill -9 $PID
        sleep 1
    else
        echo "Exiting..."
        exit 1
    fi
fi

# IMPORTANT: Add SIGTERM protection to server
grep -q "signal.signal(signal.SIGTERM, signal.SIG_IGN)" server.py
if [ $? -ne 0 ]; then
    echo "Adding SIGTERM protection to server.py"
    # Add import at the top of server.py if it doesn't exist
    sed -i '' '1i\
import signal\
signal.signal(signal.SIGTERM, signal.SIG_IGN)  # Prevent server from being killed by SIGTERM\
' server.py
fi

# Run the server directly - DO NOT add any code after this that might kill it!
exec python server.py 