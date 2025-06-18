#!/bin/bash

# Run the minimal Socket.IO version of the Minerva chat server
echo -e "\n\033[1;36m=== Running Minimal Minerva Chat ===\033[0m\n"

# Kill any existing server processes
pkill -f "python.*server.py" || true
sleep 1

# Make sure the js directory exists
mkdir -p web/static/js

# Download the correct Socket.IO client if needed
if [ ! -f "web/static/js/socket.io.min.js" ]; then
    echo "Downloading Socket.IO v4.4.1 client..."
    curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o web/static/js/socket.io.min.js
fi

# Copy our simple chat script to the web directory if needed
if [ ! -f "web/simple-chat.js" ]; then
    echo "Copying simple-chat.js to web directory..."
    cp web/static/js/simple-chat.js web/simple-chat.js 2>/dev/null || true
fi

# Copy the simple chat page to the web directory
if [ ! -f "web/simple-chat.html" ]; then
    echo "Simple chat test page is available at http://localhost:5505/simple-chat"
fi

# Check for Python, preferring python3 if available
echo "Checking for Python..."
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

# Print start message
echo -e "\n\033[1;32m=== Starting Minimal Minerva Server ===\033[0m"
echo -e "Access the chat at: \033[1;36mhttp://localhost:5505/simple-chat\033[0m"
echo -e "Alternative: \033[1;36mhttp://localhost:5505/portal\033[0m (if available)"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
$PYTHON minimal_working_server.py 