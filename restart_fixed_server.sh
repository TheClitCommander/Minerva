#!/bin/bash

# Restart Fixed Minerva Server
# This script restarts the Minerva server with all the fixes applied

echo "========================================="
echo "      Restarting Fixed Minerva Server    "
echo "========================================="

# Stop any running servers
echo "Stopping any running server processes..."
pkill -9 -f "python.*server.py" || true
sleep 1

# Make sure we're in the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "./venv_minerva" ]; then
  echo "Activating virtual environment..."
  source ./venv_minerva/bin/activate
else
  echo "Virtual environment not found, using system Python..."
fi

# Install required dependencies
echo "Installing dependencies..."
pip install -q flask flask-socketio==5.3.4 flask-cors eventlet python-socketio==5.8.0 python-engineio==4.5.1 python-dotenv markdown

# Create a backup of original files if it doesn't exist
if [ ! -f "server.py.orig" ]; then
  echo "Creating backup of original files..."
  cp server.py server.py.orig
  cp web/static/js/chat/minerva-chat.js web/static/js/chat/minerva-chat.js.orig
  cp web/minerva-portal.html web/minerva-portal.html.orig
fi

echo "Starting Minerva server with fixed code..."
echo "Server will be available at: http://localhost:5505/portal"
echo "Press Ctrl+C to stop the server"

# Start the server
python server.py

# Deactivate virtual environment on exit
deactivate

echo "Server stopped." 