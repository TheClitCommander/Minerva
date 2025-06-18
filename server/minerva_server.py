#!/usr/bin/env python3
"""
Minerva Server

Clean, modern server implementation for Minerva AI Assistant.
Consolidates best features from all previous server implementations.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import core components
from core.config import config
from core.coordinator import coordinator

# Import Flask components
from flask import Flask, request, render_template, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, Namespace

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MinervaServer:
    """Main Minerva server class with clean architecture."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Initialize the Minerva server."""
        self.host = host
        self.port = port
        self.debug = debug
        
        # Initialize Flask app
        self.app = Flask(
            __name__,
            static_folder=str(PROJECT_ROOT / 'static'),
            template_folder=str(PROJECT_ROOT / 'templates')
        )
        
        # Enable CORS for all routes
        CORS(self.app)
        
        # Initialize SocketIO
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            logger=debug,
            engineio_logger=debug,
            async_mode='threading'
        )
        
        # Set up routes
        self._setup_routes()
        self._setup_websocket_handlers()
        
        logger.info(f"Minerva server initialized on {host}:{port}")
    
    def _setup_routes(self):
        """Set up HTTP routes."""
        
        @self.app.route('/')
        def index():
            """Main page."""
            return render_template('index.html')
        
        @self.app.route('/portal')
        def portal():
            """Minerva portal interface."""
            return send_from_directory('web', 'minerva-portal.html')
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'coordinator_available': coordinator is not None,
                'models_available': len(coordinator.get_available_models()['models']) if coordinator else 0
            })
        
        @self.app.route('/api/models')
        def get_models():
            """Get available AI models."""
            if coordinator:
                return jsonify(coordinator.get_available_models())
            else:
                return jsonify({'error': 'Coordinator not available'}), 503
        
        @self.app.route('/api/config')
        def get_config():
            """Get server configuration."""
            return jsonify({
                'server': config.server_config,
                'ai': config.ai_config,
                'memory': config.memory_config
            })
        
        # Serve static files
        @self.app.route('/<path:filename>')
        def serve_static(filename):
            """Serve static files."""
            return send_from_directory('web', filename)
    
    def _setup_websocket_handlers(self):
        """Set up WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            logger.info(f"Client connected: {request.sid}")
            emit('status', {'message': 'Connected to Minerva'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('chat_message')
        def handle_chat_message(data):
            """Handle chat messages."""
            try:
                user_input = data.get('message', '')
                session_id = data.get('session_id', request.sid)
                model_preference = data.get('model', 'default')
                
                if not user_input:
                    emit('chat_reply', {
                        'error': 'Empty message',
                        'status': 'error'
                    })
                    return
                
                logger.info(f"Processing message: {user_input[:50]}...")
                
                # Generate response using coordinator
                if coordinator:
                    response = coordinator.generate_response(
                        user_input,
                        session_id=session_id,
                        model_preference=model_preference
                    )
                else:
                    response = "I'm currently in simulation mode. Please ensure the AI coordinator is properly initialized."
                
                # Send response
                emit('chat_reply', {
                    'message': response,
                    'status': 'success',
                    'session_id': session_id
                })
                
            except Exception as e:
                logger.error(f"Error processing chat message: {e}")
                emit('chat_reply', {
                    'error': str(e),
                    'status': 'error'
                })
        
        @self.socketio.on('join_session')
        def handle_join_session(data):
            """Handle session joining."""
            session_id = data.get('session_id', request.sid)
            user_id = data.get('user_id', 'anonymous')
            
            logger.info(f"User {user_id} joining session {session_id}")
            
            emit('session_joined', {
                'session_id': session_id,
                'user_id': user_id,
                'status': 'success'
            })
    
    def run(self):
        """Start the server."""
        logger.info(f"Starting Minerva server on {self.host}:{self.port}")
        logger.info(f"Debug mode: {'enabled' if self.debug else 'disabled'}")
        
        # Ensure required directories exist
        (PROJECT_ROOT / 'static').mkdir(exist_ok=True)
        (PROJECT_ROOT / 'templates').mkdir(exist_ok=True)
        
        try:
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=self.debug,
                use_reloader=False,
                log_output=True
            )
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


def main():
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description='Minerva AI Server')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=5000, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and run server
    server = MinervaServer(
        host=args.host,
        port=args.port,
        debug=args.debug
    )
    
    server.run()


if __name__ == '__main__':
    main() 