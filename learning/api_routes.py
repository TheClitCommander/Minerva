"""
API Routes for Self-Learning System

This module provides API routes for Minerva's self-learning framework, 
allowing for client interaction with learning components.
"""

import time
import logging
import json
from flask import Blueprint, request, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import learning components
from learning.web_integration import learning_web_integration

# Create a Flask Blueprint for learning routes
learning_blueprint = Blueprint('learning', __name__)

@learning_blueprint.route('/process', methods=['POST'])
def process_for_learning():
    """
    Process a user message for learning opportunities.
    
    Request format:
    {
        "message": "User message text",
        "user_id": "user_identifier",
        "session_id": "optional_session_id"
    }
    
    Response format:
    {
        "has_learning_content": true/false,
        "confirmation_requests": [
            {
                "request_id": "unique_id",
                "message": "Confirmation message to show user",
                "learning_item": {...} (internal representation),
                "type": "learning_confirmation"
            }
        ],
        "patterns_detected": {...},
        "preferences_detected": {...}
    }
    """
    data = request.json
    
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request: missing message"}), 400
        
    message = data.get('message', '')
    user_id = data.get('user_id', 'anonymous')
    session_id = data.get('session_id')
    
    try:
        # Process the message for learning
        results = learning_web_integration.process_user_message(
            message=message,
            user_id=user_id,
            session_id=session_id
        )
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error processing message for learning: {str(e)}")
        return jsonify({"error": str(e)}), 500


@learning_blueprint.route('/confirm', methods=['POST'])
def confirm_learning():
    """
    Handle user confirmation of a learning opportunity.
    
    Request format:
    {
        "confirmation_data": {
            "request_id": "unique_id",
            "learning_item": {...} (internal representation)
        },
        "confirmed": true/false,
        "user_id": "user_identifier"
    }
    
    Response format:
    {
        "success": true/false,
        "confirmed": true/false,
        "memory_created": true/false,
        "memory_id": "optional_memory_id"
    }
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "Invalid request data"}), 400
        
    confirmation_data = data.get('confirmation_data', {})
    confirmed = data.get('confirmed', False)
    user_id = data.get('user_id', 'anonymous')
    
    try:
        # Handle the confirmation
        result = learning_web_integration.handle_confirmation_response(
            confirmation_data=confirmation_data,
            confirmed=confirmed,
            user_id=user_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error handling learning confirmation: {str(e)}")
        return jsonify({"error": str(e), "success": False}), 500


@learning_blueprint.route('/context', methods=['POST'])
def get_learning_context():
    """
    Get learning context for a given user query.
    
    Request format:
    {
        "query": "User query text",
        "user_id": "user_identifier",
        "context_data": {...}  # Existing context data to enrich
    }
    
    Response format:
    {
        "context_data": {...},  # Enhanced context with learned information
        "learning_applied": true/false
    }
    """
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({"error": "Invalid request: missing query"}), 400
        
    query = data.get('query', '')
    user_id = data.get('user_id', 'anonymous')
    context_data = data.get('context_data', {})
    
    try:
        # Apply learned context
        enhanced_context = learning_web_integration.apply_learned_context(
            user_query=query,
            user_id=user_id,
            context_data=context_data
        )
        
        return jsonify(enhanced_context)
        
    except Exception as e:
        logger.error(f"Error retrieving learning context: {str(e)}")
        return jsonify({"error": str(e), "context_data": context_data, "learning_applied": False}), 500


@learning_blueprint.route('/status', methods=['GET'])
def learning_system_status():
    """
    Get the status of the learning system.
    
    Response format:
    {
        "status": "active",
        "components": {
            "pattern_detector": {"status": "active", "patterns_tracked": 15},
            "preference_tracker": {"status": "active", "preferences_tracked": 8}
        },
        "memory_integration": {"status": "active", "memories_created": 23}
    }
    """
    # Get status from each component
    pattern_status = {
        "status": "active",
        "patterns_tracked": len(learning_web_integration.learning.pattern_detector.patterns)
    }
    
    preference_status = {
        "status": "active", 
        "preferences_tracked": len(learning_web_integration.learning.preference_tracker.explicit_preferences)
    }
    
    memory_status = {
        "status": "active",
        "last_updated": time.time()
    }
    
    return jsonify({
        "status": "active",
        "components": {
            "pattern_detector": pattern_status,
            "preference_tracker": preference_status
        },
        "memory_integration": memory_status
    })


def register_learning_routes(app):
    """
    Register learning blueprint routes with the Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(learning_blueprint, url_prefix='/api/learning')
    logger.info("Learning API routes registered")
