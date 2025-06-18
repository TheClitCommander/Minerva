#!/usr/bin/env python3
"""
Standalone WebSocket Server for Minerva Testing

This script creates a minimal Flask-SocketIO server that simulates
Minerva's WebSocket functionality with the reliability fixes applied.
It helps isolate and verify the WebSocket fix without needing the full app.
"""
import os
import sys
import time
import json
import uuid
import logging
import threading
from datetime import datetime
from flask import Flask, render_template_string, request, session
from flask_socketio import SocketIO, emit, disconnect

# Add Minerva modules to path
minerva_path = os.path.dirname(os.path.abspath(__file__))
web_path = os.path.join(minerva_path, 'web')
if web_path not in sys.path:
    sys.path.append(web_path)

# Setup logging is already done above

# Import Minerva AI systems
minerva_ai_available = False
coordinator = None

try:
    # Define fallback functions in case the actual ones can't be imported
    def route_request(message):
        """Fallback routing function"""
        logger.warning(f"⚠️ Using fallback route_request function")
        return {
            "priority_models": ["default"],
            "query_complexity": 5,
            "query_tags": ["general"]
        }
    
    def validate_response(response, query):
        """Fallback validation function"""
        logger.warning(f"⚠️ Using fallback validate_response function")
        return {
            "is_valid": True,
            "quality_score": response.get('confidence', 0.7) if isinstance(response, dict) else 0.7,
            "reason": "Simplified validation"
        }
    
    def evaluate_response_quality(response, query):
        """Fallback quality evaluation function"""
        logger.warning(f"⚠️ Using fallback evaluate_response_quality function")
        return 0.7
    
    # Try importing the coordinator
    logger.info("🔍 Attempting to import MultiAICoordinator...")
    from web.multi_ai_coordinator import MultiAICoordinator
    logger.info("✅ Successfully imported MultiAICoordinator")
    
    # Try to import model_router if it exists
    try:
        logger.info("🔍 Attempting to import model_router...")
        # Check different possible locations
        try:
            from Gpt.ai_codes.model_router import route_request, evaluate_responses
            logger.info("✅ Imported model_router from Gpt.ai_codes")
        except ImportError:
            try:
                from model_router import route_request, evaluate_responses
                logger.info("✅ Imported model_router from root directory")
            except ImportError:
                try:
                    from web.model_router import route_request, evaluate_responses
                    logger.info("✅ Imported model_router from web directory")
                except ImportError:
                    logger.warning("⚠️ Could not import model_router, using fallback routing")
    except Exception as e:
        logger.warning(f"⚠️ Error importing routing functions: {e}")
    
    # Try to import validation system if it exists
    try:
        logger.info("🔍 Attempting to import validation system...")
        # Check different possible locations
        try:
            from ai_decision.validator import validate_response, evaluate_response_quality
            logger.info("✅ Imported validation system from ai_decision")
        except ImportError:
            try:
                from web.ensemble_validator import validate_response, evaluate_response_quality
                logger.info("✅ Imported validation system from web.ensemble_validator")
            except ImportError:
                try:
                    from validator import validate_response, evaluate_response_quality
                    logger.info("✅ Imported validation system from root directory")
                except ImportError:
                    logger.warning("⚠️ Could not import validation system, using fallback validation")
    except Exception as e:
        logger.warning(f"⚠️ Error importing validation functions: {e}")
    
    # If we got this far, we can use Minerva AI
    minerva_ai_available = True
    logger.info("✅ Successfully set up Minerva AI imports")

except ImportError as e:
    logger.warning(f"⚠️ Could not import Minerva AI systems: {e}")
    logger.warning("⚠️ Falling back to simulated AI responses")

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/standalone_websocket.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('standalone_websocket')

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minerva_test_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Constants
DEFAULT_TIMEOUT = 30  # seconds
MAX_ACTIVE_REQUESTS = 100

# Request tracking
active_requests = {}
request_lock = threading.Lock()

# Initialize Minerva AI systems if available
coordinator = None

