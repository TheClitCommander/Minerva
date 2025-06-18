#!/bin/bash

# Kill any existing server instances
pkill -f server.py || true

# Clear the Python cache
find . -name "__pycache__" -exec rm -rf {} +  2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Make sure static directory exists
mkdir -p web/static/js

# Ensure Socket.IO client is available
if [ ! -f "web/static/js/socket.io.min.js" ]; then
    echo "Downloading Socket.IO client..."
    curl -s https://cdn.socket.io/4.6.0/socket.io.min.js -o web/static/js/socket.io.min.js
fi

# Set Socket.IO debug mode
export SOCKETIO_DEBUG=1

# Activate virtual environment if it exists
if [ -d "venv_minerva" ]; then
    source venv_minerva/bin/activate
fi

# Run the server
python server.py 