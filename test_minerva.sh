#!/bin/bash
# Minerva Test Launcher - Shell Wrapper

echo "🌟 Starting Minerva Test Launcher..."
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

# Run the Python launcher
python3 test_minerva.py

echo ""
echo "🚀 Minerva Test Launcher finished." 