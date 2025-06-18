#!/usr/bin/env python3
"""
Automated fix for Minerva server.py to work with Python 3.13
- Replaces eventlet with threading mode
- Fixes the broken Socket.IO initialization
- Adds allowEIO3 and allowEIO4 flags for client compatibility
"""

import os
import sys
import re
import shutil
import datetime

def create_backup(filepath):
    """Create a backup of the original file"""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found")
        return False
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.bak_{timestamp}"
    
    try:
        shutil.copy2(filepath, backup_path)
        print(f"Created backup at: {backup_path}")
        return True
    except Exception as e:
        print(f"Failed to create backup: {e}")
        return False

def fix_server_py(filepath):
    """Apply fixes to server.py to make it compatible with Python 3.13"""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found")
        return False
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for the syntax error in SocketIO initialization
        broken_socketio_pattern = r"raise, cors_allowed_origins=\"\*\", logger=True, engineio_logger=True\)"
        if re.search(broken_socketio_pattern, content):
            print("Found broken SocketIO initialization")
            content = re.sub(
                broken_socketio_pattern,
                "socketio = SocketIO(app, cors_allowed_origins=\"*\", logger=True, engineio_logger=True, async_mode='threading', allowEIO3=True, allowEIO4=True)",
                content
            )
        
        # Add threading fallback for eventlet
        if "import eventlet" in content:
            print("Adding eventlet compatibility for Python 3.13")
            content = content.replace(
                "import eventlet",
                """# Eventlet is incompatible with Python 3.13 (missing 'imp' module)
# We add a graceful fallback to threading mode
try:
    import eventlet
    print("✅ Eventlet imported successfully")
except ImportError:
    print("⚠️ Eventlet not available, using threading mode instead")
"""
            )
        
        # Add fallback for eventlet monkey patching
        if "eventlet.monkey_patch()" in content:
            print("Adding fallback for eventlet monkey patching")
            content = content.replace(
                "eventlet.monkey_patch()",
                """try:
    eventlet.monkey_patch()
    print("✅ Eventlet monkey patching successful")
except (ImportError, AttributeError):
    print("⚠️ Eventlet monkey patching failed, using threading mode")
    # Continue with threading mode
"""
            )
        
        # Ensure SocketIO uses threading mode if eventlet fails
        socketio_pattern = r"socketio\s*=\s*SocketIO\(.*?\)"
        if re.search(socketio_pattern, content, re.DOTALL) and "async_mode='threading'" not in content:
            print("Updating SocketIO configuration to support threading mode")
            content = re.sub(
                socketio_pattern,
                """socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    # Fall back to threading if eventlet is not available
    async_mode='threading',
    # Support both old and new clients
    allowEIO3=True,
    allowEIO4=True,
    ping_timeout=60
)""",
                content,
                flags=re.DOTALL
            )
        
        # Add proper Socket.IO client serving
        if "@app.route('/socket.io/socket.io.js')" not in content:
            print("Adding proper Socket.IO client serving route")
            socket_io_route = """
@app.route('/socket.io/socket.io.js')
def serve_socketio_client():
    """Serve the Socket.IO client at the expected path"""
    static_dirs = ['static/js', 'web/static/js']
    
    # Look in possible locations
    for directory in static_dirs:
        js_path = os.path.join(directory, 'socket.io.min.js')
        if os.path.exists(js_path):
            return send_from_directory(os.path.dirname(js_path), 'socket.io.min.js')
    
    # If not found locally, redirect to CDN
    return '''
    console.warn("Local Socket.IO client not found, using CDN");
    document.write('<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>');
    '''
"""
            # Find a good place to insert it - after the last route
            last_route_match = re.search(r'(@app\.route.*?\n\s*def.*?:.*?)(?=\n\s*@|\n\s*if __name__|$)', content, re.DOTALL)
            if last_route_match:
                insert_pos = last_route_match.end()
                content = content[:insert_pos] + socket_io_route + content[insert_pos:]
            else:
                # If no route found, add it before if __name__ == '__main__'
                main_pattern = r"if __name__ == '__main__':"
                if re.search(main_pattern, content):
                    content = re.sub(
                        main_pattern,
                        socket_io_route + "\n" + main_pattern,
                        content
                    )
        
        # Write the changes back to the file
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"✅ Successfully applied Python 3.13 compatibility fixes to {filepath}")
        return True
    
    except Exception as e:
        print(f"Error while fixing {filepath}: {e}")
        return False

def main():
    # Default server.py path
    filepath = 'server.py'
    
    # Allow specifying a different file
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    
    print(f"Trying to fix {filepath} for Python 3.13 compatibility...")
    
    # Create backup first
    if not create_backup(filepath):
        choice = input("Failed to create backup. Continue anyway? (y/n): ")
        if choice.lower() != 'y':
            print("Aborting.")
            return
    
    # Apply fixes
    if fix_server_py(filepath):
        print("\n===== SUCCESS =====")
        print(f"Fixed {filepath} for Python 3.13 compatibility.")
        print("You can now run the server with Python 3.13 using:")
        print(f"python {filepath}")
        print("\nIf you still encounter issues, try our standalone solution:")
        print("./final_solution.sh")
    else:
        print("\n===== ERROR =====")
        print("Failed to apply fixes. Please use our standalone solution:")
        print("./final_solution.sh")

if __name__ == "__main__":
    main() 