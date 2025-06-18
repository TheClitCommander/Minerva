"""
WebSocket Handler Fix for Minerva

Enhances the WebSocket message handling to prevent stuck requests and ensure all
messages receive a response, even when AI models fail.
"""
import logging
import os
import sys
from pathlib import Path
import importlib

# Setup logging
os.makedirs('logs', exist_ok=True)
logger = logging.getLogger('websocket_fix')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('logs/websocket_fix.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def patch_websocket_handler():
    """
    Patches the WebSocket handler to ensure all messages get responses
    using the RequestTracker for monitoring.
    """
    logger.info("🔧 Patching WebSocket handler...")
    
    try:
        # Import required modules
        minerva_path = Path('/Users/bendickinson/Desktop/Minerva')
        sys.path.append(str(minerva_path))
        sys.path.append(str(minerva_path / 'web'))
        
        # Import sockets module and RequestTracker
        from web import sockets
        from websocket_request_tracker import get_request_tracker
        
        # Store original handler
        original_handler = sockets.handle_chat_message
        
        # Define patched handler
        def patched_handle_chat_message(message_data):
            """
            Patched WebSocket message handler that tracks requests and ensures
            all messages receive responses.
            """
            message_id = message_data.get('message_id')
            session_id = message_data.get('session_id')
            
            logger.info(f"📥 [MESSAGE_RECEIVED] Processing message {message_id}")
            
            # Track this request
            from flask_socketio import emit
            request_tracker = get_request_tracker()
            request_tracker.add_request(message_id, session_id, emit)
            
            try:
                # Call original handler
                result = original_handler(message_data)
                
                # Request completed successfully
                request_tracker.complete_request(message_id)
                logger.info(f"✅ [MESSAGE_COMPLETED] Message {message_id} processed successfully")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ [MESSAGE_ERROR] Error processing message {message_id}: {str(e)}")
                
                # Don't mark as complete - let the timeout handler deal with it
                # The request tracker will send a fallback response if needed
                
                # Re-raise exception for normal error handling
                raise
        
        # Apply the patch
        sockets.handle_chat_message = patched_handle_chat_message
        
        logger.info("✅ WebSocket handler successfully patched")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to patch WebSocket handler: {str(e)}")
        return False
