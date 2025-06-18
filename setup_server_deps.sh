#!/bin/bash

# Simple script to install the minimal required dependencies for the Minerva server
echo "========================================"
echo "Setting up minimal Minerva server dependencies"
echo "========================================"

# Create a virtual environment if it doesn't exist
if [ ! -d "./venv_minerva" ]; then
    echo "Creating new virtual environment..."
    python3 -m venv venv_minerva
else
    echo "Using existing virtual environment..."
fi

# Activate the virtual environment
source ./venv_minerva/bin/activate

# Install core dependencies
echo "Installing core dependencies..."
pip install flask flask-socketio eventlet flask-cors python-dotenv requests

# Install AI client libraries
echo "Installing AI client libraries..."
pip install openai anthropic

# Verify installation
echo "Verifying installation..."
python3 -c "
import sys
print(f'Python version: {sys.version}')
print('Checking dependencies:')
deps = ['flask', 'flask_socketio', 'eventlet', 'flask_cors', 'dotenv', 'requests', 'openai', 'anthropic']
for dep in deps:
    try:
        __import__(dep.replace('_', '.'))
        print(f'✅ {dep} installed')
    except ImportError:
        print(f'❌ {dep} NOT installed')
"

echo -e "\nSetup complete! You can now run:"
echo "  ./simple_run_server.sh" 