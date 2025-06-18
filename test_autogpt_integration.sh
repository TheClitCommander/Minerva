#!/bin/bash
# AutoGPT Integration Test Script for Minerva
# This script runs a sequence of tests to verify AutoGPT integration

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print info message
print_info() {
    echo -e "${YELLOW}• $1${NC}"
}

# Change to Minerva directory
cd "$(dirname "$0")"
print_header "Running AutoGPT Integration Tests from $(pwd)"

# Activate virtual environment
if [ -d "fresh_venv" ]; then
    print_info "Activating virtual environment..."
    source fresh_venv/bin/activate
    if [ $? -eq 0 ]; then
        print_success "Virtual environment activated successfully"
    else
        print_error "Failed to activate virtual environment"
        exit 1
    fi
else
    print_error "Virtual environment not found. Please run setup.py first."
    exit 1
fi

# Verify Python version
print_info "Checking Python version..."
python --version
if [ $? -ne 0 ]; then
    print_error "Python not found"
    exit 1
fi

# Step 1: Run AutoGPT integration unit tests
print_header "Running AutoGPT Integration Unit Tests"
python run_tests.py --type autogpt --verbose
if [ $? -eq 0 ]; then
    print_success "AutoGPT integration unit tests passed"
else
    print_error "AutoGPT integration unit tests failed"
    exit 1
fi

# Step 2: Start Minerva in the background
print_header "Starting Minerva Server"
# Check if port 5001 is already in use
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    print_info "Port 5001 is already in use. Killing existing process..."
    kill $(lsof -Pi :5001 -sTCP:LISTEN -t)
    sleep 2
fi

print_info "Starting Minerva in the background..."
python run_minerva.py --debug --port 5001 > minerva_server.log 2>&1 &
MINERVA_PID=$!
print_success "Minerva started with PID: $MINERVA_PID"

# Wait for server to start
print_info "Waiting for server to start..."
sleep 5

# Verify server is running
if ! kill -0 $MINERVA_PID > /dev/null 2>&1; then
    print_error "Minerva server failed to start. Check minerva_server.log for details."
    cat minerva_server.log
    exit 1
fi
print_success "Minerva server is running"

# Step 3: Run WebSocket test client
print_header "Running WebSocket Test Client"
print_info "Testing WebSocket communication with AutoGPT..."
python tests/test_websocket_with_autogpt.py http://localhost:5001
WEBSOCKET_RESULT=$?

# Step 4: Cleanup
print_header "Cleaning Up"
print_info "Stopping Minerva server..."
kill $MINERVA_PID
wait $MINERVA_PID 2>/dev/null
print_success "Minerva server stopped"

# Final report
print_header "Test Summary"
if [ $WEBSOCKET_RESULT -eq 0 ]; then
    print_success "WebSocket tests completed successfully"
else
    print_error "WebSocket tests failed"
fi

if [ $WEBSOCKET_RESULT -eq 0 ]; then
    print_success "ALL TESTS PASSED"
    exit 0
else
    print_error "SOME TESTS FAILED"
    exit 1
fi
