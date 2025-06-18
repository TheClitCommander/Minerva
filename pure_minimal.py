#!/usr/bin/env python3
"""
Ultra-minimal Socket.IO server - Python 3.13 compatible
NO eventlet, ONLY threading mode
"""

from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit
import os
import logging
import sys

# Configure logging to show everything
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minerva-secret'

# Create SocketIO instance with threading mode ONLY
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading',  # ONLY use threading mode (no eventlet)
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=50 * 1024 * 1024,
    allowEIO3=True,          # Allow older clients
    allowEIO4=True,           # Allow newer clients
    always_connect=True      # Connect even with protocol mismatch
)

# Basic HTML test page with embedded client
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Ultra-Minimal Chat</title>
    <style>
        body { margin: 0; padding: 20px; font-family: Arial; max-width: 800px; margin: 0 auto; }
        #chat { height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 20px; }
        #form { display: flex; }
        #input { flex-grow: 1; padding: 10px; margin-right: 10px; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; }
    </style>
    <script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>
</head>
<body>
    <h1>Ultra-Minimal Chat</h1>
    <div id="chat"></div>
    <form id="form">
        <input id="input" autocomplete="off" placeholder="Type a message..." />
        <button>Send</button>
    </form>

    <script>
        const form = document.getElementById('form');
        const input = document.getElementById('input');
        const chat = document.getElementById('chat');
        
        // Connect to Socket.IO using ONLY polling (no websocket)
        const socket = io({
            transports: ['polling'],
            reconnection: true,
            reconnectionAttempts: 10,
            reconnectionDelay: 1000
        });

        // Add message to chat
        function addMessage(message, type = 'server') {
            const item = document.createElement('div');
            const time = new Date().toLocaleTimeString();
            const className = type === 'server' ? 'server-msg' : 'my-msg';
            item.className = className;
            item.innerHTML = `<span class="time">[${time}]</span> <span class="msg">${message}</span>`;
            chat.appendChild(item);
            chat.scrollTop = chat.scrollHeight;
        }

        // Connection events
        socket.on('connect', () => {
            console.log('Connected to server');
            addMessage('Connected to server');
        });

        socket.on('disconnect', (reason) => {
            console.log('Disconnected:', reason);
            addMessage('Disconnected: ' + reason);
        });

        socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            addMessage('Connection error: ' + error.message);
        });

        // Server messages
        socket.on('message', function(data) {
            console.log('Received message:', data);
            addMessage(data);
        });

        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            if (input.value) {
                console.log('Sending message:', input.value);
                socket.emit('message', input.value);
                addMessage(input.value, 'me');
                input.value = '';
            }
        });
    </script>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    """Serve the main page"""
    return HTML

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    """Client connected"""
    client_id = request.sid
    print(f"🟢 Client connected: {client_id}")
    # CRITICAL: broadcast=True is required when using threading mode
    emit('message', f'Welcome! You are connected as {client_id}', broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print(f"🔴 Client disconnected: {request.sid}")

@socketio.on('message')
def handle_message(message):
    """Handle incoming messages"""
    client_id = request.sid
    print(f"📨 Message from {client_id}: {message}")
    
    # CRITICAL: broadcast=True is required when using threading mode
    emit('message', f"Echo: {message}", broadcast=True)
    print(f"📤 Echo sent with broadcast=True")

if __name__ == '__main__':
    print("\n=== ULTRA-MINIMAL SOCKET.IO SERVER ===")
    print(f"Python version: {sys.version}")
    try:
        import flask_socketio
        print(f"Flask-SocketIO: {flask_socketio.__version__}")
    except:
        print("Could not determine Flask-SocketIO version")
    
    print("\nConfiguration:")
    print(f"  async_mode: {socketio.async_mode}")
    print(f"  cors_allowed_origins: {socketio.cors_allowed_origins}")
    
    print("\nStarting server at http://localhost:5505")
    print("Debug interface at http://localhost:5505/")
    print("Press Ctrl+C to stop\n")
    
    # Start the server with threading mode only
    socketio.run(app, host='0.0.0.0', port=5505, debug=True, allow_unsafe_werkzeug=True) 