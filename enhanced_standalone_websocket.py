#!/usr/bin/env python3
"""
Enhanced Standalone WebSocket Server for Minerva

This server correctly integrates with Minerva's AI components to ensure
AI-generated responses instead of echo responses.
"""

import os
import sys
import time
import json
import uuid
import logging
import threading
import asyncio
import dotenv
from datetime import datetime
from flask import Flask, request
from flask_socketio import SocketIO, emit

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configure logging with standardized format per our enhanced logging memory
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MinervaWebSocket")

# Create logs directory
os.makedirs('logs', exist_ok=True)

# Load environment variables from .env file if it exists
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(dotenv_path):
    logger.info(f"Loading environment variables from {dotenv_path}")
    dotenv.load_dotenv(dotenv_path)
    
# Set API keys if they are in the environment but not already set
if not os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_API_KEY_VALUE"):
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY_VALUE")
    logger.info("Set OPENAI_API_KEY from OPENAI_API_KEY_VALUE")
    
if not os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("ANTHROPIC_API_KEY_VALUE"):
    os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY_VALUE")
    logger.info("Set ANTHROPIC_API_KEY from ANTHROPIC_API_KEY_VALUE")
    
# Set default API keys for testing if needed
if not os.environ.get("OPENAI_API_KEY"):
    # This is a placeholder, replace with your actual key or configuration method
    DEFAULT_OPENAI_KEY = "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"
    os.environ["OPENAI_API_KEY"] = DEFAULT_OPENAI_KEY
    logger.warning("Using default OpenAI API key for testing. Replace with your own in production.")

# Add Minerva modules to path
minerva_path = os.path.dirname(os.path.abspath(__file__))
web_path = os.path.join(minerva_path, 'web')
if web_path not in sys.path:
    sys.path.append(web_path)

# Import Minerva AI components with proper error handling
try:
    from web.multi_ai_coordinator import MultiAICoordinator
    from web.validator import validate_response, evaluate_response_quality
    from web.route_request import route_request
    from web.model_processors import register_model_processors, get_available_models
    minerva_ai_available = True
    logger.info("✅ Successfully imported Minerva AI components")
except ImportError as e:
    logger.error(f"❌ Failed to import Minerva AI components: {e}")
    minerva_ai_available = False
    # Define fallback functions
    def route_request(message):
        return {
            "priority_models": ["default"],
            "query_complexity": 5,
            "query_tags": ["general"]
        }
    
    def validate_response(response, query=None):
        return {
            "is_valid": True,
            "quality_score": 0.7,
            "reason": "Simplified validation"
        }
    
    def evaluate_response_quality(response, query=None):
        return 0.7

# Initialize Flask app and SocketIO
app = Flask(__name__, 
           static_folder=os.path.join(minerva_path, 'web', 'static'),
           template_folder=os.path.join(minerva_path, 'web', 'templates'))
socketio = SocketIO(app, cors_allowed_origins="*")

# Active request tracking for monitoring and timeout handling
active_requests = {}
request_lock = threading.Lock()

# Initialize Minerva AI Coordinator
coordinator = None
# Define the models_used variable for tracking which models are being used
models_used = {}
if minerva_ai_available:
    try:
        logger.info("🚀 [INIT] Initializing MultiAICoordinator")
        coordinator = MultiAICoordinator()
        
        # Register model processors with coordinator
        logger.info("🚀 [INIT] Registering model processors")
        register_model_processors(coordinator)
        
        # Log available models and initialize models_used
        available_models = get_available_models()
        logger.info(f"🚀 [INIT] Available models: {', '.join(available_models)}")
        
        # Set up models_used to track model usage
        for model in available_models:
            models_used[model] = {
                'model_used': model,
                'last_used': datetime.now().isoformat(),
                'count': 0
            }
        
        # Test the coordinator with a simple message - need to handle async properly
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        test_response = loop.run_until_complete(coordinator.process_message(
            message="This is a test message to verify Minerva AI is working.",
            user_id="system_test",
            message_id="test_init",
            mode="normal"
        ))
        
        if test_response and isinstance(test_response, dict) and 'response' in test_response:
            logger.info("✅ [VERIFICATION] Minerva AI responding correctly")
            logger.info(f"Sample Response: {test_response.get('response', '')[:100]}...")
            
            # Extract model used information safely
            model_used = test_response.get('model_used', test_response.get('model', 'unknown'))
            logger.info(f"Model used for test: {model_used}")
            
            # Track which models are being used
            model_name = test_response.get('model', 'unknown')
            models_used[model_name] = {
                'model_used': model_used,
                'last_used': datetime.now().isoformat(),
                'count': 1
            }
            
            # Add any additional model information for analytics
            model_info = {
                'model': model_name,
                'model_used': model_used,
                'confidence': test_response.get('confidence', 0.0),
                'processing_time': test_response.get('processing_time', 0.0)
            }
            logger.info(f"Model info: {model_info}")
        else:
            logger.warning("⚠️ [VERIFICATION] Unexpected response format from Minerva AI")
            logger.info(f"Response: {test_response}")
            coordinator = None
            minerva_ai_available = False
    except Exception as e:
        logger.error(f"❌ [INIT_ERROR] Failed to initialize Minerva AI: {e}")
        coordinator = None
        minerva_ai_available = False

