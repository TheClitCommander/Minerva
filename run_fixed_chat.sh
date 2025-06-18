#!/bin/bash

echo -e "\n\033[1;32m=== Running Fixed Minerva Chat ===\033[0m\n"

# Kill any existing server processes
pkill -f "python server.py" || true
sleep 1

# Clear Python cache
rm -rf web/__pycache__ 2>/dev/null
rm -rf __pycache__ 2>/dev/null

# Activate virtual environment if it exists
if [ -d "venv_minerva" ]; then
    source venv_minerva/bin/activate
    echo "Using existing virtual environment in venv_minerva"
else
    echo "Creating new virtual environment in venv_minerva"
    python3 -m venv venv_minerva
    source venv_minerva/bin/activate
    
    # Install required packages
    pip install flask flask-socketio==5.3.2 python-socketio==5.7.2 python-engineio==4.3.4 eventlet==0.30.2
fi

# Ensure socket.io client file exists
mkdir -p web/static/js
echo "Downloading Socket.IO client v4.4.1 (compatible with server)"
curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o web/static/js/socket.io.min.js

# Simple test to check that all dependencies are installed
echo "Testing imports..."
python -c "import flask, flask_socketio, eventlet, socketio, engineio; print('All dependencies installed!')" || {
    echo "Error importing dependencies! Installing required packages..."
    pip install flask flask-socketio==5.3.2 python-socketio==5.7.2 python-engineio==4.3.4 eventlet==0.30.2
}

# Add diagnostic info
echo "Starting Minerva with diagnostic output..."
echo ""
echo "Access the chat at: http://localhost:5505/portal"
echo "Access the debug interface at: http://localhost:5505/debug-chat"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
python server.py 