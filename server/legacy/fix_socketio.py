#!/usr/bin/env python3
"""
Minerva Socket.IO Connection Fix
This script fixes Socket.IO connection issues by properly configuring eventlet
and setting up compatible server/client configurations.
"""

import os
import sys
import shutil
import subprocess

def run_command(cmd):
    """Run a shell command and return the output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def main():
    print("\n\033[1;36m================================\033[0m")
    print("\033[1;36m  Minerva Socket.IO Connection Fix\033[0m")
    print("\033[1;36m================================\033[0m\n")
    
    # Step 1: Install or upgrade eventlet
    print("Step 1: Installing/upgrading eventlet...")
    if not run_command("pip install eventlet --upgrade"):
        print("Failed to install eventlet. Please install it manually.")
        return False
    
    # Step 2: Verify the Flask-SocketIO installation
    print("\nStep 2: Verifying Flask-SocketIO installation...")
    if not run_command("pip install flask-socketio==5.3.4 --upgrade"):
        print("Failed to install Flask-SocketIO. Please install it manually.")
        return False
    
    # Step 3: Create static directory if it doesn't exist
    static_js_dir = os.path.join("web", "static", "js")
    os.makedirs(static_js_dir, exist_ok=True)
    print(f"\nStep 3: Created static directory at {static_js_dir}")
    
    # Step 4: Download the correct Socket.IO client version
    socketio_js_path = os.path.join(static_js_dir, "socket.io.min.js")
    print("\nStep 4: Downloading compatible Socket.IO client...")
    if not run_command(f"curl -s https://cdn.socket.io/4.6.0/socket.io.min.js -o {socketio_js_path}"):
        print("Failed to download Socket.IO client. Please download it manually.")
        return False
    
    # Step 5: Fix server.py to properly initialize Socket.IO
    print("\nStep 5: Fixing server.py to properly initialize Socket.IO...")
    
    if os.path.exists("server.py"):
        # Backup server.py
        shutil.copy2("server.py", "server.py.bak")
        print("Created backup at server.py.bak")
        
        with open("server.py", "r") as f:
            content = f.read()
        
        # Fix create_socketio_server function
        if "def create_socketio_server" in content:
            # Replace the function with a more compatible version
            import re
            socketio_init_pattern = r"def create_socketio_server\([^)]*\):.*?return socketio"
            socketio_init_replacement = """def create_socketio_server(app, async_mode='eventlet'):
    \"\"\"Create and configure the SocketIO server with the app\"\"\"
    try:
        # Make sure to import eventlet and do the monkey patching
        import eventlet
        eventlet.monkey_patch()
        
        socketio = SocketIO(
            app, 
            async_mode=async_mode,
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True,
            # Critical compatibility parameters
            always_connect=True,
            allowEIO3=True,
            allowEIO4=True,
            ping_timeout=60,
            ping_interval=25
        )
        return socketio
    except Exception as e:
        print(f"Error creating SocketIO server: {e}")
        raise"""
            
            # Use regex with re.DOTALL to match across multiple lines
            modified_content = re.sub(socketio_init_pattern, socketio_init_replacement, content, flags=re.DOTALL)
            
            # Fix the socket.io client serving routes
            socketio_route_pattern = r"@app\.route\('\/socket\.io\/socket\.io\.js'\).*?return send_from_directory\([^)]*\)"
            socketio_route_replacement = """@app.route('/socket.io/socket.io.js')
def serve_socketio_client():
    \"\"\"Serve the Socket.IO client library at the default path\"\"\"
    return send_from_directory('web/static/js', 'socket.io.min.js')"""
            
            modified_content = re.sub(socketio_route_pattern, socketio_route_replacement, modified_content, flags=re.DOTALL)
            
            with open("server.py", "w") as f:
                f.write(modified_content)
            
            print("Updated server.py with compatible Socket.IO configuration")
        else:
            print("Could not find create_socketio_server function in server.py")
            return False
    else:
        print("server.py not found!")
        return False
    
    # Step 6: Create a script to ensure proper initialization sequence
    print("\nStep 6: Creating a guaranteed startup script...")
    with open("run_fixed_socketio_server.sh", "w") as f:
        f.write("""#!/bin/bash

echo -e "\\n\\033[1;36m==========================================="
echo "   🚀 Starting Minerva with Socket.IO Fix   "
echo -e "===========================================\\033[0m\\n"

# Kill any existing server processes
pkill -f server.py || true
sleep 2

# Clear Python cache
find . -name "__pycache__" -exec rm -rf {} +  2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Set required environment variables
export FLASK_DEBUG=1
export SOCKETIO_DEBUG=1

# Activate virtual environment if it exists
if [ -d "venv_minerva" ]; then
    echo "🔄 Activating Python virtual environment..."
    source venv_minerva/bin/activate
fi

# Execute with the correct parameters
python server.py
""")
    
    os.chmod("run_fixed_socketio_server.sh", 0o755)
    print("Created run_fixed_socketio_server.sh script")
    
    print("\n\033[1;32m✅ Socket.IO fixes applied successfully!\033[0m")
    print("\033[1;32mRun ./run_fixed_socketio_server.sh to start the server with the fixes.\033[0m\n")
    
    return True

if __name__ == "__main__":
    main() 