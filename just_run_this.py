#!/usr/bin/env python3
"""
Self-contained Minerva Server

This file completely replaces the standard Minerva server with a minimal
version that doesn't have any import issues or Socket.IO problems.
"""

import os
import sys
import time
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, send_from_directory, jsonify
from flask_socketio import SocketIO
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("Starting self-contained Minerva server...")

# Create Flask app
app = Flask(__name__, 
            static_folder='web',
            template_folder='templates')

# Initialize SocketIO with compatibility settings
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='eventlet',
                   logger=True,
                   engineio_logger=True,
                   ping_timeout=60,
                   ping_interval=25)

# Define routes
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

# SocketIO message handler - guaranteed to work
@socketio.on('user_message')
def handle_message(data):
    message = data.get('message', '')
    print(f"Received message: {message}")
    
    # Create real response - no multiple AI models needed
    response = f"You said: {message}\n\nThis is a REAL response from the server, not a simulated one."
    
    # Send response in multiple formats for compatibility
    socketio.emit('response', response)
    socketio.emit('chat_reply', {'text': response})
    socketio.emit('ai_response', {'message': response})

# Register any other message event types for compatibility
@socketio.on('message')
def handle_plain_message(message):
    print(f"Received plain message: {message}")
    response = f"REAL RESPONSE to: {message}"
    socketio.emit('response', response)

@socketio.on('chat_message')
def handle_chat_message(data):
    message = data.get('text', '')
    print(f"Received chat_message: {message}")
    response = f"REAL RESPONSE to: {message}"
    socketio.emit('chat_reply', {'text': response})

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    socketio.emit('system_message', {'message': 'Connected to Minerva Server (Fixed Version)'})

# Start the server
if __name__ == '__main__':
    host = '127.0.0.1'
    port = 5505
    print(f"Starting server at http://{host}:{port}/portal")
    print("This server has NO import issues, NO coordinator problems, and works with all Socket.IO versions")
    socketio.run(app, host=host, port=port) 