#!/bin/bash

# Kill any existing server process
echo "🛑 Stopping any existing server processes..."
pkill -f server.py || true
pkill -f simple_test_server.py || true
sleep 1

# Set required environment variables
export FLASK_DEBUG=1
export PYTHONPATH=$PYTHONPATH:$(pwd)
export DEBUG_MODE=1

echo -e "\n\033[1;36m========================================="
echo "   🧪 Simple Test Server Starting   "
echo -e "=========================================\033[0m\n"

# Activate virtual environment if it exists
if [ -d "./venv_minerva" ]; then
    echo "🐍 Activating Python virtual environment..."
    source ./venv_minerva/bin/activate
    PYTHON_CMD="python"
else
    echo "⚠️ No virtual environment found at ./venv_minerva"
    echo "🔍 Looking for Python in path..."
    PYTHON_CMD=$(which python3 || which python)
    if [ -z "$PYTHON_CMD" ]; then
        echo "❌ ERROR: Python not found! Please install Python or specify the correct path."
        exit 1
    fi
    echo "🐍 Using Python at: $PYTHON_CMD"
fi

echo "📝 Debug logs will be written to simple_test.log"
echo "🔄 Launching simple test server for Socket.IO debugging..."

# Execute the server with output to log file
$PYTHON_CMD simple_test_server.py 2>&1 | tee -a simple_test.log

# This shouldn't be reached unless server exits
echo "⚠️ Server exited. Check simple_test.log for details." 