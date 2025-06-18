import os
import sys
import signal
import logging
import time
import socket

# Configure eventlet (must be done before other imports)
try:
    import eventlet
    eventlet.monkey_patch()
    async_mode = 'eventlet'
except ImportError:
    try:
        import gevent
        import gevent.monkey
        gevent.monkey.patch_all()
        async_mode = 'gevent'
    except ImportError:
        async_mode = 'threading'

# Now we can import Flask and other modules
from flask import Flask, render_template, send_from_directory, send_file, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if async_mode == 'eventlet':
    logger.info("Using eventlet for Socket.IO")
elif async_mode == 'gevent':
    logger.info("Using gevent for Socket.IO")
else:
    logger.info("Using threading for Socket.IO (not recommended for production)")

# Create Flask app
app = Flask(__name__)
CORS(app)

# Create SocketIO instance with compatibility settings
socketio = SocketIO(
    app, 
    async_mode=async_mode, 
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=5 * 1024 * 1024,  # 5MB buffer
    # Allow compatibility with older client versions
    allowEIO3=True,
    allowEIO4=True,
)

# Set up signal handlers to prevent termination
def handle_signal(sig, frame):
    logger.info(f"Received signal {sig}, but ignoring it to keep server running")
    # Don't terminate, just log the signal
    
# Register signal handlers
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGHUP, handle_signal)

# Check if port is available
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Find an available port starting from the preferred port
def find_available_port(preferred_port=5505):
    port = preferred_port
    while is_port_in_use(port):
        logger.warning(f"Port {port} is already in use, trying port {port+1}")
        port += 1
    return port

# Serve the socket_fix.js file if it exists
@app.route('/socket_fix.js')
def serve_socket_fix():
    if os.path.exists('socket_fix.js'):
        return send_file('socket_fix.js')
    else:
        return "Socket fix file not found", 404

