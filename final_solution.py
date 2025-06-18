#!/usr/bin/env python3
"""
Ultra-minimal Socket.IO server that demonstrably works with Python 3.13
- No eventlet dependency
- Simple echo handler
- Traces all events
"""

from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'debug-key'

# Initialize SocketIO with threading
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading',  # Critical: Use threading instead of eventlet
    ping_timeout=60,
    ping_interval=25,
    allowEIO3=True,    # Support older clients
    allowEIO4=True     # Support newer clients
)

# HTML test page
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Socket.IO Test</title>
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 20px; }
        #status { padding: 10px; border-radius: 4px; margin-bottom: 10px; }
        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
        #log { height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; 
              font-family: monospace; margin-bottom: 10px; }
        button { padding: 8px 16px; margin: 5px; }
        input { padding: 8px; width: 80%; }
    </style>
</head>
<body>
    <h1>Socket.IO Test</h1>
    <div id="status" class="disconnected">Disconnected</div>
    
    <div>
        <button id="test-emit">Test Message</button>
        <button id="test-chat">Test Chat Message</button>
    </div>
    
    <div style="margin-top: 10px;">
        <input id="message-input" placeholder="Type a message...">
        <button id="send-btn">Send</button>
    </div>
    
    <h3>Events:</h3>
    <div id="log"></div>
    
    <script src="/socket.io/socket.io.js"></script>
    
    <script>
        // Fallback to CDN if needed
        if (typeof io === 'undefined') {
            document.write('<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"><\\/script>');
        }
        
        const log = document.getElementById('log');
        const status = document.getElementById('status');
        const testBtn = document.getElementById('test-emit');
        const testChatBtn = document.getElementById('test-chat');
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        
        function addLog(msg, type = 'info') {
            const line = document.createElement('div');
            line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
            
            if (type === 'sent') line.style.color = 'blue';
            if (type === 'received') line.style.color = 'green';
            if (type === 'error') line.style.color = 'red';
            
            log.appendChild(line);
            log.scrollTop = log.scrollHeight;
            console.log(msg);
        }
        
        // Initialize Socket.IO connection
        addLog('Connecting to server...');
        const socket = io({
            reconnection: true,
            reconnectionAttempts: 5,
            transports: ['websocket', 'polling'] // Try both transports
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
        
        // Listen for EVERY event (debug mode)
        const originalOnEvent = socket.onevent;
        socket.onevent = function(packet) {
            const args = packet.data || [];
            const event = args[0];
            addLog(`Received event '${event}': ${JSON.stringify(args.slice(1))}`, 'received');
            originalOnEvent.call(this, packet);
        };
        
        // Specific event listeners
        socket.on('chat_reply', (data) => {
            addLog(`🧠 Received chat_reply: ${JSON.stringify(data)}`, 'received');
        });
        
        socket.on('chat_response', (data) => {
            addLog(`🧠 Received chat_response: ${JSON.stringify(data)}`, 'received');
        });
        
        // Test event button
        testBtn.addEventListener('click', () => {
            const testMsg = 'hello from orb ' + Date.now();
            addLog(`Sending 'message': ${testMsg}`, 'sent');
            socket.emit('message', testMsg);
        });
        
        // Test chat button
        testChatBtn.addEventListener('click', () => {
            const testMsg = 'hello chat ' + Date.now();
            addLog(`Sending 'chat_message': ${testMsg}`, 'sent');
            socket.emit('chat_message', { message: testMsg });
        });
        
        // Send message button
        sendBtn.addEventListener('click', () => {
            const text = messageInput.value.trim();
            if (text) {
                addLog(`Sending message: ${text}`, 'sent');
                socket.emit('message', text);
                messageInput.value = '';
            }
        });
        
        // Send on Enter key
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendBtn.click();
            }
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
    """Serve the Socket.IO client at the expected path"""
    # Create the js directory if it doesn't exist
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
        except Exception as e:
            print(f"Error downloading Socket.IO client: {e}")
            # Return a script that will use CDN
            return """
            console.warn("Local Socket.IO client not found, using CDN");
            document.write('<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>');
            """
    
    return send_from_directory('static/js', 'socket.io.min.js')

# Socket.IO Event Handlers
@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    print(f"🟢 CLIENT CONNECTED: {request.sid}")
    # Send an immediate welcome message
    emit('chat_reply', {'text': "Connected to server!"})
    print(f"📤 SENT welcome message to {request.sid}")

@socketio.on('message')
def handle_message(msg):
    """The critical message handler that must work"""
    print(f"🔥 MESSAGE RECEIVED: {msg}")
    reply = f"Echo: {msg}"
    print(f"📤 SENDING: {reply}")
    # IMPORTANT: Use broadcast=True to ensure everyone gets the message
    emit('chat_reply', {'text': reply}, broadcast=True)
    print(f"✅ EMIT COMPLETED")

@socketio.on('chat_message')
def handle_chat(data):
    """Handle chat_message events"""
    print(f"💬 CHAT MESSAGE RECEIVED: {data}")
    
    # Extract message from data
    if isinstance(data, dict):
        message = data.get('message', '') or data.get('text', '') or str(data)
    else:
        message = str(data)
    
    reply = f"You said: {message}"
    print(f"📤 SENDING CHAT REPLY: {reply}")
    
    # Try all possible event types
    emit('chat_reply', {'text': reply}, broadcast=True)
    emit('chat_response', {'message': reply}, broadcast=True)
    emit('message', reply, broadcast=True)
    
    print("✅ ALL EMITS COMPLETED")

# Catch all events for debugging
@socketio.on_error_default
def default_error_handler(e):
    print(f"❌ ERROR: {e}")

if __name__ == '__main__':
    port = 5505
    
    # Critical diagnostic info
    print("\n========= Socket.IO Diagnostic Mode =========")
    print(f"Python version: {sys.version}")
    try:
        print(f"Flask-SocketIO version: {socketio.__version__}")
    except:
        print("Could not determine Flask-SocketIO version")
    
    print(f"\nServer configuration:")
    print(f"- async_mode: {socketio.async_mode}")
    print(f"- cors_allowed_origins: {socketio.cors_allowed_origins}")
    print(f"- Using threading mode (not eventlet)")
    
    print(f"\nStarting server at http://0.0.0.0:{port}")
    print(f"Open http://localhost:{port}/ in your browser")
    print("Press Ctrl+C to stop the server\n")
    
    # Run with threading mode
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True) 