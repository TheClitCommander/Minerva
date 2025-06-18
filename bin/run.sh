#!/bin/bash
"""
Minerva Launch Wrapper

Simple shell wrapper for the Python launcher.
"""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Run the Python launcher
python3 "$SCRIPT_DIR/launch_minerva.py" "$@" 