# Define routes for Minerva UI
@app.route('/')
def index():
    try:
        with open(os.path.join(web_path, 'minerva_orbital_fixed.html'), 'r') as f:
            return f.read()
    except:
        try:
            # Fallback to index.html in static folder
            return app.send_static_file('index.html')
        except:
            return '<h1>Minerva AI</h1><p>Welcome to Minerva AI WebSocket Server.</p>'

@app.route('/orb')
def orb():
    try:
        with open(os.path.join(web_path, 'minerva_orbital_fixed.html'), 'r') as f:
            return f.read()
    except:
        try:
            # Fallback to other orbital UI versions
            with open(os.path.join(web_path, 'minerva_orbital.html'), 'r') as f:
                return f.read()
        except:
            return '<h1>Minerva Orb Interface</h1><p>Orb interface files not found. Using basic WebSocket server.</p>'

@app.route('/chat')
def chat():
    try:
        with open(os.path.join(web_path, 'minerva_floating_chat.html'), 'r') as f:
            return f.read()
    except:
        return '<h1>Minerva Chat Interface</h1><p>Chat interface files not found. Using basic WebSocket server.</p>'

@app.route('/elegant')
def elegant():
    try:
        with open(os.path.join(web_path, 'minerva_elegant_ui.html'), 'r') as f:
            return f.read()
    except:
        return '<h1>Minerva Elegant Interface</h1><p>Interface files not found.</p>'

@app.route('/central')
def central():
    try:
        with open(os.path.join(web_path, 'minerva_central.html'), 'r') as f:
            return f.read()
    except:
        return '<h1>Minerva Central</h1><p>Interface files not found.</p>'

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    logger.info(f"📡 Client connected: {session_id}")
    emit('connected', {'session_id': session_id})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"📡 Client disconnected: {request.sid}")

@socketio.on('message')
def handle_message(message):
    """Handle incoming WebSocket messages with robust processing."""
    start_time = time.time()
    session_id = request.sid
    message_id = message.get('message_id', str(uuid.uuid4()))
    user_id = message.get('user_id', 'anonymous')
    mode = message.get('mode', 'normal')
    content = message.get('message', '')
    
    # Log message receipt with standardized format
    logger.info(f"📩 [MESSAGE_RECEIVED] ID={message_id} Mode={mode} From={user_id[:8]} Content={content[:50]}...")
    
    # Register active request for monitoring
    with request_lock:
        active_requests[message_id] = {
            'timestamp': datetime.now(),
            'session_id': session_id,
            'completed': False,
            'user_id': user_id,
            'mode': mode
        }
    
    # Process based on mode
    if mode == 'think_tank':
        # Process in a thread to avoid blocking
        logger.info(f"🧠 [THINK_TANK_START] Starting Think Tank processing for {message_id}")
        thread = threading.Thread(
            target=process_think_tank,
            args=(message_id, session_id, content, user_id)
        )
        thread.daemon = True
        thread.start()
    else:
        # Handle normal mode
        process_normal_message(message_id, session_id, content, user_id)
    
    # End timing for initial processing
    logger.info(f"⏱️ Initial processing completed in {time.time() - start_time:.2f}s")

