"""
Patch to fix the WebSocket integration with MultiAICoordinator in app.py.
This will replace the temporary test responses with proper calls to process_message.
"""
import socketio
import asyncio
import time
import uuid
import logging
import os

from flask import Flask, request
from flask_socketio import SocketIO, emit

# Setup logging for this patch
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/websocket_fix.log',
    filemode='a'
)
logger = logging.getLogger('websocket_fix')

def fix_websocket_handler(app, socketio, coordinator):
    """
    Patch the chat_message event handler to correctly use MultiAICoordinator.
    This function replaces the temporary test responses with proper calls to process_message.
    """
    # Remove existing handler if present
    try:
        if hasattr(socketio, 'handlers') and 'chat_message' in socketio.handlers.get('/', {}):
            logger.info("Removing existing chat_message handler")
            del socketio.handlers['/']['chat_message']
    except Exception as e:
        logger.error(f"Error removing existing handler: {str(e)}")
    
    @socketio.on('chat_message')
    def handle_chat_message(data):
        """
        Enhanced chat_message handler that properly uses MultiAICoordinator.
        """
        start_time = time.time()
        logger.info(f"[WEBSOCKET] Processing chat_message: {data}")
        
        # Get message content
        message = data.get('message', '').strip()
        session_id = data.get('session_id', request.sid)
        user_id = data.get('user_id', session_id)
        message_id = data.get('message_id', str(uuid.uuid4()))
        mode = data.get('mode', 'think_tank')
        include_model_info = data.get('include_model_info', True)
        test_mode = data.get('test_mode', False)
        
        if not message:
            emit('error', {
                'code': 'empty_message',
                'message': 'Message cannot be empty'
            })
            return
        
        # Log the processing request
        logger.info(f"[WEBSOCKET] Processing message '{message[:50]}...' with mode={mode}")
        logger.info(f"[WEBSOCKET] Using coordinator instance: {coordinator}")
        
        try:
            # First emit an update that we're starting to process
            emit('processing_update', {'step': 'Starting message processing'})
            
            # Check if coordinator is properly initialized
            if not coordinator:
                raise Exception("MultiAICoordinator not initialized")
            
            # Determine if we should use async or sync processing
            is_async = hasattr(coordinator, 'process_message') and asyncio.iscoroutinefunction(coordinator.process_message)
            
            result = None
            if is_async:
                logger.info(f"[WEBSOCKET] Using async process_message")
                # Create an async task
                async def process_async():
                    try:
                        return await coordinator.process_message(
                            message=message,
                            user_id=user_id,
                            message_id=message_id,
                            mode=mode,
                            include_model_info=include_model_info,
                            test_mode=test_mode,
                            headers=request.headers
                        )
                    except Exception as e:
                        logger.error(f"[WEBSOCKET] Error in async process_message: {str(e)}")
                        raise
                
                # Run the async task with a timeout
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    asyncio.wait_for(process_async(), timeout=45.0)
                )
            else:
                logger.info(f"[WEBSOCKET] Using synchronous process_message")
                # Call directly if it's not async
                result = coordinator.process_message(
                    message=message,
                    user_id=user_id,
                    message_id=message_id,
                    mode=mode,
                    include_model_info=include_model_info,
                    test_mode=test_mode,
                    headers=request.headers
                )
            
            # Validate the result
            if not result:
                raise Exception("Coordinator returned empty result")
            
            if not isinstance(result, dict):
                raise Exception(f"Coordinator returned {type(result).__name__} instead of dict")
            
            # Extract response and model_info
            response = result.get('response', '')
            model_info = result.get('model_info', {})
            processing_time = time.time() - start_time
            
            # Log the response
            logger.info(f"[WEBSOCKET] Response received from coordinator, length: {len(response)}")
            
            # Emit the final response
            response_data = {
                'session_id': session_id,
                'message_id': message_id,
                'response': response,
                'model_info': model_info,
                'time': processing_time,
                'source': 'think_tank'
            }
            
            emit('response', response_data)
            logger.info(f"[WEBSOCKET] Emitted response for message {message_id}")
            
        except Exception as e:
            logger.error(f"[WEBSOCKET] Error processing message: {str(e)}", exc_info=True)
            # Send error response
            emit('response', {
                'session_id': session_id,
                'message_id': message_id,
                'response': f"Error processing your message: {str(e)}",
                'model_info': {"error": str(e)},
                'time': time.time() - start_time,
                'source': 'error'
            })
    
    logger.info("Successfully patched chat_message handler to use MultiAICoordinator")
    return handle_chat_message
