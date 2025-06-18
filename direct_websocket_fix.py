#!/usr/bin/env python3
"""
Direct WebSocket Fix for Minerva

This script directly patches the WebSocket handler in app.py to:
1. Add comprehensive request tracking
2. Handle timeouts automatically
3. Ensure all messages receive a response

Run with: python direct_websocket_fix.py
"""
import os
import sys
import time
import logging
import threading
from datetime import datetime

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/direct_websocket_fix.log',
    filemode='a'
)
logger = logging.getLogger('direct_websocket_fix')

# Constants
REQUEST_TIMEOUT = 30  # seconds

# Request tracking dictionary
active_requests = {}
request_lock = threading.Lock()

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
            
            # Clean up old completed requests (after 5 minutes)
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
    logger.warning(f"Request {message_id} timed out after {REQUEST_TIMEOUT}s")
    
    try:
        with request_lock:
            if message_id not in active_requests:
                return
                
            request = active_requests[message_id]
            if request['completed']:
                return
                
            # Mark as completed to prevent duplicate handling
            request['completed'] = True
            
            # Get emit function and session ID
            emit_func = request.get('emit_func')
            session_id = request.get('session_id')
            
            if not emit_func or not session_id:
                logger.error(f"Missing emit function or session ID for {message_id}")
                return
        
        # Send fallback response
        emit_func('response', {
            'message_id': message_id,
            'session_id': session_id,
            'response': "I'm sorry, but this request has timed out. Please try again.",
            'source': 'Timeout Handler',
            'model_info': {'error': True, 'timeout': True}
        }, room=session_id)
        
        logger.info(f"Sent timeout fallback for {message_id}")
        
    except Exception as e:
        logger.error(f"Failed to send timeout fallback: {e}")

def apply_fix():
    """Apply the WebSocket fix to the running Minerva instance"""
    try:
        # Import app module, assuming we're in the same directory
        sys.path.insert(0, os.path.abspath('.'))
        from web.app import socketio, handle_chat_message
        from flask_socketio import emit
        
        logger.info("Successfully imported Flask-SocketIO and app modules")
        
        # Store original handler
        original_handler = handle_chat_message
        logger.info(f"Stored original handler: {original_handler.__name__}")
        
        # Define enhanced handler with request tracking
        def enhanced_handle_chat_message(data):
            """Enhanced chat message handler with request tracking"""
            # Extract message ID and session ID
            message_id = data.get('message_id', 'unknown')
            session_id = data.get('session_id', 'unknown')
            
            logger.info(f"Processing message {message_id} from session {session_id}")
            
            # Track this request
            with request_lock:
                active_requests[message_id] = {
                    'timestamp': datetime.now(),
                    'session_id': session_id,
                    'completed': False,
                    'emit_func': emit  # Store the emit function
                }
            
            try:
                # Call original handler
                result = original_handler(data)
                
                # Mark as completed if it returned
                with request_lock:
                    if message_id in active_requests:
                        active_requests[message_id]['completed'] = True
                        logger.info(f"Message {message_id} completed successfully")
                
                return result
                
            except Exception as e:
                logger.error(f"Error processing message {message_id}: {e}")
                
                # Send an error response to prevent stuck UI
                try:
                    emit('response', {
                        'message_id': message_id,
                        'session_id': session_id,
                        'response': "I'm sorry, but an error occurred while processing your request. Please try again.",
                        'source': 'Error Handler',
                        'model_info': {'error': True, 'exception': str(e)}
                    }, room=session_id)
                    
                    # Mark as completed
                    with request_lock:
                        if message_id in active_requests:
                            active_requests[message_id]['completed'] = True
                except Exception as emit_error:
                    logger.error(f"Failed to send error response: {emit_error}")
                
                # Re-raise the exception for normal error handling
                raise
        
        # Replace the original handler
        from web import app
        app.handle_chat_message = enhanced_handle_chat_message
        
        # Update the socketio handler
        socketio.on('chat_message')(enhanced_handle_chat_message)
        
        logger.info("Successfully patched WebSocket handler with request tracking")
        
        # Start the timeout monitor thread
        monitor_thread = threading.Thread(target=monitor_timeouts, daemon=True)
        monitor_thread.start()
        logger.info("Started timeout monitor thread")
        
        print("✅ WebSocket fix successfully applied!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply WebSocket fix: {e}")
        print(f"❌ Failed to apply WebSocket fix: {e}")
        return False

