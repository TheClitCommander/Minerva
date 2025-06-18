#!/usr/bin/env python3
"""
Ultra minimal chat server for Minerva
- No eventlet dependency (works with Python 3.13)
- Uses werkzeug directly 
- Compatible with Socket.IO clients
"""

from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO
import os
import logging
import datetime
import json
import uuid
import urllib.request

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minerva-secret'

# Initialize SocketIO without eventlet 
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    # Critical compatibility parameters
    async_mode='threading',  # Use threading instead of eventlet
    allowEIO3=True,
    allowEIO4=True,
    ping_timeout=60,
    ping_interval=25,
    path="/socket.io"  # Explicitly set the path
)

# Ensure necessary directories exist
os.makedirs(os.path.join('web', 'static', 'js'), exist_ok=True)

# Download Socket.IO client if needed
SOCKET_IO_CLIENT_PATH = os.path.join('web', 'static', 'js', 'socket.io.min.js')
if not os.path.exists(SOCKET_IO_CLIENT_PATH):
    print("Downloading Socket.IO client v4.4.1...")
    try:
        urllib.request.urlretrieve(
            'https://cdn.socket.io/4.4.1/socket.io.min.js',
            SOCKET_IO_CLIENT_PATH
        )
        print("Downloaded Socket.IO client successfully")
    except Exception as e:
        print(f"Error downloading Socket.IO client: {e}")

# Routes
@app.route('/')
def index():
    return '<h1>Minerva Server</h1><p>Go to <a href="/chat">/chat</a> to access chat.</p>'

@app.route('/chat')
def chat():
    return send_from_directory('web', 'simple-chat.html')

@app.route('/portal')
def portal():
    return send_from_directory('web', 'minerva-portal.html')

@app.route('/debug-chat')
def debug_chat():
    return send_from_directory('web', 'debug-chat.html') 

@app.route('/socket.io/socket.io.js')
def serve_socketio():
    """Serve the Socket.IO client at the standard path"""
    return send_from_directory('web/static/js', 'socket.io.min.js')

@app.route('/static/js/<path:filename>')
def serve_static_js(filename):
    return send_from_directory('web/static/js', filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('web/static', filename)

@app.route('/<path:filename>')
def serve_web_files(filename):
    """Serve files from the web directory"""
    if os.path.exists(os.path.join('web', filename)):
        return send_from_directory('web', filename)
    else:
        return f"File not found: {filename}", 404

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    print(f"✅ Client connected: {client_id}")
    # Send welcome message
    socketio.emit('chat_reply', {
        'text': "Welcome to the Minerva chat! I'm online and ready to chat.",
        'status': 'success'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    print(f"❌ Client disconnected: {client_id}")

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat messages from clients"""
    client_id = request.sid
    print(f"📩 Received message from {client_id}: {data}")
    
    # Extract the message text
    if isinstance(data, str):
        message = data
    elif isinstance(data, dict):
        message = data.get('message') or data.get('text') or data.get('content') or str(data)
    else:
        message = str(data)
    
    print(f"💬 Processed message: '{message}'")
    
    # Generate a simple response - no AI needed
    response = generate_simple_response(message)
    
    print(f"📤 Sending response: '{response}'")
    
    # Send response in multiple formats for maximum compatibility
    socketio.emit('chat_reply', {
        'text': response,
        'status': 'success'
    })
    
    socketio.emit('chat_response', {
        'message': response
    })
    
    socketio.emit('response', {
        'text': response
    })
    
    print("✅ Response sent successfully")

def generate_simple_response(message):
    """Generate a simple response to the given message"""
    message = message.lower()
    
    # Simple pattern matching
    if any(greeting in message for greeting in ['hello', 'hi', 'hey']):
        return "Hello! I'm Minerva. How can I help you today?"
    
    if 'how are you' in message:
        return "I'm functioning well, thank you for asking! I'm here and ready to assist you."
    
    if any(word in message for word in ['help', 'assist', 'support']):
        return "I'd be happy to help! I can answer questions, provide information, or assist with various tasks. What specifically do you need help with?"
    
    if 'who are you' in message or 'what are you' in message:
        return "I'm Minerva, an AI assistant designed to provide helpful responses and assist with various tasks and questions."
    
    if 'thank' in message:
        return "You're welcome! I'm glad I could be of assistance. Is there anything else I can help with?"
    
    if any(word in message for word in ['bye', 'goodbye', 'see you', 'later']):
        return "Goodbye! Feel free to chat again whenever you need assistance."
        
    # Default response 
    return f"I received your message: '{message}'. This is a simple test response to show the chat system is working correctly."

# In case someone runs this directly
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5505))
    host = '0.0.0.0'  # Listen on all interfaces
    
    print(f"\n✨ Starting minimal Minerva chat server on http://{host}:{port}")
    print(f"💬 Access the chat at: http://localhost:{port}/chat")
    print(f"🌍 Access the portal at: http://localhost:{port}/portal")
    print(f"🔍 Access debug chat at: http://localhost:{port}/debug-chat")
    print("Press Ctrl+C to stop the server\n")
    
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True) 