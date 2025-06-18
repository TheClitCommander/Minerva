#!/usr/bin/env python3
"""
Ultra-minimal Socket.IO server - Python 3.13 compatible with NO eventlet
THREADING MODE ONLY (not eventlet)
"""

from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Create SocketIO instance with threading mode
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading',  # THREADING MODE ONLY
    allowEIO3=True,
    allowEIO4=True
)

# HTML test page
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Chat Test</title>
    <style>
        body { font-family: Arial; margin: 0; padding: 20px; max-width: 800px; margin: 0 auto; }
        #messages { height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 20px; font-family: monospace; }
        #message-form { display: flex; }
        #message-input { flex-grow: 1; padding: 10px; margin-right: 10px; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Simple Chat Test</h1>
    <div id="messages"></div>
    <form id="message-form">
        <input id="message-input" placeholder="Type a message..." autocomplete="off"/>
        <button type="submit">Send</button>
    </form>

    <script src="/socket.io/socket.io.js"></script>
    <script>
        // Connect to Socket.IO
        const socket = io();
        const messages = document.getElementById('messages');
        const form = document.getElementById('message-form');
        const input = document.getElementById('message-input');

        // Add a message to the chat
        function addMessage(message, isServer = false) {
            const div = document.createElement('div');
            div.textContent = message;
            if (isServer) {
                div.style.color = 'blue';
            }
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }

        // Socket.IO events
        socket.on('connect', () => {
            addMessage('Connected to server', true);
        });

        socket.on('disconnect', () => {
            addMessage('Disconnected from server', true);
        });

        socket.on('message', (data) => {
            addMessage(`Server: ${data}`, true);
        });

        socket.on('chat_reply', (data) => {
            addMessage(`Server: ${data.text}`, true);
        });

        // Send message
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            if (input.value) {
                // Send the message to the server
                socket.emit('chat_message', {text: input.value});
                addMessage(`You: ${input.value}`);
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

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    print(f"Client connected: {client_id}")
    # CRITICAL: broadcast=True is required when using threading mode
    emit('message', f'Welcome! Your ID is {client_id}', broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('chat_message')
def handle_message(data):
    client_id = request.sid
    message = data.get('text', '')
    print(f"Message from {client_id}: {message}")
    
    # Echo the message back to all clients
    # CRITICAL: broadcast=True is required when using threading mode
    emit('chat_reply', {'text': f"Echo: {message}"}, broadcast=True)

if __name__ == '__main__':
    print("\n=== ULTRA-MINIMAL SOCKET.IO CHAT SERVER ===")
    print(f"Python version: {sys.version}")
    print(f"Using async_mode: {socketio.async_mode}")
    print(f"Socket.IO version: {socketio.__version__}")
    print("\nStarting server at http://localhost:5505")
    print("Press Ctrl+C to stop\n")
    
    # Start the server
    socketio.run(app, host='0.0.0.0', port=5505, debug=True, allow_unsafe_werkzeug=True) 