# Set up standardized logging with markers as per your enhanced logging system
coordinator_logger = logging.getLogger('CoordinatorLogger')
coordinator_logger.setLevel(logging.DEBUG)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Add file handler with formatting
file_handler = logging.FileHandler('logs/coordinator.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
coordinator_logger.addHandler(file_handler)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
coordinator_logger.addHandler(console_handler)

if minerva_ai_available:
    try:
        # Initialize coordinator
        logger.info("🚀 [INIT] Initializing MultiAICoordinator")
        coordinator = MultiAICoordinator()
        logger.info("✅ [INIT_COMPLETE] MultiAICoordinator initialized successfully")
        
        # Test coordinator availability
        test_response = coordinator.process_message(
            message="This is a test message to verify the coordinator is working.",
            user_id="system_test",
            message_id="test_init",
            mode="normal")
        
        if test_response and 'response' in test_response:
            logger.info("✅ [VERIFICATION] MultiAICoordinator responding correctly")
        else:
            logger.warning("⚠️ [VERIFICATION] MultiAICoordinator response format unexpected")
            logger.info(f"Response: {test_response}")
            
    except Exception as e:
        logger.error(f"❌ [INIT_ERROR] Failed to initialize MultiAICoordinator: {e}")
        coordinator = None
        minerva_ai_available = False
else:
    logger.warning("⚠️ Minerva AI components not available, will use simulated responses")

# Monitor thread for tracking request timeouts
def monitor_timeouts():
    """Background thread to check for timed out requests"""
    logger.info("🕒 Starting timeout monitoring thread")
    
    while True:
        time.sleep(5)  # Check every 5 seconds
        
        try:
            now = datetime.now()
            timed_out = []
            
            # Find timed out requests
            with request_lock:
                for msg_id, request in list(active_requests.items()):
                    if not request.get('completed', False):
                        elapsed = (now - request['timestamp']).total_seconds()
                        if elapsed > DEFAULT_TIMEOUT:
                            timed_out.append(msg_id)
            
            # Handle each timeout
            for msg_id in timed_out:
                try:
                    handle_timeout(msg_id)
                except Exception as e:
                    logger.error(f"❌ Error handling timeout for {msg_id}: {e}")
            
            # Clean up old completed requests
            clean_old_requests()
            
        except Exception as e:
            logger.error(f"❌ Error in timeout monitor: {e}")

def clean_old_requests(max_age_minutes=5):
    """Remove old completed requests"""
    now = datetime.now()
    with request_lock:
        for msg_id in list(active_requests.keys()):
            request = active_requests[msg_id]
            if request.get('completed', False):
                age = (now - request['timestamp']).total_seconds() / 60
                if age > max_age_minutes:
                    del active_requests[msg_id]
                    logger.info(f"🧹 Cleaned up old request {msg_id}")

def handle_timeout(message_id):
    """Handle a timed out request by sending fallback response"""
    logger.warning(f"⏰ Request {message_id} timed out after {DEFAULT_TIMEOUT}s")
    
    try:
        with request_lock:
            if message_id not in active_requests:
                return
                
            request = active_requests[message_id]
            if request.get('completed', False):
                return
                
            # Mark as completed to prevent duplicate handling
            request['completed'] = True
            
            # Get session ID
            session_id = request.get('session_id')
            
            if not session_id:
                logger.error(f"❌ Missing session ID for {message_id}")
                return
        
        # Send fallback response
        emit('response', {
            'message_id': message_id,
            'session_id': session_id,
            'response': "I'm sorry, but this request has timed out. Please try again.",
            'source': 'Timeout Handler',
            'model_info': {'error': True, 'timeout': True}
        }, room=session_id, namespace='/')
        
        logger.info(f"📤 Sent timeout fallback for {message_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send timeout fallback: {e}")

# Simple HTML test page
@app.route('/')
def index():
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Minerva WebSocket Test</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #messages { margin-top: 20px; border: 1px solid #ccc; padding: 10px; height: 300px; overflow-y: auto; }
            #controls { margin-top: 20px; }
            .message { margin-bottom: 10px; padding: 5px; border-bottom: 1px solid #eee; }
            .user { color: blue; }
            .system { color: green; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>Minerva WebSocket Test</h1>
        <div id="status">Status: Disconnected</div>
        
        <div id="controls">
            <input type="text" id="messageInput" placeholder="Enter a message">
            <button id="sendButton">Send</button>
            <button id="testTimeoutButton">Test Timeout</button>
            <button id="testThinkTankButton">Test Think Tank</button>
        </div>
        
        <div id="messages"></div>
        
        <script>
            const socket = io();
            let socketId = null; // Will be set by server response
            
            // Connection events
            socket.on('connect', () => {
                document.getElementById('status').textContent = 'Status: Connected';
                addMessage('System', 'Connected to server');
                
                // Request initial connection message to get server-assigned ID
                socket.emit('chat_message', {
                    message_id: 'server',
                    session_id: 'connection',
                    message: 'connection_request',
                    mode: 'normal'
                });
            });
            
            socket.on('disconnect', () => {
                document.getElementById('status').textContent = 'Status: Disconnected';
                addMessage('System', 'Disconnected from server');
            });
            
            // Response handling
            socket.on('response', (data) => {
                // Save the session ID assigned by the server on first response
                if (data.message_id === 'server') {
                    socketId = data.session_id;
                    console.log('Received server session ID:', socketId);
                }
                
                // Format response more nicely
                addMessage('Response', JSON.stringify(data, null, 2));
            });
            
            // Helper to add messages to the UI
            function addMessage(type, content) {
                const messages = document.getElementById('messages');
                const message = document.createElement('div');
                message.className = `message ${type.toLowerCase()}`;
                
                if (typeof content === 'object') {
                    // Format JSON objects more nicely
                    content = JSON.stringify(content, null, 2);
                }
                
                // Use innerHTML if we're showing formatted JSON
                if (content.startsWith('{') && type === 'Response') {
                    message.textContent = `[${type}] ${content}`;
                } else {
                    message.textContent = `[${type}] ${content}`;
                }
                
                messages.appendChild(message);
                messages.scrollTop = messages.scrollHeight;
            }
            
            // Send normal message
            document.getElementById('sendButton').addEventListener('click', () => {
                const message = document.getElementById('messageInput').value;
                if (message) {
                    const messageId = Math.random().toString(36).substring(2, 15);
                    const payload = {
                        message_id: messageId,
                        session_id: socketId,
                        message: message,
                        mode: 'normal'
                    };
                    socket.emit('chat_message', payload);
                    addMessage('User', `Sent: ${message} (ID: ${messageId})`);
                    document.getElementById('messageInput').value = '';
                }
            });
            
            // Test timeout functionality
            document.getElementById('testTimeoutButton').addEventListener('click', () => {
                const messageId = Math.random().toString(36).substring(2, 15);
                const payload = {
                    message_id: messageId,
                    session_id: socketId,
                    message: 'This is a timeout test',
                    mode: 'test_timeout'
                };
                socket.emit('chat_message', payload);
                addMessage('User', `Sent timeout test (ID: ${messageId})`);
            });
            
            // Test think tank functionality
            document.getElementById('testThinkTankButton').addEventListener('click', () => {
                const messageId = Math.random().toString(36).substring(2, 15);
                const payload = {
                    message_id: messageId,
                    session_id: socketId,
                    message: 'This is a think tank test',
                    mode: 'think_tank'
                };
                socket.emit('chat_message', payload);
                addMessage('User', `Sent think tank test (ID: ${messageId})`);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(test_html)

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"👋 Client connected: {request.sid}")
    
    # Emit a welcome message with the session ID
    emit('response', {
        'message_id': 'server',
        'session_id': request.sid,
        'response': 'Connected to Minerva standalone WebSocket server',
        'source': 'System',
        'model_info': {'test': True}
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"👋 Client disconnected: {request.sid}")

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle incoming chat messages with simulated processing"""
    try:
        message_id = data.get('message_id', 'unknown')
        session_id = data.get('session_id', request.sid)
        message = data.get('message', '')
        mode = data.get('mode', 'normal')
        
        # Debug log for session tracking
        logger.info(f"🔑 Received message with session ID: {session_id} (SID: {request.sid})")
        
        logger.info(f"📩 Received message: ID={message_id}, Mode={mode}")
        
        # Track this request
        with request_lock:
            active_requests[message_id] = {
                'timestamp': datetime.now(),
                'session_id': session_id,
                'message': message,
                'mode': mode,
                'completed': False
            }
            
        # Log some debug info
        logger.info(f"ℹ️ Active requests: {len(active_requests)}")
        
        # Special test mode: timeout simulation
        if mode == 'test_timeout':
            logger.info(f"⏰ Timeout test for {message_id} - not sending response")
            # We intentionally don't respond or complete this request
            # The timeout monitor should catch it
            return
            
        # Process based on mode
        if mode == 'think_tank':
            # Simulate think tank processing in a thread to test parallel processing
            thread = threading.Thread(target=process_think_tank, args=(message_id, session_id, message))
            thread.daemon = True
            thread.start()
            logger.info(f"🧠 Started think tank processing for {message_id}")
        else:
            # Normal mode - use Minerva AI if available
            logger.info(f"[PROCESS_START] 🔄 Normal mode processing for {message_id}")
            
            if minerva_ai_available and coordinator:
                # Use Minerva AI for normal mode too
                logger.info(f"[MODEL_PROCESSING] 🧠 Using Minerva AI for normal mode")
                
                try:
                    # Route the request for single model selection
                    routing_info = route_request(message)
                    logger.info(f"[ROUTING_COMPLETE] 📊 Normal mode routing: {routing_info.get('query_tags', ['general'])}")
                    
                    # Process with coordinator in normal mode (single best model)
                    result = coordinator.process_message(
                        message=message,
                        user_id=session_id,
                        message_id=message_id,
                        mode="normal",  # Use normal mode instead of think tank
                        routing_info=routing_info,
                        include_model_info=True
                    )
                    
                    # Create enhanced response payload
                    response_payload = {
                        'message_id': message_id,
                        'session_id': session_id,
                        'response': result.get('response', f"I processed your message about: {message}"),
                        'source': 'Minerva AI',
                        'model_info': {
                            'model_used': result.get('model_used', 'default'),
                            'query_tags': routing_info.get('query_tags', ['general']),
                            'complexity_score': routing_info.get('query_complexity', 3),
                            'think_tank': False  # Normal mode uses a single model
                        }
                    }
                    
                    logger.info(f"[RESPONSE_RETURN] 🏁 Minerva AI normal mode response ready")
                except Exception as e:
                    logger.error(f"❌ Error using Minerva AI for normal mode: {str(e)}")
                    # Fallback to echo response
                    response_payload = {
                        'message_id': message_id,
                        'session_id': session_id,
                        'response': f"I received your message, but I'm experiencing technical difficulties: {str(e)}",
                        'source': 'Normal Mode Fallback',
                        'model_info': {'error': True, 'fallback': True}
                    }
            else:
                # Fallback to simple echo if Minerva AI is not available
                logger.warning(f"⚠️ Minerva AI not available, using echo for normal mode")
                delay = 1  # shorter delay for fallback
                time.sleep(delay)
                
                # Create simple response payload
                response_payload = {
                    'message_id': message_id,
                    'session_id': session_id,
                    'response': f"Echo: {message}",
                    'source': 'Normal Mode',
                    'model_info': {'processing_time': delay, 'test': True}
                }
            
            # Print detailed debug information about what's being sent
            import json
            logger.info(f"🔍 OUTGOING NORMAL RESPONSE PAYLOAD: {json.dumps(response_payload, indent=2)}")
            
            # Send response
            emit('response', response_payload, room=session_id)
            
            # Mark as completed
            with request_lock:
                if message_id in active_requests:
                    active_requests[message_id]['completed'] = True
            
            logger.info(f"✅ Completed normal processing for {message_id}")
    
    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        # Send error response
        emit('response', {
            'message_id': data.get('message_id', 'error'),
            'session_id': data.get('session_id', request.sid),
            'response': f"Error processing your request: {str(e)}",
            'source': 'Error Handler',
            'model_info': {'error': True, 'exception': str(e)}
        }, room=data.get('session_id', request.sid))

def process_think_tank(message_id, session_id, message):
    """Process messages using Minerva's real AI model coordination system"""
    try:
        # Use standardized logging markers as per your enhanced logging system
        logger.info(f"[PROCESS_START] 🔄 Think Tank processing started for {message_id}")
        
        if minerva_ai_available and coordinator:
            # Step 1: Route the request using Minerva's intelligent model selection
            logger.info(f"[ROUTING] 🧭 Analyzing query for intelligent routing")
            try:
                routing_info = route_request(message)
                logger.info(f"[ROUTING_COMPLETE] 📊 Query classified with tags: {routing_info.get('query_tags', ['general'])}")
            except Exception as e:
                logger.error(f"❌ Routing error: {str(e)}")
                # Fallback routing info
                routing_info = {
                    "priority_models": ["default"],
                    "query_complexity": 5,
                    "query_tags": ["general"]
                }
            
            # Step 2: Process through MultiAICoordinator with the routing information
            try:
                logger.info(f"[MODEL_PROCESSING] 🧠 Sending to Minerva AI Coordinator")
                # Process message with coordinator
                result = coordinator.process_message(
                    message=message,
                    user_id=session_id,
                    message_id=message_id,
                    mode="think_tank",
                    routing_info=routing_info,
                    include_model_info=True
                )
                logger.info(f"[MODEL_PROCESSING_COMPLETE] ✅ Coordinator returned responses")
                
                # Extract model responses
                if 'model_responses' in result:
                    responses = result['model_responses']
                else:
                    # Fallback for older coordinator versions
                    responses = [{
                        'model': result.get('model_used', 'unknown'),
                        'response': result.get('response', 'No response'),
                        'confidence': result.get('confidence', 0.8)
                    }]
                
                logger.info(f"[RESPONSE_VALIDATION] 🔍 Validating {len(responses)} responses")
            except Exception as e:
                logger.error(f"❌ Coordinator processing error: {str(e)}")
                # Fallback responses
                responses = [{
                    'model': 'fallback',
                    'response': f"I processed your request about: {message}\n\nHowever, I'm currently experiencing some technical difficulties. Could you please try again?",
                    'confidence': 0.5
                }]
            
            # Step 3: Validate responses using quality assessment system
            validated_responses = []
            for idx, resp in enumerate(responses):
                try:
                    validation_result = validate_response(resp, message)
                    resp['quality_score'] = validation_result.get('quality_score', 0.5)
                    resp['validation_result'] = validation_result
                    validated_responses.append(resp)
                    logger.info(f"[RESPONSE_VALIDATION] ✅ Response {idx+1} quality score: {validation_result.get('quality_score', 0.5):.2f}")
                except Exception as e:
                    logger.error(f"❌ Validation error for response {idx+1}: {str(e)}")
                    resp['quality_score'] = 0.5
                    validated_responses.append(resp)
            
            # Step 4: Select the best response based on quality scores
            if validated_responses:
                logger.info(f"[RESPONSE_ASSEMBLY] 🔄 Selecting best response from {len(validated_responses)} candidates")
                # Sort by quality score
                validated_responses.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
                best_response = validated_responses[0]
                logger.info(f"[RESPONSE_ASSEMBLY] ✅ Selected response from {best_response.get('model', 'unknown')} with score {best_response.get('quality_score', 0):.2f}")
            else:
                logger.error(f"❌ No validated responses available for {message_id}")
                best_response = {
                    'model': 'emergency_fallback',
                    'response': f"I received your message, but I'm having trouble processing it at the moment. Please try again shortly.",
                    'confidence': 0.1,
                    'quality_score': 0.1
                }
        else:
            # Fallback to simulation if Minerva AI is not available
            logger.warning(f"⚠️ Minerva AI not available, using simulation for {message_id}")
            
            # Simulate multiple model processing
            total_models = 2
            successful_models = 0
            responses = []
            
            # Model 1 simulation
            time.sleep(3)
            responses.append({
                'model': 'Model-A',
                'response': f"First model response to: {message}",
                'confidence': 0.8,
                'quality_score': 0.85
            })
            successful_models += 1
            logger.info(f"✅ Model-A completed for {message_id}")
            
            # Model 2 simulation
            time.sleep(2)
            responses.append({
                'model': 'Model-B',
                'response': f"Second model response to: {message}",
                'confidence': 0.75,
                'quality_score': 0.7
            })
            successful_models += 1
            logger.info(f"✅ Model-B completed for {message_id}")
            
            # Sort by quality score
            responses.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
            best_response = responses[0]
        
        # Retrieve the actual session ID from active_requests to ensure correct routing
        actual_sid = None
        with request_lock:
            if message_id in active_requests:
                actual_sid = active_requests[message_id].get('session_id', session_id)
                logger.info(f"🔄 Using actual session ID for {message_id}: {actual_sid}")
        
        # If no valid session ID found, fall back to the passed one
        if not actual_sid:
            actual_sid = session_id
            logger.info(f"⚠️ No active request found, using passed session ID: {session_id}")
        
        # Create the complete response payload with metadata
        model_used = best_response.get('model', 'unknown')
        quality_score = best_response.get('quality_score', 0.0)
        logger.info(f"[RESPONSE_METADATA] 📊 Preparing metadata for response")
        
        response_payload = {
            'message_id': message_id,
            'session_id': actual_sid,
            'response': best_response['response'],
            'source': 'Minerva AI',
            'model_info': {
                'think_tank': True,
                'models_used': len(responses) if 'responses' in locals() else 1,
                'best_model': model_used,
                'quality_score': quality_score,
                'query_tags': routing_info.get('query_tags', ['general']) if 'routing_info' in locals() else ['general'],
                'complexity_score': routing_info.get('query_complexity', 5) if 'routing_info' in locals() else 5
            }
        }
        
        # Print and log detailed debug information about what's being sent
        import json
        debug_payload = json.dumps(response_payload, indent=2)
        logger.info(f"🔍 OUTGOING RESPONSE PAYLOAD: {debug_payload}")
        logger.info(f"[RESPONSE_RETURN] 🏁 Returning final response")
        
        # Emit the response to the client
        try:
            socketio.emit('response', response_payload, namespace='/', room=actual_sid)
            logger.info(f"📤 Emitted response for {message_id} to session {actual_sid}")
            logger.info(f"[PROCESS_COMPLETE] 🏁 Processing complete for {message_id}")
        except Exception as e:
            logger.error(f"❌ Failed to emit response: {str(e)}")
            logger.error(f"Current session ID: {session_id}")
            logger.error(f"Falling back to standard emit...")
            try:
                emit('response', response_payload, room=actual_sid)
                logger.info(f"📤 Emitted response using fallback method")
            except Exception as e2:
                logger.error(f"❌ Fallback emit also failed: {str(e2)}")
        
        # Mark as completed in the request tracking system
        with request_lock:
            if message_id in active_requests:
                active_requests[message_id]['completed'] = True
        
        logger.info(f"✅ Think Tank processing completed for {message_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in Think Tank processing: {str(e)}")
        # Send error response to client
        try:
            error_payload = {
                'message_id': message_id,
                'session_id': session_id,
                'response': f"Error in Think Tank processing: {str(e)}",
                'source': 'Think Tank Error',
                'model_info': {'error': True, 'exception': str(e)}
            }
            socketio.emit('response', error_payload, room=session_id)
            logger.info(f"📤 Emitted error response for {message_id}")
        except Exception as e2:
            logger.error(f"❌ Failed to send error response: {str(e2)}")
        
        # Mark as completed
        with request_lock:
            if message_id in active_requests:
                active_requests[message_id]['completed'] = True
        return False

if __name__ == '__main__':
    # Start the timeout monitor thread
    monitor_thread = threading.Thread(target=monitor_timeouts, daemon=True)
    monitor_thread.start()
    
    # Log server start
    logger.info("🚀 Starting standalone WebSocket server for Minerva testing")
    print("🚀 Starting standalone WebSocket server for Minerva testing")
    print("✅ Open http://localhost:5050 in your browser to test")
    
    # Start the server
    socketio.run(app, host='0.0.0.0', port=5050, debug=True, use_reloader=False)
