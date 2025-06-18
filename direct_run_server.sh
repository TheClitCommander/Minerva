#!/bin/bash
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
