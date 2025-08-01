#!/usr/bin/env python3
"""
Minerva Server with proper routing

This script starts the Flask server with proper routing to serve
minerva_central.html as the default page and provides WebSocket
support for the chat interface with advanced Think Tank features.
"""

# Import libraries
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
import eventlet
from functools import wraps
from threading import Timer
from urllib.parse import urljoin

# Set up logging first before any other imports
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# First thing: apply eventlet monkey patch
try:
    eventlet.monkey_patch()
    print("✅ Eventlet monkey patching successful")
    logger.info("✅ Eventlet monkey patching successful")
except Exception as e:
    print(f"⚠️ Eventlet monkey patching error: {e}")
    logger.error(f"⚠️ Eventlet monkey patching error: {e}")

# Now do other imports after the monkey patching
from flask import Flask, request, Response, send_from_directory, render_template, jsonify, redirect, url_for
from flask_cors import CORS  # Import CORS module
from flask_socketio import SocketIO, emit, Namespace, join_room, leave_room, disconnect
import markdown
import threading
import argparse
import socket
import atexit

# Setup environment variables from .env if available
try:
    from dotenv import load_dotenv
    # Check for .env file
    if os.path.exists('.env'):
        print("Loading environment variables from .env file...")
        load_dotenv()
        print("Environment loaded successfully!")
        
        # Print detected API keys (partial, for security)
        detected_keys = []
        for key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'MISTRAL_API_KEY', 'HUGGINGFACE_API_KEY']:
            if os.environ.get(key):
                detected_keys.append(key)
        
        if detected_keys:
            print(f"API keys detected: {', '.join(detected_keys)}")
    else:
        print("No .env file found, using system environment variables")
except ImportError:
    print("python-dotenv not installed, using system environment variables")

# Track server start time for uptime reporting
SERVER_START_TIME = datetime.datetime.now()

# Set up the Flask application
app = Flask(__name__, 
           static_folder='web/static',
           template_folder='web')

# Enable CORS for all routes to allow local frontend to connect
CORS(app)

# Import AI coordinator - add paths first
web_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')
if web_path not in sys.path:
    sys.path.insert(0, web_path)

# Create data directories if they don't exist
os.makedirs('data/chat_history', exist_ok=True)
os.makedirs('data/web_research_cache', exist_ok=True)

# Initialize coordinator variables
coordinator = None
ai_coordinator = None
has_coordinator = False
USING_SIMULATED_RESPONSES = True

print("\n=== Initializing AI Coordinator ===")

# Import directly from the singleton
try:
    from ai_coordinator_singleton import coordinator as ai_coordinator, Coordinator
    print(f"✅ Successfully imported coordinator from singleton: {id(ai_coordinator)}")
    coordinator = ai_coordinator  # Local alias
    has_coordinator = True
    USING_SIMULATED_RESPONSES = False
    
    # Show available models
    try:
        models = ai_coordinator.get_available_models()['models'] if hasattr(ai_coordinator, 'get_available_models') else []
        print(f"Available models: {models}")
    except Exception as e:
        print(f"⚠️ Error accessing coordinator models: {e}")
except ImportError as e:
    print(f"❌ Failed to import coordinator from singleton: {e}")
    print("Checking fallback method...")
    
    # Fallback to old import method
    try:
        import web.multi_ai_coordinator
        print("Successfully imported multi_ai_coordinator module")
        
        if hasattr(web.multi_ai_coordinator, 'Coordinator'):
            coordinator = web.multi_ai_coordinator.Coordinator
            ai_coordinator = coordinator
            has_coordinator = True
            USING_SIMULATED_RESPONSES = False
            print(f"✅ Found Coordinator in module: {id(coordinator)}")
    except Exception as e:
        print(f"❌ Fallback import also failed: {e}")
        
# Display status of coordinator initialization
if has_coordinator:
    print(f"\n✅ Coordinator successfully initialized")
    try:
        models = ai_coordinator.get_available_models()['models'] if hasattr(ai_coordinator, 'get_available_models') else []
        print(f"Available models: {models}")
    except Exception as e:
        print(f"⚠️ Error accessing coordinator models: {e}")
else:
    print("\n⚠️ Failed to initialize coordinator - using simulated responses")

# Import Minerva extensions AFTER we have the coordinator
try:
    from web.minerva_extensions import MinervaExtensions
    # Use the coordinator we just initialized - make sure it's not None
    if coordinator is not None:
        minerva_extensions = MinervaExtensions(coordinator)
        print(f"✅ Created MinervaExtensions with coordinator: {coordinator.__class__.__name__}")
    else:
        # Try to let MinervaExtensions find it on its own
        minerva_extensions = MinervaExtensions()
        print("⚠️ Created MinervaExtensions without coordinator - it will try to find one")
    
    # Log success
    logger.info("✅ Successfully loaded Minerva extensions for chat persistence and web research")
    print("✅ Successfully loaded Minerva extensions for chat persistence and web research")
