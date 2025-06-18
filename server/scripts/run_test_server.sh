#!/bin/bash

# Ultra minimal test server for Socket.IO communication
# Works with Python 3.13 by avoiding eventlet

echo -e "\n\033[1;36m=== Running Minimal Socket.IO Test Server ===\033[0m\n"

# Kill any running server processes
pkill -f "python.*server.py" || true
sleep 1

# Ensure Python is available
if command -v python3 &>/dev/null; then
    PYTHON=python3
    echo "Using Python 3"
elif command -v python &>/dev/null; then
    PYTHON=python
    echo "Using Python"
else
    echo "Error: Python not found. Please install Python to run this server."
    exit 1
fi

# Create directories if they don't exist
mkdir -p static/js

# Install required packages
echo -e "\n\033[1;33mInstalling required packages...\033[0m"
$PYTHON -m pip install flask flask-socketio>=5.3.0 python-socketio>=5.7.0 || {
    echo "Error installing required packages."
    exit 1
}

# Download Socket.IO client
if [ ! -f "static/js/socket.io.min.js" ]; then
    echo -e "\n\033[1;33mDownloading Socket.IO client...\033[0m"
    curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o static/js/socket.io.min.js || {
        echo "Error downloading Socket.IO client. Will use CDN fallback."
    }
fi

# Run the server
echo -e "\n\033[1;32m=== Starting Server ===\033[0m"
echo "Server will be available at: http://localhost:5505/test.html"
echo "Press Ctrl+C to stop the server"
echo ""

$PYTHON minimal_test_server.py

echo "Server stopped." 