#!/bin/bash
# Start Minerva server with proper environment setup

# Set to exit on error
set -e

# Define colors for output
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# Default values
PORT=9876
DEBUG=0
VENV_PATH="fresh_venv"

# Help message
function show_help {
    echo -e "${BLUE}Minerva Server Starter${NC}"
    echo "Usage: ./start_minerva.sh [options]"
    echo
    echo "Options:"
    echo "  -p, --port PORT    Specify port (default: 9876)"
    echo "  -d, --debug        Enable debug mode"
    echo "  -v, --venv PATH    Virtual environment path (default: fresh_venv)"
    echo "  -h, --help         Show this help message"
    echo
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG=1
            shift
            ;;
        -v|--venv)
            VENV_PATH="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_PATH${NC}"
    echo -e "Run setup_venv.sh first or specify correct path with -v option"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Check for eventlet
if ! pip list | grep -q eventlet; then
    echo -e "${YELLOW}Installing eventlet...${NC}"
    pip install eventlet
fi

# Build debug flag
DEBUG_FLAG=""
if [ $DEBUG -eq 1 ]; then
    DEBUG_FLAG="--debug"
    echo -e "${YELLOW}Running in debug mode${NC}"
fi

# Start server
echo -e "${GREEN}Starting Minerva server on port $PORT...${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"

python run_minerva.py --port "$PORT" $DEBUG_FLAG
