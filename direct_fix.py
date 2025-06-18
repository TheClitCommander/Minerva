"""
Direct WebSocket and Think Tank Fix for Minerva

This script directly modifies Minerva's components to:
1. Add WebSocket request tracking and timeout handling
2. Enhance Think Tank mode with parallel processing and fallbacks
3. Fix response validation to prevent stuck connections
"""
import os
import sys
import time
import logging
import threading
from datetime import datetime
from pathlib import Path

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/direct_fix.log',
    filemode='a'
)
logger = logging.getLogger('direct_fix')

# Add the virtual environment
sys.path.append('/Users/bendickinson/Desktop/Minerva/venv/bin/python')

# Constants
REQUEST_TIMEOUT = 30  # seconds
THINK_TANK_TIMEOUT = 25  # seconds
FALLBACK_RESPONSE = "I apologize, but I encountered an issue processing this request. Please try again later."

# Active request tracking
active_requests = {}
request_lock = threading.Lock()

class FixResult:
    """Tracks the result of applying a fix"""
    def __init__(self, name):
        self.name = name
        self.success = False
        self.message = ""
        self.error = None
    
    def mark_success(self, message=""):
        self.success = True
        self.message = message
        logger.info(f"✅ [{self.name}] Success: {message}")
    
    def mark_failure(self, error, message=""):
        self.success = False
        self.error = error
        self.message = message
        logger.error(f"❌ [{self.name}] Failed: {message} - {error}")
        
    def __str__(self):
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        return f"{status}: {self.name} - {self.message}"

def monitor_timeouts():
    """Background thread to check for timed out requests"""
    logger.info("Starting request timeout monitor")
    
    while True:
        time.sleep(5)  # Check every 5 seconds
        
        try:
            now = datetime.now()
            timed_out = []
            
            # Find timed out requests
            with request_lock:
                for msg_id, request in list(active_requests.items()):
                    if not request['completed']:
                        elapsed = (now - request['timestamp']).total_seconds()
                        if elapsed > REQUEST_TIMEOUT:
                            timed_out.append(msg_id)
            
            # Handle each timeout
            for msg_id in timed_out:
                try:
                    handle_timeout(msg_id)
                except Exception as e:
                    logger.error(f"Error handling timeout for {msg_id}: {e}")
            
            # Clean up old completed requests
            clean_old_requests()
            
        except Exception as e:
            logger.error(f"Error in timeout monitor: {e}")

def clean_old_requests(max_age_minutes=5):
    """Remove old completed requests"""
    now = datetime.now()
    with request_lock:
        for msg_id in list(active_requests.keys()):
            request = active_requests[msg_id]
            if request['completed']:
                age = (now - request['timestamp']).total_seconds() / 60
                if age > max_age_minutes:
                    del active_requests[msg_id]

def handle_timeout(message_id):
    """Handle a timed out request by sending a fallback response"""
    with request_lock:
        if message_id not in active_requests:
            return
            
        request = active_requests[message_id]
        if request['completed']:
            return
            
        # Mark as completed to prevent duplicate handling
        request['completed'] = True
    
    logger.warning(f"⏰ Request {message_id} timed out after {REQUEST_TIMEOUT}s")
    
    try:
        # Get WebSocket emit function and session ID
        from flask_socketio import emit
        session_id = request['session_id']
        
        # Send fallback response
        emit('response', {
            'message_id': message_id,
            'session_id': session_id,
            'response': "I'm sorry, but this request has timed out. Please try again.",
            'source': 'Timeout Fallback',
            'model_info': {'error': True, 'timeout': True}
        }, room=session_id)
        
        logger.info(f"📤 Sent timeout fallback for {message_id}")
        
    except Exception as e:
        logger.error(f"Failed to send timeout fallback: {e}")

