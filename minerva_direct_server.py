#!/usr/bin/env python3
"""
Minerva Direct Server

A standalone server that:
1. Ignores SIGTERM signals
2. Properly handles Socket.IO client versions
3. Provides its own coordinator implementation
4. Works with the existing portal
"""

import os
import sys
import time
import json
import signal
import logging
import datetime
import traceback
from pathlib import Path

# === CRITICAL: SIGNAL HANDLING (MUST BE FIRST) ===
signal.signal(signal.SIGTERM, signal.SIG_IGN)
original_sigint = signal.getsignal(signal.SIGINT)
signal.signal(signal.SIGINT, lambda signum, frame: exit_handler())
print("✅ Signal handlers installed - server ignores SIGTERM")

# === SETUP LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("minerva-direct")

# === INSTALL DEPENDENCIES IF NEEDED ===
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
    from flask_socketio import SocketIO, emit
    from flask_cors import CORS
except ImportError:
    print("Installing Flask and Socket.IO...")
    os.system(f"{sys.executable} -m pip install -q flask flask-socketio flask-cors")
    from flask import Flask, render_template, send_from_directory, jsonify, request
    from flask_socketio import SocketIO, emit
    from flask_cors import CORS
    print("✅ Flask and Socket.IO installed")

# === COORDINATOR IMPLEMENTATION ===
class MultiAICoordinator:
    """
    Self-contained AI coordinator that works with both simulated and real models
    """
    def __init__(self):
        self.available_models = {}
        self.setup_models()
        print(f"✅ MultiAICoordinator initialized with {len(self.available_models)} models")
    
    def setup_models(self):
        """Initialize available models based on API keys"""
        default_model = None
        
        # Check for OpenAI
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if openai_key and openai_key.startswith("sk-"):
            self.available_models["gpt-4"] = {
                "name": "gpt-4",
                "provider": "openai",
                "api_key": openai_key
            }
            default_model = "gpt-4"
            print("✅ OpenAI GPT-4 model available")
        
        # Check for Anthropic
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if anthropic_key and anthropic_key.startswith("sk-ant"):
            self.available_models["claude-3"] = {
                "name": "claude-3-opus-20240229",
                "provider": "anthropic",
                "api_key": anthropic_key
            }
            if not default_model:
                default_model = "claude-3"
            print("✅ Anthropic Claude 3 model available")
        
        # Check for Mistral
        mistral_key = os.environ.get("MISTRAL_API_KEY", "")
        if mistral_key:
            self.available_models["mistral"] = {
                "name": "mistral-large-latest",
                "provider": "mistral",
                "api_key": mistral_key
            }
            if not default_model:
                default_model = "mistral"
            print("✅ Mistral model available")
        
        # Add simulated model as fallback
        self.available_models["simulated"] = {
            "name": "simulated",
            "provider": "local",
            "api_key": None
        }
        
        # Set default if none available
        if not default_model:
            default_model = "simulated"
            print("⚠️ No API keys found, using simulation mode by default")
        
        self.default_model = default_model
    
    def get_available_models(self):
        """Return dictionary of available models"""
        return {
            "models": self.available_models,
            "default": self.default_model
        }
    
    def generate_response(self, message, model_preference=None, session_id=None, **kwargs):
        """Generate a response using the specified model or the default"""
        model = model_preference or self.default_model
        
        # If model not available, use default
        if model not in self.available_models:
            model = self.default_model
        
        # Get model details
        model_info = self.available_models[model]
        provider = model_info["provider"]
        
        try:
            # Call appropriate provider
            if provider == "openai":
                return self._call_openai(message, model_info["name"])
            elif provider == "anthropic":
                return self._call_anthropic(message, model_info["name"])
            elif provider == "mistral":
                return self._call_mistral(message, model_info["name"])
            else:
                # Use simulation as fallback
                return self._generate_simulated_response(message)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            logger.error(traceback.format_exc())
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _call_openai(self, message, model_name):
        """Call OpenAI API"""
        try:
            import openai
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            response = openai.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": message}],
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {str(e)}")
            return f"OpenAI API error: {str(e)}"
    
    def _call_anthropic(self, message, model_name):
        """Call Anthropic API"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model=model_name,
                max_tokens=1024,
                temperature=0.7,
                messages=[{"role": "user", "content": message}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic error: {str(e)}")
            return f"Anthropic API error: {str(e)}"
    
    def _call_mistral(self, message, model_name):
        """Call Mistral API"""
        try:
            import mistralai.client
            from mistralai.client import MistralClient
            client = MistralClient(api_key=os.environ.get("MISTRAL_API_KEY"))
            response = client.chat(
                model=model_name,
                messages=[{"role": "user", "content": message}],
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Mistral error: {str(e)}")
            return f"Mistral API error: {str(e)}"
    
    def _generate_simulated_response(self, message):
        """Generate a simulated response when no models are available"""
        # Simple response patterns based on input
        if "hello" in message.lower() or "hi" in message.lower():
            return "Hello! I'm Minerva, your AI assistant. How can I help you today?"
        
        elif "who are you" in message.lower():
            return "I'm Minerva, an AI assistant designed to help with a variety of tasks and questions. What can I help you with today?"
        
        elif "how are you" in message.lower():
            return "I'm functioning well, thank you for asking! How can I assist you today?"
        
        elif any(word in message.lower() for word in ["thanks", "thank you"]):
            return "You're welcome! Feel free to ask if you need anything else."
        
        elif "?" in message:
            return f"That's an interesting question about '{message}'. While I'm in simulation mode, I can't provide a detailed answer, but I'd be happy to discuss this further when connected to an AI model."
        
        elif len(message) < 10:
            return f"I see you wrote '{message}'. Could you provide more details about what you'd like to know or discuss?"
        
        else:
            return f"Thank you for your message about '{message[:30]}...'. I understand this is important to you. When I'm connected to an AI model, I can provide more helpful and detailed responses."

# Create global coordinator instance
coordinator = MultiAICoordinator()
Coordinator = coordinator  # Capitalized version for compatibility

# === FLASK APP SETUP ===
app = Flask(__name__, 
            static_folder='web',
            template_folder='templates')
CORS(app)

# Initialize Socket.IO with compatibility settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    # Critical for compatibility with different clients
    allowEIO3=True,
    allowEIO4=True,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=10 * 1024 * 1024  # 10MB buffer
)

# === ROUTES ===
@app.route("/")
def index():
    """Serve index page"""
    return render_template('index.html')

@app.route("/portal")
def portal():
    """Serve portal page"""
    return render_template('portal.html')

@app.route("/<path:path>")
def static_files(path):
    """Serve static files"""
    return send_from_directory('web', path)

@app.route("/api/status")
def status():
    """Return API status"""
    uptime = datetime.datetime.now() - start_time
    return jsonify({
        'status': 'healthy',
        'uptime': str(uptime),
        'mode': 'direct',
        'models': coordinator.get_available_models()
    })

# === SOCKET.IO EVENT HANDLERS ===
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    print(f"Client connected: {request.sid}")
    emit('system_message', {'message': 'Connected to Minerva Direct Server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")
    print(f"Client disconnected: {request.sid}")

# === CENTRALIZED MESSAGE HANDLING ===
# Support all possible message formats from various client versions
@socketio.on('chat_message')
@socketio.on('user_message')
@socketio.on('chat')
@socketio.on('message')
def handle_message(data):
    """Handle user messages regardless of format"""
    try:
        # Extract message from different possible formats
        if isinstance(data, str):
            user_message = data
        else:
            # Try different field names
            user_message = (
                data.get('message', '') or 
                data.get('text', '') or 
                data.get('content', '') or
                str(data)
            ).strip()
        
        session_id = data.get('session_id', f'session_{int(time.time())}') if isinstance(data, dict) else None
        model = data.get('model', None) if isinstance(data, dict) else None
        
        # Log the received message
        logger.info(f"Received message: '{user_message}'")
        print(f"Received message: '{user_message}'")
        
        # Start typing indicator
        emit('typing_indicator', {'status': 'typing'})
        
        if not user_message:
            response_text = "I received an empty message. Please try again."
        else:
            # Generate response using coordinator
            response_text = coordinator.generate_response(
                user_message, 
                model_preference=model,
                session_id=session_id
            )
        
        logger.info(f"Sending response: '{response_text[:50]}...'")
        print(f"Sending response: '{response_text[:50]}...'")
        
        # Send through all possible response channels for compatibility
        # Different client versions use different event/data formats
        
        # Format 1: Raw string (oldest clients)
        emit('response', response_text)
        
        # Format 2: Response object with message property (newer clients)
        emit('response', {'message': response_text, 'reply': response_text})
        
        # Format 3: AI response object (common format)
        emit('ai_response', {'message': response_text})
        
        # Format 4: Chat reply object (portal format)
        emit('chat_reply', {
            'text': response_text,
            'status': 'success',
            'session_id': session_id
        })
        
        # Turn off typing indicator
        emit('typing_indicator', {'status': 'idle'})
        
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        logger.error(traceback.format_exc())
        emit('system_message', {'message': f"Error: {str(e)}"})
        emit('typing_indicator', {'status': 'idle'})

# === ERROR HANDLING ===
@socketio.on_error_default
def default_error_handler(e):
    logger.error(f"Socket.IO error: {str(e)}")
    logger.error(traceback.format_exc())
    emit('system_message', {'message': f"Socket.IO error: {str(e)}"})

# === CLEAN EXIT HANDLING ===
def exit_handler():
    print("\nShutting down gracefully...")
    print("Server terminated by user")
    # Restore original handler and exit
    signal.signal(signal.SIGINT, original_sigint)
    sys.exit(0)

# === MAIN EXECUTION ===
if __name__ == '__main__':
    start_time = datetime.datetime.now()
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5505))
    
    print("\n==================================================")
    print(f"🚀 STARTING MINERVA DIRECT SERVER on port {port}")
    print("==================================================")
    print(f"✅ Visit http://{host}:{port}/portal in your browser")
    print(f"✅ Server is protected from SIGTERM signals")
    print(f"✅ Socket.IO compatibility enabled for all clients")
    print(f"✅ Using coordinator with models: {list(coordinator.available_models.keys())}")
    print(f"✅ Default model: {coordinator.default_model}")
    print("==================================================\n")
    
    try:
        socketio.run(app, host=host, port=port)
    except KeyboardInterrupt:
        print("\nServer shutdown requested by user")
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        traceback.print_exc()
    finally:
        print("Server shutdown complete") 