# Routes
@app.route('/')
@app.route('/portal')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Minerva Simple Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #0c0c1d; color: white; }
            h1 { color: #6e4cf8; }
            #messageContainer { 
                border: 1px solid #3a208c; 
                padding: 10px; 
                height: 300px; 
                overflow-y: auto;
                margin-bottom: 10px;
                background-color: rgba(30, 30, 50, 0.6);
                border-radius: 8px;
            }
            #messageInput { 
                width: 80%; 
                padding: 8px; 
                background-color: rgba(50, 50, 70, 0.6);
                color: white;
                border: 1px solid #3a208c;
                border-radius: 4px;
            }
            #sendButton {
                padding: 8px 15px;
                background-color: #6e4cf8;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin-left: 10px;
            }
            .message { margin-bottom: 10px; }
            .user { text-align: right; color: #a0a0ff; }
            .minerva { text-align: left; color: #e0e0ff; }
            .system { text-align: center; color: #999; font-style: italic; }
            #status {
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 5px 10px;
                border-radius: 4px;
                background: rgba(60, 60, 90, 0.7);
                color: white;
            }
            .dot {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 5px;
                background-color: #4CAF50;
            }
            .disconnected .dot { background-color: #f44336; }
            .connecting .dot { background-color: #FFC107; }
        </style>
        <!-- First load the Socket.IO fix script to ensure compatibility -->
        <script src="/socket_fix.js"></script>
        <script>
            // Wait for page load
            document.addEventListener('DOMContentLoaded', function() {
                // Status indicator
                const status = document.createElement('div');
                status.id = 'status';
                status.className = 'connecting';
                status.innerHTML = '<span class="dot"></span> Connecting...';
                document.body.appendChild(status);
                
                // Create connection when socket.io is loaded
                function initializeSocket() {
                    console.log('Initializing socket connection');
                    // Create socket with the exact path and reconnection options
                    const socket = io({
                        reconnection: true,
                        reconnectionAttempts: 5,
                        reconnectionDelay: 1000
                    });
                    
                    const messageContainer = document.getElementById('messageContainer');
                    const messageInput = document.getElementById('messageInput');
                    const sendButton = document.getElementById('sendButton');

                    // Connection events
                    socket.on('connect', function() {
                        console.log('Connected to server');
                        addMessage('System', 'Connected to Minerva server');
                        status.className = 'connected';
                        status.innerHTML = '<span class="dot"></span> Connected';
                    });
                    
                    socket.on('disconnect', function() {
                        console.log('Disconnected from server');
                        addMessage('System', 'Disconnected from server');
                        status.className = 'disconnected';
                        status.innerHTML = '<span class="dot"></span> Disconnected';
                    });

                    socket.on('connect_error', function(error) {
                        console.error('Connection error:', error);
                        status.className = 'disconnected';
                        status.innerHTML = '<span class="dot"></span> Connection Error';
                    });
                    
                    // Handle multiple response formats from different server implementations
                    socket.on('message', function(data) {
                        handleResponse(data);
                    });
                    
                    socket.on('response', function(data) {
                        handleResponse(data);
                    });
                    
                    socket.on('chat_reply', function(data) {
                        handleResponse(data);
                    });
                    
                    socket.on('ai_response', function(data) {
                        handleResponse(data);
                    });
                    
                    function handleResponse(data) {
                        console.log('Received response:', data);
                        let text;
                        
                        // Handle different possible response formats
                        if (typeof data === 'string') {
                            text = data;
                        } else if (data && (data.text || data.message || data.content || data.response)) {
                            text = data.text || data.message || data.content || data.response;
                        } else {
                            // If the format is unknown, stringify the data
                            try {
                                text = JSON.stringify(data);
                            } catch (e) {
                                text = "Received data in unknown format";
                            }
                        }
                        
                        addMessage('Minerva', text);
                    }
                    
                    // Send message function
                    function sendMessage() {
                        const message = messageInput.value.trim();
                        if (message) {
                            // Send using multiple event names for compatibility
                            const messageObj = {text: message};
                            socket.emit('message', messageObj);
                            socket.emit('chat_message', messageObj);
                            socket.emit('user_message', messageObj);
                            
                            addMessage('You', message);
                            messageInput.value = '';
                        }
                    }
                    
                    // Add message to container
                    function addMessage(sender, text) {
                        const messageElement = document.createElement('div');
                        messageElement.className = 'message ' + (sender === 'Minerva' ? 'minerva' : (sender === 'You' ? 'user' : 'system'));
                        messageElement.innerHTML = '<strong>' + sender + ':</strong> ' + text;
                        messageContainer.appendChild(messageElement);
                        messageContainer.scrollTop = messageContainer.scrollHeight;
                    }
                    
                    // Event listeners
                    sendButton.addEventListener('click', sendMessage);
                    messageInput.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            sendMessage();
                        }
                    });
                    
                    // Initial message
                    addMessage('System', 'Welcome to Minerva Chat! Type a message to begin.');
                }
                
                // Initialize socket when ready
                if (typeof io !== 'undefined') {
                    initializeSocket();
                } else {
                    // Wait for socket.io script to load
                    document.addEventListener('socketio-compatible-loaded', initializeSocket);
                }
            });
        </script>
    </head>
    <body>
        <h1>Minerva Simple Stable Server</h1>
        <div id="messageContainer"></div>
        <input type="text" id="messageInput" placeholder="Type your message here...">
        <button id="sendButton">Send</button>
    </body>
    </html>
    """

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected from {request.remote_addr if hasattr(request, 'remote_addr') else 'unknown'}")
    emit('system_message', {'message': 'Connected to Minerva Server'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected")

# Handle messages in different formats for compatibility
@socketio.on('message')
def handle_message(data):
    handle_any_message(data)

@socketio.on('chat_message')
def handle_chat_message(data):
    handle_any_message(data)

@socketio.on('user_message')
def handle_user_message(data):
    handle_any_message(data)

# Unified message handler
def handle_any_message(data):
    logger.info(f"Received message: {data}")
    
    # Extract message text from different possible formats
    if isinstance(data, str):
        message_text = data
    elif isinstance(data, dict):
        message_text = data.get('text', '') or data.get('message', '') or data.get('content', '')
    else:
        message_text = str(data)
    
    # Echo back with a simulated response after a short delay
    time.sleep(0.5)
    
    # Generate response
    response_text = f"I received your message: '{message_text}'"
    
    # Emit response in multiple formats for compatibility
    socketio.emit('message', {'text': response_text})
    socketio.emit('response', {'text': response_text})
    socketio.emit('chat_reply', {'text': response_text, 'status': 'success'})
    socketio.emit('ai_response', {'message': response_text})

def write_pid_file():
    # Write PID to file for external monitoring/management
    pid = os.getpid()
    with open('.minerva_server.pid', 'w') as f:
        f.write(str(pid))
    logger.info(f"Server PID {pid} written to .minerva_server.pid")

if __name__ == '__main__':
    # Find available port
    port = find_available_port(5505)
    
    # Write PID file for external management
    write_pid_file()
    
    # Print startup message
    print(f"\n{'='*40}")
    print(f"   Minerva Simple Stable Server")
    print(f"{'='*40}")
    print(f"\nServer running at: http://localhost:{port}")
    print(f"Access the portal at: http://localhost:{port}/portal")
    print(f"\nThis server will ignore termination signals.")
    print(f"To forcibly stop it, run: pkill -9 -f simple_stable_server.py")
    print(f"{'='*40}\n")
    
    try:
        # Start server - this should be resistant to most signals
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        # Even if there's an exception, keep the process alive
        while True:
            logger.info("Server error recovery - attempting to restart...")
            time.sleep(10)  # Wait before retry
            try:
                socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
            except Exception as e:
                logger.error(f"Restart failed: {e}") 