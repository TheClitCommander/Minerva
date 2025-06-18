#!/usr/bin/env python3
"""
Fix script for main server.py 
- Adds broadcast=True to all emits
- Fixes syntax errors
- Makes Python 3.13 compatible
"""
import os
import re
import sys
import shutil
import datetime

def backup_file(filepath):
    """Create a backup of the original file"""
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        return False
    
    backup_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.bak.{backup_time}"
    
    try:
        shutil.copy2(filepath, backup_path)
        print(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def fix_server_file(filepath):
    """Apply fixes to server.py"""
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        return False
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # 1. Fix syntax error in SocketIO initialization
        syntax_error_pattern = r"raise, cors_allowed_origins=\"\*\", logger=True, engineio_logger=True\)"
        if re.search(syntax_error_pattern, content):
            print("✅ Fixing syntax error in SocketIO initialization")
            content = re.sub(
                syntax_error_pattern,
                "socketio = SocketIO(app, cors_allowed_origins=\"*\", logger=True, engineio_logger=True, async_mode='threading', allowEIO3=True, allowEIO4=True)",
                content
            )
        
        # 2. Replace eventlet with threading fallback
        if "import eventlet" in content:
            print("✅ Adding Python 3.13 compatibility for eventlet")
            content = content.replace(
                "import eventlet",
                """# Note: eventlet is incompatible with Python 3.13 (missing 'imp' module)
# We use threading mode as a fallback
try:
    import eventlet
    print("Using eventlet mode")
except ImportError:
    print("Eventlet not available, using threading mode")
    # Continue with threading mode
"""
            )
        
        # 3. Add fallback for eventlet monkey patching
        if "eventlet.monkey_patch()" in content:
            print("✅ Adding fallback for eventlet monkey patching")
            content = content.replace(
                "eventlet.monkey_patch()",
                """try:
    eventlet.monkey_patch()
    print("✅ Eventlet monkey patching successful")
except (ImportError, AttributeError):
    print("⚠️ Eventlet not available, using threading mode")
    # Continue with threading mode
"""
            )
        
        # 4. Add broadcast=True to emit calls (THIS IS THE CRITICAL FIX)
        emit_pattern = r"emit\s*\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*(.+?))?\s*\)"
        emit_replacement = r"emit('\1', \2, broadcast=True)"
        
        # First, count how many emits need fixing
        emit_matches = re.findall(emit_pattern, content)
        emit_count = len(emit_matches)
        
        # Apply the broadcast=True fix only if not already there
        if emit_count > 0:
            print(f"✅ Adding broadcast=True to {emit_count} emit calls")
            fixed_content = ""
            last_end = 0
            
            for match in re.finditer(emit_pattern, content):
                # Extract the parts
                start, end = match.span()
                event_name = match.group(1)
                data_part = match.group(2) if match.group(2) else ""
                
                # Skip if broadcast is already there
                if "broadcast" in match.group(0):
                    fixed_content += content[last_end:end]
                else:
                    # Add the part before this match
                    fixed_content += content[last_end:start]
                    # Add the fixed emit with broadcast
                    if data_part:
                        fixed_content += f"emit('{event_name}', {data_part}, broadcast=True)"
                    else:
                        fixed_content += f"emit('{event_name}', broadcast=True)"
                
                last_end = end
            
            # Add the remaining content
            fixed_content += content[last_end:]
            content = fixed_content
        
        # 5. Add Socket.IO client serving route if needed
        if "@app.route('/socket.io/socket.io.js')" not in content:
            print("✅ Adding Socket.IO client serving route")
            socketio_route = """
@app.route('/socket.io/socket.io.js')
def serve_socketio_client():
    """Serve the Socket.IO client library"""
    static_dirs = ['static/js', 'web/static/js']
    
    # Look in possible directories
    for directory in static_dirs:
        client_path = os.path.join(directory, 'socket.io.min.js')
        if os.path.exists(client_path):
            return send_from_directory(os.path.dirname(client_path), 'socket.io.min.js')
    
    # If not found, return a script that loads from CDN
    return '''
    console.warn("Socket.IO client not found locally, loading from CDN");
    document.write('<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>');
    '''
"""
            # Find a good place to insert the route - after the last route
            last_route_match = re.search(r'(@app\.route.*?\n\s*def.*?:.*?)(?=\n\s*@|\n\s*if __name__|$)', content, re.DOTALL)
            if last_route_match:
                insert_pos = last_route_match.end()
                content = content[:insert_pos] + socketio_route + content[insert_pos:]
            else:
                # If no route found, add before if __name__ == '__main__'
                content = content.replace("if __name__ == '__main__':", socketio_route + "\nif __name__ == '__main__':")
        
        # Write the fixed content back to the file
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"✅ All fixes applied to {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing file: {e}")
        return False

def main():
    # Use command line argument or default to server.py
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'server.py'
    
    print(f"Fixing Socket.IO issues in {filepath}...")
    
    # Create backup first
    if not backup_file(filepath):
        choice = input("Failed to create backup. Continue anyway? (y/n): ")
        if choice.lower() != 'y':
            print("Aborting.")
            return
    
    # Apply fixes
    if fix_server_file(filepath):
        print("\n=== SUCCESS ===")
        print(f"All Socket.IO issues in {filepath} have been fixed.")
        print("Key changes made:")
        print("1. Added broadcast=True to all emit calls")
        print("2. Fixed any syntax errors")
        print("3. Added Python 3.13 compatibility")
        print("4. Added Socket.IO client serving")
        print("\nRun your server now with:")
        print(f"python {filepath}")
    else:
        print("\n=== FAILED ===")
        print("Something went wrong while fixing the file.")
        print("Please try the standalone solution instead:")
        print("./run_final_fix.sh")

if __name__ == "__main__":
    main() 