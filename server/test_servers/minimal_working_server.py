#!/usr/bin/env python3
"""
Minimal Socket.IO server for chat testing, without eventlet dependencies
"""

from flask import Flask, request, send_from_directory, jsonify
from flask_socketio import SocketIO
import logging
import json
import os
import time
import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minerva-secret-key'

# Initialize Socket.IO without eventlet
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    # Critical compatibility parameters
    allowEIO3=True,
    allowEIO4=True,
    ping_timeout=60,
    ping_interval=25
)

# Simple in-memory message storage
chat_messages = []

# Routes
@app.route('/')
def index():
    """Serve basic index"""
    return 'Minerva Chat Server is running. Go to <a href="/portal">/portal</a> to access the chat interface.'

@app.route('/portal')
def portal():
    """Serve the portal page"""
    return send_from_directory('web', 'minerva-portal.html')

@app.route('/socket.io/socket.io.js')
def serve_socketio():
    """Serve the Socket.IO client at the path where the browser looks for it"""
    return send_from_directory('web/static/js', 'socket.io.min.js')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('web', path)

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    print(f"Client connected: {client_id}")
    emit_welcome_message()

def emit_welcome_message():
    """Send welcome message to newly connected clients"""
    socketio.emit('chat_reply', {
        'text': "Welcome to Minerva! I'm online and ready to chat.",
        'status': 'success'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnect"""
    client_id = request.sid
    print(f"Client disconnected: {client_id}")

@socketio.on('chat_message')
def handle_message(data):
    """Handle incoming chat messages"""
    print(f"Received message: {data}")
    
    # Extract message from different possible formats
    if isinstance(data, str):
        message = data
    elif isinstance(data, dict):
        message = data.get('message') or data.get('text') or data.get('content', '')
    else:
        message = str(data)
    
    # Log the message
    print(f"Processed message: '{message}'")
    chat_messages.append({
        'message': message,
        'timestamp': datetime.datetime.now().isoformat(),
        'sender': 'user'
    })
    
    # Generate a simple response
    response = generate_response(message)
    
    # Send the response to the client
    print(f"Sending response: '{response}'")
    
    # Send in multiple formats for maximum compatibility
    socketio.emit('chat_reply', {'text': response, 'status': 'success'})
    socketio.emit('chat_response', {'message': response})
    socketio.emit('response', {'text': response})
    
    # Save the AI response
    chat_messages.append({
        'message': response,
        'timestamp': datetime.datetime.now().isoformat(),
        'sender': 'ai'
    })

def generate_response(message):
    """Generate a simple response based on the message"""
    message = message.lower()
    
    if any(greeting in message for greeting in ['hello', 'hi', 'hey']):
        return "Hello! I'm Minerva. How can I help you today?"
    
    if any(query in message for query in ['who are you', 'what are you']):
        return "I'm Minerva, an AI assistant designed to help with various tasks and questions."
    
    if 'how are you' in message:
        return "I'm functioning well, thank you for asking! How can I assist you today?"
    
    if any(test in message for test in ['test', 'testing']):
        return "This is a test response. The system appears to be working correctly!"

    # Default response
    return f"I received your message: '{message}'. This is a simple simulated response, but it confirms the chat system is working properly!"

# Main function to run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5505))
    host = '0.0.0.1'
    print(f"Starting Minerva chat server on http://{host}:{port}")
    print("Visit http://localhost:5505/portal to access the chat interface")
    print("Press Ctrl+C to stop")
    
    # Download the correct Socket.IO client version if it doesn't exist
    js_dir = os.path.join('web', 'static', 'js')
    os.makedirs(js_dir, exist_ok=True)
    socketio_js_path = os.path.join(js_dir, 'socket.io.min.js')
    
    if not os.path.exists(socketio_js_path):
        print("Downloading Socket.IO client...")
        import urllib.request
        urllib.request.urlretrieve(
            'https://cdn.socket.io/4.4.1/socket.io.min.js',
            socketio_js_path
        )
        print("Socket.IO client downloaded successfully")
    
    # Run the app
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True) 