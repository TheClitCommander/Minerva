#!/usr/bin/env python3
"""
Minerva Web Interface - Python 3.13 Compatible Version

This module provides a web-based interface for interacting with Minerva,
with Eventlet-related code removed for Python 3.13 compatibility.
"""

# Import standard libraries
import os
import sys
import json
from pathlib import Path
from datetime import datetime
import logging
import threading
import uuid
import time
from logging.handlers import RotatingFileHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"✅ Environment variables loaded from {env_path}")

# Import Flask and related modules
import time
import traceback
import asyncio
from functools import wraps
from flask import (
    Flask, render_template, redirect, url_for, request, jsonify, 
    send_from_directory, abort, Response, stream_with_context, session
)

# Import Minerva components (adjust import paths as needed)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import our processor modules
try:
    from web.advanced_model_router import AdvancedModelRouter
    from web.multi_model_processor import validate_response, route_request
    from web.multi_ai_coordinator import MultiAICoordinator
    from web.response_handler import clean_ai_response, format_response
    from web.error_handlers import register_error_handlers, handle_api_error, MinervaError
except ModuleNotFoundError:
    # Try relative imports for when running directly
    from advanced_model_router import AdvancedModelRouter
    from multi_model_processor import validate_response, route_request
    from multi_ai_coordinator import MultiAICoordinator  
    from response_handler import clean_ai_response, format_response
    from error_handlers import register_error_handlers, handle_api_error, MinervaError

# Initialize Flask app
app = Flask(__name__,
            template_folder='templates' if os.path.exists('templates') else 'web/templates',
            static_folder='static' if os.path.exists('static') else 'web/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'minerva-secret-key')
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Set admin API key
ADMIN_API_KEY = os.environ.get("MINERVA_ADMIN_KEY", "minerva-admin-key")

# MultiAI Coordinator reference
global multi_ai_coordinator
multi_ai_coordinator = MultiAICoordinator.get_instance()
logger.info("Initialized MultiAICoordinator at global level")

# Register error handlers
register_error_handlers(app)

# Import relevant functions from app.py
try:
    from web.app import get_multi_ai_coordinator, initialize_ai_router, get_query_tags
    from web.app import register_real_api_processors
    # Note: add_simulated_processors has been removed from web.app
except ImportError:
    # Define simplified versions of these functions
    def get_multi_ai_coordinator():
        return multi_ai_coordinator
    
    def initialize_ai_router():
        coordinator = get_multi_ai_coordinator()
        if coordinator:
            register_real_api_processors(coordinator)
            # We no longer use simulated processors in production
            # Use real model processors instead
            logger.info("✅ AI Router initialized with MultiAICoordinator")
            return True
        return False
    
    def register_real_api_processors(coordinator):
        # Try to register any available real models
        logger.warning("⚠️ Using simplified processor registration")
        try:
            # Check if any API keys are available for registering real models
            import os
            real_models_registered = []
            
            # Add minimal fallback if needed for compatibility
            if not real_models_registered and hasattr(coordinator, 'register_model_processor'):
                logger.warning("⚠️ No real models available, using minimal fallback")
                # Register a minimal fallback processor
                async def minimal_fallback_processor(message):
                    return {"response": "I'm sorry, I couldn't process your request. Please try again later.", 
                            "model": "fallback", 
                            "quality_score": 0.5}
                coordinator.register_model_processor("fallback", minimal_fallback_processor)
                
            return real_models_registered
        except Exception as e:
            logger.error(f"❌ Failed to register processors: {e}")
            return []
    
    def get_query_tags(message):
        # Simplified version that returns basic tags
        return ["general"]

# Initialize the AI router
initialize_ai_router()

# Define API routes
@app.route('/api/v1/advanced-think-tank', methods=['POST'])
def advanced_think_tank_api():
    """
    Advanced Think Tank API endpoint using the new model router.
    """
    try:
        # Extract data from request
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract and validate required fields
        message = data.get('message')
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        user_id = data.get('user_id', 'anonymous')
        conversation_id = data.get('conversation_id', str(uuid.uuid4()))
        test_mode = 'X-Test-Mode' in request.headers
        
        # Log request information
        request_id = str(uuid.uuid4())
        logger.info(f"Think Tank Request {request_id}: {message[:50]}... (Length: {len(message)})")
        
        # Process message with the Think Tank
        coordinator = get_multi_ai_coordinator()
        if not coordinator:
            return jsonify({"error": "Think Tank system not available"}), 503
        
        # The advanced router will select appropriate models based on message content
        router = AdvancedModelRouter()
        response_data = router.route_and_process_query(message)
        
        # Return the response
        return jsonify(response_data), 200
    
    except Exception as e:
        error_message = f"Error in advanced think tank: {str(e)}"
        logger.error(f"{error_message}\n{traceback.format_exc()}")
        return jsonify({"error": error_message}), 500

@app.route('/api/test', methods=['GET'])
def test_route():
    """Simple test endpoint to verify the API is working."""
    return jsonify({
        "status": "success",
        "message": "Minerva API is working correctly",
        "version": "1.0.0"
    })

# Main route
@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

if __name__ == '__main__':
    # Run the app directly when this script is executed
    app.run(host='127.0.0.1', port=9876, debug=False)
