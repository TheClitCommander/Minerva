#!/usr/bin/env python3
"""
Ultra-minimal Socket.IO diagnostic script - will work with Python 3.13
- No dependencies on eventlet
- Confirms basic Socket.IO functionality
- Prints all events received and sent
"""

from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
import logging
import os
import sys
import json

# Configure verbose logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'debug-key'

# Initialize SocketIO with threading mode and debug
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading',  # Use threading instead of eventlet
    ping_timeout=60,
    ping_interval=25,
    # Important compatibility settings
    allowEIO3=True,
    allowEIO4=True
)

# A simple test page that connects to Socket.IO
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Socket.IO Test</title>
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 20px; }
        #status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
        .log { background: #f8f9fa; padding: 10px; border-radius: 4px; height: 200px; overflow-y: auto; font-family: monospace; }
        button { padding: 8px 16px; margin: 5px; }
    </style>
</head>
<body>
    <h1>Socket.IO Diagnostic Page</h1>
    
    <div id="status" class="disconnected">Disconnected</div>
    
    <div>
        <button id="test-message">Send 'message' event</button>
        <button id="test-chat-message">Send 'chat_message' event</button>
        <button id="test-custom">Send custom event</button>
    </div>
    
    <h3>Event Log:</h3>
    <div id="log" class="log"></div>
    
    <script src="/socket.io/socket.io.js"></script>
    <script>
        // Fallback to CDN if needed
        if (typeof io === 'undefined') {
            console.warn('Local Socket.IO client not found, using CDN');
            document.write('<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"><\\/script>');
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            const statusEl = document.getElementById('status');
            const logEl = document.getElementById('log');
            
            // Log helper
            function log(msg, type = 'info') {
                console.log(msg);
                const entry = document.createElement('div');
                entry.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
                if (type === 'error') entry.style.color = '#dc3545';
                if (type === 'success') entry.style.color = '#28a745';
                logEl.appendChild(entry);
                logEl.scrollTop = logEl.scrollHeight;
            }
            
            // Connect to Socket.IO server
            log('Initializing Socket.IO connection...');
            const socket = io({
                reconnection: true,
                timeout: 20000,
                transports: ['websocket', 'polling']
            });
            
            // Connection events
            socket.on('connect', () => {
                statusEl.className = 'connected';
                statusEl.textContent = `Connected (ID: ${socket.id})`;
                log('✅ Socket.IO Connected!', 'success');
            });
            
            socket.on('disconnect', (reason) => {
                statusEl.className = 'disconnected';
                statusEl.textContent = 'Disconnected';
                log(`❌ Socket.IO Disconnected: ${reason}`, 'error');
            });
            
            socket.on('connect_error', (error) => {
                log(`❌ Connection Error: ${error.message}`, 'error');
            });
            
            // Listen for responses
            socket.on('chat_reply', (data) => {
                log(`📥 Received 'chat_reply': ${JSON.stringify(data)}`, 'success');
            });
            
            socket.on('chat_response', (data) => {
                log(`📥 Received 'chat_response': ${JSON.stringify(data)}`, 'success');
            });
            
            // Generic message handler
            socket.on('message', (data) => {
                log(`📥 Received 'message': ${JSON.stringify(data)}`, 'success');
            });
            
            // Button event handlers
            document.getElementById('test-message').addEventListener('click', () => {
                const testMsg = 'Test message ' + Date.now();
                log(`📤 Sending 'message': ${testMsg}`);
                socket.emit('message', testMsg);
            });
            
            document.getElementById('test-chat-message').addEventListener('click', () => {
                const testMsg = { message: 'Test chat message ' + Date.now() };
                log(`📤 Sending 'chat_message': ${JSON.stringify(testMsg)}`);
                socket.emit('chat_message', testMsg);
            });
            
            document.getElementById('test-custom').addEventListener('click', () => {
                const eventName = prompt('Enter event name:', 'custom_event');
                if (!eventName) return;
                
                const testMsg = prompt('Enter message:', 'Test data');
                if (!testMsg) return;
                
                log(`📤 Sending '${eventName}': ${testMsg}`);
                socket.emit(eventName, testMsg);
                
                // Add a listener for this custom event
                if (!socket.hasListeners(eventName)) {
                    socket.on(eventName, (data) => {
                        log(`📥 Received '${eventName}': ${JSON.stringify(data)}`, 'success');
                    });
                    log(`👂 Added listener for '${eventName}'`);
                }
            });
        });
    </script>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    return HTML

