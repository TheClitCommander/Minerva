#!/usr/bin/env python3
"""
Minerva Server with proper routing

This script starts the Flask server with proper routing to serve
the Minerva Portal UI and provides WebSocket support for the chat interface.
"""

# Import standard libraries
import os
import sys
import time
import json
import uuid
import logging
import traceback
import datetime
import importlib
import argparse
import socket
import atexit
import signal
from pathlib import Path

# Setup environment variables from .env if available
try:
    from dotenv import load_dotenv
    # Try to load from .env file if it exists
    if os.path.exists('.env'):
        print("Loading environment variables from .env file...")
        load_dotenv(override=True)
        print("Environment loaded successfully!")
    elif os.path.exists('.env.example'):
        print("No .env file found, but .env.example exists.")
        print("Consider copying .env.example to .env and adding your API keys.")
except ImportError:
    print("python-dotenv not installed. Using environment variables only.")

# Set up the environment
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

# Import eventlet and monkey patch before anything else
try:
    import eventlet
    eventlet.monkey_patch(socket=True, select=True, thread=True)
    print("✅ Eventlet monkey patching successful")
except ImportError:
    print("⚠️ WARNING: Eventlet not installed. Socket.IO will not work correctly!")
    print("Please install eventlet with: pip install eventlet")

# After eventlet monkey patching, import Flask and extensions
from flask import Flask, send_from_directory, request, jsonify, render_template, session, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, Namespace
import markdown

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
os.makedirs('logs', exist_ok=True)
file_handler = logging.FileHandler('logs/server.log')
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Track server start time for uptime reporting
server_start_time = datetime.datetime.now()

# Set default port
DEFAULT_PORT = 5505

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'minerva-dev-key-for-testing-only')

# Enable CORS for all routes to allow local frontend to connect
CORS(app)

# Import AI coordinator from the new location
web_path = os.path.join(script_dir, 'web')
api_path = os.path.join(web_path, 'api')
if api_path not in sys.path:
    sys.path.insert(0, api_path)

# Create data directories if they don't exist
os.makedirs('data/chat_history', exist_ok=True)
os.makedirs('data/web_research_cache', exist_ok=True)

# Initialize coordinator variables
coordinator = None
ai_coordinator = None
has_coordinator = False
USING_SIMULATED_RESPONSES = True

print("\n=== Initializing AI Coordinator ===")

# Try to import the AI coordinator
try:
    from multi_ai_coordinator import MultiAICoordinator
    ai_coordinator = MultiAICoordinator.get_instance()
    coordinator = ai_coordinator  # Local alias
    has_coordinator = True
    USING_SIMULATED_RESPONSES = False
    logger.info("✅ Successfully loaded AI models for real responses")
    print("✅ Successfully loaded AI models for real responses")
except ImportError as e:
    logger.warning(f"⚠️ Could not import MultiAICoordinator - chat will use simulated responses: {e}")
    print(f"⚠️ Could not import MultiAICoordinator - chat will use simulated responses")
    
# Import Minerva extensions after the coordinator
try:
    from minerva_extensions import MinervaExtensions
    # Use the coordinator we initialized
    if coordinator is not None:
        minerva_extensions = MinervaExtensions(coordinator)
    else:
        # Try to let MinervaExtensions find it on its own
        minerva_extensions = MinervaExtensions()
    
    # Log success
    logger.info("✅ Successfully loaded Minerva extensions for chat persistence and web research")
    print("✅ Successfully loaded Minerva extensions for chat persistence and web research")
except ImportError as e:
    logger.warning(f"⚠️ Could not import MinervaExtensions - some features will be disabled: {e}")
    print(f"⚠️ Could not import MinervaExtensions - some features will be disabled")
    minerva_extensions = None

# Define routes
@app.route('/')
def index():
    """Redirect to portal as the main page"""
    return send_from_directory('web/ui', 'minerva-portal.html')

