#!/bin/bash

# ======================================
# Minerva Server - NO KILL VERSION
# ======================================
# This script runs Minerva without killing it with SIGTERM

# Add color to the output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}     Starting Minerva (No Kill)      ${NC}"
echo -e "${GREEN}======================================${NC}"

# Clear Python cache to ensure fresh imports
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Check if port 5505 is in use
PID=$(lsof -ti:5505)
if [ -n "$PID" ]; then
    echo -e "${YELLOW}Port 5505 is already in use by process $PID${NC}"
    read -p "Do you want to kill this process? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Killing process $PID..."
        kill -9 $PID
        sleep 1
    else
        echo "Exiting..."
        exit 1
    fi
fi

# Set up API keys (using dummy values if needed)
if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY="sk-dummy-key-12345"
    echo -e "${YELLOW}Using dummy OpenAI API key${NC}"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    export ANTHROPIC_API_KEY="sk-ant-dummy-key-12345"
    echo -e "${YELLOW}Using dummy Anthropic API key${NC}"
fi

if [ -z "$MISTRAL_API_KEY" ]; then
    export MISTRAL_API_KEY="dummy-key-12345"
    echo -e "${YELLOW}Using dummy Mistral API key${NC}"
fi

# Enable unbuffered Python output
export PYTHONUNBUFFERED=1

# Modify server.py to ignore SIGTERM
echo "Adding SIGTERM protection to server.py..."
TMP_FILE=$(mktemp)
grep -q "signal.signal(signal.SIGTERM, signal.SIG_IGN)" server.py
if [ $? -ne 0 ]; then
    # Add SIGTERM handling if it doesn't exist
    cat <<'EOF' > $TMP_FILE
import signal
# Protect against SIGTERM by ignoring it
print("Setting up signal handlers to prevent termination...")
signal.signal(signal.SIGTERM, signal.SIG_IGN)
print("✅ SIGTERM handler installed - server won't be killed by SIGTERM")

EOF
    FIRST_IMPORT_LINE=$(grep -n "^import" server.py | head -1 | cut -d: -f1)
    if [ -n "$FIRST_IMPORT_LINE" ]; then
        # Insert after the first import line
        AFTER_IMPORT=$((FIRST_IMPORT_LINE + 1))
        head -n $FIRST_IMPORT_LINE server.py > temp_server.py
        cat $TMP_FILE >> temp_server.py
        tail -n +$AFTER_IMPORT server.py >> temp_server.py
        mv temp_server.py server.py
        echo "✅ SIGTERM protection added to server.py"
    else
        echo "${RED}Could not find import line in server.py${NC}"
    fi
else
    echo "✅ SIGTERM protection already exists in server.py"
fi
rm $TMP_FILE

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}     Starting Minerva Server...      ${NC}"
echo -e "${GREEN}======================================${NC}"
echo "Access the portal at http://localhost:5505/portal"
echo "Press Ctrl+C to stop the server"
echo

# *** IMPORTANT: Run server with exec to replace this shell process ***
# This prevents any cleanup code in the script from running and killing the server
exec python server.py 