def apply_think_tank_fix():
    """Apply the Think Tank fix to the running Minerva instance"""
    try:
        # Import multi_ai_coordinator module
        sys.path.insert(0, os.path.abspath('.'))
        from web.multi_ai_coordinator import MultiAICoordinator
        
        logger.info("Successfully imported MultiAICoordinator")
        
        # Check if process_think_tank method exists
        if not hasattr(MultiAICoordinator, 'process_think_tank'):
            logger.warning("MultiAICoordinator does not have process_think_tank method, adding default implementation")
            
            # Add default implementation
            from flask_socketio import emit
            
            def default_process_think_tank(self, message_id, session_id, query):
                """Default implementation of Think Tank processing"""
                # Get available models
                models = self.get_available_models()
                if not models:
                    emit('response', {
                        'message_id': message_id,
                        'session_id': session_id,
                        'response': "No AI models are currently available. Please try again later.",
                        'source': 'Error',
                        'model_info': {'error': True}
                    }, room=session_id)
                    return None
                
                # Fall back to single model
                model = models[0]
                return self.process_message(message_id, session_id, query, model)
            
            # Add method to class
            MultiAICoordinator.process_think_tank = default_process_think_tank
            logger.info("Added default process_think_tank method")
        
        # Store original method
        original_method = MultiAICoordinator.process_think_tank
        logger.info(f"Original process_think_tank method stored: {original_method.__name__}")
        
        # Define enhanced method
        from flask_socketio import emit
        import threading
        
        def enhanced_process_think_tank(self, message_id, session_id, query, **kwargs):
            """Enhanced Think Tank processor with timeout and parallel processing"""
            logger.info(f"Processing Think Tank request {message_id}")
            
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
            
            # Track responses
            responses = []
            response_lock = threading.Lock()
            
            def query_model(model):
                try:
                    logger.info(f"Querying model: {model.name}")
                    
                    # Process with this model
                    response = self.process_message(message_id, session_id, query, model)
                    
                    if response:
                        with response_lock:
                            responses.append({
                                'model': model.name,
                                'response': response
                            })
                            logger.info(f"Got response from {model.name}")
                except Exception as e:
                    logger.error(f"Error from model {model.name}: {e}")
            
            # Create threads for each model
            threads = []
            for model in models[:2]:  # Limit to first 2 models
                thread = threading.Thread(target=query_model, args=(model,))
                thread.start()
                threads.append(thread)
            
            # Wait for threads with timeout (25 seconds)
            for thread in threads:
                thread.join(timeout=25)
            
            # Check if we got any responses
            if responses:
                # Take the first response for now (could be improved)
                best_response = responses[0]
                logger.info(f"Using response from {best_response['model']}")
                
                return best_response['response']
            
            # Fall back to original implementation
            logger.warning("No responses from parallel processing, falling back to original method")
            return original_method(self, message_id, session_id, query, **kwargs)
        
        # Apply enhanced method
        MultiAICoordinator.process_think_tank = enhanced_process_think_tank
        logger.info("Successfully patched process_think_tank method")
        
        print("✅ Think Tank fix successfully applied!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply Think Tank fix: {e}")
        print(f"❌ Failed to apply Think Tank fix: {e}")
        return False

if __name__ == "__main__":
    print("\n===== Applying Direct WebSocket Fix to Minerva =====")
    
    # Apply WebSocket fix
    print("\nApplying WebSocket fix...")
    ws_success = apply_fix()
    
    # Apply Think Tank fix
    print("\nApplying Think Tank fix...")
    tt_success = apply_think_tank_fix()
    
    # Print summary
    print("\n===== Fix Application Summary =====")
    print(f"WebSocket Fix: {'✅ SUCCESS' if ws_success else '❌ FAILED'}")
    print(f"Think Tank Fix: {'✅ SUCCESS' if tt_success else '❌ FAILED'}")
    
    if ws_success and tt_success:
        print("\n✅ All fixes successfully applied!")
    else:
        print("\n⚠️ Some fixes could not be applied. Check the logs for details.")
    
    print("\n===== Next Steps =====")
    print("1. Restart your Minerva application for the fixes to take effect")
    print("2. Run the verification test:")
    print("   python minerva_verification_test.py")
    print("3. Check the logs for detailed information:")
    print("   - logs/direct_websocket_fix.log")
    
    print("\n===== Fix Application Completed =====")
