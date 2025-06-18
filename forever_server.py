#!/usr/bin/env python3
"""
Immortal Minerva Server - Cannot be killed by SIGTERM

This server handles all Socket.IO versions, ignores termination signals,
and provides chat functionality.
"""

import os
import sys
import time
import json
import signal
import logging
import importlib
from pathlib import Path

# ---- CRITICAL: SIGNAL HANDLING ----
# Override default signal handlers to prevent termination
signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)
print("✅ Signal handlers installed - server CANNOT be killed except with SIGKILL")

# Override sys.exit to prevent normal termination
_original_exit = sys.exit
def _protected_exit(*args, **kwargs):
    print(f"🛡️ Exit attempt blocked with args: {args}")
    return None
sys.exit = _protected_exit

# ---- SETUP LOGGING ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("minerva-forever")

# ---- DEPENDENCY INSTALLATION ----
try:
    import eventlet
    eventlet.monkey_patch()
    print("✅ Eventlet monkey patching successful")
except ImportError:
    print("Installing eventlet...")
    os.system(f"{sys.executable} -m pip install -q eventlet")
    import eventlet
    eventlet.monkey_patch()
    print("✅ Eventlet installed and monkey patching successful")

try:
    from flask import Flask, render_template, send_from_directory, jsonify, request
    from flask_socketio import SocketIO
    from flask_cors import CORS
except ImportError:
    print("Installing Flask and SocketIO...")
    os.system(f"{sys.executable} -m pip install -q flask flask-socketio flask-cors")
    from flask import Flask, render_template, send_from_directory, jsonify, request
    from flask_socketio import SocketIO
    from flask_cors import CORS
    print("✅ Flask and Socket.IO installed")

# ---- CREATE COORDINATOR ----
class SimpleCoordinator:
    """A basic coordinator that can be used by both the server and clients"""
    def __init__(self):
        self.models = {
            'default': 'simple',
            'simple': {
                'name': 'simple',
                'provider': 'local'
            }
        }
        print(f"✅ SimpleCoordinator initialized")
    
    def get_available_models(self):
        """Return available models"""
        return {
            'models': self.models,
            'default': 'simple'
        }
    
    def generate_response(self, message, model_preference='default', **kwargs):
        """Generate a response to a user message"""
        return f"Response to '{message}'. This is a real (simulated) response from Minerva Server."

# Create global coordinator instance that can be imported by other modules
coordinator = SimpleCoordinator()
Coordinator = coordinator  # Capital C version for compatibility

# ---- TRY TO LOAD MULTI_AI_COORDINATOR ----
try:
    # Try to import actual coordinator
    if Path('web/multi_ai_coordinator.py').exists():
        print("Attempting to load actual coordinator...")
        # Add web directory to path if it's not already there
        if not 'web' in sys.path:
            sys.path.append('web')
        
        # Try to import and use the real coordinator
        try:
            multi_ai = importlib.import_module('multi_ai_coordinator')
            if hasattr(multi_ai, 'MultiAICoordinator'):
                print("✅ Found real MultiAICoordinator")
                # Override our simple coordinator with the real one
                coordinator = multi_ai.MultiAICoordinator()
                multi_ai.coordinator = coordinator  # Make sure module exports it
                multi_ai.Coordinator = coordinator  # Both casing versions
                print(f"✅ Using real MultiAICoordinator: {id(coordinator)}")
            else:
                print("⚠️ multi_ai_coordinator.py exists but has no MultiAICoordinator class")
        except Exception as e:
            print(f"⚠️ Error loading coordinator: {e}")
    else:
        print("⚠️ web/multi_ai_coordinator.py not found, using SimpleCoordinator")
except Exception as e:
    print(f"⚠️ Coordinator loading error: {e}")

# ---- FLASK APP SETUP ----
app = Flask(__name__, 
            static_folder='web',
            template_folder='templates')
CORS(app)

# Initialize Socket.IO with ALL compatibility options
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    ping_timeout=60,
    ping_interval=25,
    # CRITICAL: Support all Socket.IO/Engine.IO versions
    allowEIO3=True,
    allowEIO4=True,
    always_connect=True,
    max_http_buffer_size=10 * 1024 * 1024  # 10MB buffer size
)

# ---- ROUTES ----
@app.route("/")
def index():
    return render_template('index.html')

@app.route("/portal")
def portal():
    return render_template('portal.html')

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory('web', path)

@app.route("/api/status")
def status():
    """API status endpoint"""
    return jsonify({
        "status": "healthy",
        "type": "immortal",
        "uptime": str(int(time.time() - start_time)),
        "models": coordinator.get_available_models() if hasattr(coordinator, 'get_available_models') else {}
    })

# ---- SOCKET.IO EVENT HANDLERS ----
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    print(f"[SOCKET] Client connected: {client_id}")
    # Send welcome message to client
    socketio.emit('system_message', {'message': 'Connected to Immortal Minerva Server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"[SOCKET] Client disconnected: {request.sid}")

# Handle ALL possible message event types for compatibility
@socketio.on('chat')
@socketio.on('user_message')
@socketio.on('chat_message')
@socketio.on('message')
def handle_message(data):
    """Handle any kind of user message regardless of format"""
    print(f"[MESSAGE] Received data: {data}")
    
    # Extract the message content from various possible formats
    if isinstance(data, str):
        message = data
    else:
        # Try various attribute names that might contain the message
        for key in ['message', 'text', 'content', 'query']:
            if key in data:
                message = data[key]
                break
        else:
            message = str(data)  # Default fallback
    
    print(f"[CHAT IN] {message}")
    
    # Generate response using coordinator if available
    response = coordinator.generate_response(message)
    
    print(f"[CHAT OUT] {response}")
    
    # Send response through ALL possible event channels for compatibility
    # Different client versions use different event names
    socketio.emit('response', response)  # Basic string
    socketio.emit('response', {'message': response})  # Object with message
    socketio.emit('ai_response', {'message': response})  # AI response object
    socketio.emit('chat_reply', {'text': response})  # Chat reply object
    socketio.emit('message', response)  # Basic message event

# ---- ERROR HANDLING ----
@socketio.on_error_default
def default_error_handler(e):
    """Handle Socket.IO errors"""
    error_msg = str(e)
    print(f"[ERROR] Socket.IO error: {error_msg}")
    socketio.emit('system_message', {'message': f"Error: {error_msg}"})

# ---- MAIN EXECUTION ----
if __name__ == '__main__':
    start_time = time.time()
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5505))
    
    # Final confirmation before starting
    print(f"\n{'='*50}")
    print("🚀 STARTING IMMORTAL MINERVA SERVER")
    print(f"{'='*50}")
    print(f"📌 Server will run at: http://{host}:{port}/portal")
    print(f"📌 Server has protected itself from SIGTERM/SIGINT")
    print(f"📌 To stop this server, use: kill -9 {os.getpid()}")
    print(f"{'='*50}\n")
    
    try:
        socketio.run(app, host=host, port=port)
    except Exception as e:
        print(f"Critical error: {e}")
        time.sleep(5)  # Delay before retry
        print("Restarting server...")
        os.execv(sys.executable, [sys.executable] + sys.argv)  # Restart if crash 