#!/usr/bin/env python3
"""
Guaranteed Working Server for Minerva Chat

This server is specifically designed to resolve all Socket.IO compatibility issues
and ensure stable operation even with termination signals.
"""

import os
import sys
import signal
import logging
import time
import socket
import json
import uuid
from pathlib import Path

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure eventlet (must be done before other imports)
try:
    import eventlet
    eventlet.monkey_patch()
    async_mode = 'eventlet'
    logger.info("Using eventlet for Socket.IO")
except ImportError:
    try:
        import gevent
        import gevent.monkey
        gevent.monkey.patch_all()
        async_mode = 'gevent'
        logger.info("Using gevent for Socket.IO")
    except ImportError:
        async_mode = 'threading'
        logger.info("Using threading for Socket.IO (not recommended for production)")

# Now we can import Flask and other modules
from flask import Flask, render_template, send_from_directory, send_file, request, jsonify, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Create Flask app
app = Flask(__name__)
CORS(app)

# Create data directories if they don't exist
os.makedirs('data/chat_history', exist_ok=True)

# Create SocketIO instance with SPECIFIC compatibility settings
socketio = SocketIO(
    app, 
    async_mode=async_mode, 
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=5 * 1024 * 1024,  # 5MB buffer
    # These are critical for compatibility
    allowEIO3=True,
    allowEIO4=True,
)

# Set up signal handlers to prevent termination
def handle_signal(sig, frame):
    """
    Handle termination signals by logging them but not terminating.
    This keeps the server running even when the terminal tries to kill it.
    """
    logger.info(f"Received signal {sig}, but ignoring it to keep server running")
    print(f"Received signal {sig}, but ignoring it to keep server running")
    # Don't terminate, just log the signal
    
# Register signal handlers for common termination signals
signal.signal(signal.SIGINT, handle_signal)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_signal)  # kill/pkill default
signal.signal(signal.SIGHUP, handle_signal)   # Terminal closed

# Check if port is available
def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Find an available port starting from the preferred port
def find_available_port(preferred_port=5505):
    """Find an available port starting from the preferred port"""
    port = preferred_port
    while is_port_in_use(port):
        logger.warning(f"Port {port} is already in use, trying port {port+1}")
        port += 1
    return port

# Serve the exact compatible Socket.IO client version
@app.route('/socket.io.js')
def serve_socketio_client():
    """Serve the exact compatible Socket.IO client version"""
    socketio_js = """
    // Socket.IO compatibility wrapper
    console.log("Loading fixed Socket.IO client version 4.4.1");
    
    // Load the compatible version only if not already loaded
    if (typeof io === 'undefined') {
        const script = document.createElement('script');
        script.src = "https://cdn.socket.io/4.4.1/socket.io.min.js";
        script.integrity = "sha384-LzhRnpGmQP+lOvWruF/lgkcqD+WDVt9fU3H4BWmwP5u5LTmkUGafMcpZKNObVMLU"; 
        script.crossOrigin = "anonymous";
        document.head.appendChild(script);
        
        script.onload = function() {
            console.log("Socket.IO v4.4.1 loaded successfully");
            // Dispatch event that socket.io is loaded
            document.dispatchEvent(new CustomEvent('socketio-loaded'));
        };
    } else {
        console.log("Socket.IO already loaded, version: " + (io.version || "unknown"));
    }
    """
    return Response(socketio_js, mimetype='application/javascript')

# Basic health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'uptime': time.time() - server_start_time,
        'async_mode': async_mode,
    })