def fix_websocket_handler():
    """Fix the WebSocket handler to track requests and handle timeouts"""
    result = FixResult("WebSocket Fix")
    
    try:
        # Import sockets module
        from web import sockets
        logger.info("Imported web.sockets module")
        
        # Store original handler
        original_handler = sockets.handle_chat_message
        logger.info(f"Stored original handler: {original_handler.__name__}")
        
        # Define patched message handler
        def patched_handle_chat_message(message_data):
            """Enhanced chat message handler with request tracking"""
            message_id = message_data.get('message_id')
            session_id = message_data.get('session_id')
            
            logger.info(f"📥 Processing message {message_id} from session {session_id}")
            
            # Track this request
            with request_lock:
                active_requests[message_id] = {
                    'timestamp': datetime.now(),
                    'session_id': session_id,
                    'completed': False
                }
            
            try:
                # Call original handler
                result = original_handler(message_data)
                
                # Mark as completed if it returned
                with request_lock:
                    if message_id in active_requests:
                        active_requests[message_id]['completed'] = True
                        logger.info(f"✅ Message {message_id} completed successfully")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Error processing message {message_id}: {e}")
                
                # The request tracker will handle the timeout if needed
                # Don't mark as complete here to let the timeout handler work
                
                # Re-raise the exception for normal error handling
                raise
        
        # Apply the patch
        sockets.handle_chat_message = patched_handle_chat_message
        logger.info("Applied WebSocket handler patch")
        
        # Start the timeout monitor thread if not already running
        monitor_thread = threading.Thread(target=monitor_timeouts, daemon=True)
        monitor_thread.start()
        logger.info("Started timeout monitor thread")
        
        result.mark_success("WebSocket handler patched and timeout monitor started")
        return result
        
    except Exception as e:
        result.mark_failure(e, "Failed to patch WebSocket handler")
        return result

def fix_think_tank_processor():
    """Fix the Think Tank processor to handle multiple models with timeouts"""
    result = FixResult("Think Tank Fix")
    
    try:
        # Import MultiAICoordinator
        from web import multi_ai_coordinator
        logger.info("Imported multi_ai_coordinator module")
        
        # Check if process_think_tank method exists
        if not hasattr(multi_ai_coordinator.MultiAICoordinator, 'process_think_tank'):
            logger.warning("MultiAICoordinator does not have process_think_tank method")
            
            # Define the method if it doesn't exist
            def default_process_think_tank(self, message_id, session_id, query, **kwargs):
                """Default Think Tank processor implementation"""
                models = self.get_available_models()
                logger.info(f"Using {len(models)} available models")
                
                # Use the first model as fallback
                if models:
                    model = models[0]
                    logger.info(f"Using single model: {model.name}")
                    return self.process_message(message_id, session_id, query, model)
                else:
                    logger.error("No models available for Think Tank mode")
                    from flask_socketio import emit
                    emit('response', {
                        'message_id': message_id,
                        'session_id': session_id,
                        'response': "No AI models are currently available. Please try again later.",
                        'source': 'Error',
                        'model_info': {'error': True}
                    }, room=session_id)
                    return None
            
            # Add the default method
            multi_ai_coordinator.MultiAICoordinator.process_think_tank = default_process_think_tank
            logger.info("Added default process_think_tank method")
        
        # Store original method
        original_process = multi_ai_coordinator.MultiAICoordinator.process_think_tank
        logger.info(f"Stored original process_think_tank method: {original_process.__name__}")
        
        # Define enhanced Think Tank processor
        def enhanced_process_think_tank(self, message_id, session_id, query, **kwargs):
            """
            Enhanced Think Tank processor with parallel model processing and timeout handling
            """
            from flask_socketio import emit
            logger.info(f"🧠 [THINK_TANK] Processing message {message_id}")
            
            # Get available models
            models = self.get_available_models()
            if not models:
                logger.error("No models available for Think Tank mode")
                emit('response', {
                    'message_id': message_id,
                    'session_id': session_id,
                    'response': "No AI models are currently available. Please try again later.",
                    'source': 'Think Tank Error',
                    'model_info': {'error': True}
                }, room=session_id)
                return None
            
            logger.info(f"Using models: {[model.name for model in models]}")
            
            # Process models in parallel
            responses = []
            errors = {}
            
            def query_model(model):
                try:
                    logger.info(f"Querying model: {model.name}")
                    start_time = time.time()
                    
                    # Generate response
                    response = model.generate_response(query)
                    
                    processing_time = time.time() - start_time
                    logger.info(f"Model {model.name} returned in {processing_time:.2f}s")
                    
                    # Validate response if possible
                    valid = True
                    validation_info = {}
                    try:
                        from web.multi_model_processor import validate_response
                        valid, validation_info = validate_response(
                            response, query, model.name, debug_mode=True
                        )
                    except Exception as e:
                        logger.error(f"Validation error for {model.name}: {e}")
                    
                    if valid and response:
                        responses.append({
                            'model': model.name,
                            'response': response,
                            'time': processing_time,
                            'validation': validation_info
                        })
                        logger.info(f"✅ Added valid response from {model.name}")
                    else:
                        errors[model.name] = {
                            'error': 'Validation failed',
                            'details': validation_info
                        }
                        logger.warning(f"⚠️ Model {model.name} response failed validation")
                
                except Exception as e:
                    errors[model.name] = {'error': str(e)}
                    logger.error(f"❌ Error from model {model.name}: {e}")
            
            # Create and start threads for each model
            threads = []
            for model in models:
                thread = threading.Thread(target=query_model, args=(model,))
                thread.start()
                threads.append(thread)
            
            # Wait for all threads with timeout
            for thread in threads:
                thread.join(timeout=THINK_TANK_TIMEOUT)
            
            # Check if we got any valid responses
            if responses:
                # Sort by model preference or validation score
                # For now, just take the first response
                best_response = responses[0]
                logger.info(f"✅ Selected response from {best_response['model']}")
                
                # Send the response
                emit('response', {
                    'message_id': message_id,
                    'session_id': session_id,
                    'response': best_response['response'],
                    'source': f"Think Tank ({best_response['model']})",
                    'model_info': {
                        'name': best_response['model'],
                        'processing_time': best_response['time']
                    }
                }, room=session_id)
                
                return best_response['response']
            
            # No valid responses - try original handler as fallback
            logger.warning("⚠️ No valid responses from any models, trying original handler")
            try:
                return original_process(self, message_id, session_id, query, **kwargs)
            except Exception as e:
                logger.error(f"❌ Original handler also failed: {e}")
                
                # Last resort - send fallback response
                emit('response', {
                    'message_id': message_id,
                    'session_id': session_id,
                    'response': FALLBACK_RESPONSE,
                    'source': 'Think Tank Fallback',
                    'model_info': {'error': True, 'errors': errors}
                }, room=session_id)
                
                return None
        
        # Apply the patch
        multi_ai_coordinator.MultiAICoordinator.process_think_tank = enhanced_process_think_tank
        logger.info("Applied Think Tank processor patch")
        
        result.mark_success("Think Tank processor enhanced with parallel processing and timeouts")
        return result
        
    except Exception as e:
        result.mark_failure(e, "Failed to patch Think Tank processor")
        return result