@app.route('/socket.io/socket.io.js')
def serve_socketio_client():
    """Serve the Socket.IO client"""
    static_dir = 'static/js'
    os.makedirs(static_dir, exist_ok=True)
    
    client_path = os.path.join(static_dir, 'socket.io.min.js')
    if not os.path.exists(client_path):
        try:
            import urllib.request
            print("Downloading Socket.IO client v4.4.1...")
            urllib.request.urlretrieve(
                'https://cdn.socket.io/4.4.1/socket.io.min.js',
                client_path
            )
            print("Socket.IO client downloaded successfully")
        except Exception as e:
            print(f"Error downloading Socket.IO client: {e}")
            return """
            console.warn("Local Socket.IO client not found, using CDN");
            document.write('<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>');
            """
    
    return send_from_directory(static_dir, 'socket.io.min.js')

# Socket.IO Event Handlers
@socketio.on('connect')
def on_connect():
    print(f"🟢 CLIENT CONNECTED: {request.sid}")
    # Send a welcome message immediately on connect
    emit('chat_reply', {'text': "Server welcomes you!"})
    print(f"📤 SENT welcome to {request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    print(f"🔴 CLIENT DISCONNECTED: {request.sid}")

@socketio.on('message')
def handle_message(message):
    """Handle 'message' event"""
    print(f"🔥 MESSAGE RECEIVED: {message}")
    
    # Echo back the message
    response = f"Echo: {message}"
    print(f"📤 SENDING: {response}")
    
    # Try different emit approaches
    try:
        # Method 1: Standard emit
        emit('chat_reply', {'text': response})
        print("  ✓ Method 1: Standard emit")
        
        # Method 2: Explicit emit with room
        emit('chat_response', {'message': response}, room=request.sid)
        print("  ✓ Method 2: Room-based emit")
        
        # Method 3: Direct socketio.emit
        socketio.emit('message', response)
        print("  ✓ Method 3: socketio.emit")
    except Exception as e:
        print(f"❌ ERROR during emit: {e}")

@socketio.on('chat_message')
def handle_chat(data):
    """Handle 'chat_message' event"""
    print(f"🔥 CHAT MESSAGE RECEIVED: {data}")
    
    try:
        # Extract message text
        if isinstance(data, dict):
            message_text = data.get('message', '') or data.get('text', '') or str(data)
        else:
            message_text = str(data)
        
        # Create response
        response = f"You said: {message_text}"
        print(f"📤 SENDING: {response}")
        
        # Try all possible emit formats
        emit('chat_reply', {'text': response})
        emit('chat_response', {'message': response})
        emit('message', response)
        
        print("✅ Response sent on all channels")
    except Exception as e:
        print(f"❌ ERROR: {e}")

# Catch-all event handler to debug any incoming events
@socketio.on_error_default
def default_error_handler(e):
    print(f"❌ ERROR: {e}")

# Catch-all event handler to see every event
@socketio.on('*')
def catch_all(event, data):
    print(f"🕵️ CATCH-ALL: Event '{event}' with data: {data}")

if __name__ == '__main__':
    # Print diagnostic info
    print("\n=== Socket.IO Diagnostic Server ===")
    print(f"Python version: {sys.version}")
    print(f"Flask-SocketIO version: {socketio.__version__}")
    print("Configuration:")
    print(f"  async_mode: {socketio.async_mode}")
    print(f"  cors_allowed_origins: {socketio.cors_allowed_origins}")
    print(f"  allowEIO3: {getattr(socketio, 'allowEIO3', 'N/A')}")
    print(f"  allowEIO4: {getattr(socketio, 'allowEIO4', 'N/A')}")
    
    # Run server
    host = '0.0.0.0'
    port = 5505
    print(f"\nStarting server at http://{host}:{port}")
    print("Open http://localhost:5505/ in your browser")
    print("Press Ctrl+C to stop\n")
    
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True) 