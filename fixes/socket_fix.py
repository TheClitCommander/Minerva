#!/usr/bin/env python3
"""
Minerva Socket.IO Fix - Complete standalone solution that fixes Socket.IO compatibility issues
"""
import os
import sys
import signal
import logging
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('minerva.socket_fix')

# Important: Import and patch eventlet BEFORE anything else
try:
    import eventlet
    eventlet.monkey_patch()
    logger.info("✅ Successfully patched eventlet")
except ImportError:
    logger.error("❌ Failed to import eventlet - Socket.IO will not work properly")
    logger.error("   Run: pip install eventlet==0.33.3")
    sys.exit(1)

# Create Flask app and configure SocketIO with EXACT compatibility settings
app = Flask(__name__, static_folder='../web', template_folder='../web')
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    # Critical: These settings ensure compatibility with ALL Socket.IO clients
    allowEIO3=True,
    allowEIO4=True,
    always_connect=True,
    ping_timeout=60,
    ping_interval=25
)

# Prevent the server from terminating unexpectedly
signal.signal(signal.SIGTERM, lambda *args: logger.info("Ignoring SIGTERM"))
signal.signal(signal.SIGINT, lambda *args: logger.info("Ignoring SIGINT"))

# Serve the compatible Socket.IO client
@app.route('/socket.io/socket.io.js')
def serve_socketio_js():
    """Serve the Socket.IO client with a compatible version"""
    logger.info("Serving compatible Socket.IO client")
    return send_from_directory('../fixes/static', 'socket.io-4.4.1.min.js')

# Serve a diagnostics page
@app.route('/socket-test')
def socket_test():
    """Serve a diagnostic page to test Socket.IO connection"""
    logger.info("Serving Socket.IO test page")
    return render_template('socket_test.html')

# Serve the main portal
@app.route('/portal')
def portal():
    """Serve the main Minerva portal"""
    logger.info("Serving Minerva portal")
    return render_template('minerva-portal.html')

# Handle Socket.IO connection
@socketio.on('connect')
def on_connect():
    """Handle Socket.IO connection event"""
    logger.info("✅ Client connected to Socket.IO")
    emit('status', {'status': 'connected', 'message': 'Socket.IO connection successful'})

# Handle Socket.IO disconnection
@socketio.on('disconnect')
def on_disconnect():
    """Handle Socket.IO disconnection event"""
    logger.info("❌ Client disconnected from Socket.IO")

# Handle Socket.IO errors
@socketio.on_error()
def on_error(e):
    """Handle Socket.IO errors"""
    logger.error(f"❌ Socket.IO error: {str(e)}")

# Handle Socket.IO debug events
@socketio.on('debug')
def on_debug(data):
    """Handle debug events"""
    logger.info(f"🔍 Debug data received: {data}")
    emit('debug_response', {'status': 'ok', 'received': data, 'server_time': eventlet.time.time()})

# Handle chat messages - supports multiple event types for compatibility
@socketio.on('message')
@socketio.on('chat_message')
@socketio.on('user_message')
def on_message(data):
    """Handle chat messages from the client"""
    # Extract message from different possible formats
    if isinstance(data, dict):
        message = data.get('message', data.get('text', data.get('content', '')))
    else:
        message = str(data)
    
    logger.info(f"📨 Message received: {message}")
    
    # Echo the message back with some processing
    response = f"Echo: {message}"
    logger.info(f"📤 Sending response: {response}")
    
    # Emit on multiple channels for maximum compatibility
    emit('chat_reply', {'text': response, 'status': 'success'})
    emit('response', {'message': response, 'status': 'success'})
    emit('message', response)

# Main entry point
if __name__ == '__main__':
    # Ensure static directory exists
    os.makedirs('../fixes/static', exist_ok=True)
    os.makedirs('../fixes/templates', exist_ok=True)
    
    # Download compatible Socket.IO client if needed
    socketio_js_path = '../fixes/static/socket.io-4.4.1.min.js'
    if not os.path.exists(socketio_js_path):
        import urllib.request
        logger.info("Downloading compatible Socket.IO client...")
        urllib.request.urlretrieve(
            'https://cdn.socket.io/4.4.1/socket.io.min.js',
            socketio_js_path
        )
        logger.info("✅ Downloaded Socket.IO client v4.4.1")
    
    # Start the server
    logger.info("Starting Socket.IO server on http://localhost:5505")
    socketio.run(app, host='0.0.0.0', port=5505, debug=True)
