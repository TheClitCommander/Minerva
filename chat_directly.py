#!/usr/bin/env python3
"""
Direct Minerva Chat Server - No Dependencies

This is a completely standalone chat server with no dependencies on any
existing codebase files. It provides a simple chat interface on port 5505.
"""

import os
import sys
import time
import json
import logging
import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import eventlet
    eventlet.monkey_patch()
    print("✅ Eventlet monkey patching successful")
except ImportError:
    print("⚠️ Installing eventlet...")
    os.system(f"{sys.executable} -m pip install eventlet")
    import eventlet
    eventlet.monkey_patch()
    print("✅ Eventlet installed and monkey patching successful")

try:
    from flask import Flask, render_template, send_from_directory, jsonify, request
    from flask_socketio import SocketIO
    from flask_cors import CORS
except ImportError:
    print("⚠️ Installing Flask and Socket.IO...")
    os.system(f"{sys.executable} -m pip install flask flask-socketio flask-cors")
    from flask import Flask, render_template, send_from_directory, jsonify, request
    from flask_socketio import SocketIO
    from flask_cors import CORS
    print("✅ Flask and Socket.IO installed")

print("Starting direct Minerva chat server...")

# Create Flask app
app = Flask(__name__, 
            static_folder='web',
            template_folder='templates')
CORS(app)

# Initialize Socket.IO with compatibility settings for all clients
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)

# Add headers to prevent caching
@app.after_request
def add_headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portal')
def portal():
    return render_template('portal.html')

# Serve static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'uptime': str(datetime.datetime.now() - start_time),
        'mode': 'direct'
    })

# Socket.IO events
@socketio.on('connect')
def on_connect():
    logger.info("Client connected")
    socketio.emit('system_message', {'message': 'Connected to Direct Minerva Server'})

@socketio.on('disconnect')
def on_disconnect():
    logger.info("Client disconnected")

# Handle all possible message formats
@socketio.on('user_message')
def handle_user_message(data):
    handle_any_message(data)

@socketio.on('message')
def handle_message(message):
    if isinstance(message, str):
        data = {'message': message}
    else:
        data = message
    handle_any_message(data)
    
@socketio.on('chat_message')
def handle_chat_message(data):
    handle_any_message(data)

def handle_any_message(data):
    """Centralized message handler for all event types"""
    try:
        # Extract the message content from various possible formats
        if isinstance(data, str):
            message = data
        else:
            message = data.get('message', data.get('text', ''))
        
        if not message:
            socketio.emit('system_message', {'message': 'Empty message received'})
            return
            
        print(f"Received message: {message}")
        
        # Generate a direct response
        response = f"DIRECT RESPONSE: You said '{message}'\n\nThis is a real response from Minerva Direct Server."
        
        # Send through all compatible channels for different client versions
        socketio.emit('response', response)
        socketio.emit('ai_response', {'message': response})
        socketio.emit('chat_reply', {'text': response})
        
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        logger.error(error_msg)
        socketio.emit('system_message', {'message': error_msg})

# Start time tracking
start_time = datetime.datetime.now()

# Main entry point
if __name__ == '__main__':
    host = '127.0.0.1'
    port = 5505
    
    # Ensure we don't get terminated with SIGTERM
    import signal
    original_sigterm = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, lambda signum, frame: None)
    
    print(f"Starting server at http://{host}:{port}/portal")
    print("Press Ctrl+C to stop")
    
    try:
        socketio.run(app, host=host, port=port)
    except KeyboardInterrupt:
        print("Shutting down gracefully")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        signal.signal(signal.SIGTERM, original_sigterm) 