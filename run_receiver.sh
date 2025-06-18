#!/bin/bash

# Think Tank Receiver Launcher Script
# This script runs a server that receives messages but doesn't send responses

echo -e "\n\033[1;35m========================================="
echo "   🔮 Think Tank Receiver - No Response Mode   "
echo -e "=========================================\033[0m\n"

# Stop any existing servers
echo "🛑 Stopping any existing servers..."
pkill -f "python.*server.py" || true
pkill -f "think_tank_receiver.py" || true
sleep 1

# Make server script executable
echo "🔧 Setting up server..."
chmod +x think_tank_receiver.py

# Install required dependencies
echo "📦 Checking dependencies..."
pip install -q flask flask-socketio==5.3.4 flask-cors eventlet python-socketio==5.8.0 python-engineio==4.5.1

# Create data directory if it doesn't exist
mkdir -p data/messages

echo -e "\n\033[1;32m🚀 Starting Think Tank Receiver...\033[0m"
echo -e "\033[1;33mIMPORTANT: This server will only RECEIVE messages and will NOT respond\033[0m"
echo -e "To forcibly stop it, use: \033[1;31mpkill -9 -f think_tank_receiver.py\033[0m\n"

# Run the receiver server
./think_tank_receiver.py 