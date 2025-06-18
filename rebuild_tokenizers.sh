#!/bin/bash
# Script to rebuild tokenizers and transformers for Minerva

set -e  # Exit on error

echo "===== Minerva Dependency Rebuild Script ====="
echo "This script will rebuild the tokenizers and transformers packages"

# Activate the virtual environment
if [ -d "fresh_venv" ]; then
    echo "Activating virtual environment..."
    source fresh_venv/bin/activate
else
    echo "Error: fresh_venv directory not found!"
    exit 1
fi

# Ensure pip is up to date
echo "Upgrading pip..."
pip install --upgrade pip

# Completely remove problematic packages
echo "Removing existing packages..."
pip uninstall -y tokenizers transformers huggingface-hub safetensors

# Install rust (needed for tokenizers compilation)
echo "Checking if Rust is installed..."
if ! command -v rustc &> /dev/null; then
    echo "Rust not found, installing..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
else
    echo "Rust is already installed"
    rustc --version
fi

# Install build tools
echo "Installing build dependencies..."
pip install setuptools-rust wheel build

# Install packages in the correct order with specific versions
echo "Installing huggingface-hub..."
pip install huggingface-hub==0.16.4

echo "Installing tokenizers from source..."
pip install git+https://github.com/huggingface/tokenizers.git@v0.13.3

echo "Installing other dependencies..."
pip install einops>=0.6.1 safetensors>=0.3.1

echo "Installing transformers with specific version..."
pip install transformers==4.29.2

echo "Verifying installations..."
python -c "import tokenizers; print(f'tokenizers version: {tokenizers.__version__}')"
python -c "import transformers; print(f'transformers version: {transformers.__version__}')"

echo "===== Rebuilding Dependencies Complete! ====="
echo "You can now try running Minerva again with: python run_minerva.py"
