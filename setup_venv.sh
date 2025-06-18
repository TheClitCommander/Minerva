#!/bin/bash
# Minerva AI - Virtual Environment Setup Script

# Exit on error
set -e

echo "==== Minerva AI - Virtual Environment Setup ===="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install base requirements
echo "Installing base requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Install optional dependencies
echo
echo "Do you want to install optional dependencies? (y/n)"
read -p "> " install_optional

if [[ $install_optional == "y" || $install_optional == "Y" ]]; then
    echo "Installing document processing dependencies..."
    pip install PyPDF2 python-docx
    
    echo "Installing embedding model dependencies..."
    pip install sentence-transformers
fi

# Create instance directory for uploads
echo "Creating instance directory..."
mkdir -p instance/uploads

echo
echo "==== Setup Complete ===="
echo "To activate the virtual environment, run:"
echo "source venv/bin/activate"
echo
echo "To start the web interface, run:"
echo "python run_web_interface.py"
echo
echo "Navigate to http://127.0.0.1:5000 in your web browser."