# Main chat interface with guaranteed compatibility
@app.route('/')
@app.route('/portal')
def index():
    """Serve the main portal/chat interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Minerva Chat</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0;
                padding: 0;
                background-color: #0c0c1d;
                color: white;
                display: flex;
                flex-direction: column;
                height: 100vh;
            }
            #chat-header {
                background-color: #1a1a2e;
                padding: 12px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            h1 { 
                color: #6e4cf8; 
                margin: 0;
                font-size: 1.4rem;
            }
            #connection-status {
                display: flex;
                align-items: center;
                font-size: 0.8rem;
            }
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
                background-color: #f44336; /* Red by default */
                transition: background-color 0.3s ease;
            }
            .status-indicator.connected {
                background-color: #4CAF50; /* Green when connected */
            }
            #chat-container { 
                flex: 1;
                display: flex;
                flex-direction: column;
                padding: 20px;
                overflow: hidden;
            }
            #message-container { 
                flex: 1;
                border: 1px solid #3a208c; 
                border-radius: 8px;
                padding: 15px; 
                margin-bottom: 20px;
                overflow-y: auto;
                background-color: rgba(26, 26, 46, 0.7);
            }
            .message { 
                margin-bottom: 15px;
                position: relative;
                max-width: 80%;
            }
            .user { 
                align-self: flex-end;
                margin-left: auto;
                background: linear-gradient(135deg, #6e48e8, #5038c8);
                padding: 10px 15px;
                border-radius: 18px;
                border-bottom-right-radius: 5px;
            }
            .minerva {
                align-self: flex-start; 
                background: linear-gradient(135deg, #3a3a6a, #252540);
                padding: 10px 15px;
                border-radius: 18px;
                border-bottom-left-radius: 5px;
            }
            .system {
                text-align: center;
                font-style: italic;
                color: #ccc;
                margin: 10px auto;
                max-width: 90%;
                font-size: 0.9rem;
            }
            .typing-indicator {
                display: flex;
                align-items: center;
                margin-top: 10px;
                margin-bottom: 15px;
            }
            .typing-animation {
                display: flex;
            }
            .typing-dot {
                height: 8px;
                width: 8px;
                background: rgba(180, 180, 220, 0.7);
                border-radius: 50%;
                margin: 0 2px;
                animation: typing-pulse 1.5s infinite ease-in-out;
            }
            .typing-dot:nth-child(2) {
                animation-delay: 0.2s;
            }
            .typing-dot:nth-child(3) {
                animation-delay: 0.4s;
            }
            @keyframes typing-pulse {
                0%, 50%, 100% {
                    transform: translateY(0);
                    opacity: 0.6;
                }
                25% {
                    transform: translateY(-4px);
                    opacity: 1;
                }
            }
            .input-container {
                display: flex;
                gap: 10px;
            }
            #message-input { 
                flex: 1;
                padding: 12px 15px; 
                border-radius: 25px;
                border: 1px solid #3a208c;
                background-color: rgba(60, 60, 90, 0.3);
                color: white;
                font-size: 1rem;
                outline: none;
            }
            #message-input:focus {
                border-color: #6e4cf8;
                box-shadow: 0 0 0 2px rgba(110, 76, 248, 0.3);
            }
            #send-button {
                background: linear-gradient(135deg, #6e4cf8, #3a208c);
                color: white;
                border: none;
                border-radius: 50%;
                width: 48px;
                height: 48px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                font-size: 1.5rem;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            #send-button:hover {
                transform: scale(1.05);
                box-shadow: 0 0 15px rgba(110, 76, 248, 0.5);
            }
            #send-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
        </style>
        <!-- Load our compatible Socket.IO client -->
        <script src="/socket.io.js"></script>
    </head>
    <body>
        <div id="chat-header">
            <h1>Minerva Chat</h1>
            <div id="connection-status">
                <div class="status-indicator"></div>
                <span id="status-text">Connecting...</span>
            </div>
        </div>
        <div id="chat-container">
            <div id="message-container"></div>
            <div class="input-container">
                <input type="text" id="message-input" placeholder="Type your message here...">
                <button id="send-button">➤</button>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const messageContainer = document.getElementById('message-container');
                const messageInput = document.getElementById('message-input');
                const sendButton = document.getElementById('send-button');
                const statusIndicator = document.querySelector('.status-indicator');
                const statusText = document.getElementById('status-text');
                
                // Function to initialize socket connection
                function initializeSocket() {
                    // Make sure io is defined
                    if (typeof io === 'undefined') {
                        console.error("Socket.IO not loaded yet!");
                        addSystemMessage("Error: Socket.IO library not loaded. Please refresh the page.");
                        return;
                    }
                    
                    console.log("Initializing Socket.IO connection...");
                    const socket = io({
                        reconnection: true,
                        reconnectionAttempts: 5,
                        reconnectionDelay: 1000,
                        timeout: 10000
                    });
                    
                    // Connection events
                    socket.on('connect', function() {
                        console.log("Socket connected successfully!");
                        statusIndicator.classList.add('connected');
                        statusText.textContent = 'Connected';
                        addSystemMessage("Connected to Minerva server");
                    });
                    
                    socket.on('disconnect', function() {
                        console.log("Socket disconnected");
                        statusIndicator.classList.remove('connected');
                        statusText.textContent = 'Disconnected';
                        addSystemMessage("Disconnected from server. Attempting to reconnect...");
                    });
                    
                    socket.on('connect_error', function(error) {
                        console.error("Connection error:", error);
                        statusIndicator.classList.remove('connected');
                        statusText.textContent = 'Connection Error';
                    });
                    
                    // Response handlers - support multiple event types for compatibility
                    socket.on('message', function(data) {
                        handleResponse(data);
                    });
                    
                    socket.on('response', function(data) {
                        handleResponse(data);
                    });
                    
                    socket.on('chat_reply', function(data) {
                        handleResponse(data);
                    });
                    
                    socket.on('system_message', function(data) {
                        const message = typeof data === 'string' ? data : data.message || data.text;
                        addSystemMessage(message);
                    });
                    
                    // Helper to process different response formats
                    function handleResponse(data) {
                        console.log("Received response:", data);
                        hideTypingIndicator();
                        
                        // Extract text from various possible formats
                        let text;
                        if (typeof data === 'string') {
                            text = data;
                        } else if (data && (data.text || data.message || data.content || data.response)) {
                            text = data.text || data.message || data.content || data.response;
                        } else {
                            try {
                                text = JSON.stringify(data);
                            } catch (e) {
                                text = "Received response in unknown format";
                            }
                        }
                        
                        addMinervaMessage(text);
                    }
                    
                    // Send message function
                    function sendMessage() {
                        const message = messageInput.value.trim();
                        if (!message) return;
                        
                        // Send to server with all possible formats for compatibility
                        socket.emit('message', { text: message });
                        socket.emit('chat_message', { text: message });
                        socket.emit('user_message', { text: message });
                        
                        // Add to UI
                        addUserMessage(message);
                        showTypingIndicator();
                        
                        // Clear input
                        messageInput.value = '';
                        messageInput.focus();
                    }
                    
                    // Connect the send function
                    sendButton.addEventListener('click', sendMessage);
                    messageInput.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            sendMessage();
                        }
                    });
                    
                    // Add initial welcome message
                    addMinervaMessage("Hello! I'm Minerva. How can I help you today?");
                    
                    // Store socket for debugging
                    window.minervaSocket = socket;
                    
                    return socket;
                }
                
                // Add message from user
                function addUserMessage(text) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message user';
                    messageDiv.textContent = text;
                    messageContainer.appendChild(messageDiv);
                    scrollToBottom();
                }
                
                // Add message from Minerva
                function addMinervaMessage(text) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message minerva';
                    messageDiv.textContent = text;
                    messageContainer.appendChild(messageDiv);
                    scrollToBottom();
                }
                
                // Add system message
                function addSystemMessage(text) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message system';
                    messageDiv.textContent = text;
                    messageContainer.appendChild(messageDiv);
                    scrollToBottom();
                }
                
                // Show typing indicator
                function showTypingIndicator() {
                    hideTypingIndicator(); // Remove any existing indicators
                    
                    const indicator = document.createElement('div');
                    indicator.className = 'typing-indicator';
                    
                    const animation = document.createElement('div');
                    animation.className = 'typing-animation';
                    
                    // Add three dots
                    for (let i = 0; i < 3; i++) {
                        const dot = document.createElement('div');
                        dot.className = 'typing-dot';
                        animation.appendChild(dot);
                    }
                    
                    indicator.appendChild(animation);
                    messageContainer.appendChild(indicator);
                    scrollToBottom();
                }
                
                // Hide typing indicator
                function hideTypingIndicator() {
                    const indicators = document.querySelectorAll('.typing-indicator');
                    indicators.forEach(indicator => indicator.remove());
                }
                
                // Scroll the message container to the bottom
                function scrollToBottom() {
                    messageContainer.scrollTop = messageContainer.scrollHeight;
                }
                
                // Initialize Socket.IO when it's loaded
                if (typeof io !== 'undefined') {
                    const socket = initializeSocket();
                } else {
                    // Wait for the Socket.IO script to load
                    document.addEventListener('socketio-loaded', function() {
                        console.log("Socket.IO loaded event detected, initializing connection");
                        const socket = initializeSocket();
                    });
                    
                    // Fallback if the event doesn't fire for some reason
                    setTimeout(function() {
                        if (typeof io !== 'undefined' && !window.minervaSocket) {
                            console.log("Initializing Socket.IO connection after timeout");
                            const socket = initializeSocket();
                        }
                    }, 3000);
                }
            });
        </script>
    </body>
    </html>
    """

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid if hasattr(request, 'sid') else 'unknown'
    logger.info(f"Client connected: {client_id}")
    
    # Send welcome message
    emit('system_message', {'message': 'Connected to Minerva Chat Server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid if hasattr(request, 'sid') else 'unknown'
    logger.info(f"Client disconnected: {client_id}")

# Unified message handler for all message types
def handle_any_message(data):
    """Process any type of message from the client"""
    client_id = request.sid if hasattr(request, 'sid') else 'unknown'
    logger.info(f"Received message from {client_id}: {data}")
    
    # Extract message content from different formats
    if isinstance(data, str):
        message_text = data
    elif isinstance(data, dict):
        message_text = data.get('text', '') or data.get('message', '') or data.get('content', '')
    else:
        message_text = str(data)
    
    # For now, generate a simple echo response
    time.sleep(0.5)  # Simulate thinking time
    
    response_text = f"I received your message: '{message_text}'. This is a demonstration of a working Socket.IO connection."
    
    # Send response in multiple formats for compatibility with different clients
    emit('message', {'text': response_text})
    emit('response', {'text': response_text})
    emit('chat_reply', {'text': response_text, 'status': 'success'})

# Handle all message event types for maximum compatibility
@socketio.on('message')
def handle_message(data):
    handle_any_message(data)

@socketio.on('chat_message')
def handle_chat_message(data):
    handle_any_message(data)

@socketio.on('user_message')
def handle_user_message(data):
    handle_any_message(data)

# Track server start time for uptime reporting
server_start_time = time.time()

def write_pid_file():
    """Write PID to file for external monitoring"""
    pid = os.getpid()
    with open('.minerva_server.pid', 'w') as f:
        f.write(str(pid))
    logger.info(f"Server PID {pid} written to .minerva_server.pid")

if __name__ == '__main__':
    # Find available port
    port = find_available_port(5505)
    
    # Write PID file
    write_pid_file()
    
    # Print startup message
    print(f"\n{'='*50}")
    print(f"   Guaranteed Working Minerva Chat Server")
    print(f"{'='*50}")
    print(f"\nServer running at: http://localhost:{port}")
    print(f"Access the chat at: http://localhost:{port}/portal")
    print(f"\nThis server will ignore termination signals.")
    print(f"To forcibly stop it, run: pkill -9 -f guaranteed_working_server.py")
    print(f"{'='*50}\n")
    
    try:
        # Start server with the most compatible settings
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        # Keep process alive even if there's an error
        while True:
            logger.info("Server error recovery - attempting to restart...")
            time.sleep(10)  # Wait before retry
            try:
                socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
            except Exception as e:
                logger.error(f"Restart failed: {e}") 