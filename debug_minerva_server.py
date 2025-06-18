#!/usr/bin/env python3
"""
Debug Minerva Server

A stripped-down version of the server with extensive logging to identify
exactly where message processing fails.
"""

import os
import sys
import signal
import logging
import time
import socket
import json
import traceback
from pathlib import Path

# Configure very verbose logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('minerva_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# CRITICAL: Ignore termination signals to prevent server shutdown
signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)

# Configure eventlet (must be done before other imports)
try:
    import eventlet
    eventlet.monkey_patch()
    async_mode = 'eventlet'
    logger.info("✅ Using eventlet for Socket.IO")
except ImportError:
    try:
        import gevent
        import gevent.monkey
        gevent.monkey.patch_all()
        async_mode = 'gevent'
        logger.info("✅ Using gevent for Socket.IO")
    except ImportError:
        async_mode = 'threading'
        logger.info("⚠️ Using threading for Socket.IO (not recommended)")

# Import Flask and Socket.IO
try:
    from flask import Flask, render_template, send_from_directory, send_file, request, jsonify
    from flask_socketio import SocketIO, emit
    from flask_cors import CORS
    logger.info("✅ Successfully imported Flask and SocketIO")
except Exception as e:
    logger.error(f"❌ Error importing Flask dependencies: {e}")
    sys.exit(1)

# Create Flask app
app = Flask(__name__)
CORS(app)
logger.info("✅ Created Flask app with CORS enabled")

# Create data directories
os.makedirs('data/chat_history', exist_ok=True)

# Create Socket.IO server with MAXIMUM compatibility settings
socketio = SocketIO(
    app, 
    async_mode=async_mode,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=5 * 1024 * 1024,
    allowEIO3=True,
    allowEIO4=True,
)
logger.info("✅ Created Socket.IO server with compatibility settings")

# Attempt to import AI Coordinator in isolated try-except blocks
try:
    from web.multi_ai_coordinator import MultiAICoordinator
    logger.info("✅ Successfully imported MultiAICoordinator")
    
    try:
        coordinator = MultiAICoordinator()
        logger.info(f"✅ Successfully initialized MultiAICoordinator: {coordinator}")
        COORDINATOR_AVAILABLE = True
    except Exception as e:
        logger.error(f"❌ Error initializing MultiAICoordinator: {e}")
        traceback.print_exc()
        COORDINATOR_AVAILABLE = False
except Exception as e:
    logger.error(f"❌ Error importing MultiAICoordinator: {e}")
    traceback.print_exc()
    COORDINATOR_AVAILABLE = False

# Attempt to import Minerva Extensions
try:
    from web.minerva_extensions import MinervaExtensions
    logger.info("✅ Successfully imported MinervaExtensions")
    
    try:
        minerva_extensions = MinervaExtensions()
        logger.info(f"✅ Successfully initialized MinervaExtensions: {minerva_extensions}")
        EXTENSIONS_AVAILABLE = True
    except Exception as e:
        logger.error(f"❌ Error initializing MinervaExtensions: {e}")
        traceback.print_exc()
        EXTENSIONS_AVAILABLE = False
except Exception as e:
    logger.error(f"❌ Error importing MinervaExtensions: {e}")
    traceback.print_exc()
    EXTENSIONS_AVAILABLE = False

