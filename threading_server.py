#!/usr/bin/env python3
"""
Python 3.13 Compatible Chat Server
- Uses threading instead of eventlet
- Shows detailed logs for debugging
- Compatible with Socket.IO 4.4.1 client
"""

from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit
import os
import logging
import json
import datetime
import urllib.request

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'debug-key'

# Initialize SocketIO with threading (not eventlet)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading',  # Critical: Use threading instead of eventlet
    ping_timeout=60,
    ping_interval=25,
    # Allow both EIO3 and EIO4 for maximum compatibility
    allowEIO3=True,
    allowEIO4=True
)

# Static file directories
STATIC_DIRS = ['static', 'web', 'web/static']

# Routes
@app.route('/')
def index():
    """Simple index page with links to test pages"""
    return """
    <h1>Socket.IO Test Server</h1>
    <p><a href="/debug">Debug Interface</a></p>
    <p><a href="/portal">Portal (Original App)</a></p>
    """

@app.route('/debug')
def debug_page():
    """Debug interface for testing Socket.IO connections"""
    return send_from_directory('.', 'debug.html')

@app.route('/portal')
def portal():
    """Original portal page"""
    if os.path.exists('web/minerva-portal.html'):
        return send_from_directory('web', 'minerva-portal.html')
    return "Portal page not found", 404

@app.route('/socket.io/socket.io.js')
def serve_socketio_client():
    """Critical: Serve the Socket.IO client at the URL the client expects"""
    # Look in multiple possible locations
    for directory in STATIC_DIRS:
        js_path = f"{directory}/js/socket.io.min.js"
        if os.path.exists(js_path):
            logger.info(f"Serving Socket.IO client from {js_path}")
            return send_from_directory(os.path.dirname(js_path), os.path.basename(js_path))
    
    # If not found locally, redirect to CDN
    logger.warning("Socket.IO client not found locally, redirecting to CDN")
    return """
    console.warn("Local Socket.IO client not found, using CDN");
    document.write('<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>');
    """

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from multiple directories"""
    # Try each directory
    for directory in STATIC_DIRS:
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            return send_from_directory(directory, filename)
    
    # Direct file access
    if os.path.exists(filename):
        return send_from_directory(os.path.dirname(filename) or '.', os.path.basename(filename))
    
    return f"File {filename} not found", 404

# Socket.IO event handlers
@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    logger.info(f"🟢 CLIENT CONNECTED: {request.sid}")
    print(f"🟢 CLIENT CONNECTED: {request.sid}")
    
    # Send a welcome message
    emit('chat_reply', {'text': "👋 Connected to server!"})
    print(f"📤 SENT welcome message to {request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    logger.info(f"🔴 CLIENT DISCONNECTED: {request.sid}")
    print(f"🔴 CLIENT DISCONNECTED: {request.sid}")

@socketio.on('message')
def on_message(message):
    """Handle generic 'message' event"""
    logger.info(f"📨 GENERIC MESSAGE RECEIVED: {message}")
    print(f"📨 GENERIC MESSAGE RECEIVED: {message}")
    
    # Echo back the message
    response = f"Echo: {message}"
    emit('message', response)
    emit('chat_reply', {'text': response})
    emit('chat_response', {'message': response})
    print(f"📤 SENT RESPONSE: {response}")

@socketio.on('chat_message')
def on_chat_message(data):
    """Handle 'chat_message' event"""
    logger.info(f"💬 CHAT MESSAGE RECEIVED: {data}")
    print(f"💬 CHAT MESSAGE RECEIVED: {data}")
    
    # Extract the message text
    if isinstance(data, dict):
        message = data.get('message', '') or data.get('text', '') or str(data)
    else:
        message = str(data)
    
    # Echo back on multiple channels for compatibility
    response = f"You said: {message}"
    print(f"📤 SENDING RESPONSE: {response}")
    
    # Emit on multiple channels for max compatibility
    emit('chat_reply', {'text': response})
    emit('chat_response', {'message': response})
    emit('response', {'text': response})
    
    print(f"✅ RESPONSE SENT to {request.sid}")

if __name__ == '__main__':
    # Create static directories if they don't exist
    for directory in STATIC_DIRS:
        js_dir = os.path.join(directory, 'js')
        os.makedirs(js_dir, exist_ok=True)
    
    # Download Socket.IO client if it doesn't exist
    socketio_dest = 'static/js/socket.io.min.js'
    if not os.path.exists(socketio_dest):
        try:
            print("⬇️ Downloading Socket.IO client v4.4.1...")
            urllib.request.urlretrieve(
                'https://cdn.socket.io/4.4.1/socket.io.min.js',
                socketio_dest
            )
            print("✅ Socket.IO client downloaded successfully")
        except Exception as e:
            print(f"❌ Error downloading Socket.IO client: {e}")
    
    # Run the server
    port = 5505
    host = '0.0.0.0'
    print(f"\n⚡ Starting server at http://{host}:{port}")
    print(f"📱 Debug interface: http://localhost:{port}/debug")
    print(f"🔗 Portal: http://localhost:{port}/portal")
    print("\nPress Ctrl+C to stop the server\n")
    
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True) 