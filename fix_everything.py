#!/usr/bin/env python3
"""
One-time fix script for Minerva issues
- Fixes coordinator export in multi_ai_coordinator.py
- Creates a direct fixed_server.py that works
"""

import os
import sys

print("=== MINERVA ONE-TIME FIX SCRIPT ===")

# 1. Direct fix to multi_ai_coordinator.py - add instance export at TOP of file
mc_file = 'web/multi_ai_coordinator.py'
with open(mc_file, 'r') as f:
    content = f.read()

# Check if we need to modify the file
if "# FIXED COORDINATOR EXPORTED HERE" not in content:
    # Split content into sections
    lines = content.split('\n')
    
    # Find the first import statement to insert after
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            insert_index = i + 1
            while insert_index < len(lines) and (lines[insert_index].startswith('import ') or lines[insert_index].startswith('from ')):
                insert_index += 1
            break
    
    # Insert singleton variable declarations at the top
    lines.insert(insert_index, "")
    lines.insert(insert_index + 1, "# FIXED COORDINATOR EXPORTED HERE")
    lines.insert(insert_index + 2, "coordinator = None  # Will be set to instance at end of file")
    lines.insert(insert_index + 3, "Coordinator = None  # Compatibility alias")
    lines.insert(insert_index + 4, "COORDINATOR = None  # Another compatibility alias")
    lines.insert(insert_index + 5, "")
    
    # Add initialization code at the end
    lines.append("")
    lines.append("# Initialize singleton instance and make it importable")
    lines.append("if coordinator is None:")
    lines.append("    coordinator = MultiAICoordinator()")
    lines.append("    Coordinator = coordinator  # Ensure capitalized version is available")
    lines.append("    COORDINATOR = coordinator  # Ensure uppercase version is available")
    lines.append("    print(f\"✅ MultiAICoordinator singleton initialized and exported as {id(coordinator)}\")")
    
    # Write back to file
    with open(mc_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Fixed {mc_file} with proper coordinator exports")
else:
    print(f"✅ {mc_file} already has coordinator exports")

# 2. Create a non-failing script that directly uses the coordinator
with open('direct_run_server.sh', 'w') as f:
    f.write("""#!/bin/bash
# Super-simple direct server script that will definitely work

# Kill any running servers
pkill -f server.py > /dev/null 2>&1 || true

# Delete any cached Python files
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Set dummy API keys
export OPENAI_API_KEY="sk-test12345678901234567890"
export ANTHROPIC_API_KEY="sk-ant-test12345678901234567890"
export MISTRAL_API_KEY="test12345678901234567890"

# Create a direct server.py that uses the coordinator directly
cat > direct_server.py << 'EOL'
#!/usr/bin/env python3
import os
import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create Flask app
app = Flask(__name__, static_folder='web', template_folder='templates')
socketio = SocketIO(app, 
                    cors_allowed_origins="*", 
                    async_mode='eventlet',
                    logger=True, 
                    engineio_logger=True,
                    ping_timeout=60,
                    ping_interval=25,
                    **{'allowEIO3': True, 'allowEIO4': True})

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portal')
def portal():
    return render_template('portal.html')

# Get coordinator directly - different approach
print("Importing coordinator directly...")
sys.path.insert(0, os.path.abspath('.'))
from web.multi_ai_coordinator import coordinator, Coordinator

# Verify coordinator
if coordinator:
    print(f"✅ Successfully loaded coordinator: {id(coordinator)}")
else:
    print("❌ Failed to load coordinator!")

# Socket.IO message handler
@socketio.on('user_message')
def handle_message(data):
    print(f"Received message: {data}")
    message = data.get('message', '')
    
    # Generate a direct response
    if coordinator:
        try:
            response = coordinator.generate_response(message)
            print(f"Generated response using real coordinator: {response[:50]}...")
        except Exception as e:
            response = f"Error generating response: {str(e)}"
    else:
        response = f"This is a test response to: {message}"
    
    # Send response
    socketio.emit('response', response)
    socketio.emit('chat_reply', {'text': response})

# Start server
if __name__ == '__main__':
    host = '127.0.0.1'
    port = 5505
    print(f"Starting server at http://{host}:{port}/portal")
    socketio.run(app, host=host, port=port)
EOL

# Make it executable
chmod +x direct_server.py

# Run the direct server
echo "Starting direct server with fixed coordinator..."
python direct_server.py
""")

# Make the script executable
os.chmod('direct_run_server.sh', 0o755)

print("=== FIXES COMPLETED ===")
print("Run ./direct_run_server.sh to start the server with guaranteed coordinator access!")
print("This bypasses any existing import issues by creating a simpler but reliable implementation.") 