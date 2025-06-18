#!/bin/bash

# Stop any existing server
pkill -f server.py || true

# Clear Python cache
find . -name "__pycache__" -exec rm -rf {} +  2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Ensure Socket.IO client is available
if [ ! -f "web/static/js/socket.io.min.js" ]; then
    echo "Downloading Socket.IO client..."
    curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o web/static/js/socket.io.min.js
fi

# Activate virtual environment if it exists
if [ -d "venv_minerva" ]; then
    source venv_minerva/bin/activate
fi

# Run the server
echo -e "\n\033[1;32m=== Starting Minerva with Fixed Socket.IO ===\033[0m\n"
echo "Access the portal at: http://localhost:5505/portal"
echo -e "==========================================\n"

python server.py
