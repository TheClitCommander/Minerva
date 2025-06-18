#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minerva Server Launcher

This script correctly launches the Minerva server from the web directory
to ensure static files are served properly.
"""

import os
import sys
import subprocess

def main():
    # Get the directory where this script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the web directory
    web_dir = os.path.join(base_dir, 'web')
    
    # Change to the web directory
    os.chdir(web_dir)
    print(f"Changing directory to: {web_dir}")
    
    # Path to the server script
    server_script = os.path.join(web_dir, 'minerva_server.py')
    
    # Verify the file exists
    if not os.path.exists(server_script):
        print(f"Error: Server script not found at {server_script}")
        return 1
    
    print(f"Starting Minerva server...")
    print(f"Once server starts, access at: http://localhost:8888/simplest_test.html")
    
    # Launch the server script
    try:
        # Use sys.executable to ensure we use the same Python interpreter
        subprocess.run([sys.executable, server_script])
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
