#!/bin/bash

# Minerva Fixes Diagnostic Script
# This tests all the critical components to ensure they're working correctly

# Terminal colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}     Minerva Fixes Diagnostic Tool     ${NC}"
echo -e "${BLUE}========================================${NC}"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found! Please install Python 3.8 or newer${NC}"
    exit 1
fi

python_version=$(python3 --version | cut -d ' ' -f 2)
echo -e "${GREEN}✓ Using Python version: ${python_version}${NC}"

# Verify virtual environment
if [ -d "./venv_minerva" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
    # Activate virtual environment
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source ./venv_minerva/bin/activate
else
    echo -e "${YELLOW}! Virtual environment not found. Continuing with system Python${NC}"
fi

# Test 1: Verify critical Python dependencies
echo -e "\n${BLUE}Testing critical dependencies...${NC}"
python3 -c "
import sys
critical_modules = ['flask', 'flask_socketio', 'eventlet']
missing = []
for module in critical_modules:
    try:
        __import__(module)
        print(f'✅ {module} is installed')
    except ImportError:
        missing.append(module)
        print(f'❌ {module} is NOT installed')

if missing:
    print(f'\n❌ Missing {len(missing)} critical dependencies! Install with:')
    print(f'pip install {\" \".join(missing)}')
    sys.exit(1)
else:
    print('✅ All critical dependencies are installed')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Critical dependencies test failed!${NC}"
    exit 1
fi

# Test 2: Verify MultiAICoordinator module import
echo -e "\n${BLUE}Testing MultiAICoordinator imports...${NC}"
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    # Test direct import
    from web.multi_ai_coordinator import coordinator, MultiAICoordinator
    print('✅ Direct import of coordinator and MultiAICoordinator successful')
    print(f'✅ Coordinator has {len(coordinator.available_models)} models')
    
    # Check coordinator attributes
    if hasattr(coordinator, 'available_models'):
        print(f'✅ Coordinator has expected attributes')
    else:
        print('❌ Coordinator missing expected attributes')
        
except ImportError as e:
    print(f'❌ Web module import failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ MultiAICoordinator import test failed!${NC}"
else
    echo -e "${GREEN}✓ MultiAICoordinator import test passed!${NC}"
fi

# Test 3: Check if Socket.IO client version in HTML matches server
echo -e "\n${BLUE}Testing Socket.IO version compatibility...${NC}"
SOCKET_IO_CLIENT=$(grep -o 'socket.io/[0-9.]\+/' web/minerva-portal.html | head -1 | sed 's/socket.io\///' | sed 's/\///')
SOCKET_IO_SERVER=$(pip freeze | grep -i 'python-socketio' | head -1 | cut -d= -f2)

echo -e "Socket.IO client version: ${SOCKET_IO_CLIENT:-Unknown}"
echo -e "Socket.IO server version: ${SOCKET_IO_SERVER:-Unknown}"

if [[ -z "$SOCKET_IO_CLIENT" ]]; then
    echo -e "${YELLOW}! Could not detect Socket.IO client version in HTML${NC}"
elif [[ -z "$SOCKET_IO_SERVER" ]]; then
    echo -e "${YELLOW}! Could not detect Socket.IO server Python package${NC}"
elif [[ "${SOCKET_IO_CLIENT%%.*}" == "4" && "${SOCKET_IO_SERVER%%.*}" == "5" ]]; then
    echo -e "${GREEN}✓ Socket.IO versions are compatible (client v4, server v5)${NC}"
elif [[ "${SOCKET_IO_CLIENT%%.*}" == "${SOCKET_IO_SERVER%%.*}" ]]; then
    echo -e "${GREEN}✓ Socket.IO versions appear compatible (both major version ${SOCKET_IO_CLIENT%%.*})${NC}" 
else
    echo -e "${YELLOW}! Socket.IO versions may be incompatible${NC}"
fi

# Test 4: Verify server.py file integrity
echo -e "\n${BLUE}Testing server.py file integrity...${NC}"
python3 -m py_compile server.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ server.py compiled successfully (no syntax errors)${NC}"
else
    echo -e "${RED}✗ server.py has syntax errors!${NC}"
    exit 1
fi

# Test 5: Check start script permissions
echo -e "\n${BLUE}Testing server startup scripts...${NC}"
if [ -f "./start_minerva_server.sh" ]; then
    echo -e "${GREEN}✓ start_minerva_server.sh exists${NC}"
    if [ -x "./start_minerva_server.sh" ]; then
        echo -e "${GREEN}✓ start_minerva_server.sh is executable${NC}"
    else
        echo -e "${YELLOW}! start_minerva_server.sh is not executable. Run: chmod +x start_minerva_server.sh${NC}"
        chmod +x ./start_minerva_server.sh
        echo -e "${GREEN}✓ Fixed permissions on start_minerva_server.sh${NC}"
    fi
else
    echo -e "${RED}✗ start_minerva_server.sh not found!${NC}"
fi

echo -e "\n${BLUE}Diagnostic Tests Complete!${NC}"
echo -e "${GREEN}✓ All critical tests completed${NC}"
echo -e "${YELLOW}To start the server, run: ./start_minerva_server.sh${NC}" 