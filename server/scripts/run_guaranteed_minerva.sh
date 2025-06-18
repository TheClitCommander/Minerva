#!/bin/bash

# Guaranteed Working Minerva Chat Server Launcher
# This script ensures the server starts properly and remains running

echo -e "\n\033[1;35m========================================="
echo "   🔮 Minerva Chat - Guaranteed Working   "
echo -e "=========================================\033[0m\n"

# Stop any existing servers
echo "🛑 Stopping any existing Minerva servers..."
pkill -f "python.*server.py" || true
pkill -f "guaranteed_working_server.py" || true
sleep 1

# Make server script executable
echo "🔧 Setting up server..."
chmod +x guaranteed_working_server.py

# Install required dependencies
echo "📦 Checking dependencies..."
pip install -q flask flask-socketio==5.3.4 flask-cors eventlet python-socketio==5.8.0 python-engineio==4.5.1

# Create a symbolic link to ensure the server can be accessed at /portal
if [ ! -L "web/portal" ]; then
  mkdir -p web
  ln -sf ../ web/portal
fi

echo -e "\n\033[1;32m🚀 Starting Guaranteed Working Server...\033[0m"
echo -e "\033[1;33mIMPORTANT: This server is designed to IGNORE termination signals!\033[0m"
echo -e "To forcibly stop it, use: \033[1;31mpkill -9 -f guaranteed_working_server.py\033[0m\n"

# Run the server
./guaranteed_working_server.py

# This should never be reached due to signal handling, but just in case
echo "🔄 Server exited unexpectedly. Restarting in 3 seconds..."
sleep 3
exec $0 