except ImportError as e:
    logger.warning(f"⚠️ Could not import MinervaExtensions - some features will be disabled: {e}")
    print(f"⚠️ Could not import MinervaExtensions - some features will be disabled: {e}")
    minerva_extensions = None
except Exception as e:
    logger.error(f"Error initializing MinervaExtensions: {e}")
    print(f"Error initializing MinervaExtensions: {e}")
    minerva_extensions = None

# Define routes
@app.route('/')
def index():
    return render_template('index.html')


# Socket.IO compatibility routes - Added by fix_minerva_socketio.sh
@app.route('/socket.io/socket.io.js')
def serve_socketio_client():
    """Serve the Socket.IO client library at the default path"""
    return send_from_directory('web/static/js', 'socket.io.min.js')

@app.route('/compatible-socket.io.js')
def serve_compatible_socketio():
    """Serve a compatibility version of Socket.IO client for older browsers"""
    return send_from_directory('web/static/js', 'socket.io.min.js')

@app.route('/portal')
def portal():
    """Serve the new Minerva Portal UI."""
    return send_from_directory('web', 'minerva-portal.html')

@app.route('/improved-portal')
def improved_portal():
    """Serve the improved Minerva Portal UI with better orbital interactions."""
    return send_from_directory('web', 'minerva-portal-improved.html')

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

# Serve static files from the web directory
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from the web directory"""
    return send_from_directory('web', path)

try:
    socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True, 
                        async_mode='threading', allowEIO3=True, allowEIO4=True)
    print("✅ SocketIO server initialized with threading mode")
except Exception as e:
    print(f"Error creating SocketIO server: {e}")

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
                    response_text = process_with_coordinator(
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

# Create message response handler function for reuse
def process_chat_message(data, session_id=None, user_id=None, room=None):
    """Process a chat message and return a response.
    
    This function centralizes all message handling logic for reuse across
    different Socket.IO event handlers.
    """
    try:
        # Start timer for metrics
        start_time = time.time()
        
        # Log receiving the message
        logger.info(f"Processing chat message: {data}")
        
        # Extract the message text from different possible formats
        if isinstance(data, str):
            user_input = data
            model_preference = 'default'
        else:
            user_input = data.get('text', '') or data.get('message', '') or data.get('content', '')
            model_preference = data.get('model_preference', 'default')
            # Use provided session_id if available
            if data.get('session_id'):
                session_id = data.get('session_id')
        
        # Ensure we have a valid session ID
        if not session_id:
            session_id = f'temp_{int(time.time())}'
            logger.info(f"No session ID provided, using temporary: {session_id}")
        
        # Ensure we have content
        if not user_input:
            logger.warning("Empty message received")
            # Respond with error
            response_data = {
                'text': "I received an empty message. Please try again.",
                'status': 'error',
                'session_id': session_id
            }
            return response_data
            
        # Try to use the AI coordinator if available
        if ai_coordinator and not USING_SIMULATED_RESPONSES:
            logger.info(f"Using AI coordinator with model: {model_preference}")
            response = ai_coordinator.generate_response(
                user_input, 
                model_preference=model_preference,
                session_id=session_id
            )
            
            # Ensure we have a valid response
            if response:
                logger.info(f"Generated AI response in {time.time() - start_time:.2f}s")
            else:
                logger.warning("AI coordinator returned None response")
                response = "I apologize, but I couldn't generate a response at this time."
        else:
            # Use simulated response
            logger.info("Using simulated response")
            time.sleep(0.3)  # Simulate thinking time
            response = f"Simulated response to: '{user_input}'"
                        
        # Format response for consistency
        if isinstance(response, str):
            response_data = {
                'text': response,
                'status': 'success',
                'session_id': session_id
            }
        else:
            # Already an object, ensure it has the expected fields
            response_data = response
            if 'text' not in response_data and 'message' not in response_data:
                response_data['text'] = str(response)
            response_data['status'] = response_data.get('status', 'success')
            response_data['session_id'] = session_id
        
        # Add metrics
        response_data['metrics'] = {
            'response_time': time.time() - start_time,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Store in chat history if extensions available
        if minerva_extensions:
            try:
                # Add messages to history
                minerva_extensions.chat_history.add_message(
                    session_id=session_id,
                    role='user',
                    content=user_input,
                    metadata={'user_id': user_id}
                )
                
                minerva_extensions.chat_history.add_message(
                    session_id=session_id,
                    role='assistant',
                    content=response_data.get('text', '') or response_data.get('message', ''),
                    metadata=response_data.get('metadata', {})
                )
            except Exception as e:
                logger.error(f"Error storing messages in chat history: {e}")
        
        return response_data
        
    except Exception as e:
        # Handle any errors
        logger.error(f"Error processing chat message: {e}")
        logger.error(traceback.format_exc())
        return {
            'text': f"I apologize, but I encountered an error processing your message: {str(e)}",
            'status': 'error',
            'session_id': session_id
        }

# Main Socket.IO handlers (default namespace) for compatibility
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    print(f"Client connected: {client_id}")
    # Send welcome message
    emit('chat_response', {'message': 'Welcome to Minerva! How can I help you today?'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    print(f"Client disconnected: {client_id}")

@socketio.on('message')
def handle_message(data):
    """Handle generic message event (compatibility with older clients)"""
    logger.info(f"Received message event in default namespace: {data}")
    response_data = process_chat_message(data)
    emit('message', response_data)
    # Also send on response channel for compatibility
    emit('response', response_data)
    
@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat messages from clients"""
    client_id = request.sid
    print(f"🔥 Received chat_message: {data} from client {client_id}")
    
    # DIAGNOSTIC: Temporary hardcoded test response
    print("📤 Sending test response to client...")
    emit('chat_reply', {
        'text': "🧪 This is a forced test reply from the server",
        'status': 'success'
    })
    print("✅ Test response sent")
    
    try:
        # Extract message from various formats for maximum compatibility
        if isinstance(data, str):
            message = data
        elif isinstance(data, dict):
            message = data.get('message') or data.get('text') or data.get('content') or str(data)
        else:
            message = str(data)
            
        print(f"📝 Processed message: '{message}'")
            
        # Process message (using simulated response for testing)
        response = f"You said: {message}"
        print(f"🧠 Generated response: '{response}'")
        
        # Send response in multiple formats for compatibility
        print("📤 Sending actual response to client...")
        emit('chat_response', {'message': response})
        emit('chat_reply', {'text': response})  # Legacy format
        emit('response', {'text': response})    # Legacy format
        print("✅ Actual response sent")
            
        except Exception as e:
        print(f"❌ ERROR in handle_chat_message: {e}")
        import traceback
        traceback.print_exc()
        # Send error message to client
        emit('chat_response', {'message': f"Sorry, there was an error: {e}"})
        emit('chat_reply', {'text': f"Sorry, there was an error: {e}"})

