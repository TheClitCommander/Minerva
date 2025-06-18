#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Minerva server...${NC}"

# Read server PID from file if exists
if [ -f .minerva_server.pid ]; then
    PID=$(cat .minerva_server.pid)
    if ps -p $PID > /dev/null; then
        echo -e "${YELLOW}Sending graceful termination signal to process ${PID}...${NC}"
        kill $PID
        sleep 2
        
        # Check if process still exists
        if ps -p $PID > /dev/null; then
            echo -e "${YELLOW}Process still running, sending force kill signal...${NC}"
            kill -9 $PID
            sleep 1
        fi
        
        if ! ps -p $PID > /dev/null; then
            echo -e "${GREEN}✅ Server stopped successfully.${NC}"
            rm .minerva_server.pid
        else
            echo -e "${RED}❌ Failed to stop server process ${PID}.${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}Process ${PID} not found. It may have already terminated.${NC}"
        rm .minerva_server.pid
    fi
else
    # Try to find and kill any server.py processes
    echo -e "${YELLOW}No PID file found. Attempting to find and stop all server.py processes...${NC}"
    PIDS=$(pgrep -f "python.*server\.py")
    
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}Found server processes: ${PIDS}${NC}"
        pkill -f "python.*server\.py"
        sleep 2
        
        # Check if any processes still exist
        REMAINING=$(pgrep -f "python.*server\.py")
        if [ -n "$REMAINING" ]; then
            echo -e "${YELLOW}Some processes still running, sending force kill...${NC}"
            pkill -9 -f "python.*server\.py"
            sleep 1
        fi
        
        if [ -z "$(pgrep -f "python.*server\.py")" ]; then
            echo -e "${GREEN}✅ All server processes stopped successfully.${NC}"
        else
            echo -e "${RED}❌ Failed to stop some server processes.${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}No running server processes found.${NC}"
    fi
fi

echo -e "${GREEN}Server shutdown complete.${NC}" 