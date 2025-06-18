#!/usr/bin/env python3
"""
Think Tank Receiver for Minerva Chat

This server only receives messages and logs them without sending responses back.
"""

import os
import sys
import signal
import logging
import time
import socket
import json
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
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Create Flask app
app = Flask(__name__)
CORS(app)

# Create data directories if they don't exist
os.makedirs('data/messages', exist_ok=True)

# Create SocketIO instance with compatibility settings
socketio = SocketIO(
    app, 
    async_mode=async_mode,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=5 * 1024 * 1024,
    allowEIO3=True,
    allowEIO4=True,
)

# Set up signal handlers to prevent termination
def handle_signal(sig, frame):
    """Handle termination signals by logging them but not terminating."""
    logger.info(f"Received signal {sig}, but ignoring it to keep server running")
    print(f"Received signal {sig}, but ignoring it to keep server running")
    
# Register signal handlers for common termination signals
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGHUP, handle_signal)

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

# Serve Socket.IO client
@app.route('/socket.io.js')
def serve_socketio_client():
    """Serve Socket.IO client version 4.4.1"""
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
            document.dispatchEvent(new CustomEvent('socketio-loaded'));
        };
    } else {
        console.log("Socket.IO already loaded, version: " + (io.version || "unknown"));
    }
    """
    return Response(socketio_js, mimetype='application/javascript')

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'uptime': time.time() - server_start_time,
        'async_mode': async_mode,
        'message_count': message_count
    })

# Main interface
@app.route('/')
@app.route('/portal')
def index():
    """Serve the main interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Think Tank Receiver</title>
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
            #header {
                background-color: #1a1a2e;
                padding: 15px 20px;
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
            #container { 
                flex: 1;
                display: flex;
                flex-direction: column;
                padding: 20px;
                overflow: auto;
            }
            .stats-box {
                background-color: rgba(26, 26, 46, 0.7);
                border: 1px solid #3a208c;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
            .message-log {
                flex: 1;
                background-color: rgba(26, 26, 46, 0.7);
                border: 1px solid #3a208c;
                border-radius: 8px;
                padding: 15px;
                overflow-y: auto;
                font-family: monospace;
                white-space: pre-wrap;
            }
            .log-entry {
                margin-bottom: 5px;
                border-bottom: 1px solid rgba(80, 80, 120, 0.5);
                padding-bottom: 5px;
            }
            .info {
                color: #4CAF50;
            }
            .warning {
                color: #FFC107;
            }
            .error {
                color: #F44336;
            }
        </style>
        <script src="/socket.io.js"></script>
    </head>
    <body>
        <div id="header">
            <h1>Think Tank Receiver</h1>
            <div id="connection-status">
                <div class="status-indicator"></div>
                <span id="status-text">Connecting...</span>
            </div>
        </div>
        <div id="container">
            <div class="stats-box">
                <h2>Stats</h2>
                <p>Messages received: <span id="message-count">0</span></p>
                <p>Running since: <span id="uptime">0s</span></p>
            </div>
            <div class="message-log" id="message-log">
                <div class="log-entry info">Server started. Waiting for messages...</div>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const statusIndicator = document.querySelector('.status-indicator');
                const statusText = document.getElementById('status-text');
                const messageLog = document.getElementById('message-log');
                const messageCount = document.getElementById('message-count');
                const uptimeDisplay = document.getElementById('uptime');
                
                let startTime = Date.now();
                let msgCount = 0;
                
                function formatUptime() {
                    const seconds = Math.floor((Date.now() - startTime) / 1000);
                    if (seconds < 60) return `${seconds}s`;
                    if (seconds < 3600) return `${Math.floor(seconds/60)}m ${seconds%60}s`;
                    return `${Math.floor(seconds/3600)}h ${Math.floor((seconds%3600)/60)}m ${seconds%60}s`;
                }
                
                function updateUptime() {
                    uptimeDisplay.textContent = formatUptime();
                }
                
                setInterval(updateUptime, 1000);
                
                function addLogEntry(message, type = 'info') {
                    const entry = document.createElement('div');
                    entry.className = `log-entry ${type}`;
                    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
                    messageLog.appendChild(entry);
                    messageLog.scrollTop = messageLog.scrollHeight;
                }
                
                // Initialize Socket.IO when it's loaded
                function initializeSocket() {
                    if (typeof io === 'undefined') {
                        addLogEntry('Socket.IO not loaded yet!', 'error');
                        return;
                    }
                    
                    addLogEntry('Initializing Socket.IO connection...');
                    
                    const socket = io({
                        reconnection: true,
                        reconnectionAttempts: 5,
                        reconnectionDelay: 1000,
                        timeout: 10000
                    });
                    
                    // Connection events
                    socket.on('connect', function() {
                        statusIndicator.classList.add('connected');
                        statusText.textContent = 'Connected';
                        addLogEntry('Connected to server');
                    });
                    
                    socket.on('disconnect', function() {
                        statusIndicator.classList.remove('connected');
                        statusText.textContent = 'Disconnected';
                        addLogEntry('Disconnected from server', 'warning');
                    });
                    
                    socket.on('connect_error', function(error) {
                        statusIndicator.classList.remove('connected');
                        statusText.textContent = 'Connection Error';
                        addLogEntry(`Connection error: ${error}`, 'error');
                    });
                    
                    // Listen for message stats
                    socket.on('message_stats', function(data) {
                        msgCount = data.count;
                        messageCount.textContent = msgCount;
                        addLogEntry(`Message count updated: ${msgCount}`);
                    });
                    
                    // Store socket for debugging
                    window.receiverSocket = socket;
                    
                    return socket;
                }
                
                if (typeof io !== 'undefined') {
                    initializeSocket();
                } else {
                    document.addEventListener('socketio-loaded', function() {
                        initializeSocket();
                    });
                    
                    setTimeout(function() {
                        if (typeof io !== 'undefined' && !window.receiverSocket) {
                            initializeSocket();
                        }
                    }, 3000);
                }
            });
        </script>
    </body>
    </html>
    """

# Global message counter
message_count = 0

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid if hasattr(request, 'sid') else 'unknown'
    logger.info(f"Client connected: {client_id}")
    emit('message_stats', {'count': message_count})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid if hasattr(request, 'sid') else 'unknown'
    logger.info(f"Client disconnected: {client_id}")

# Message handling function that just receives but doesn't respond
def handle_any_message(data):
    """Process a message without sending a response"""
    global message_count
    client_id = request.sid if hasattr(request, 'sid') else 'unknown'
    
    # Extract message content from different formats
    if isinstance(data, str):
        message_text = data
    elif isinstance(data, dict):
        message_text = data.get('text', '') or data.get('message', '') or data.get('content', '')
    else:
        message_text = str(data)
    
    # Log the message
    logger.info(f"Received message from {client_id}: {message_text}")
    
    # Save message to file for analysis
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    try:
        with open(f"data/messages/msg_{timestamp}_{message_count}.txt", "w") as f:
            f.write(f"From: {client_id}\nTimestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\nContent: {message_text}\n")
    except Exception as e:
        logger.error(f"Error saving message: {e}")
    
    # Increment counter and broadcast stats
    message_count += 1
    socketio.emit('message_stats', {'count': message_count})
    
    # Don't send any response - this is the key difference

# Register handlers for all message event types
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

if __name__ == '__main__':
    # Find available port
    port = find_available_port(5505)
    
    # Print startup message
    print(f"\n{'='*50}")
    print(f"   Think Tank Receiver - Messages Only   ")
    print(f"{'='*50}")
    print(f"\nServer running at: http://localhost:{port}")
    print(f"Access the interface at: http://localhost:{port}/portal")
    print(f"\nThis server will:") 
    print(f"✓ Receive messages from Minerva chat")
    print(f"✓ Log messages for analysis")
    print(f"✗ NOT send any responses back")
    print(f"\nTo forcibly stop it, run: pkill -9 -f think_tank_receiver.py")
    print(f"{'='*50}\n")
    
    try:
        # Start server
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        # Keep process alive even if there's an error
        while True:
            logger.info("Server error recovery - attempting to restart...")
            time.sleep(10)
            try:
                socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
            except Exception as e:
                logger.error(f"Restart failed: {e}") 