#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test server for Minerva that integrates with MultiAICoordinator.
It's designed to test WebSocket communication and enhanced logging.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
import uuid
import eventlet
eventlet.monkey_patch()

# Set up logging path
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/coordinator_process.log',
    filemode='a'
)

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

# Import MultiAICoordinator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.multi_ai_coordinator import MultiAICoordinator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'minerva-test-server'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize MultiAICoordinator
coordinator = MultiAICoordinator()
logger = logging.getLogger('test_server')
logger.info("Initialized MultiAICoordinator for testing")

@app.route('/')
def index():
    """Index page that redirects to the chat page"""
    return render_template('simple_chat.html')

@app.route('/test_chat')
def test_chat():
    """Serve the test chat HTML file"""
    return app.send_static_file('test_chat.html')

@app.route('/api/direct', methods=['POST'])
def direct_api():
    """Direct API endpoint that always returns a response"""
    data = request.json
    message = data.get('message', '')
    
    print(f"[API] Received message: {message}")
    
    # Generate a simple response
    response = f"This is a test response to: {message}"
    
    return jsonify({
        'response': response,
        'message_id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"[SOCKET] Client connected: {request.sid}")
    emit('message', {'message': 'Connected to Minerva test server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"[SOCKET] Client disconnected: {request.sid}")

@socketio.on('message')
def handle_basic_message(message):
    """Handle basic message events"""
    print(f"[SOCKET] Received message: {message}")
    
    # Simple echo back
    emit('message', {'message': f"Echo: {message}"})

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle structured chat message events using the real MultiAICoordinator"""
    print(f"[SOCKET] Received chat message: {data}")
    
    message = data.get('message', '')
    message_id = data.get('message_id', str(uuid.uuid4()))
    user_id = data.get('session_id', 'default_user')
    mode = data.get('mode', 'think_tank')
    include_model_info = data.get('include_model_info', True)
    
    # Log the received message
    logger.info(f"Processing message: {message_id} from {user_id}")
    
    # Send thinking status
    emit('thinking', {'message': 'Thinking...'})
    
    try:
        # Process the message using MultiAICoordinator
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async processing in the eventlet-compatible way
        def process_with_coordinator():
            result = loop.run_until_complete(
                coordinator.process_message(
                    message=message,
                    user_id=user_id,
                    message_id=message_id,
                    mode=mode,
                    include_model_info=include_model_info,
                    test_mode=True
                )
            )
            return result
        
        # Execute the processing
        result = process_with_coordinator()
        
        # Prepare response based on result type
        if isinstance(result, dict):
            # Standard think tank response
            response_data = {
                'session_id': user_id,
                'message_id': message_id,
                'response': result.get('response', 'No response generated'),
                'model_info': result.get('model_info', {'test': True, 'response_id': f'resp_{uuid.uuid4().hex[:8]}'}),
                'time': result.get('processing_time', 0.1),
                'source': result.get('model_used', 'think_tank_test')
            }
        else:
            # Simple string response
            response_data = {
                'session_id': user_id,
                'message_id': message_id,
                'response': result if isinstance(result, str) else 'No response generated',
                'model_info': {'test': True, 'response_id': f'resp_{uuid.uuid4().hex[:8]}'},
                'time': 0.1,
                'source': 'think_tank_test'
            }
        
        logger.info(f"Processed message {message_id} successfully")
    except Exception as e:
        # Handle errors and provide a fallback response
        error_msg = f"Error processing message: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        
        response_data = {
            'session_id': user_id,
            'message_id': message_id,
            'response': f"I apologize, but there was an error processing your request: {str(e)}",
            'model_info': {'test': True, 'error': True, 'response_id': f'resp_{uuid.uuid4().hex[:8]}'},
            'time': 0.1,
            'source': 'error_handler'
        }
    
    # Send the response back to the client
    emit('response', response_data)
    
    # Also emit a message received confirmation
    emit('message_received', {'session_id': user_id, 'message_id': message_id})

if __name__ == '__main__':
    print("[INFO] Starting Minerva test server on port 9876")
    socketio.run(app, host='0.0.0.0', port=9876, debug=True)
