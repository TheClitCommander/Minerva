#!/usr/bin/env python3
"""
Quick Fix for Minerva

This script directly patches all files to fix the coordinator export issues
and Socket.IO compatibility issues in one quick operation.
"""

import os
import sys
import glob

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("==== MINERVA QUICK FIX SCRIPT ====")
print("This script will fix your Minerva installation")

# 1. Fix the multi_ai_coordinator.py file to add direct exports at the bottom
mc_file = 'web/multi_ai_coordinator.py'
if os.path.exists(mc_file):
    print(f"Fixing {mc_file}...")
    
    with open(mc_file, 'r') as f:
        content = f.read()
    
    # Check if we already have the fix
    if "# DIRECT EXPORT ADDED BY QUICK FIX" not in content:
        with open(mc_file, 'a') as f:
            f.write("\n\n# DIRECT EXPORT ADDED BY QUICK FIX\n")
            f.write("# This ensures the coordinator is available for import\n")
            f.write("coordinator = MultiAICoordinator()\n")
            f.write("Coordinator = coordinator  # Capital C for compatibility with old imports\n")
            f.write("print(f\"✅ MultiAICoordinator initialized and exported as Coordinator: {id(coordinator)}\")\n")
            f.write("print(f\"Available models: {list(coordinator.available_models.keys()) if hasattr(coordinator, 'available_models') else []}\")\n")
        print("✅ Added coordinator exports")
    else:
        print("✅ Coordinator exports already exist")

# 2. Find and fix all HTML files with Socket.IO
for html_file in glob.glob("templates/*.html") + glob.glob("web/*.html") + glob.glob("web/templates/*.html"):
    print(f"Checking {html_file}...")
    
    with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Skip if already has the fixed Socket.IO import
    if "cdn.socket.io/5.3.6/socket.io.min.js" in content:
        print(f"✅ {html_file} already has correct Socket.IO version")
        continue
        
    # Fix Socket.IO imports
    if "socket.io" in content:
        print(f"Fixing Socket.IO in {html_file}...")
        
        # Replace any Socket.IO imports with the correct version
        content = content.replace(
            'src="https://cdn.socket.io/4.7.2/socket.io.min.js"', 
            'src="https://cdn.socket.io/5.3.6/socket.io.min.js"'
        )
        content = content.replace(
            'src="https://cdn.socket.io/socket.io-4.7.2.min.js"',
            'src="https://cdn.socket.io/5.3.6/socket.io.min.js"'
        )
        content = content.replace(
            'src="/socket.io/socket.io.js"',
            'src="https://cdn.socket.io/5.3.6/socket.io.min.js"'
        )
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ Fixed Socket.IO in {html_file}")

# 3. Create a fixed run script
run_script = 'run_fixed_minerva.sh'
print(f"Creating {run_script}...")

with open(run_script, 'w') as f:
    f.write("""#!/bin/bash
# Fixed Minerva Run Script
# Created by quick_fix.py

# Kill any existing server
pkill -f server.py 2>/dev/null || true

# Add dummy API keys for testing
export OPENAI_API_KEY="sk-test12345678901234567890123456789012345678"
export ANTHROPIC_API_KEY="sk-ant-api12345678901234567890123456789012345"
export MISTRAL_API_KEY="test12345678901234567890123456789012345"

# Enable debugging
export PYTHONUNBUFFERED=1

# Clear Python cache to ensure new changes are loaded
find . -name "__pycache__" -type d -exec rm -rf {} +  2>/dev/null || true
find . -name "*.pyc" -delete  2>/dev/null || true

# Ensure we're using the updated code
echo "Starting fixed Minerva server..."
python server.py
""")

# Make the script executable
os.chmod(run_script, 0o755)
print(f"✅ Created {run_script}")

print("\n==== FIXES COMPLETE ====")
print("To run the fixed server, use:")
print(f"  ./{run_script}")
print("\nThis should fix all coordination and Socket.IO issues!") 