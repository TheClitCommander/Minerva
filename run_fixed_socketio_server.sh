#!/bin/bash

echo -e "\n\033[1;36m==========================================="
echo "   🚀 Starting Minerva with Socket.IO Fix   "
echo -e "===========================================\033[0m\n"

# Kill any existing server processes
echo "🔄 Stopping any existing server processes..."
pkill -f server.py || true
sleep 2

# Clear Python cache
echo "🧹 Clearing Python cache..."
find . -name "__pycache__" -exec rm -rf {} +  2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Create static directories if they don't exist
echo "📁 Ensuring static directories exist..."
mkdir -p web/static/js

# Ensure Socket.IO client is downloaded
if [ ! -f "web/static/js/socket.io.min.js" ]; then
    echo "📥 Downloading Socket.IO client library..."
    curl -s https://cdn.socket.io/4.6.0/socket.io.min.js -o web/static/js/socket.io.min.js
    if [ $? -ne 0 ]; then
        echo "❌ Failed to download Socket.IO client. Check your internet connection."
    else
        echo "✅ Socket.IO client downloaded successfully"
    fi
fi

# Set required environment variables
export FLASK_DEBUG=1
export SOCKETIO_DEBUG=1

# Activate virtual environment if it exists
if [ -d "venv_minerva" ]; then
    echo "🐍 Activating Python virtual environment..."
    source venv_minerva/bin/activate
    PYTHON_CMD="python"
else
    echo "⚠️ No virtual environment found, using system Python..."
    PYTHON_CMD=$(which python3 || which python)
    if [ -z "$PYTHON_CMD" ]; then
        echo "❌ ERROR: Python not found! Please install Python or create a virtual environment."
        exit 1
    fi
fi

echo -e "\n\033[1;32m==== Starting Minerva Socket.IO Server ====\033[0m"
echo "📊 Server will be available at: http://localhost:5505/portal"
echo -e "\033[1;32m==============================\033[0m\n"

# Execute with the correct parameters
$PYTHON_CMD server.py

# Check exit status
if [ $? -ne 0 ]; then
    echo -e "\n\033[1;31mServer exited with an error. Check the logs above.\033[0m"
else
    echo -e "\n\033[1;32mServer stopped gracefully.\033[0m"
fi
