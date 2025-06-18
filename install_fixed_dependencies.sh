#!/bin/bash

# Fix dependencies for Minerva Socket.IO chat
echo "===== INSTALLING COMPATIBLE DEPENDENCIES FOR MINERVA ====="

# Activate virtual environment if it exists
if [ -d "venv_minerva" ]; then
    source venv_minerva/bin/activate
    echo "✅ Activated virtual environment"
else
    echo "ℹ️ Virtual environment not found, installing globally"
fi

# First uninstall any existing Socket.IO related packages to avoid version conflicts
echo "🔄 Removing any existing Socket.IO packages..."
pip uninstall -y eventlet flask-socketio python-socketio python-engineio

# Install exact versions known to work together with Socket.IO 4.7.2 client
echo "📦 Installing Socket.IO components with compatible versions..."
pip install eventlet==0.33.3
pip install flask-socketio==5.3.6
pip install python-socketio==5.10.0
pip install python-engineio==4.8.0

# Install other core dependencies
echo "📦 Installing other core dependencies..."
pip install flask==2.2.5
pip install flask-cors==4.0.0
pip install requests==2.31.0
pip install python-dotenv==1.0.0
pip install markdown==3.5.2

# Make the script executable for future reference
chmod +x install_fixed_dependencies.sh

echo
echo "===== DEPENDENCY INSTALLATION COMPLETE ====="
echo "✅ All required packages installed with compatible versions"
echo "ℹ️ Run ./simple_run_server.sh to start the Minerva server"
echo "ℹ️ For best results, restart your browser before connecting"
echo 