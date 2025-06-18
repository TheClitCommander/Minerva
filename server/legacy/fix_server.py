#!/usr/bin/env python3
"""
Automated fix for server.py with the broken Socket.IO initialization
"""

import os
import sys
import re
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the file before modifying it"""
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        return False
    
    backup_path = f"{filepath}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"Created backup at {backup_path}")
    return True

def fix_socketio_initialization(filepath):
    """Fix the broken Socket.IO initialization in server.py"""
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        return False
    
    # Read the entire file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Look for the broken initialization pattern
    broken_pattern = r"raise, cors_allowed_origins=\"\*\", logger=True, engineio_logger=True\)"
    
    if not re.search(broken_pattern, content):
        print("The broken pattern was not found. The file might be already fixed or have a different issue.")
        return False
    
    # Fix the broken initialization
    fixed_content = re.sub(
        broken_pattern,
        "socketio = SocketIO(app, cors_allowed_origins=\"*\", logger=True, engineio_logger=True, async_mode='threading')",
        content
    )
    
    # Add the engineio compatibility flags
    if "async_mode='threading'" in fixed_content and "allowEIO" not in fixed_content:
        # Find the socketio initialization and add the compatibility flags
        socketio_pattern = r"socketio = SocketIO\(app, cors_allowed_origins=\"\*\", logger=True, engineio_logger=True, async_mode='threading'\)"
        fixed_content = re.sub(
            socketio_pattern,
            "socketio = SocketIO(app, cors_allowed_origins=\"*\", logger=True, engineio_logger=True, async_mode='threading',\n               allowEIO3=True, allowEIO4=True)",
            fixed_content
        )
    
    # Check if we need to switch from eventlet to threading
    if "import eventlet" in fixed_content:
        # Add note about eventlet incompatibility with Python 3.13
        fixed_content = fixed_content.replace(
            "import eventlet",
            "# Note: eventlet is incompatible with Python 3.13 (fails with 'imp' module not found)\n# We use threading mode instead\nimport eventlet"
        )
        
        # Add threading fallback
        if "eventlet.monkey_patch()" in fixed_content and "# Fallback to threading" not in fixed_content:
            fixed_content = fixed_content.replace(
                "eventlet.monkey_patch()",
                "try:\n    eventlet.monkey_patch()\n    print('✅ Eventlet monkey patching successful')\nexcept ImportError:\n    print('⚠️ Eventlet not available, using threading mode instead')\n    # Fallback to threading mode"
            )
    
    # Write the fixed content back to the file
    with open(filepath, 'w') as f:
        f.write(fixed_content)
    
    print(f"Fixed Socket.IO initialization in {filepath}")
    return True

def main():
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = 'server.py'
    
    print(f"Attempting to fix Socket.IO initialization in {filepath}...")
    
    # Create backup
    if not backup_file(filepath):
        return
    
    # Fix the file
    if fix_socketio_initialization(filepath):
        print("Successfully fixed the Socket.IO initialization.")
        print("You should now be able to run the server with Python 3.13.")
        print("\nTo run the server, use:")
        print("  python server.py")
    else:
        print("Failed to fix the Socket.IO initialization.")
        print("Please check the file manually or use our diagnostic server instead.")

if __name__ == "__main__":
    main() 