# Serve the portal index page
@app.route('/')
@app.route('/portal')
def index():
    logger.info("🌐 Serving portal index page")
    try:
        return send_file('web/minerva-portal.html')
    except:
        # Fallback to simplified HTML with debug info
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Minerva Debug Portal</title>
            <script src="https://cdn.socket.io/4.6.0/socket.io.min.js"></script>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 0;
                    padding: 20px;
                    background: #111;
                    color: #eee;
                }
                #status {
                    padding: 10px;
                    margin-bottom: 15px;
                    border-radius: 5px;
                    background: #222;
                }
                #history {
                    border: 1px solid #444;
                    padding: 15px;
                    margin-bottom: 15px;
                    height: 300px;
                    overflow-y: auto;
                    border-radius: 5px;
                    background: #222;
                }
                input, button {
                    padding: 8px;
                    margin: 5px 0;
                }
                input {
                    width: 80%;
                    background: #333;
                    color: #fff;
                    border: 1px solid #555;
                    border-radius: 3px;
                }
                button {
                    background: #553399;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                }
                .debug {
                    color: #aaa;
                    font-family: monospace;
                    font-size: 0.8em;
                }
                .user { color: #77aaff; }
                .system { color: #ffaa77; }
            </style>
        </head>
        <body>
            <h1>Minerva Debug Portal</h1>
            <div id="status">Status: Initializing...</div>
            <div id="history"></div>
            <input id="message" placeholder="Type a message..." />
            <button id="send">Send</button>
            <div class="debug">Debug info will appear in the console (F12)</div>
            
            <script>
                const status = document.getElementById('status');
                const history = document.getElementById('history');
                const messageInput = document.getElementById('message');
                const sendBtn = document.getElementById('send');
                
                // Initialize socket with verbose logging
                let socket;
                
                try {
                    console.log("Attempting to connect Socket.IO...");
                    socket = io({
                        reconnection: true,
                        reconnectionAttempts: 5,
                        reconnectionDelay: 1000,
                        timeout: 20000,
                        transports: ['websocket', 'polling']
                    });
                    
                    // Connection events with extensive logging
                    socket.on('connect', () => {
                        console.log("✅ Socket.IO connected");
                        status.innerHTML = `Status: Connected <span style="color:green">●</span>`;
                        addSystemMessage("Connected to server");
                    });
                    
                    socket.on('disconnect', () => {
                        console.warn("❌ Socket.IO disconnected");
                        status.innerHTML = `Status: Disconnected <span style="color:red">●</span>`;
                        addSystemMessage("Disconnected from server");
                    });
                    
                    socket.on('connect_error', (err) => {
                        console.error("❌ Connect error:", err);
                        status.innerHTML = `Status: Connection Error <span style="color:orange">●</span>`;
                        addSystemMessage(`Connection error: ${err.message}`);
                    });
                    
                    // Add listeners for ALL possible response event types
                    socket.on('message', (data) => {
                        console.log("📥 Received 'message' event:", data);
                        handleResponse(data);
                    });
                    
                    socket.on('chat_reply', (data) => {
                        console.log("📥 Received 'chat_reply' event:", data);
                        handleResponse(data);
                    });
                    
                    socket.on('response', (data) => {
                        console.log("📥 Received 'response' event:", data);
                        handleResponse(data);
                    });
                    
                    socket.on('ai_response', (data) => {
                        console.log("📥 Received 'ai_response' event:", data);
                        handleResponse(data);
                    });
                    
                    function handleResponse(data) {
                        // Extract text from various possible formats
                        let responseText;
                        if (typeof data === 'string') {
                            responseText = data;
                        } else if (data && (data.text || data.message || data.content || data.response)) {
                            responseText = data.text || data.message || data.content || data.response;
                        } else {
                            responseText = JSON.stringify(data);
                        }
                        
                        addSystemMessage(responseText);
                    }
                } catch (e) {
                    console.error("Fatal Socket.IO initialization error:", e);
                    status.innerHTML = `Status: Failed to initialize <span style="color:red">●</span>`;
                    addSystemMessage(`Failed to initialize Socket.IO: ${e.message}`);
                }
                
                // Send message on button click or Enter key
                sendBtn.addEventListener('click', sendMessage);
                messageInput.addEventListener('keypress', e => {
                    if (e.key === 'Enter') sendMessage();
                });
                
                function sendMessage() {
                    const message = messageInput.value.trim();
                    if (!message) return;
                    
                    addUserMessage(message);
                    messageInput.value = '';
                    
                    try {
                        // Send using multiple event names for maximum compatibility
                        console.log("📤 Emitting 'chat_message' event:", message);
                        socket.emit('chat_message', { text: message });
                        
                        // Also try these alternative event names
                        console.log("📤 Emitting 'message' event for compatibility");
                        socket.emit('message', { text: message });
                        
                        console.log("📤 Emitting 'user_message' event for compatibility");
                        socket.emit('user_message', { text: message });
                    } catch (e) {
                        console.error("Error sending message:", e);
                        addSystemMessage(`Error sending message: ${e.message}`);
                    }
                }
                
                function addUserMessage(text) {
                    const div = document.createElement('div');
                    div.className = 'user';
                    div.textContent = `You: ${text}`;
                    history.appendChild(div);
                    history.scrollTop = history.scrollHeight;
                }
                
                function addSystemMessage(text) {
                    const div = document.createElement('div');
                    div.className = 'system';
                    div.textContent = `Minerva: ${text}`;
                    history.appendChild(div);
                    history.scrollTop = history.scrollHeight;
                }
                
                // Add initial system message
                addSystemMessage("Debug interface initialized. Try sending a message.");
            </script>
        </body>
        </html>
        """

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    logger.info(f"🌐 Serving static file: {path}")
    return send_from_directory('web/static', path)

# Serve the Socket.IO client script for compatibility
@app.route('/socket.io.js')
def serve_socketio_js():
    logger.info("🌐 Serving compatible Socket.IO client")
    return """
    console.log("Loading fixed Socket.IO client version 4.6.0");
    
    if (typeof io === 'undefined') {
        const script = document.createElement('script');
        script.src = "https://cdn.socket.io/4.6.0/socket.io.min.js";
        script.crossOrigin = "anonymous";
        document.head.appendChild(script);
        
        script.onload = function() {
            console.log("Socket.IO v4.6.0 loaded successfully");
            document.dispatchEvent(new CustomEvent('socketio-loaded'));
        };
    } else {
        console.log("Socket.IO already loaded: " + (io.version || "unknown version"));
    }
    """, {"Content-Type": "application/javascript"}

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid if hasattr(request, 'sid') else 'unknown'
    logger.info(f"🔌 Client connected: {client_id}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid if hasattr(request, 'sid') else 'unknown'
    logger.info(f"🔌 Client disconnected: {client_id}")

# Main message handler with all possible event names
@socketio.on('chat_message')
def handle_chat_message(data):
    """Process a chat message and send a response"""
    try:
        client_id = request.sid if hasattr(request, 'sid') else 'unknown'
        logger.info(f"🔥 Received 'chat_message' from {client_id}: {data}")
        
        # Extract the message text from various formats
        if isinstance(data, str):
            user_input = data
        elif isinstance(data, dict):
            user_input = data.get('text', '') or data.get('message', '') or data.get('content', '')
        else:
            user_input = str(data)
        
        logger.info(f"📝 Extracted message: '{user_input}'")
        
        # Try each response pathway with fallbacks
        response_text = None
        
        # Part 1: Try using the MultiAICoordinator first
        if COORDINATOR_AVAILABLE:
            try:
                logger.info("🧠 Attempting to use MultiAICoordinator...")
                response_text = process_with_coordinator(user_input)
                logger.info(f"✅ Got response from MultiAICoordinator: {response_text[:100]}...")
            except Exception as e:
                logger.error(f"❌ MultiAICoordinator failed: {e}")
                traceback.print_exc()
        
        # Part 2: Try using MinervaExtensions as fallback
        if response_text is None and EXTENSIONS_AVAILABLE:
            try:
                logger.info("🧩 Attempting to use MinervaExtensions...")
                response_text = process_with_extensions(user_input)
                logger.info(f"✅ Got response from MinervaExtensions: {response_text[:100]}...")
            except Exception as e:
                logger.error(f"❌ MinervaExtensions failed: {e}")
                traceback.print_exc()
        
        # Part 3: Use subprocess isolation if all else fails
        if response_text is None:
            try:
                logger.info("🔄 Attempting to use isolated subprocess...")
                response_text = call_isolated_ai(user_input)
                logger.info(f"✅ Got response from subprocess: {response_text[:100]}...")
            except Exception as e:
                logger.error(f"❌ Subprocess isolation failed: {e}")
                traceback.print_exc()
        
        # Part 4: Emergency fallback to dummy response
        if response_text is None:
            logger.warning("⚠️ All AI methods failed, using dummy response")
            response_text = f"🔧 DEBUG: This is a dummy response to your message: '{user_input}'"
        
        # Send the response using all possible event types for maximum compatibility
        logger.info(f"📤 Sending response via 'chat_reply': {response_text[:100]}...")
        emit('chat_reply', {'text': response_text})
        
        logger.info(f"📤 Sending response via 'response' for compatibility")
        emit('response', {'text': response_text})
        
        logger.info(f"📤 Sending response via 'message' for compatibility")
        emit('message', {'text': response_text})
        
        logger.info(f"📤 Sending response via 'ai_response' for compatibility")
        emit('ai_response', {'text': response_text})
        
        return True
        
    except Exception as e:
        error_msg = f"❌ Error in chat_message handler: {e}"
        logger.error(error_msg)
        traceback.print_exc()
        
        # Send error message to client
        emit('chat_reply', {'text': f"Error processing your message: {str(e)}"})
        return False

# Register alternative event handlers that just call the main handler
@socketio.on('message')
def handle_message(data):
    logger.info(f"🔥 Received 'message' event: {data}")
    return handle_chat_message(data)

@socketio.on('user_message')
def handle_user_message(data):
    logger.info(f"🔥 Received 'user_message' event: {data}")
    return handle_chat_message(data)

# Process message with AI coordinator
def process_with_coordinator(message):
    """Process message with MultiAICoordinator"""
    try:
        logger.info(f"🧠 Using MultiAICoordinator for: '{message[:50]}...'")
        
        if not COORDINATOR_AVAILABLE:
            logger.warning("⚠️ MultiAICoordinator not available")
            return None
        
        # Call the coordinator's generate_response method
        response = coordinator.generate_response(message)
        logger.info(f"✅ Coordinator response: {response[:100]}...")
        return response
    except Exception as e:
        logger.error(f"❌ Error in process_with_coordinator: {e}")
        traceback.print_exc()
        return None

# Process message with Minerva Extensions
def process_with_extensions(message):
    """Process message with MinervaExtensions"""
    try:
        logger.info(f"🧩 Using MinervaExtensions for: '{message[:50]}...'")
        
        if not EXTENSIONS_AVAILABLE:
            logger.warning("⚠️ MinervaExtensions not available")
            return None
        
        # Call the extensions' process_message method
        response = minerva_extensions.process_message(message)
        logger.info(f"✅ Extensions response: {response[:100]}...")
        return response
    except Exception as e:
        logger.error(f"❌ Error in process_with_extensions: {e}")
        traceback.print_exc()
        return None

# Call AI in isolated subprocess
def call_isolated_ai(prompt):
    """Call AI in isolated subprocess to avoid import/state issues"""
    try:
        logger.info(f"🔄 Using subprocess isolation for: '{prompt[:50]}...'")
        
        # Create isolation script if it doesn't exist
        isolation_script = "scripts/call_model.py"
        os.makedirs("scripts", exist_ok=True)
        
        if not os.path.exists(isolation_script):
            with open(isolation_script, "w") as f:
                f.write("""#!/usr/bin/env python3
import sys
import os
import json

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_fallback_response(prompt):
    # Simple rule-based fallback
    if "hello" in prompt.lower():
        return "Hello! I'm Minerva. How can I help you today?"
    elif "who are you" in prompt.lower():
        return "I am Minerva, an AI assistant designed to help with your questions."
    elif "what can you do" in prompt.lower():
        return "I can answer questions, provide information, and assist with various tasks."
    else:
        return f"I received your message: '{prompt}'. This is a simulated response from the isolated subprocess."

try:
    # Try to import the real coordinator first
    from web.multi_ai_coordinator import MultiAICoordinator
    coordinator = MultiAICoordinator()
    
    # Get the prompt from command line arguments
    prompt = sys.argv[1]
    
    # Generate response
    response = coordinator.generate_response(prompt)
    
    # Print response for the parent process to capture
    print(response)
    
except Exception as e:
    # Fallback to dummy response if coordinator fails
    try:
        prompt = sys.argv[1]
        fallback = generate_fallback_response(prompt)
        print(fallback)
    except:
        print("Error generating response in subprocess.")
""")
        
        # Make the script executable
        os.chmod(isolation_script, 0o755)
        
        # Call the script with the prompt as argument
        import subprocess
        result = subprocess.run(
            ["python3", isolation_script, prompt],
            capture_output=True,
            text=True,
            timeout=10  # Set timeout to prevent hanging
        )
        
        if result.returncode != 0:
            logger.error(f"❌ Subprocess failed with code {result.returncode}: {result.stderr}")
            if result.stderr:
                return f"Error generating response: {result.stderr[:100]}..."
            return None
        
        response = result.stdout.strip()
        logger.info(f"✅ Subprocess response: {response[:100]}...")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in call_isolated_ai: {e}")
        traceback.print_exc()
        return None

if __name__ == '__main__':
    try:
        # Determine port to use (default: 5505)
        port = int(os.environ.get('PORT', 5505))
        
        # Print startup message
        print(f"\n{'='*50}")
        print(f"   Debug Minerva Server (port {port})   ")
        print(f"{'='*50}")
        print(f"\nVisit: http://localhost:{port}/portal")
        print(f"❗ Logs written to minerva_debug.log\n")
        
        # Start Socket.IO server
        socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
        
    except Exception as e:
        logger.critical(f"❌❌❌ Fatal error: {e}")
        traceback.print_exc() 