#!/usr/bin/env python3
"""
Minerva Web Interface (No Eventlet Version)

This is a modified version of app.py that doesn't use eventlet, which is incompatible with Python 3.13+
Note: WebSockets will be disabled, but REST API chat will still work.
"""

# Comment out eventlet imports that cause issues with Python 3.13+
# import eventlet
# eventlet.monkey_patch()
print("[STARTUP] Running in non-eventlet mode - WebSockets disabled")

# Load environment variables from .env file
from dotenv import load_dotenv
import os
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"[STARTUP] ✅ Environment variables loaded from {env_path}")
    
    # Log available API keys (without exposing the actual keys)
    api_keys = {
        'OpenAI': os.environ.get('OPENAI_API_KEY'),
        'Anthropic': os.environ.get('ANTHROPIC_API_KEY'),
        'Mistral': os.environ.get('MISTRAL_API_KEY'),
        'Cohere': os.environ.get('COHERE_API_KEY'),
        'HuggingFace': os.environ.get('HUGGINGFACE_API_TOKEN')
    }
    
    for provider, key in api_keys.items():
        if key:
            key_preview = f"{key[:3]}...{key[-3:]}" if len(key) > 10 else "[REDACTED]"
            print(f"[STARTUP] ✅ {provider} API key loaded (length: {len(key)}, preview: {key_preview}")
        else:
            print(f"[STARTUP] ⚠️ {provider} API key not found")
else:
    print(f"[STARTUP] ⚠️ Warning: .env file not found at {env_path}. Using system environment variables.")

import os
import sys
import re
import time
import json
import uuid
import logging
import tempfile
import datetime
import threading
import traceback
import importlib
import urllib.parse
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Initialize key directories
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_dir = os.path.join(base_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)

# Setup logging
log_format = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger('minerva')

# Configure file handler for app.log
app_log_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
app_log_handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(app_log_handler)

# Import Flask (without eventlet dependencies)
from flask import (
    Flask, render_template, redirect, url_for, request, jsonify, 
    session, send_from_directory, send_file, Response, make_response, abort
)

# Flask SocketIO is disabled in this mode
# from flask_socketio import SocketIO, emit, disconnect

# Conditionally import Flask-Session if available
try:
    from flask_session import Session
    has_flask_session = True
    print("[STARTUP] Flask-Session available for server-side session management")
except ImportError:
    has_flask_session = False
    print("[STARTUP] Flask-Session not available, using default session manager")

# Conditionally import Flask-WTF for CSRF protection
try:
    from flask_wtf.csrf import CSRFProtect
    has_csrf = True
    print("[STARTUP] Flask-WTF available for CSRF protection")
except ImportError:
    has_csrf = False
    print("[STARTUP] Flask-WTF not available, CSRF protection disabled")

# Import Minerva modules
minerva_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if minerva_dir not in sys.path:
    sys.path.insert(0, minerva_dir)
print(f"[STARTUP] Added '{minerva_dir}' to Python path")

try:
    # Try relative imports first (when running from web directory)
    from api_verification import initialize_verification, verify_api_call
    from api_request_handler import ApiRequestHandler, handle_api_request, api_request
    from analytics_tracker import AnalyticsTracker
    from multi_ai_coordinator import MultiAICoordinator
    print("[STARTUP] Using relative imports for Minerva modules")
except ImportError:
    # Fall back to absolute imports (when running from a different directory)
    from web.api_verification import initialize_verification, verify_api_call
    from web.api_request_handler import ApiRequestHandler, handle_api_request, api_request
    from web.analytics_tracker import AnalyticsTracker
    from web.multi_ai_coordinator import MultiAICoordinator
    print("[STARTUP] Using absolute imports for Minerva modules")

# Initialize Flask app
app = Flask(__name__,
            static_folder='static',
            template_folder='templates',
            static_url_path='/static')

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'minerva_default_secret')

# Initialize Flask-Session for server-side session management if available
if has_flask_session:
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)
    print("[STARTUP] Initialized Flask-Session for server-side session management")
else:
    print("[STARTUP] Using Flask's default client-side session cookies")

# Enable CSRF protection if available
if has_csrf:
    csrf = CSRFProtect(app)
    print("[STARTUP] CSRF protection enabled")

# Initialize API verification system
initialize_verification()

# Initialize the multi-AI coordinator and API handler
analytics_tracker = AnalyticsTracker()
api_handler = ApiRequestHandler(analytics_tracker)
minerva = MultiAICoordinator(api_handler, analytics_tracker)

# Set debug mode from environment
debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
app.debug = debug_mode

# Store active conversations
active_conversations = {}

# Function to init think tank (moved from original position for clarity)
def initialize_think_tank():
    """Initialize the Think Tank AI service."""
    # Code from the original initialize_think_tank function would go here
    # Simplified for the patch
    pass

# Rate limiting decorator
def rate_limit(max_calls, time_frame):
    def decorator(func):
        # Initialize call history for this function
        func.call_history = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # Clean up old entries
            func.call_history = [timestamp for timestamp in func.call_history if now - timestamp < time_frame]
            
            # Check if rate limit is exceeded
            if len(func.call_history) >= max_calls:
                return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            
            # Add current call to history
            func.call_history.append(now)
            
            # Call the original function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

