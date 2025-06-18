#!/usr/bin/env python3
"""
Ultra minimal chat server that works with Python 3.13
- NO eventlet dependency (uses threading instead)
- Direct diagnostic logging
"""

from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO
import logging
import datetime
import os

# Set up logging to see everything
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'debugging-key'

# Initialize SocketIO with threading (not eventlet)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading',  # Use threading, not eventlet
    ping_timeout=60,
    ping_interval=25,
    allowEIO3=True,
    allowEIO4=True
)

# Routes
@app.route('/')
def index():
    return '<h1>Test Server</h1><a href="/test.html">Test Chat</a>'

@app.route('/test.html')
def test_page():
    return send_from_directory('.', 'minimal_test.html')

@app.route('/socket.io/socket.io.js')
def serve_socketio():
    """Serve the Socket.IO client at the path the client expects"""
    if os.path.exists('static/js/socket.io.min.js'):
        return send_from_directory('static/js', 'socket.io.min.js')
    elif os.path.exists('web/static/js/socket.io.min.js'):
        return send_from_directory('web/static/js', 'socket.io.min.js')
    else:
        # If file doesn't exist, respond with error so client falls back to CDN
        return "File not found", 404

@app.route('/<path:filename>')
def serve_file(filename):
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    elif os.path.exists(os.path.join('web', filename)):
        return send_from_directory('web', filename)
    else:
        return "File not found", 404

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"🔌 CLIENT CONNECTED: {request.sid}")
    # Send a test message as soon as client connects
    socketio.emit('chat_reply', {
        'text': "👋 I'm connected! Send me a message."
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"🔌 CLIENT DISCONNECTED: {request.sid}")

@socketio.on('message')
def handle_message(message):
    """Handle simple 'message' event for testing"""
    print(f"💬 GENERIC MESSAGE RECEIVED: {message}")
    # Echo back
    socketio.emit('chat_reply', {
        'text': f"ECHO: {message}"
    })
    print(f"📤 SENT REPLY: ECHO: {message}")

@socketio.on('chat_message')
def handle_chat(data):
    """Handle 'chat_message' event"""
    print(f"💬 CHAT MESSAGE RECEIVED: {data}")
    
    # Extract message
    if isinstance(data, str):
        message_text = data
    else:
        message_text = data.get('message', '') or data.get('text', '') or str(data)
    
    # Create response
    response = f"You said: {message_text}"
    print(f"📤 SENDING RESPONSE: {response}")
    
    # Emit on multiple channels for compatibility
    socketio.emit('chat_reply', {'text': response})
    socketio.emit('chat_response', {'message': response})
    socketio.emit('response', {'text': response})
    
    print("✅ RESPONSE SENT SUCCESSFULLY")

if __name__ == '__main__':
    port = 5505
    print(f"⚡ Starting minimal server on port {port}")
    print(f"📱 Test interface: http://localhost:{port}/test.html")
    
    # Make JS directory if needed
    os.makedirs('static/js', exist_ok=True)
    
    # Download Socket.IO client if it doesn't exist
    socketio_js_path = 'static/js/socket.io.min.js'
    if not os.path.exists(socketio_js_path):
        try:
            import urllib.request
            print("📥 Downloading Socket.IO client v4.4.1...")
            urllib.request.urlretrieve(
                'https://cdn.socket.io/4.4.1/socket.io.min.js',
                socketio_js_path
            )
            print("✅ Socket.IO client downloaded successfully")
        except Exception as e:
            print(f"❌ Error downloading Socket.IO client: {e}")
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True) 