#!/bin/bash
# Script to install dependencies needed for Minerva server

echo "Installing dependencies for Minerva server..."

# Determine which Python to use
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python not found. Please install Python 3.x"
    exit 1
fi

# Determine which pip to use
if command -v pip3 &> /dev/null; then
    PIP=pip3
elif command -v pip &> /dev/null; then
    PIP=pip
else
    echo "Error: pip not found. Please install pip"
    exit 1
fi

# Check for virtual environment
if [ -d "venv_minerva" ]; then
    echo "Using existing virtual environment in venv_minerva..."
    # Activate the virtual environment
    source venv_minerva/bin/activate
elif [ -d ".venv" ]; then
    echo "Using existing virtual environment in .venv..."
    # Activate the virtual environment
    source .venv/bin/activate
fi

# Install required packages
echo "Installing/upgrading eventlet for WebSocket support..."
$PIP install --upgrade eventlet

# Install other key dependencies
echo "Installing/upgrading Flask-SocketIO..."
$PIP install --upgrade flask-socketio

echo "Installing/upgrading other dependencies..."
$PIP install --upgrade flask flask-cors markdown python-dotenv

# Try to install AI API packages if available
echo "Attempting to install optional AI packages (will skip if not available)..."
$PIP install --upgrade openai anthropic google-generativeai &>/dev/null || true

echo "Dependencies installation complete!"
echo "You can now run ./start_minerva_portal.sh to start the server" 