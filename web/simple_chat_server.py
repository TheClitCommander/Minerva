#!/usr/bin/env python3
"""
Simple Chat Server
Serves the simplest_test.html file and proxies API requests to the Think Tank
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("simple_chat_server")

# Load environment variables from .env file
env_path = os.path.join(parent_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
    
    # Log available API keys (without exposing the actual keys)
    api_keys = {
        'OpenAI': os.environ.get('OPENAI_API_KEY'),
        'Anthropic': os.environ.get('ANTHROPIC_API_KEY'),
        'Mistral': os.environ.get('MISTRAL_API_KEY'),
        'Google': os.environ.get('GOOGLE_API_KEY'),
        'Cohere': os.environ.get('COHERE_API_KEY'),
        'HuggingFace': os.environ.get('HUGGINGFACE_API_KEY')
    }
    
    for provider, key in api_keys.items():
        if key:
            key_preview = f"{key[:5]}...{key[-3:]}" if len(key) > 10 else "[REDACTED]"
            logger.info(f"{provider} API key loaded (preview: {key_preview})")
        else:
            logger.warning(f"{provider} API key not found")
else:
    logger.warning(f".env file not found at {env_path}")

# Force MINERVA_TEST_MODE to false to use real API calls
os.environ["MINERVA_TEST_MODE"] = "false"
logger.info("Using real API calls (MINERVA_TEST_MODE=false)")

# Import the processor module directly
try:
    from processor.think_tank import process_with_think_tank
    logger.info("Successfully imported Think Tank processor")
except ImportError as e:
    logger.error(f"Failed to import Think Tank processor: {e}")
    logger.error("Make sure the processor module is properly installed")
    sys.exit(1)

# Import Flask for the web server
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    """Serve the minimal_chat.html file"""
    try:
        return send_from_directory(current_dir, 'minimal_chat.html')
    except Exception as e:
        logger.error(f"Error serving index page: {e}")
        return f"<html><body><h1>Error loading page</h1><p>Error: {str(e)}</p><p>Please check server logs.</p></body></html>"

@app.route('/api/think-tank', methods=['POST'])
def think_tank_api():
    """Process a message using the Think Tank"""
    try:
        # Get the request data
        data = request.json
        message = data.get('message', '')
        conversation_id = data.get('conversation_id', 'simple-chat')
        model_preferences = data.get('model_preferences', {})
        
        logger.info(f"Processing message: {message[:50]}...")
        
        # Process with Think Tank
        result = process_with_think_tank(
            message=message,
            model_priority=["gpt-4o", "claude-3-opus", "gpt-4"],
            complexity=0.5,  # Medium complexity to encourage good responses
            query_tags=None  # Let the system determine tags automatically
        )
        
        # Get the response
        response = result.get('response')
        
        # If there's no response, but we have individual model responses, use the one from gpt-4o
        if not response and 'model_responses' in result:
            model_responses = result.get('model_responses', {})
            if 'gpt-4o' in model_responses:
                response = model_responses['gpt-4o']
            elif model_responses:
                # Take the first available response
                response = next(iter(model_responses.values()))
            else:
                response = "I apologize, but I couldn't generate a response at this time."
        
        # Prepare the model info
        model_info = result.get('model_info', {})
        if not model_info:
            # Create basic model info if none exists
            used_models = []
            for model in result.get('model_responses', {}):
                used_models.append(model)
            
            model_info = {
                'models_used': used_models,
                'primary_model': used_models[0] if used_models else "gpt-4o"
            }
        
        # Return the response
        return jsonify({
            'response': response,
            'model_info': model_info,
            'conversation_id': conversation_id,
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return jsonify({
            'status': 'error',
            'message': f"An error occurred while processing your request: {str(e)}",
            'response': "I apologize, but I encountered an error while processing your request. Please try again."
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Simple Chat Server'
    })

# Serve static files (CSS, JS, etc.)
@app.route('/<path:path>')
def static_files(path):
    """Serve static files from the web directory"""
    return send_from_directory(current_dir, path)

if __name__ == '__main__':
    port = 9090  # Changed to 9090 since 8080 is also in use
    logger.info("Starting Simple Chat Server...")
    logger.info(f"Access the chat interface at: http://localhost:{port}/")
    app.run(debug=True, host='0.0.0.0', port=port)
