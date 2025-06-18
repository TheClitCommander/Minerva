#!/bin/bash

echo "=== Running ULTRA-MINIMAL Socket.IO Server ==="
echo "Python 3.13 compatible, NO eventlet, THREADING MODE ONLY"
echo

# Kill any existing server processes
pkill -f server.py
pkill -f pure_minimal.py

# Create a new dedicated virtual environment
if [ ! -d "venv_socket" ]; then
    echo "Creating fresh virtual environment..."
    python3 -m venv venv_socket
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv_socket/bin/activate

# Install required packages (latest compatible versions)
echo "Installing compatible packages for Python 3.13..."
pip install flask flask-socketio flask-cors python-dotenv --upgrade

# Create static directory
mkdir -p static/js

# Make script executable
chmod +x pure_minimal.py

# Start the server
echo
echo "Starting server..."
echo "Access at: http://localhost:5505"
echo "Press Ctrl+C to stop"
echo

# Run the server
python pure_minimal.py 