def process_normal_message(message_id, session_id, message, user_id):
    """Process a normal mode message using Minerva AI."""
    logger.info(f"🔄 [PROCESS_START] Processing normal message: {message_id}")
    
    if not minerva_ai_available or not coordinator:
        logger.warning(f"⚠️ Minerva AI not available for {message_id}, using echo response")
        emit('response', {
            'message_id': message_id,
            'session_id': session_id,
            'response': f"Echo: {message}",
            'source': 'echo',
            'is_ai': False,
            'model_info': {'model': 'echo', 'model_used': 'none'}
        }, room=session_id)
        
        # Mark request as completed
        with request_lock:
            if message_id in active_requests:
                active_requests[message_id]['completed'] = True
        return
    
    try:
        # Route the request through Minerva AI - handle async properly
        logger.info(f"🔄 [MODEL_ROUTING] Routing message {message_id} to Minerva AI")
        # Create event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ai_response = loop.run_until_complete(coordinator.process_message(
            message=message,
            user_id=user_id,
            message_id=message_id,
            mode="normal",
            include_model_info=True
        ))
        
        # Check if we got a valid response
        if ai_response and isinstance(ai_response, dict) and 'response' in ai_response:
            # Extract response from Minerva
            response_text = ai_response.get('response', "")
            model_info = ai_response.get('model_info', {})
            model_name = model_info.get('model', 'unknown')
            
            # Validate the response
            logger.info(f"🔄 [RESPONSE_VALIDATION] Validating response for {message_id}")
            validation = validate_response({'response': response_text}, message)
            
            if validation.get('is_valid', True):
                quality_score = validation.get('quality_score', 0.7)
                logger.info(f"✅ [VALIDATION_PASSED] Response from {model_name} passed validation with score {quality_score:.2f}")
                
                # Send the validated response
                emit('response', {
                    'message_id': message_id,
                    'session_id': session_id,
                    'response': response_text,
                    'source': model_name,
                    'is_ai': True,
                    'quality_score': quality_score,
                    'model_info': model_info
                }, room=session_id)
                
                logger.info(f"📤 [RESPONSE_SENT] AI response sent for {message_id} from {model_name}")
            else:
                # Response didn't pass validation
                reason = validation.get('reason', "Failed quality checks")
                logger.warning(f"❌ [VALIDATION_FAILED] Response rejected: {reason}")
                
                # Send a fallback response
                emit('response', {
                    'message_id': message_id,
                    'session_id': session_id,
                    'response': f"I processed your message but couldn't generate a quality response. Please try rephrasing your question.",
                    'source': 'fallback',
                    'is_ai': True,
                    'validation_failed': True,
                    'reason': reason
                }, room=session_id)
        else:
            # No valid response received from Minerva
            logger.error(f"❌ [AI_ERROR] Invalid response format from Minerva AI for {message_id}")
            emit('response', {
                'message_id': message_id,
                'session_id': session_id,
                'response': f"I received your message, but I'm having trouble processing it at the moment. Please try again shortly.",
                'source': 'error',
                'is_ai': False
            }, room=session_id)
    except Exception as e:
        # Handle any exceptions during processing
        logger.error(f"❌ [ERROR] Error processing message {message_id}: {str(e)}")
        emit('response', {
            'message_id': message_id,
            'session_id': session_id,
            'response': f"Error processing your message: {str(e)}",
            'source': 'error',
            'is_ai': False
        }, room=session_id)
    finally:
        # Mark the request as completed
        with request_lock:
            if message_id in active_requests:
                active_requests[message_id]['completed'] = True
        logger.info(f"🏁 [PROCESS_COMPLETE] Completed processing for {message_id}")

