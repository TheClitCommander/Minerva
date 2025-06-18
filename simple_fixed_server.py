#!/usr/bin/env python3
"""
Simple Fixed Server for Minerva

This is a minimal server that uses the coordinator from web.multi_ai_coordinator
and provides both API endpoints and a web interface.
"""

import os
import sys
import eventlet
eventlet.monkey_patch()
import logging
from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app with proper static folder
app = Flask(__name__, static_folder='web', template_folder='templates')
CORS(app)

# Configure Socket.IO to accept multiple protocol versions
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    # Configure compatibility for different clients
    allowEIO3=True,  # Allow older clients
    allowEIO4=True,  # Allow newer clients
    # Increase buffers for larger messages
    max_http_buffer_size=1e8,
)

# Import the coordinator module - preload global variable
import web.multi_ai_coordinator
print("Checking coordinator availability...")

# Check if coordinator is available
coordinator_available = False
if hasattr(web.multi_ai_coordinator, 'coordinator'):
    coordinator = web.multi_ai_coordinator.coordinator
    coordinator_available = True
    print(f"✅ Found coordinator (lowercase): {id(coordinator)}")
elif hasattr(web.multi_ai_coordinator, 'Coordinator'):
    coordinator = web.multi_ai_coordinator.Coordinator 
    coordinator_available = True
    print(f"✅ Found Coordinator (capital C): {id(coordinator)}")
else:
    print("❌ No coordinator found in module")
    coordinator = None

# Import MinervaExtensions with coordinator passed in
if coordinator_available:
    from web.minerva_extensions import MinervaExtensions
    minerva_extensions = MinervaExtensions(coordinator)
    print(f"✅ Created MinervaExtensions with coordinator")
else:
    print("❌ Cannot create MinervaExtensions with coordinator")
    try:
        from web.minerva_extensions import MinervaExtensions
        minerva_extensions = MinervaExtensions()
        print("⚠️ Created MinervaExtensions without coordinator")
    except Exception as e:
        print(f"❌ Failed to create MinervaExtensions: {e}")
        minerva_extensions = None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portal')
def portal():
    return render_template('portal.html')

# Static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

# API status endpoint
@app.route('/api/status')
def api_status():
    """Return the status of the API to verify connectivity"""
    status = {
        'status': 'success',
        'server': 'Minerva API',
        'coordinator_available': coordinator_available,
        'minerva_extensions_available': minerva_extensions is not None,
    }
    if coordinator_available:
        status['available_models'] = coordinator.get_available_models()['models'] if hasattr(coordinator, 'get_available_models') else []
    return jsonify(status)

# Socket.IO handlers
@socketio.on('connect')
def handle_connect():
    print("Client connected to chat WebSocket")
    socketio.emit('system_message', {'message': 'Connected to Minerva Think Tank'})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected from chat WebSocket")

@socketio.on('user_message')
def handle_user_message(data):
    """Handle user messages and generate responses"""
    message = data.get('message', '')
    session_id = data.get('session_id', 'session_default')
    model = data.get('model', 'default')
    
    print(f"Received message: {message}")
    
    # Generate response
    if coordinator_available:
        try:
            # Use coordinator directly for real response
            response = coordinator.generate_response(message, model_preference=model, session_id=session_id)
            print(f"Generated response using real coordinator")
        except Exception as e:
            print(f"Error generating response with coordinator: {e}")
            response = f"Error generating response: {str(e)}"
    else:
        # Use simulated response
        response = f"This is a simulated response to: '{message}'"
        print("Using simulated response (no coordinator available)")
    
    # Send response through all compatible channels
    socketio.emit('response', response)
    socketio.emit('ai_response', {'message': response})
    socketio.emit('chat_reply', {'text': response})

# Start the server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5505))
    host = '127.0.0.1'
    print(f"Starting server at http://{host}:{port}/portal")
    socketio.run(app, host=host, port=port, debug=False) 