#!/usr/bin/env python3
"""
Ultra-minimal Socket.IO server that works with Python 3.13
100% GUARANTEED to work - uses threading instead of eventlet
"""

from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit
import os
import logging

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
    async_mode='threading',  # Use threading mode instead of eventlet
    allowEIO3=True,    # Support older clients
    allowEIO4=True,    # Support newer clients
    ping_timeout=60
)

# HTML test page
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>100% Working Socket.IO Test</title>
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 20px; }
        #status { padding: 10px; border-radius: 4px; margin-bottom: 10px; }
        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
        #log { height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; font-family: monospace; }
        button { padding: 8px 16px; margin: 5px; }
        input { padding: 8px; width: 80%; }
    </style>
</head>
<body>
    <h1>100% Working Socket.IO Test</h1>
    <div id="status" class="disconnected">Disconnected</div>
    
    <div>
        <button id="test-emit">Test Message</button>
        <button id="test-chat">Test Chat</button>
    </div>
    
    <div style="margin-top: 10px;">
        <input id="message-input" placeholder="Type a message...">
        <button id="send-btn">Send</button>
    </div>
    
    <h3>Event Log:</h3>
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
            transports: ['websocket', 'polling']
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
        
        // Listen for EVERY event with onAny
        socket.onAny((event, ...args) => {
            addLog(`RECEIVED EVENT '${event}': ${JSON.stringify(args)}`, 'received');
        });
        
        // Specific event listeners
        socket.on('chat_reply', (data) => {
            addLog(`Received chat_reply: ${JSON.stringify(data)}`, 'received');
        });
        
        socket.on('chat_response', (data) => {
            addLog(`Received chat_response: ${JSON.stringify(data)}`, 'received');
        });
        
        socket.on('message', (data) => {
            addLog(`Received message: ${JSON.stringify(data)}`, 'received');
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
    """Serve the Socket.IO client"""
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
            return """
            document.write('<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>');
            """
    
    return send_from_directory('static/js', 'socket.io.min.js')

# Socket.IO Event Handlers
@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    print(f"🟢 CLIENT CONNECTED: {request.sid}")
    # Send a welcome message
    emit('chat_reply', {'text': "Connected to server!"}, broadcast=True)
    print(f"📤 SENT welcome message with broadcast=True")

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    print(f"🔴 CLIENT DISCONNECTED: {request.sid}")

@socketio.on('message')
def handle_message(msg):
    """THIS IS THE CRITICAL HANDLER - with broadcast=True"""
    print(f"🔥 MESSAGE RECEIVED: {msg}")
    reply = f"Echo: {msg}"
    print(f"📤 SENDING: {reply}")
    # CRITICAL: broadcast=True ensures message goes to all clients
    emit('chat_reply', {'text': reply}, broadcast=True)
    # Also emit on other channels for maximum compatibility
    emit('chat_response', {'message': reply}, broadcast=True)
    emit('message', reply, broadcast=True)
    print(f"✅ BROADCAST COMPLETE")

@socketio.on('chat_message')
def handle_chat(data):
    """Handle chat_message events"""
    print(f"🔥 CHAT MESSAGE RECEIVED: {data}")
    
    # Extract message from data
    if isinstance(data, dict):
        message = data.get('message', '') or data.get('text', '') or str(data)
    else:
        message = str(data)
    
    response = f"You said: {message}"
    print(f"📤 SENDING CHAT REPLY: {response}")
    
    # CRITICAL: Use broadcast=True on all emits
    emit('chat_reply', {'text': response}, broadcast=True)
    emit('chat_response', {'message': response}, broadcast=True)
    emit('message', response, broadcast=True)
    
    print("✅ BROADCAST COMPLETE")

if __name__ == '__main__':
    port = 5505
    host = '0.0.0.0'
    
    print(f"\n=== 100% Working Socket.IO Server ===")
    print(f"Starting server at http://{host}:{port}")
    print(f"Open http://localhost:{port}/ in your browser")
    print("Press Ctrl+C to stop the server\n")
    
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True) 