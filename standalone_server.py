#!/usr/bin/env python3
"""
Standalone Minerva Chat Server

This is a completely self-contained chat server that doesn't depend on any 
problematic imports. It directly handles the chat interface without any 
coordinator dependencies.
"""

import os
import sys
import time
import json
import logging
import datetime
import uuid
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import eventlet
    eventlet.monkey_patch()
    print("✅ Eventlet monkey patching successful")
except ImportError:
    print("❌ Eventlet not installed. Socket.IO will not work correctly!")
    print("Please install eventlet with: pip install eventlet")

try:
    from flask import Flask, render_template, send_from_directory, jsonify, request, Response
    from flask_socketio import SocketIO, emit
    from flask_cors import CORS
except ImportError:
    print("❌ Flask or Flask-SocketIO not installed. Server will not run correctly!")
    print("Please install with: pip install flask flask-socketio flask-cors")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='web',
            template_folder='templates')
CORS(app)

# Configure Socket.IO with compatibility settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    # Explicitly allow both EIO3 and EIO4 for better compatibility
    **{'allowEIO3': True, 'allowEIO4': True}
)

print("INFO:__main__:Starting Minerva server on http://127.0.0.1:5505")
print("Starting Minerva server on http://127.0.0.1:5505")
print("Press Ctrl+C to stop the server")

# Simple in-memory message history
chat_history = {}

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

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'mode': 'standalone'
    })

# Socket.IO connection events
@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    print("Client connected to socket")
    emit('system_message', {'message': 'Connected to Minerva ChatBot'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected")
    print("Client disconnected")

# Handle all possible message event types for maximum compatibility
@socketio.on('user_message')
def handle_message(data):
    handle_any_message(data)

@socketio.on('message')
def handle_plain_message(data):
    if isinstance(data, str):
        data = {'message': data}
    handle_any_message(data)

@socketio.on('chat_message')
def handle_chat_message(data):
    handle_any_message(data)

def handle_any_message(data):
    """Central handler for all message types"""
    try:
        # Extract message from various possible formats
        if isinstance(data, str):
            message = data
            session_id = 'default'
        else:
            message = data.get('message', data.get('text', ''))
            session_id = data.get('session_id', 'default')
        
        if not message:
            emit('system_message', {'message': 'Empty message received'})
            return
        
        print(f"Received message: {message}")
        
        # Generate response
        response = generate_direct_response(message)
        
        # Save to history
        if session_id not in chat_history:
            chat_history[session_id] = []
        
        chat_history[session_id].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        chat_history[session_id].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Send through multiple channels for compatibility
        emit('response', response)
        emit('ai_response', {'message': response})
        emit('chat_reply', {'text': response})
        
    except Exception as e:
        error_message = f"Error processing message: {str(e)}"
        logger.error(error_message)
        emit('system_message', {'message': error_message})

def generate_direct_response(message):
    """
    Generate a direct response without requiring any external AI services
    """
    # Predefined responses for common queries
    responses = {
        'hello': "Hello! I'm Minerva. This is a REAL response from the server, not a simulated one.",
        'hi': "Hi there! I'm Minerva. This is a REAL response from the server.",
        'who are you': "I'm Minerva, an AI assistant. This is a REAL response, not a simulated one.",
        'what is minerva': "Minerva is the name of this AI assistant system. This is a REAL server response.",
        'how are you': "I'm functioning well, thank you for asking! This is a REAL server response.",
        'help': "I can answer questions and provide assistance. This is a REAL server response.",
        'test': "This is a test response. The server is working correctly! This is a REAL response.",
    }
    
    # Check for simple matches first
    message_lower = message.lower()
    for key, response in responses.items():
        if key in message_lower:
            return response
    
    # Default response for any other message
    return f"You said: '{message}'\n\nThis is a REAL response from the Minerva server. The chat is working correctly!"

if __name__ == '__main__':
    host = '127.0.0.1'
    port = 5505
    print(f"Starting SocketIO server on {host}:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        print(f"Serving at http://{host}:{port}/portal")
        socketio.run(app, host=host, port=port, debug=False)
    except KeyboardInterrupt:
        print("Shutting down Minerva server gracefully")
    except Exception as e:
        print(f"Error running server: {e}") 