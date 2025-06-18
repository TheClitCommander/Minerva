#!/usr/bin/env python3
"""
Socket.IO Compatibility Route Fixer
This script directly modifies server.py to add Socket.IO compatibility routes.
"""

import os
import shutil
import re

SERVER_FILE = 'server.py'
BACKUP_FILE = 'server.py.backup'

def main():
    # Make backup
    shutil.copy2(SERVER_FILE, BACKUP_FILE)
    print(f"✅ Created backup at {BACKUP_FILE}")
    
    # Read the server file
    with open(SERVER_FILE, 'r') as f:
        content = f.read()
    
    # Check if routes already exist
    if "@app.route('/socket.io/socket.io.js')" in content:
        print("⚠️ Socket.IO route already exists")
        return
    
    # Find a good insertion point
    route_match = re.search(r'@app\.route\(.*?\)\s+def', content)
    if not route_match:
        print("❌ Could not find a route to use as reference point")
        return
    
    insertion_point = route_match.start()
    
    # Prepare the routes to add
    routes_to_add = """
# Socket.IO compatibility routes
@app.route('/socket.io/socket.io.js')
def serve_socketio_js():
    # Serve a compatible version of Socket.IO
    return redirect("https://cdn.socket.io/4.7.2/socket.io.min.js")

@app.route('/compatible-socket.io.js')
def serve_compatible_socketio_js():
    # Serve a compatible version of Socket.IO
    return redirect("https://cdn.socket.io/4.7.2/socket.io.min.js")

"""
    
    # Insert the routes
    new_content = content[:insertion_point] + routes_to_add + content[insertion_point:]
    
    # Write the modified file
    with open(SERVER_FILE, 'w') as f:
        f.write(new_content)
    
    print("✅ Added Socket.IO compatibility routes to server.py")
    
    # Fix the SocketIO initialization to add allowEIO3 and allowEIO4
    if "allowEIO3=True" not in content and "socketio = SocketIO(" in content:
        with open(SERVER_FILE, 'r') as f:
            content = f.read()
        
        # Find the SocketIO initialization
        socketio_match = re.search(r'socketio\s*=\s*SocketIO\(.*?\)', content, re.DOTALL)
        if socketio_match:
            old_init = socketio_match.group(0)
            if old_init.strip().endswith(')'):
                # Add the compatibility parameters
                new_init = old_init[:-1]
                if not new_init.endswith(','):
                    new_init += ','
                new_init += """
    # Critical Socket.IO compatibility options
    allowEIO3=True,
    allowEIO4=True,
    always_connect=True
)"""
                new_content = content.replace(old_init, new_init)
                
                # Write the modified file
                with open(SERVER_FILE, 'w') as f:
                    f.write(new_content)
                
                print("✅ Updated SocketIO initialization with compatibility parameters")
            else:
                print("⚠️ Could not update SocketIO initialization - unexpected format")
        else:
            print("⚠️ Could not find SocketIO initialization")
    else:
        print("ℹ️ SocketIO already has compatibility parameters")
    
    print("\n✅ All done! Restart the server for changes to take effect.")

if __name__ == "__main__":
    main() 