#!/bin/bash

# Fix dependencies for Minerva Socket.IO chat
echo "Installing compatible versions of dependencies..."

# Activate virtual environment if it exists
if [ -d "venv_minerva" ]; then
    source venv_minerva/bin/activate
    echo "Activated virtual environment"
else
    echo "Virtual environment not found, installing globally"
fi

# Install compatible versions
pip install eventlet==0.33.3
pip install flask-socketio==5.3.4
pip install python-socketio==5.8.0
pip install python-engineio==4.5.1

echo "Dependencies installation complete!"
echo "Please restart the Minerva server to apply changes."

# Make the script executable
chmod +x fix_requirements.sh 