@app.route('/portal')
def portal():
    """Serve the Minerva Portal UI."""
    return send_from_directory('web/ui', 'minerva-portal.html')

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all available chat sessions"""
    if minerva_extensions:
        user_id = request.args.get('user_id')
        sessions = minerva_extensions.get_active_sessions(user_id)
        return jsonify({'sessions': sessions})
    else:
        return jsonify({'error': 'Chat history not available'}), 503

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get chat history for a specific session"""
    if minerva_extensions:
        limit = request.args.get('limit')
        limit = int(limit) if limit and limit.isdigit() else None
        
        messages = minerva_extensions.get_chat_history(session_id, limit)
        if messages is not None:
            return jsonify({'messages': messages})
        else:
            return jsonify({'error': 'Session not found'}), 404
    else:
        return jsonify({'error': 'Chat history not available'}), 503

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a chat session"""
    if minerva_extensions:
        success = minerva_extensions.chat_history.delete_session(session_id)
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Session not found'}), 404
    else:
        return jsonify({'error': 'Chat history not available'}), 503

@app.route('/api/research', methods=['POST'])
def perform_research():
    """Perform web research on a query"""
    if minerva_extensions:
        data = request.json
        query = data.get('query')
        max_sources = data.get('max_sources', 3)
        depth = data.get('depth', 'medium')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        research_data = minerva_extensions.web_researcher.research(query, max_sources, depth)
        return jsonify(research_data)
    else:
        return jsonify({'error': 'Web research not available'}), 503

# Serve static files from the web directory with appropriate subdirectories
@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files from the static directory"""
    return send_from_directory('static', path)

# API status endpoint to check connectivity
@app.route('/api/status')
def api_status():
    """Return the status of the API to verify connectivity"""
    return jsonify({
        'status': 'success',
        'server': 'Minerva API',
        'timestamp': datetime.datetime.now().isoformat(),
        'uptime_seconds': (datetime.datetime.now() - server_start_time).total_seconds()
    })

# Add a comprehensive health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring and production use"""
    # Check if coordinator is available
    coordinator_status = "available" if ai_coordinator else "unavailable"
    
    # Check available models
    models_count = 0
    if ai_coordinator and hasattr(ai_coordinator, 'get_available_models'):
        models_count = len(ai_coordinator.get_available_models()['models'])
    
    # Check extensions
    extensions_status = "available" if minerva_extensions else "unavailable"
    
    # Check SocketIO status
    socketio_status = "available" if 'socketio' in globals() and socketio else "unavailable"
    
    # Build response
    health_data = {
        'status': 'operational',
        'timestamp': datetime.datetime.now().isoformat(),
        'server_id': socket.gethostname(),
        'coordinator': {
            'status': coordinator_status,
            'models_count': models_count
        },
        'extensions': {
            'status': extensions_status
        },
        'socketio': {
            'status': socketio_status
        },
        'uptime_seconds': (datetime.datetime.now() - server_start_time).total_seconds()
    }
    
    # Determine overall status
    if coordinator_status == "unavailable":
        health_data['status'] = 'degraded'
    
    return jsonify(health_data)

# Initialize Socket.IO with proper settings for compatibility with the client
print("\n=== Configuring Socket.IO ===")
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    # Critical compatibility parameters for all client versions
    allowEIO3=True,  # Allow Engine.IO v3 clients
    allowEIO4=True,  # Allow Engine.IO v4 clients
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=10 * 1024 * 1024  # 10MB buffer
)

