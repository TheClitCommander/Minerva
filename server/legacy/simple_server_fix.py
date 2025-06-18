#!/usr/bin/env python3
"""
Fix Socket.IO compatibility issues in Minerva
"""
import os
import subprocess
import shutil

def run_command(cmd, silent=False):
    """Run a shell command and print output"""
    if not silent:
        print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and not silent:
        print(f"Error: {result.stderr}")
    return result.returncode == 0

def main():
    print("\n\033[1;36m=== Minerva Socket.IO Compatibility Fix ===\033[0m\n")
    
    # 1. Install compatible Socket.IO versions
    print("Step 1: Installing compatible Socket.IO packages...")
    run_command("pip install python-socketio==5.7.2 python-engineio==4.3.4 flask-socketio==5.3.2 --force-reinstall")
    
    # 2. Create needed directories
    os.makedirs("web/static/js", exist_ok=True)
    
    # 3. Download compatible Socket.IO client
    print("\nStep 2: Downloading compatible Socket.IO client...")
    client_path = "web/static/js/socket.io.min.js"
    run_command(f"curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o {client_path}")
    
    # 4. Backup server.py
    if os.path.exists("server.py"):
        shutil.copy2("server.py", "server.py.bak")
        print("Created backup at server.py.bak")
    
    # 5. Fix server route for Socket.IO client
    print("\nStep 3: Adding Socket.IO client route to server.py...")
    with open("server.py", "r") as f:
        content = f.read()
    
    # Ensure we have a route to serve the Socket.IO client
    socket_route = """
@app.route('/socket.io/socket.io.js')
def serve_socketio_client():
    return send_from_directory('web/static/js', 'socket.io.min.js')

@app.route('/chat-fix.js')
def serve_chat_fix():
    return send_from_directory('web', 'chat-fix.js')
"""
    
    if "@app.route('/socket.io/socket.io.js')" not in content:
        # Insert after the first app route definition
        import re
        route_pattern = r'(@app\.route\(.*?\)[\s\n]*?def [^:]+:)'
        match = re.search(route_pattern, content, re.DOTALL)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + "\n" + socket_route + content[insert_pos:]
        else:
            # If no route found, add before the if __name__ == "__main__" block
            if "__name__" in content:
                main_pos = content.find("if __name__")
                content = content[:main_pos] + socket_route + "\n\n" + content[main_pos:]
            else:
                # Append to the end if nothing else works
                content += "\n" + socket_route
    
    # 6. Fix the SocketIO initialization
    socketio_init = """
def create_socketio_server(app, async_mode='eventlet'):
    try:
        # Import and monkey patch eventlet
        import eventlet
        eventlet.monkey_patch()
        
        return SocketIO(
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
    except Exception as e:
        print(f"Error creating SocketIO server: {e}")
        raise
"""
    
    if "create_socketio_server" in content:
        import re
        init_pattern = r'def create_socketio_server\([^)]*\):.*?return .*?SocketIO\(.*?\)'
        found = re.search(init_pattern, content, re.DOTALL)
        if found:
            content = content.replace(found.group(0), socketio_init.strip())
        else:
            print("Could not find SocketIO initialization to replace")
    else:
        print("No create_socketio_server function found to replace")
    
    # Save changes
    with open("server.py", "w") as f:
        f.write(content)
    
    # 7. Create a run script
    print("\nStep 4: Creating a fixed server run script...")
    with open("run_fixed_server.sh", "w") as f:
        f.write("""#!/bin/bash

# Kill any existing server processes
pkill -f server.py || true

# Clear Python cache files
find . -name "__pycache__" -exec rm -rf {} +  2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Ensure Socket.IO client script is available
if [ ! -f "web/static/js/socket.io.min.js" ]; then
    echo "Downloading Socket.IO client..."
    mkdir -p web/static/js
    curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o web/static/js/socket.io.min.js
fi

# Activate virtual environment if it exists
if [ -d "venv_minerva" ]; then
    source venv_minerva/bin/activate
fi

# Run the server
python server.py
""")
    
    # Make the script executable
    os.chmod("run_fixed_server.sh", 0o755)
    
    print("\n\033[1;32m✅ Fix complete!\033[0m")
    print("\033[1;32mRun ./run_fixed_server.sh to start the server with fixed Socket.IO.\033[0m\n")

if __name__ == "__main__":
    main() 