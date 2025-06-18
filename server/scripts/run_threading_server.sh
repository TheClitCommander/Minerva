#!/bin/bash

echo "=== Running Minimal Threading Socket.IO Server ==="
echo "This server uses threading mode, not eventlet"
echo "Python 3.13 compatible"
echo

# Kill any existing server processes
pkill -f server.py
pkill -f pure_threading_server.py

# Set up virtual environment if it doesn't exist
if [ ! -d "venv_minerva" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv_minerva
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv_minerva/bin/activate

# Install required packages
echo "Installing required packages..."
pip install flask flask-socketio flask-cors python-dotenv markdown

# Create static directory
mkdir -p static/js

# Start the server
echo
echo "Starting server..."
echo "Access at: http://localhost:5505"
echo "Press Ctrl+C to stop"
echo

# Run the server
python pure_threading_server.py 