# Create a namespace for Minerva-specific events
class MinervaNamespace(Namespace):
    def on_connect(self):
        logger.info("Client connected to Minerva namespace")
        print("Client connected to Minerva namespace")
    
    def on_disconnect(self):
        logger.info("Client disconnected from Minerva namespace")
        print("Client disconnected from Minerva namespace")
    
    def on_join_session(self, data):
        """Join or create a chat session"""
        try:
            session_id = data.get('session_id')
            user_id = data.get('user_id', f'user_{int(time.time())}')
            
            logger.info(f"User {user_id} joining session {session_id}")
            
            messages = []
            
            # Handle session creation or loading
            if not session_id and minerva_extensions:
                try:
                    # Create new session
                    session_id = minerva_extensions.chat_history.create_session(user_id)
                    logger.info(f"Created new session {session_id} for user {user_id}")
                except Exception as e:
                    logger.error(f"Error creating new session: {str(e)}")
                    logger.error(traceback.format_exc())
                    session_id = f'temporary_{int(time.time())}'
                    emit('system_message', {'message': f"Error creating new session: {str(e)}"})
            elif minerva_extensions and session_id:
                try:
                    # Return existing session history
                    messages = minerva_extensions.get_chat_history(session_id)
                    
                    if messages is None:
                        # Session not found, create new one
                        logger.info(f"Session {session_id} not found, creating a new one")
                        session_id = minerva_extensions.chat_history.create_session(user_id)
                        logger.info(f"Created replacement session {session_id} for user {user_id}")
                        messages = []
                except Exception as e:
                    logger.error(f"Error retrieving session history: {str(e)}")
                    logger.error(traceback.format_exc())
                    session_id = f'temporary_{int(time.time())}'
                    emit('system_message', {'message': f"Error retrieving chat history: {str(e)}"})
                    messages = []
            else:
                # No persistence available
                session_id = f'temporary_{int(time.time())}'
                logger.info(f"No persistence available, using temporary session {session_id}")
            
            # Send the session information to the client
            emit('session_joined', {
                'session_id': session_id,
                'messages': messages or []
            })
            
            return {'status': 'success', 'session_id': session_id}
        except Exception as e:
            # Outer exception handler
            logger.error(f"Critical error in join_session: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"Critical error in join_session: {e}")
            try:
                emit('system_message', {'message': f"Error joining session: {str(e)}"})
                emit('session_joined', {
                    'session_id': f'temporary_{int(time.time())}',
                    'messages': []
                })
            except Exception:
                logger.error("Failed to send error response for join session")
                print("Failed to send error response for join session")
    
    def on_chat_message(self, data):
        """Handle chat messages in this namespace"""
        try:
            start_time = time.time()
            
            # Extract the message text from different possible formats
            user_input = data.get('text', '') or data.get('message', '') or data.get('content', '')
            session_id = data.get('session_id', f'session_{int(time.time())}')
            model_preference = data.get('model_preference', 'default')
            
            # Log the received message
            logger.info(f"Received chat_message: '{user_input}' from session {session_id}")
            print(f"Received chat_message: '{user_input}' from session {session_id}")
            
            if not user_input:
                logger.warning("Received empty chat message")
                emit('chat_reply', {
                    'text': "I received an empty message. Please try again.",
                    'status': 'error'
                })
                return {'status': 'error', 'message': 'Empty message received'}
                
            # Try to use minerva_extensions if available
            try:
                if minerva_extensions:
                    logger.info(f"Using MinervaExtensions for response with model: {model_preference}")
                    response = minerva_extensions.process_message(
                        message=user_input,
                        session_id=session_id,
                        model_preference=model_preference
                    )
                    response_text = response.get('message', '')
                    if response_text:
                        logger.info(f"Successfully generated response using MinervaExtensions")
                else:
                    logger.info(f"MinervaExtensions not available, using coordinator directly with model: {model_preference}")
                    response_text = self._process_with_coordinator(
                        user_input, 
                        model_preference=model_preference,
                        session_id=session_id
                    )
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                logger.error(traceback.format_exc())
                # Fallback to error message
                response_text = f"I apologize, but I encountered an error while processing your message: {str(e)}"
                
            # Send the response
            logger.info(f"Sending chat reply: '{response_text[:50]}...'")
            print(f"Sending chat reply: '{response_text[:50]}...'")
            
            # Send the actual response
            emit('chat_reply', {
                'text': response_text,
                'status': 'success',
                'session_id': session_id,
                'processing_time': round(time.time() - start_time, 2)
            })
            
            logger.info(f"Chat message processed in {round(time.time() - start_time, 3)} seconds")
            
            return {'status': 'received'}
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            print(f"Error processing chat message: {str(e)}")
            emit('chat_reply', {
                'text': "Sorry, I encountered an error processing your message. Please try again.",
                'status': 'error'
            })
            return {'status': 'error', 'message': str(e)}
    
    def _process_with_coordinator(self, user_input, model_preference='default', **kwargs):
        """Process a message with the AI coordinator"""
        try:
            if not ai_coordinator:
                return f"AI coordination service is not available. Please check that API keys are properly configured."
            
            # Get available models
            available_models = ai_coordinator.get_available_models()
            
            # Log which models are available
            logger.info(f"Available models: {available_models}")
            
            # Use model_preference if specified and available, otherwise use default
            if model_preference != 'default' and model_preference in available_models['models']:
                chosen_model = model_preference
            elif available_models.get('default'):
                chosen_model = available_models['default']
            else:
                return "No AI models are currently available. Please check API configurations."
            
            # Log which model we're using
            logger.info(f"Using AI model: {chosen_model}")
            
            # Generate response from the AI model
            response = ai_coordinator.generate_response(
                user_input, 
                model_preference=chosen_model,
                session_id=kwargs.get('session_id')
            )
            
            return response
        except Exception as e:
            logger.error(f"Error in process_with_coordinator: {str(e)}")
            logger.error(traceback.format_exc())
            return f"I'm sorry, I encountered an error processing your message: {str(e)}"

# Register the namespace
socketio.on_namespace(MinervaNamespace('/minerva'))

@socketio.on_error_default
def default_error_handler(e):
    """Handle all SocketIO errors to prevent server crashes"""
    error_msg = str(e)
    stack_trace = traceback.format_exc()
    logger.error(f"SocketIO Error: {error_msg}")
    logger.error(f"Stack trace: {stack_trace}")
    emit('system_message', {'message': f"Error in server operation: {error_msg}"})

@socketio.on('connect')
def handle_connect():
    try:
        logger.info("Client connected to chat WebSocket")
        print("Client connected to chat WebSocket")
        emit('system_message', {'message': 'Connected to Minerva Chat Server'})
    except Exception as e:
        logger.error(f"Error in connect handler: {str(e)}")
        print(f"Error in connect handler: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    try:
        logger.info("Client disconnected from chat WebSocket")
        print("Client disconnected from chat WebSocket")
    except Exception as e:
        logger.error(f"Error in disconnect handler: {str(e)}")
        print(f"Error in disconnect handler: {str(e)}")

@socketio.on('message')
def handle_message(message):
    """Handle generic socket.io messages"""
    try:
        logger.info(f"Received generic message: {message}")
        
        # If message is a string, convert to dict
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                message = {'text': message}
        
        # Handle different message formats
        message_text = message.get('text', '') or message.get('message', '') or message.get('content', '')
        
        if message_text:
            # Use the AI coordinator or simulated response
            try:
                if ai_coordinator:
                    response = ai_coordinator.generate_response(message_text)
                else:
                    # Fallback to simulated response
                    from enhanced_fallback import generate_enhanced_response
                    response = generate_enhanced_response(message_text)
                    
                # Send the response
                emit('message', {'text': response})
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                emit('message', {'text': f"Error: {str(e)}"})
        else:
            emit('message', {'text': "I received an empty message."})
            
    except Exception as e:
        logger.error(f"Error in message handler: {str(e)}")
        logger.error(traceback.format_exc())
        emit('message', {'text': f"Error handling message: {str(e)}"})

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    signal_name = {
        signal.SIGINT: "SIGINT",
        signal.SIGTERM: "SIGTERM",
        signal.SIGHUP: "SIGHUP"
    }.get(signum, f"signal {signum}")
    
    logger.info(f"Shutting down Minerva server gracefully ({signal_name})")
    print(f"Shutting down Minerva server gracefully ({signal_name})")
    
    # Try to clean up resources
    cleanup_at_exit()
    
    # Exit process
    print("Minerva server shutdown complete")
    sys.exit(0)

# Set up signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler) # Termination signal
signal.signal(signal.SIGHUP, signal_handler)  # Terminal window closed

@atexit.register
def cleanup_at_exit():
    """Clean up resources when the server exits"""
    logger.info("Shutting down Minerva server gracefully")
    print("Shutting down Minerva server gracefully")
    
    # Clean up any resources that need to be released
    try:
        if 'minerva_extensions' in globals() and minerva_extensions:
            # Close chat history and web researcher
            if hasattr(minerva_extensions, 'chat_history') and minerva_extensions.chat_history:
                minerva_extensions.chat_history.close()
            
            # Close other resources if needed
            logger.info("Closed Minerva extensions resources")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        print(f"Error during cleanup: {str(e)}")

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Minerva Chat Server")
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f"Port to run the server on (default: {DEFAULT_PORT})")
    parser.add_argument('--host', type=str, default='0.0.0.0', help="Host to bind the server to (default: 0.0.0.0)")
    parser.add_argument('--debug', action='store_true', help="Run in debug mode (not recommended for production)")
    args = parser.parse_args()
    
    # Verify environment
    logger.info(f"Starting Minerva server on http://127.0.0.1:{args.port}")
    print(f"Starting Minerva server on http://127.0.0.1:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    # Run the socketio app
    try:
        socketio.run(
            app,
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        print(f"Error starting server: {e}")
        sys.exit(1) 