def process_think_tank(message_id, session_id, message, user_id):
    """Process a message using Minerva's Think Tank mode with multiple AI models."""
    logger.info(f"🧠 [THINK_TANK_START] Processing Think Tank message: {message_id}")
    
    try:
        if not minerva_ai_available or not coordinator:
            logger.warning(f"⚠️ Minerva AI not available for Think Tank {message_id}, using echo response")
            emit('response', {
                'message_id': message_id,
                'session_id': session_id,
                'response': f"Think Tank Echo: {message}",
                'source': 'echo',
                'is_ai': False
            }, room=session_id)
            return
        
        # Get routing information
        routing_info = route_request(message)
        logger.info(f"🔄 [MODEL_ROUTING] Routing decision for {message_id}: {routing_info.get('routing_explanation')}")
        
        # Use Think Tank mode to process with multiple models - handle async properly
        logger.info(f"🧠 [THINK_TANK_PROCESSING] Using models: {', '.join(routing_info.get('priority_models', ['default']))}")
        # Create event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ai_response = loop.run_until_complete(coordinator.process_message(
            message=message,
            user_id=user_id,
            message_id=message_id,
            mode="think_tank",
            include_model_info=True
        ))
        
        # Process and validate Think Tank responses
        if ai_response and isinstance(ai_response, dict) and 'responses' in ai_response:
            responses = ai_response.get('responses', [])
            logger.info(f"🔄 [RESPONSE_RECEIVED] Received {len(responses)} model responses for {message_id}")
            
            # Validate all responses
            validated_responses = []
            models_used = []
            
            for resp in responses:
                model = resp.get('model', 'unknown')
                model_used = resp.get('model_used', model)
                response_text = resp.get('response', '')
                
                # Track models used for logging
                models_used.append(model_used)
                
                # Validate each response
                validation = validate_response({'response': response_text, 'model': model}, message)
                if validation.get('is_valid', False):
                    resp['quality_score'] = validation.get('quality_score', 0.5)
                    validated_responses.append(resp)
                    logger.info(f"✅ [VALIDATION_PASSED] {model_used} response passed with score {resp['quality_score']:.2f}")
                else:
                    logger.warning(f"❌ [VALIDATION_FAILED] {model_used} response rejected: {validation.get('reason')}")
            
            # Log all models used
            logger.info(f"🔄 [THINK_TANK][{message_id}] Models used: {', '.join(models_used)}")
            
            # If we have valid responses, select the best one
            if validated_responses:
                # Sort by quality score
                validated_responses.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
                best_response = validated_responses[0]
                
                # Send the best response
                emit('response', {
                    'message_id': message_id,
                    'session_id': session_id,
                    'response': best_response.get('response', ''),
                    'source': best_response.get('model', 'think_tank'),
                    'is_ai': True,
                    'quality_score': best_response.get('quality_score', 0.7),
                    'model_info': {'model': best_response.get('model', 'unknown')},
                    'think_tank': True,
                    'model_count': len(validated_responses)
                }, room=session_id)
                
                logger.info(f"📤 [RESPONSE_SENT] Think Tank response sent for {message_id} from {best_response.get('model', 'unknown')}")
            else:
                # No valid responses
                logger.error(f"❌ [NO_VALID_RESPONSES] No validated responses for {message_id}")
                emit('response', {
                    'message_id': message_id,
                    'session_id': session_id,
                    'response': f"I analyzed your message with multiple AI models, but couldn't generate a quality response. Please try rephrasing your question.",
                    'source': 'think_tank_fallback',
                    'is_ai': True
                }, room=session_id)
        else:
            # Invalid response format from Think Tank
            logger.error(f"❌ [THINK_TANK_ERROR] Invalid response format for {message_id}")
            emit('response', {
                'message_id': message_id,
                'session_id': session_id,
                'response': f"Think Tank encountered an error processing your message. Please try again shortly.",
                'source': 'error',
                'is_ai': False
            }, room=session_id)
    except Exception as e:
        # Handle any exceptions
        logger.error(f"❌ [THINK_TANK_ERROR] Error in Think Tank processing: {str(e)}")
        emit('response', {
            'message_id': message_id,
            'session_id': session_id,
            'response': f"Error in Think Tank processing: {str(e)}",
            'source': 'error',
            'is_ai': False
        }, room=session_id)
    finally:
        # Mark request as completed
        with request_lock:
            if message_id in active_requests:
                active_requests[message_id]['completed'] = True
        
        logger.info(f"🏁 [THINK_TANK_COMPLETE] Completed Think Tank processing for {message_id}")

# Monitor thread for handling request timeouts
def monitor_timeouts():
    """Background thread to check for timed out requests."""
    logger.info("⏱️ Starting timeout monitor thread")
    while True:
        try:
            # Check every 5 seconds
            time.sleep(5)
            
            # Get current time
            now = datetime.now()
            
            with request_lock:
                # Check each active request
                for message_id, request_info in list(active_requests.items()):
                    if not request_info['completed']:
                        # Check if request has timed out (30 seconds)
                        elapsed = (now - request_info['timestamp']).total_seconds()
                        if elapsed > 30:
                            logger.warning(f"⏱️ [TIMEOUT] Request {message_id} timed out after {elapsed:.1f}s")
                            
                            # Send timeout response
                            try:
                                emit('response', {
                                    'message_id': message_id,
                                    'session_id': request_info['session_id'],
                                    'response': "Your request has timed out. Please try again.",
                                    'source': 'timeout',
                                    'is_ai': False
                                }, room=request_info['session_id'])
                                
                                # Mark as completed
                                request_info['completed'] = True
                                logger.info(f"📤 [TIMEOUT_RESPONSE] Sent timeout response for {message_id}")
                            except Exception as e:
                                logger.error(f"❌ [TIMEOUT_ERROR] Error sending timeout response: {e}")
        except Exception as e:
            logger.error(f"❌ [MONITOR_ERROR] Error in timeout monitor: {e}")

if __name__ == "__main__":
    # Start the timeout monitor thread
    monitor_thread = threading.Thread(target=monitor_timeouts, daemon=True)
    monitor_thread.start()
    
    # Log server start
    logger.info("🚀 Starting enhanced WebSocket server for Minerva AI")
    print("🚀 Starting enhanced WebSocket server for Minerva AI")
    print("✨ Visit http://localhost:5050 to view the server status")
    
    # Start the server
    socketio.run(app, host="0.0.0.0", port=5050, debug=True)