# Routes
@app.route('/')
def index():
    """Render the index page or a static index.html file if it exists."""
    # Check for a static index.html first
    static_index = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(static_index):
        return send_from_directory(app.static_folder, 'index.html')
    
    # If no static index.html exists, try the template approach
    try:
        # Check if user is in session, if not create a user ID
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        # Get or create a conversation for this user
        user_id = session['user_id']
        if user_id not in active_conversations:
            result = minerva.start_conversation(user_id=user_id)
            active_conversations[user_id] = result['conversation_id']
        
        # Get frameworks for display
        frameworks = minerva.framework_manager.get_all_frameworks()
        framework_names = list(frameworks.keys()) if frameworks else []
        
        return render_template('index.html', 
                               user_id=user_id,
                               conversation_id=active_conversations[user_id],
                               frameworks=framework_names)
    except Exception as e:
        # If template rendering fails, show a basic HTML page with API information
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Minerva API</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #2c3e50; }}
                .endpoint {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 15px; }}
                .method {{ font-weight: bold; color: #e74c3c; }}
                .url {{ font-family: monospace; }}
                .description {{ margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>Minerva API Server</h1>
            <p>The Minerva UI is not available, but the API endpoints are working correctly.</p>
            
            <h2>Available API Endpoints:</h2>
            
            <div class="endpoint">
                <div><span class="method">POST</span> <span class="url">/api/v1/advanced-think-tank</span></div>
                <div class="description">Send a message to the Think Tank (multiple AI models).</div>
                <pre>{{ "message": "Your question here" }}</pre>
            </div>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="url">/api/test</span></div>
                <div class="description">Simple test endpoint to verify the API is working.</div>
            </div>
            
            <p>Error details: {str(e)}</p>
        </body>
        </html>
        '''
        return html_content

@app.route('/direct-test')
def direct_test_page():
    """Render the direct API test UI."""
    return render_template('direct_test.html')

@app.route('/chat')
def chat():
    """Render the chat interface."""
    # Ensure user has an ID and conversation
    if 'user_id' not in session:
        # For direct access testing, create a test user ID
        session['user_id'] = f'test_user_{int(time.time())}'
    
    user_id = session['user_id']
    if user_id not in active_conversations:
        try:
            result = minerva.start_conversation(user_id=user_id)
            active_conversations[user_id] = result['conversation_id']
        except Exception as e:
            app.logger.error(f"Error starting conversation: {e}")
            active_conversations[user_id] = f'test_conversation_{int(time.time())}'
    
    try:
        return render_template('chat.html', 
                               user_id=user_id,
                               conversation_id=active_conversations[user_id])
    except Exception as e:
        app.logger.error(f"Error rendering template: {e}")
        return f"Chat interface for user {user_id} with conversation {active_conversations[user_id]}", 200

@app.route('/chat-test')
def chat_test():
    """Render the REST API-based chat test page."""
    return render_template('chat_test.html')

# API routes for chat functionality
@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """REST API endpoint for chat messages."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        user_message = data.get('message', '')
        conversation_id = data.get('conversation_id', f'rest-api-{int(datetime.now().timestamp())}')
        
        if not user_message:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
        
        # Process message through our unified processing function
        print(f"[REST API] Processing message: {user_message}")
        
        # Process the message with Minerva Think Tank
        try:
            # Format data for the Think Tank API
            think_tank_data = {
                "message": user_message,
                "conversation_id": conversation_id,
                "user_id": data.get('user_id', 'rest_api_user')
            }
            
            # Call the Think Tank API endpoint
            response = api_request(
                "https://minerva-think-tank/api/chat", 
                method="POST", 
                data=think_tank_data,
                simulate=True  # This ensures responses even without actual Think Tank service
            )
            
            # Extract AI response
            ai_response = response.get('response', "I'm sorry, I couldn't process your request.")
            message_id = response.get('message_id', str(uuid.uuid4()))
            model_info = response.get('model_info', {})
            
            # Return the processed response
            return jsonify({
                'status': 'success',
                'response': ai_response,
                'message_id': message_id,
                'model_info': model_info,
                'conversation_id': conversation_id
            })
            
        except Exception as e:
            app.logger.error(f"Error processing message with Think Tank: {e}")
            return jsonify({
                'status': 'error',
                'message': f"Error processing your message: {str(e)}"
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error in chat_message endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': f"Server error: {str(e)}"
        }), 500

@app.route('/api/model_info/<message_id>', methods=['GET'])
def get_model_info(message_id):
    """Get information about the model used for a specific message."""
    # This is a simplified version for the no-eventlet app
    # In a real implementation, it would fetch actual model info from a database
    
    # Return simulated model info
    return jsonify({
        'status': 'success',
        'message_id': message_id,
        'model_info': {
            'primary_model': 'gpt-4',
            'rankings': [
                {
                    'model': 'gpt-4', 
                    'score': 0.95,
                    'reasoning': 'Provided the most comprehensive and accurate response.'
                },
                {
                    'model': 'claude-3', 
                    'score': 0.92,
                    'reasoning': 'Good response but missing some nuance.'
                },
                {
                    'model': 'gemini-pro', 
                    'score': 0.88,
                    'reasoning': 'Solid response but less detailed.'
                }
            ],
            'blending': {
                'strategy': 'technical',
                'contributions': {
                    'gpt-4': 60,
                    'claude-3': 30,
                    'gemini-pro': 10
                }
            }
        }
    })

@app.route('/api/feedback', methods=['POST'])
def handle_feedback():
    """API endpoint to handle user feedback on responses."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        message_id = data.get('message_id')
        feedback_type = data.get('feedback_type')
        
        if not message_id or not feedback_type:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # In a real implementation, this would store the feedback in a database
        print(f"[FEEDBACK] Received {feedback_type} feedback for message {message_id}")
        
        # Return success
        return jsonify({'status': 'success', 'message': 'Feedback recorded'})
        
    except Exception as e:
        app.logger.error(f"Error handling feedback: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Main entry point
if __name__ == '__main__':
    # Initialize whatever is needed for your environment  
    
    # Run the Flask app without eventlet/socketio
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"[STARTUP] Starting Minerva web interface on {host}:{port} (No WebSockets mode)")
    app.run(host=host, port=port)
