#!/bin/bash

# Kill any existing server process
pkill -f server.py

# Activate the virtual environment
source ./venv_minerva/bin/activate

# Use port 8000 for testing
export PORT=8000

# Run the server
python server.py 