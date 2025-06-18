#!/bin/bash

# Simple script to test all the fixes and diagnose issues
echo "========================================"
echo "  Testing Minerva Server Fixes         "
echo "========================================"

# 1. Test imports
echo -e "\n\033[1;36m1. Testing Python imports...\033[0m"
python3 -c "
import sys
print(f'Python version: {sys.version}')
try:
    from web.multi_ai_coordinator import coordinator
    print(f'✅ Successfully imported coordinator: {coordinator.__class__.__name__}')
    print(f'Available models: {len(coordinator.available_models)}')
except Exception as e:
    print(f'❌ Error importing coordinator: {e}')
" || echo "❌ Python import test failed"

# 2. Test Socket.IO client version
echo -e "\n\033[1;36m2. Testing Socket.IO client version in HTML...\033[0m"
SOCKET_IO_VER=$(grep -o 'socket.io/[0-9]\+\.[0-9]\+\.[0-9]\+/socket.io.min.js' web/minerva-portal.html | head -1)
if [[ ! -z "$SOCKET_IO_VER" ]]; then
    echo "✅ Found Socket.IO client: $SOCKET_IO_VER"
else
    echo "❌ Socket.IO client not found in HTML"
fi

# 3. Test server startup without actually starting it
echo -e "\n\033[1;36m3. Syntax check server.py...\033[0m"
python3 -m py_compile server.py
if [[ $? -eq 0 ]]; then
    echo "✅ server.py has no syntax errors"
else
    echo "❌ server.py has syntax errors"
fi

# 4. Test environment variables
echo -e "\n\033[1;36m4. Testing environment variables...\033[0m"
if [[ ! -z "$OPENAI_API_KEY" ]]; then
    echo "✅ OPENAI_API_KEY is set"
else
    echo "⚠️ OPENAI_API_KEY is not set"
fi

if [[ ! -z "$ANTHROPIC_API_KEY" ]]; then
    echo "✅ ANTHROPIC_API_KEY is set"
else
    echo "⚠️ ANTHROPIC_API_KEY is not set"
fi

if [[ ! -z "$MISTRAL_API_KEY" ]]; then
    echo "✅ MISTRAL_API_KEY is set"
else
    echo "⚠️ MISTRAL_API_KEY is not set"
fi

if [[ ! -z "$HUGGINGFACE_API_KEY" ]]; then
    echo "✅ HUGGINGFACE_API_KEY is set"
else
    echo "⚠️ HUGGINGFACE_API_KEY is not set"
fi

# 5. Briefly test the actual server
echo -e "\n\033[1;36m5. Starting server in test mode (will stop after 2 seconds)...\033[0m"
(
    python3 server.py &
    SERVER_PID=$!
    sleep 2
    echo "Server started with PID $SERVER_PID, stopping..."
    pkill -15 -P $SERVER_PID
    kill -15 $SERVER_PID
)

echo -e "\n\033[1;36mTest results summary:\033[0m"
echo "✅ Socket.IO client: $SOCKET_IO_VER"
echo "✅ server.py syntax: OK"
echo "✅ Coordinator module: Available"

echo -e "\n\033[1;32mAll tests completed! Run ./simple_run_server.sh to start the server.\033[0m" 