def apply_fixes():
    """Apply all fixes to Minerva"""
    results = []
    
    # 1. Apply WebSocket fix
    ws_result = fix_websocket_handler()
    results.append(ws_result)
    
    # 2. Apply Think Tank fix
    tt_result = fix_think_tank_processor()
    results.append(tt_result)
    
    # Print summary
    print("\n===== Fix Application Summary =====")
    for result in results:
        status = "✅" if result.success else "❌"
        print(f"{status} {result.name}: {'Success' if result.success else 'Failed'}")
        if not result.success and result.message:
            print(f"   - {result.message}")
    
    # Return overall success
    return all(r.success for r in results)

if __name__ == "__main__":
    print("\n===== Applying Direct Fixes to Minerva =====")
    logger.info("Starting direct fix application")
    
    # Activate virtual environment
    venv_path = "/Users/bendickinson/Desktop/Minerva/venv/bin/activate"
    if os.path.exists(venv_path):
        print(f"Virtual environment found at {venv_path}")
        print("Make sure to run this script with the virtual environment activated:")
        print(f"source {venv_path} && python direct_fix.py")
    
    # Apply the fixes
    success = apply_fixes()
    
    # Summary
    if success:
        print("\n✅ All fixes have been successfully applied!")
    else:
        print("\n⚠️ Some fixes could not be applied. Check the logs for details.")
    
    print("\nNext steps:")
    print("1. Run your verification tests to confirm the fixes:")
    print("   python minerva_verification_test.py")
    print("2. Check the logs for detailed information:")
    print("   - logs/direct_fix.log")
    print("3. If issues persist, review the specific error messages in the logs")
    
    print("\n===== Fix Application Completed =====")
