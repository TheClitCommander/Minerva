#!/usr/bin/env python3
"""
Ultra-minimal Socket.IO server - Python 3.13 compatible
No eventlet dependency at all
"""

from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Initialize SocketIO with threading mode (not eventlet)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading',  # Use threading instead of eventlet
    allowEIO3=True,          # Support EIO version 3
    allowEIO4=True           # Support EIO version 4
)

# HTML test page
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Socket.IO Test</title>
    <style>
        body { font-family: Arial; margin: 0; padding: 20px; max-width: 800px; margin: 0 auto; }
        #status { padding: 10px; margin-bottom: 10px; }
        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
        #log { height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 20px; font-family: monospace; }
        button { padding: 10px; margin-right: 10px; }
    </style>
</head>
<body>
    <h1>Socket.IO Test</h1>
    
    <div id="status" class="disconnected">Disconnected</div>
    
    <div>
        <button id="send-message">Send Test Message</button>
        <button id="send-chat">Send Chat Message</button>
    </div>

    <h3>Log:</h3>
    <div id="log"></div>
    
    <script src="/socket.io/socket.io.js"></script>
    <script>
        // Fallback to CDN if needed
        if (typeof io === 'undefined') {
            console.warn('Socket.IO client not found, falling back to CDN');
            document.write('<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"><\\/script>');
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            const log = document.getElementById('log');
            const status = document.getElementById('status');
            
            function addLog(message, type = 'info') {
                const line = document.createElement('div');
                line.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
                if (type === 'sent') line.style.color = 'blue';
                if (type === 'received') line.style.color = 'green';
                if (type === 'error') line.style.color = 'red';
                
                log.appendChild(line);
                log.scrollTop = log.scrollHeight;
                console.log(message);
            }
            
            // Connect to Socket.IO
            addLog('Connecting to Socket.IO server...');
            
            const socket = io({
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000,
                transports: ['websocket', 'polling'] // Try WebSocket first, fallback to polling
            });
            
            // Connection events
            socket.on('connect', () => {
                addLog('Connected to server ✅');
                status.className = 'connected';
                status.textContent = `Connected (${socket.id})`;
            });
            
            socket.on('disconnect', (reason) => {
                addLog(`Disconnected: ${reason}`, 'error');
                status.className = 'disconnected';
                status.textContent = 'Disconnected';
            });
            
            socket.on('connect_error', (error) => {
                addLog(`Connection error: ${error.message}`, 'error');
            });
            
            // Listen for all possible event types
            socket.on('message', (data) => {
                addLog(`Received message: ${data}`, 'received');
            });
            
            socket.on('chat_reply', (data) => {
                addLog(`Received chat_reply: ${JSON.stringify(data)}`, 'received');
            });
            
            socket.on('chat_response', (data) => {
                addLog(`Received chat_response: ${JSON.stringify(data)}`, 'received');
            });
            
            // Catch all events for debugging
            socket.onAny((event, ...args) => {
                addLog(`EVENT '${event}': ${JSON.stringify(args)}`, 'received');
            });
            
            // Button event handlers
            document.getElementById('send-message').addEventListener('click', () => {
                const message = `Test message ${Date.now()}`;
                addLog(`Sending message: ${message}`, 'sent');
                socket.emit('message', message);
            });
            
            document.getElementById('send-chat').addEventListener('click', () => {
                const message = { text: `Test chat ${Date.now()}` };
                addLog(`Sending chat_message: ${JSON.stringify(message)}`, 'sent');
                socket.emit('chat_message', message);
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
def serve_socketio():
    """Serve the Socket.IO client"""
    # Create the directory if it doesn't exist
    os.makedirs('static/js', exist_ok=True)
    
    client_path = 'static/js/socket.io.min.js'
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
            console.warn("Socket.IO client not found, using CDN");
            document.write('<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>');
            """
    
    return send_from_directory('static/js', 'socket.io.min.js')

# Socket.IO event handlers
@socketio.on('connect')
def on_connect():
    print(f"🟢 CLIENT CONNECTED: {request.sid}")
    # Send welcome message
    emit('chat_reply', {'text': 'Connected to server!'}, broadcast=True)
    print(f"📤 SENT welcome message with broadcast=True")

@socketio.on('disconnect')
def on_disconnect():
    print(f"🔴 CLIENT DISCONNECTED: {request.sid}")

@socketio.on('message')
def handle_message(message):
    print(f"🔥 MESSAGE RECEIVED: {message}")
    response = f"Echo: {message}"
    print(f"📤 SENDING: {response}")
    # CRITICAL: Use broadcast=True to make it work
    emit('chat_reply', {'text': response}, broadcast=True)
    emit('message', response, broadcast=True)
    print("✅ RESPONSE SENT WITH broadcast=True")

@socketio.on('chat_message')
def handle_chat(data):
    print(f"💬 CHAT MESSAGE RECEIVED: {data}")
    
    # Extract message
    if isinstance(data, dict):
        message = data.get('text', '') or data.get('message', '') or str(data)
    else:
        message = str(data)
    
    response = f"You said: {message}"
    print(f"📤 SENDING CHAT RESPONSE: {response}")
    
    # CRITICAL: Use broadcast=True on all emissions
    emit('chat_reply', {'text': response}, broadcast=True)
    emit('chat_response', {'message': response}, broadcast=True)
    
    print("✅ RESPONSE SENT WITH broadcast=True")

if __name__ == '__main__':
    # Print diagnostic info
    print("=== Socket.IO Test Server ===")
    print(f"Python: {sys.version}")
    try:
        import flask_socketio
        print(f"Flask-SocketIO: {flask_socketio.__version__}")
    except:
        print("Could not determine Flask-SocketIO version")
    
    print("\nConfiguration:")
    print(f"  async_mode: {socketio.async_mode}")
    print(f"  cors_allowed_origins: {socketio.cors_allowed_origins}")
    print(f"  Using threading mode (not eventlet)")
    
    host = '0.0.0.0'
    port = 5505
    print(f"\nStarting server at http://{host}:{port}")
    print(f"Open http://localhost:{port}/ in your browser")
    print("Press Ctrl+C to stop\n")
    
    # Start the server
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True) 