# For compatibility, also handle 'message' and 'user_message' events 
@socketio.on('message')
def handle_message(data):
    """Handle 'message' event for compatibility"""
    return handle_chat_message(data)

@socketio.on('user_message')
def handle_user_message(data):
    """Handle 'user_message' event for compatibility"""
    return handle_chat_message(data)

@app.route('/test-socket')
def test_socket_page():
    """Serve the Socket.IO test page"""
    return send_file('test_socket_connection.html')

@app.route('/debug-chat')
def debug_chat_page():
    """Serve the debug chat page"""
    return send_from_directory('web', 'debug-chat.html')

# API status endpoint to check connectivity
@app.route('/api/status')
def api_status():
    """Return the status of the API to verify connectivity"""
    return jsonify({
        'status': 'success',
        'server': 'Minerva API',
        'timestamp': datetime.datetime.now().isoformat(),
        'mode': 'standalone'
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
    extensions_status = "available" if 'minerva_extensions' in globals() and minerva_extensions else "unavailable"
    
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
        'uptime_seconds': (datetime.datetime.now() - SERVER_START_TIME).total_seconds()
    }
    
    # Determine overall status
    if coordinator_status == "unavailable":
        health_data['status'] = 'degraded'
    
    return jsonify(health_data)

# Simple chat API endpoint
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat endpoint to handle user messages"""
    try:
        data = request.json
        user_message = data.get("message", "")
        
        # Log the incoming message
        app.logger.info(f"Received chat message: {user_message[:50]}{'...' if len(user_message) > 50 else ''}")
        
        # Implement a more intelligent response simulation since we can't connect to real AI models
        response_text = generate_simulated_response(user_message)
        
        return jsonify({
            "status": "success",
            "response": response_text,
            "timestamp": datetime.datetime.now().isoformat(),
            "model": "minerva-simulation"
        })
    except Exception as e:
        app.logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error processing your request: {str(e)}"
        }), 500

def generate_simulated_response(user_message):
    """Generate a simulated AI response when the real coordinator is not available"""
    # Simple set of canned responses
    if not user_message:
        return "I didn't receive your message. Could you please try again?"
    
    # Convert to lowercase for easier pattern matching
    user_message_lower = user_message.lower()
    
    # Log what we're doing
    print(f"Generating simulated response for: {user_message}")
    
    # Check for common patterns
    if any(greeting in user_message_lower for greeting in ['hello', 'hi', 'hey', 'greetings']):
        return "Hello! I'm Minerva, your AI assistant. How can I help you today?"
    
    if 'how are you' in user_message_lower:
        return "I'm functioning well, thank you for asking! I'm here and ready to assist you."
    
    if any(word in user_message_lower for word in ['help', 'assist', 'support']):
        return "I'd be happy to help! I can answer questions, provide information, or assist with various tasks. What specifically do you need help with?"
    
    if 'who are you' in user_message_lower or 'what are you' in user_message_lower:
        return "I'm Minerva, an AI assistant designed to provide helpful responses and assist with various tasks and questions."
    
    if 'thank' in user_message_lower:
        return "You're welcome! I'm glad I could be of assistance. Is there anything else I can help with?"
    
    if 'working' in user_message_lower or 'broken' in user_message_lower or 'functional' in user_message_lower:
        return "Yes, I'm fully operational and responding to your messages. The connection between us is working correctly."
    
    if any(word in user_message_lower for word in ['bye', 'goodbye', 'see you', 'later']):
        return "Goodbye! Feel free to chat again whenever you need assistance."
    
    # Handle test messages
    if any(test in user_message_lower for test in ['test', 'testing', 'check']):
        return "This is a test response from Minerva. The system appears to be working correctly!"
    
    if 'hey' == user_message_lower:
        return "Hey there! I'm Minerva. How can I help you today?"
        
    # Default response for anything else
    return f"I'm currently using a simulated response system. I've received your message: '{user_message}'. In normal operation, I would provide a more detailed response using AI models."

# Memory API endpoint to fetch memory items
@app.route('/api/memories')
def api_memories():
    """Return memory items"""
    try:
        # In a real implementation, this would fetch from a database
        # For now, return sample data
        memories = [
            {'id': 1, 'content': 'Minerva UI is based on an orbital design concept', 'importance': 8, 'date': datetime.datetime.now().isoformat()},
            {'id': 2, 'content': 'The chat API endpoint is /api/chat', 'importance': 9, 'date': datetime.datetime.now().isoformat()},
            {'id': 3, 'content': 'User prefers draggable chat windows', 'importance': 7, 'date': datetime.datetime.now().isoformat()},
            {'id': 4, 'content': 'Projects should support markdown formatting', 'importance': 6, 'date': datetime.datetime.now().isoformat()}
        ]
        
        return jsonify({
            'status': 'success',
            'memories': memories
        })
    except Exception as e:
        app.logger.error(f"Error fetching memories: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error fetching memories: {str(e)}"
        }), 500

# Projects API endpoint to fetch project items
@app.route('/api/projects')
def api_projects():
    """Return project items"""
    try:
        # In a real implementation, this would fetch from a database
        # For now, return sample data
        projects = [
            {'id': 1, 'name': 'Minerva UI Redesign', 'status': 'In Progress', 'description': 'Redesigning the Minerva UI with an orbital concept'},
            {'id': 2, 'name': 'API Integration', 'status': 'Pending', 'description': 'Integrating various AI APIs into Minerva'},
            {'id': 3, 'name': 'Documentation', 'status': 'Completed', 'description': 'Creating comprehensive documentation for Minerva'},
            {'id': 4, 'name': 'Memory System', 'status': 'In Progress', 'description': 'Implementing a long-term memory system for Minerva'}
        ]
        
        return jsonify({
            'status': 'success',
            'projects': projects
        })
    except Exception as e:
        app.logger.error(f"Error fetching projects: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error fetching projects: {str(e)}"
        }), 500

def process_with_coordinator(user_input, model_preference='default', **kwargs):
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
        elif available_models['default']:
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

# Proper signal handling for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully but DON'T EXIT"""
    print(f"\nShutting down Minerva server gracefully")
    logger.info(f"Shutting down Minerva server gracefully")
    
    # Create a proper shutdown sequence that won't be interrupted
    try:
        # If we have extensions, clean them up
        if 'minerva_extensions' in globals() and minerva_extensions:
            logger.info("Closing Minerva extensions...")
            if hasattr(minerva_extensions, 'close'):
                minerva_extensions.close()
        
        # If we have a coordinator, clean it up
        if 'ai_coordinator' in globals() and ai_coordinator:
            logger.info("Closing AI coordinator...")
            if hasattr(ai_coordinator, 'close'):
                ai_coordinator.close()
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
    
    # IMPORTANT: If it's SIGINT (Ctrl+C), exit, but for SIGTERM, keep running
    if signum == signal.SIGINT:
        logger.info("User initiated shutdown with Ctrl+C")
        sys.exit(0)
    else:
        # For SIGTERM, log but don't exit
        logger.info(f"Received signal {signum}, but continuing to run (ignoring it)")
        print(f"Received signal {signum}, but continuing to run")

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Also register atexit for extra safety
@atexit.register
def cleanup_at_exit():
    logger.info("Performing final cleanup at exit")
    # Add any critical cleanup here
    
# Main execution block with robust error handling
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5505))
    host = os.environ.get('HOST', '0.0.0.0')  # Use 0.0.0.0 not localhost
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    try:
        print(f"Starting Minerva server on http://{host}:{port}")
        logger.info(f"Starting Minerva server on http://{host}:{port}")
        print(f"Press Ctrl+C to stop the server")
        
        # Use socketio.run with proper parameters
        socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {port} is already in use. Try a different port.")
            print(f"Error: Port {port} is already in use. Try a different port.")
            sys.exit(1)
        else:
            logger.error(f"Error starting server: {str(e)}")
            print(f"Error starting server: {str(e)}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

# Socket.IO debug endpoint to test connectivity
@socketio.on('connect')
def socket_connect():
    logger.info(f"Client connected: {request.sid}")
    print(f"Socket.IO client connected: {request.sid}")

@socketio.on('disconnect')
def socket_disconnect():
    logger.info(f"Client disconnected: {request.sid}")
    print(f"Socket.IO client disconnected: {request.sid}")

@socketio.on('debug')
def handle_debug(data):
    """Handle debug events for troubleshooting"""
    print(f"DEBUG: {data}")
    try:
        # Log the debug data and respond
        emit('chat_response', {'message': 'Socket.IO connection is working! Type a message to chat.'})
    except Exception as e:
        print(f"Error in debug handler: {e}")
        emit('error', {'message': str(e)})

# Protect against SIGTERM by ignoring it
print("Setting up signal handlers to prevent termination...")
signal.signal(signal.SIGTERM, signal.SIG_IGN)
print("✅ SIGTERM handler installed - server won't be killed by SIGTERM")

# Add route to serve compatible Socket.IO client
@app.route('/compatible-socket.io.js')
def compatible_socketio():
    """Serve a compatible version of Socket.IO client"""
    js_content = """
    // Socket.IO compatibility wrapper
    console.log("Loading compatible Socket.IO client version 4.7.2");
    
    // Load the compatible version only if not already loaded
    if (typeof io === 'undefined') {
        const script = document.createElement('script');
        script.src = "https://cdn.socket.io/4.7.2/socket.io.min.js";
        script.integrity = "sha384-mZLF4UVrpi/QTWPA7BjNPCy9k4/q/3ZqAq+cLxgF3kGWRd/ECg9QgHck+5o5S8eZ";
        script.crossOrigin = "anonymous";
        document.head.appendChild(script);
        
        script.onload = function() {
            console.log("Socket.IO v4.7.2 loaded successfully!");
            document.dispatchEvent(new Event('socketio-loaded'));
        };
    } else {
        console.log("Socket.IO already loaded, version:", io.version);
    }
    """
    return Response(js_content, mimetype='application/javascript')

# Add utility route for health check
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'uptime': time.time() - SERVER_START_TIME,
        'mode': eventlet.monkey_patch()
    })

# Add routes for Socket.IO client compatibility
@app.route('/socket.io/socket.io.js')
def serve_socketio_client():
    """Serve the Socket.IO client library at the default path"""
    return send_from_directory('web/static/js', 'socket.io.min.js')

@socketio.on('debug')
def handle_debug(data):
    """Debug event handler to confirm Socket.IO is working"""
    logger.info(f"Received debug event with data: {data}")
    print(f"🔬 DEBUG: Received Socket.IO debug event: {data}")
    
    # Echo back the data with server info
    emit('debug_response', {
        'server_time': datetime.datetime.now().isoformat(),
        'received': data,
        'server_info': {
            'async_mode': socketio.async_mode,
            'socketio_version': flask_socketio.__version__,
            'python_socketio_version': socketio.__version__,
        }
    })
    
    # Also send a system message so it shows up in the UI
    emit('system_message', {'message': f"Debug connection successful at {datetime.datetime.now().isoformat()}"})
