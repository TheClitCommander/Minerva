#!/bin/bash

# Fix Socket.IO compatibility by setting up environment and dependencies
echo -e "\n\033[1;36m=== Running Minerva with Fixed Socket.IO ===\033[0m\n"

# Kill any existing server instances
echo "Cleaning up any existing server instances..."
pkill -f "python server.py" || true
pkill -f "python3 server.py" || true
sleep 1

# Check for virtual environment
if [ -d "venv_minerva" ]; then
    echo "Using existing virtual environment"
    # Activate the virtual environment
    source venv_minerva/bin/activate
else
    echo "Creating a new virtual environment..."
    python3 -m venv venv_minerva
    source venv_minerva/bin/activate
fi

# Install specific compatible versions of Socket.IO dependencies
echo "Installing compatible Socket.IO packages..."
pip install python-socketio==5.7.2 python-engineio==4.3.4 flask-socketio==5.3.2 eventlet==0.30.2 --force-reinstall

# Download Socket.IO client to ensure version matches
echo "Downloading compatible Socket.IO client..."
mkdir -p web/static/js
# Get version 4.4.1 which is compatible with the server components
curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o web/static/js/socket.io.min.js

# Add diagnostic info to server.py
echo "Adding diagnostic output to server.py..."
CHAT_HANDLER=$(grep -n "@socketio.on('chat_message')" server.py | cut -d: -f1)
if [ ! -z "$CHAT_HANDLER" ]; then
    # Add diagnostic print statements
    sed -i.bak "$(($CHAT_HANDLER+2))i\\    print(f\"🔥 Received chat_message: {data} from client {request.sid}\")" server.py
    echo "Added diagnostic prints to server.py"
fi

# Run the server
echo -e "\n\033[1;32m=== Starting Minerva Server with Socket.IO compatibility fixes ===\033[0m\n"
echo "Server will be available at: http://localhost:5505/portal"
echo "Debug interface available at: http://localhost:5505/debug-chat"
echo "Press Ctrl+C to stop the server"
python server.py
