#!/bin/bash

# Test HuggingFace integration in the Minerva Think Tank

# Add color to output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}   Testing HuggingFace Integration    ${NC}"
echo -e "${BLUE}======================================${NC}"

# Set up the HuggingFace API key
export HUGGINGFACE_API_KEY="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"

# Activate virtual environment
if [ -d "./venv_minerva" ]; then
    echo -e "${GREEN}Using existing virtual environment${NC}"
    source ./venv_minerva/bin/activate
else
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Please run setup_minerva.sh first"
    exit 1
fi

# Make sure required packages are installed
echo -e "${YELLOW}Installing required packages...${NC}"
pip install -q requests

# Run the test script
echo -e "${GREEN}Running HuggingFace integration test...${NC}"
./test_huggingface.py

# Check the result
if [ $? -eq 0 ]; then
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}✅ HuggingFace integration test passed!${NC}"
    echo -e "${GREEN}======================================${NC}"
else
    echo -e "${RED}======================================${NC}"
    echo -e "${RED}❌ HuggingFace integration test failed${NC}"
    echo -e "${RED}======================================${NC}"
fi 