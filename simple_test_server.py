import os
import logging
import eventlet
import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Apply monkey patch first thing
eventlet.monkey_patch()
print("✅ Eventlet monkey patching successful")

# Now import Flask and extensions
from flask import Flask, request, jsonify, send_from_directory, redirect, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Create Flask app
app = Flask(__name__, static_folder='web/static', template_folder='web')
CORS(app)

# Create SocketIO with compatibility settings
socketio = SocketIO(
    app,
    async_mode='eventlet',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    # Critical compatibility settings
    allowEIO3=True,
    allowEIO4=True,
    always_connect=True
)

# Serve the portal page
@app.route('/portal')
def portal():
    """Serve the chat portal page"""
    return render_template('minerva-portal.html')

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('web/static', path)

# Add Socket.IO client compatibility routes
@app.route('/socket.io/socket.io.js')
def serve_socketio_default_path():
    """Serve compatible Socket.IO client at the default path"""
    return redirect("https://cdn.socket.io/4.7.2/socket.io.min.js")

@app.route('/compatible-socket.io.js')
def serve_compatible_socketio():
    """Serve a specific compatible Socket.IO client"""
    return redirect("https://cdn.socket.io/4.7.2/socket.io.min.js")

# Add health check endpoint
@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.datetime.now().isoformat(),
        'socketio_config': {
            'async_mode': socketio.async_mode,
            'allow_upgrades': socketio.allow_upgrades,
            'eio3': getattr(socketio, 'allowEIO3', False),
            'eio4': getattr(socketio, 'allowEIO4', False),
        }
    })

# Debug Socket.IO event handler
@socketio.on('debug')
def handle_debug(data):
    """Debug event handler to confirm Socket.IO is working"""
    logger.info(f"Received debug event with data: {data}")
    print(f"🔬 DEBUG: Received Socket.IO debug event: {data}")
    
    # Echo back the data with server info
    emit('debug_response', {
        'server_time': datetime.datetime.now().isoformat(),
        'received': data,
        'server_info': {
            'async_mode': socketio.async_mode,
            'socketio_version': 'unknown',
            'python_socketio_version': 'unknown',
        }
    })
    
    # Also send a system message for UI debugging
    emit('system_message', {'message': f"Debug connection successful at {datetime.datetime.now().isoformat()}"})

# Handle chat message event
@socketio.on('chat_message')
def handle_chat_message(data):
    """Process a chat message from the client"""
    logger.info(f"🔥 DEBUG: Received chat message: {data}")
    print(f"🔥 DEBUG: Received chat message: {data}")
    
    # Extract message text
    if isinstance(data, str):
        message_text = data
    elif isinstance(data, dict):
        message_text = data.get('text') or data.get('message') or data.get('content') or "No message content"
    else:
        message_text = str(data)
        
    # Generate a simple echo response
    response_text = f"You said: {message_text} [Echo from simple test server]"
    
    # Emit the response to all possible event types
    print(f"📤 DEBUG: Sending response: {response_text}")
    emit('chat_reply', {'text': response_text})
    emit('response', {'text': response_text})
    emit('message', {'text': response_text})
    emit('ai_response', {'text': response_text})
    
    # Send a system message for debugging
    emit('system_message', {'message': f"Message processed successfully at {datetime.datetime.now().isoformat()}"})

# Connection events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    print(f"👤 Client connected: {request.sid}")
    emit('system_message', {'message': f"Connected to simple test server at {datetime.datetime.now().isoformat()}"})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")
    print(f"👋 Client disconnected: {request.sid}")

# Handle generic message
@socketio.on('message')
def handle_message(data):
    """Handle a generic message event"""
    logger.info(f"Received generic message: {data}")
    print(f"📨 Received generic message: {data}")
    
    # Just echo back the message
    if isinstance(data, str):
        emit('message', data)
    else:
        emit('message', {'text': f"Echo: {str(data)}"})

# Main entry point
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5505))
    print(f"Starting simple test server on http://127.0.0.1:{port}")
    print("Access the portal at http://localhost:5505/portal")
    print("Press Ctrl+C to stop the server")
    socketio.run(app, host='127.0.0.1', port=port, debug=True) 