#!/bin/bash

# Minerva AI Server - Smart Startup Script
# ---------------------------------------

# Check if we have a virtual environment and activate it
if [ -d "venv_minerva" ]; then
    echo "Activating Minerva virtual environment..."
    source ./venv_minerva/bin/activate
else
    echo "No virtual environment found. Using system Python."
fi

# Make sure the port is free
PORT=${PORT:-5505}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "Port $PORT is already in use. Killing existing process..."
    pkill -f server.py || true
    sleep 2  # Give it time to shut down
fi

# Check for environment variables and load if necessary
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "No .env file found, but .env.example exists."
    echo "Would you like to create a .env file now? (y/n)"
    read -r answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo "Created .env file from template. Please edit it with your API keys."
        echo "Would you like to edit it now? (y/n)"
        read -r edit_answer
        if [[ "$edit_answer" =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        fi
    fi
fi

# Check if any API keys are configured
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$MISTRAL_API_KEY" ] && [ -z "$HUGGINGFACE_API_KEY" ]; then
    if [ -f "set_api_keys.sh" ]; then
        echo "No API keys detected. Would you like to set them now? (y/n)"
        read -r keys_answer
        if [[ "$keys_answer" =~ ^[Yy]$ ]]; then
            source ./set_api_keys.sh
        else
            echo "⚠️ Warning: Starting in SIMULATION MODE (no real AI access)"
        fi
    else
        echo "⚠️ Warning: No API keys detected. Server will run in SIMULATION MODE"
    fi
fi

# Start the server
echo "========================================="
echo "      Starting Minerva AI Server         "
echo "========================================="
echo "Starting on: http://localhost:$PORT/portal"
echo "Press Ctrl+C to stop the server"
echo "-----------------------------------------"

python server.py 