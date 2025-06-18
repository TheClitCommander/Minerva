#!/bin/bash
# Minerva AI Setup Script
# This script sets up the Minerva AI system with all required dependencies

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Minerva AI Setup Script ===${NC}"
echo -e "${BLUE}This script will install all dependencies for Minerva's multi-model AI system${NC}"

# Check if Python is installed
if command -v python3 &>/dev/null; then
    python_version=$(python3 --version)
    echo -e "${GREEN}✓ Python is installed: ${python_version}${NC}"
else
    echo -e "${RED}✗ Python 3 is not installed. Please install Python 3.9 or higher.${NC}"
    exit 1
fi

# Check for pip
if command -v pip3 &>/dev/null; then
    echo -e "${GREEN}✓ pip is installed${NC}"
else
    echo -e "${RED}✗ pip is not installed. Installing pip...${NC}"
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi

# Check for virtual environment
if [ -d "fresh_venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
else
    echo -e "${YELLOW}! Creating new virtual environment...${NC}"
    python3 -m venv fresh_venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source fresh_venv/bin/activate

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${BLUE}Installing Minerva dependencies...${NC}"
pip install --upgrade -r requirements.txt

# Install specialized ML libraries
echo -e "${BLUE}Installing specialized AI dependencies...${NC}"
pip install --upgrade transformers huggingface_hub gpt4all langchain loguru psutil

# Check for torch and install if needed
if python3 -c "import torch" &>/dev/null; then
    echo -e "${GREEN}✓ PyTorch is installed${NC}"
else
    echo -e "${YELLOW}! Installing PyTorch...${NC}"
    pip install torch torchvision torchaudio
fi

# Check for bitsandbytes (for 8-bit quantization)
if python3 -c "import bitsandbytes" &>/dev/null; then
    echo -e "${GREEN}✓ bitsandbytes is installed${NC}"
else
    echo -e "${YELLOW}! Installing bitsandbytes for model quantization...${NC}"
    pip install bitsandbytes
fi

echo -e "${GREEN}✓ All dependencies installed successfully!${NC}"

# Verify installation
echo -e "${BLUE}Verifying installation...${NC}"
python3 verify_models.py

echo -e "${BLUE}=== Minerva AI Setup Complete ===${NC}"
echo -e "${BLUE}To start Minerva, run:${NC}"
echo -e "${GREEN}source fresh_venv/bin/activate && python run_minerva.py${NC}"
