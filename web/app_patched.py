#!/usr/bin/env python3
"""
Minerva Web Interface

This module provides a web-based interface for interacting with Minerva,
allowing for chat, settings management, and visualization of memories.
"""

# Import and configure eventlet first, before any other imports
import eventlet
eventlet.monkey_patch()
print("[STARTUP] Eventlet monkey patching applied for app.py")

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import logging
import threading
import uuid
import time
import traceback
import asyncio
from functools import wraps
from flask import (
    Flask, render_template, redirect, url_for, request, jsonify, 
    send_from_directory, abort, Response, stream_with_context, session
)
from flask_socketio import SocketIO, emit, disconnect
from flask_session import Session  # Import Flask-Session
from flask import copy_current_request_context
from flask_wtf.csrf import CSRFProtect

# Import our response handler module
from response_handler import clean_ai_response, format_response
from werkzeug.utils import secure_filename

# Add the parent directory to the path to import Minerva modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import error handling module
from error_handlers import register_error_handlers, handle_api_error, MinervaError, DocumentNotFoundError, InvalidRequestError, log_error

# Import Minerva components
from minerva_main import MinervaAI
from memory.memory_manager import MemoryManager
from knowledge.knowledge_manager import KnowledgeManager

# Import plugin system
from plugins.base import PluginManager

# Import user preference manager
from users.user_preference_manager import user_preference_manager

# Initialize Flask app
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'minerva-secret-key')
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)  # Initialize Flask-Session
# Temporarily disable CSRF protection to fix API issues
# csrf = CSRFProtect(app)
app.config['WTF_CSRF_ENABLED'] = False

# Set admin API key (in production, use environment variable)
ADMIN_API_KEY = os.environ.get("MINERVA_ADMIN_KEY", "minerva-admin-key")

# MultiAI Coordinator reference - initialize at global level
global multi_ai_coordinator
try:
    from multi_ai_coordinator import multi_ai_coordinator as global_coordinator
    multi_ai_coordinator = global_coordinator
    print("[STARTUP] Initialized MultiAICoordinator at global level")
except Exception as e:
    print(f"[ERROR] Failed to initialize MultiAICoordinator at global level: {e}")
    multi_ai_coordinator = None

def get_multi_ai_coordinator():
    """
    Helper function to get the MultiAICoordinator instance.
    Makes testing and dependency injection easier.
    
    Returns:
        MultiAICoordinator or None: The instance if available
    """
    global multi_ai_coordinator
    if multi_ai_coordinator is None:
        logger.info("[WARNING] MultiAICoordinator is None, attempting re-initialization")
        try:
            # Import and initialize the coordinator
            from multi_ai_coordinator import multi_ai_coordinator as global_coordinator, MultiAICoordinator
            multi_ai_coordinator = global_coordinator
            
            # Make sure it's initialized
            if hasattr(multi_ai_coordinator, 'initialize'):
                logger.info("[RECOVERY] Explicitly initializing MultiAICoordinator")
                multi_ai_coordinator.initialize()
            
            logger.info("[RECOVERY] MultiAICoordinator re-initialized successfully")
        except Exception as e:
            logger.error(f"[ERROR] Failed to re-initialize MultiAICoordinator: {e}")
    
    # Always check if we need to register simulated processors, regardless of whether coordinator was just initialized
    if multi_ai_coordinator and hasattr(multi_ai_coordinator, 'model_processors') and len(multi_ai_coordinator.model_processors) == 0:
        try:
            # Define simulated processors directly to avoid import issues
            def simple_gpt4_processor(message):
                return {"response": f"Simulated GPT-4 response for query: {message[:50]}...", "model": "gpt4", "quality_score": 0.92}
            
            def simple_claude3_processor(message):
                return {"response": f"Simulated Claude-3 response for: {message[:50]}...", "model": "claude3", "quality_score": 0.89}
            
            def simple_mistral_processor(message):
                return {"response": f"Simulated Mistral-7B response about: {message[:50]}...", "model": "mistral7b", "quality_score": 0.81}
            
            def simple_gpt4all_processor(message):
                return {"response": f"Simulated GPT4All response regarding: {message[:50]}...", "model": "gpt4all", "quality_score": 0.76}
            
            # Register simulated processors directly
            multi_ai_coordinator.register_model_processor('gpt4', simple_gpt4_processor)
            multi_ai_coordinator.register_model_processor('claude3', simple_claude3_processor)
            multi_ai_coordinator.register_model_processor('mistral7b', simple_mistral_processor)
            multi_ai_coordinator.register_model_processor('gpt4all', simple_gpt4all_processor)
            logger.info("[RECOVERY] Registered simulated model processors for Think Tank testing")
        except Exception as e:
            logger.error(f"[ERROR] Failed to register simulated processors: {e}")
    
    return multi_ai_coordinator
    
def initialize_ai_router():
    """
    Initialize the AI router with our enhanced 'think tank' approach to the MultiAICoordinator.
    This ensures that Minerva consults multiple AI models and selects the best response.
    """
    try:
        # Import necessary components
        global multi_ai_coordinator
        try:
            from multi_model_processor import route_request, get_query_tags, validate_response
            router_components_loaded = True
            print("[STARTUP] Successfully loaded AI router components")
        except ImportError as import_error:
            router_components_loaded = False
            print(f"[WARNING] Failed to import router components: {import_error}")
            print("[RECOVERY] Will attempt to use fallback model selection")
        
        if not multi_ai_coordinator:
            print("[ERROR] MultiAICoordinator not initialized, attempting recovery")
            try:
                from multi_ai_coordinator import multi_ai_coordinator as global_coordinator
                multi_ai_coordinator = global_coordinator
                print("[STARTUP] Recovered MultiAICoordinator instance during router initialization")
            except Exception as recovery_error:
                print(f"[CRITICAL] Failed to recover MultiAICoordinator: {recovery_error}")
                return False
        
        # Create a model selection override function that uses the route_request function
        def enhanced_model_selection(user_id, message):
            """
            Enhanced model selection function that implements the 'think tank' approach.
            Instead of selecting one model, it returns ALL available models in priority order.
            The MultiAICoordinator will query all models and select the best response.
            """
            print(f"[AI ROUTER] Analyzing message for think tank approach...")
            
            # Safety check and fallback
            if not router_components_loaded or not message:
                print("[AI ROUTER] Using fallback model selection")
                # Simple fallback that still enables think tank mode
                return {
                    'models_to_use': list(multi_ai_coordinator.model_processors.keys()),
                    'timeout': 20.0,
                    'formatting_params': {},
                    'retrieval_depth': 'standard',
                    'repository_guided': False,
                    'dashboard_guided': False,
                    'complexity': 2,  # Medium complexity
                    'confidence_threshold': 0.6,
                    'query_tags': ['general'],
                    'think_tank_mode': True
                }
            
            try:
                # Get available models from the coordinator
                available_models = list(multi_ai_coordinator.model_processors.keys()) if hasattr(multi_ai_coordinator, 'model_processors') else []
                print(f"[AI ROUTER] Available models: {available_models}")
                
                if not available_models:
                    print("[AI ROUTER] No models available, using huggingface fallback")
                    available_models = ['huggingface']
                
                # Get routing decision with all available models in priority order
                routing_decision = route_request(message, available_models)
                print(f"[AI ROUTER] Think tank routing decision: {routing_decision}")
                
                # Safety check for routing_decision
                if not isinstance(routing_decision, dict):
                    print("[AI ROUTER] Invalid routing decision, using fallback")
                    # Fallback to simple model list
                    return {
                        'models_to_use': available_models,
                        'timeout': 20.0,
                        'formatting_params': {},
                        'complexity': 2,
                        'confidence_threshold': 0.7,
                        'query_tags': ['general'],
                        'think_tank_mode': True
                    }
                
                # Create a decision dictionary for the MultiAICoordinator with the correct key names
                coordinator_decision = {
                    'models_to_use': routing_decision.get('models', available_models),
                    'timeout': 30.0,  # Longer timeout for multiple models
                    'formatting_params': {},
                    'retrieval_depth': 'standard',
                    'repository_guided': False,
                    'dashboard_guided': True,
                    'complexity': routing_decision.get('complexity', 2),  # Default to medium if missing
                    'confidence_threshold': routing_decision.get('confidence', 0.7),
                    'query_tags': routing_decision.get('query_tags', ['general']),
                    'think_tank_mode': routing_decision.get('think_tank_mode', True)
                }
                
                # Add detailed analytics if available
                if 'message_analysis' in routing_decision:
                    coordinator_decision['message_analysis'] = routing_decision['message_analysis']
                
                print(f"[AI ROUTER] Coordinator decision: {coordinator_decision}")
                return coordinator_decision
                
            except Exception as routing_error:
                print(f"[ERROR] Error in enhanced model selection: {routing_error}")
                # Return a safe fallback decision
                return {
                    'models_to_use': available_models if available_models else ['huggingface'],
                    'timeout': 20.0,
                    'formatting_params': {},
                    'complexity': 2,
                    'confidence_threshold': 0.7,
                    'query_tags': ['general'],
                    'think_tank_mode': True
                }
        
        # Set the model selection override in the MultiAICoordinator
        multi_ai_coordinator.set_model_selection_override(enhanced_model_selection)
        print("[AI SYSTEM] Think tank AI approach initialized successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to initialize AI router: {e}")
        return False
        
def get_query_tags(message):
    """
    Analyze a user message and return relevant tags for better model selection and evaluation.
    """
    tags = []
    message_lower = message.lower()
    
    # Check for different query types
    if any(term in message_lower for term in ["calculate", "math", "equation", "solve", "formula", "computation"]):
        tags.append("math")
    if any(term in message_lower for term in ["code", "programming", "function", "algorithm", "python", "javascript", "java"]):
        tags.append("code")
    if any(term in message_lower for term in ["finance", "economics", "money", "business", "investment", "stocks"]):
        tags.append("finance")
    if any(term in message_lower for term in ["explain", "analyze", "compare", "contrast", "synthesize", "evaluate"]):
        tags.append("analytical")
    if len(message) > 200:
        tags.append("complex")
    if any(term in message_lower for term in ["creative", "imagine", "story", "fiction", "poem", "design"]):
        tags.append("creative")
    if any(term in message_lower for term in ["fact", "when", "where", "historical", "event", "date"]):
        tags.append("factual")
    
    # Add a general tag if no specific tags were identified
    if not tags:
        tags.append("general")
        
    return tags

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in header
        api_key = request.headers.get('X-Admin-API-Key')
        if not api_key or api_key != ADMIN_API_KEY:
            return jsonify({"status": "error", "message": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# API endpoint for think tank insights
@app.route('/api/think-tank/insights', methods=['GET'])
def get_think_tank_insights():
    """Return insights about the think tank model evaluations."""
    try:
        # Get statistics from both the model evaluator and insights manager
        from model_evaluator import evaluator
        from model_insights_manager import model_insights_manager
        
        # Enhanced debugging
        logger.info(f"[THINK TANK DEBUG] Getting evaluator statistics...")
        
        # Check the evaluator directory exists
        eval_storage_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evaluation_storage")
        os.makedirs(eval_storage_dir, exist_ok=True)
        logger.info(f"[THINK TANK DEBUG] Evaluation storage dir: {eval_storage_dir}, exists: {os.path.exists(eval_storage_dir)}")
        
        # Manual check for files in the evaluation directory
        eval_files = os.listdir(eval_storage_dir) if os.path.exists(eval_storage_dir) else []
        logger.info(f"[THINK TANK DEBUG] Files in evaluation_storage: {eval_files}")
        
        # Get statistics from both sources
        evaluator_stats = evaluator.get_evaluation_stats()
        logger.info(f"[THINK TANK DEBUG] Evaluator stats: {evaluator_stats['total_evaluations']} evaluations")
        
        insights_stats = model_insights_manager.get_think_tank_evaluations()
        logger.info(f"[THINK TANK DEBUG] Insights stats: {insights_stats.get('total_evaluations', 0)} evaluations")
        
        # If we have no evaluations, but files exist in the directory, try to load them manually
        if evaluator_stats['total_evaluations'] == 0 and len(eval_files) > 0:
            logger.info(f"[THINK TANK DEBUG] No evaluations in evaluator, but files exist. Attempting to load...")
            try:
                # Pick the latest file
                latest_file = sorted(eval_files)[-1] if eval_files else None
                if latest_file:
                    with open(os.path.join(eval_storage_dir, latest_file), 'r') as f:
                        loaded_data = json.load(f)
                        logger.info(f"[THINK TANK DEBUG] Loaded {len(loaded_data)} evaluations from {latest_file}")
                        
                        # Add this data to the stats
                        evaluator_stats['manual_loaded_evaluations'] = len(loaded_data)
                        evaluator_stats['recent_evaluations'] = list(loaded_data.values())[:5]
                        evaluator_stats['total_evaluations'] = len(loaded_data)
            except Exception as load_err:
                logger.error(f"[THINK TANK DEBUG] Error loading evaluation file: {load_err}")
        
        # Merge the statistics, preferring insights manager data when available
        stats = {
            **evaluator_stats,
            **insights_stats,
            'think_tank_enabled': True,
            'timestamp': datetime.now().isoformat(),
            'data_sources': ['model_evaluator', 'model_insights_manager'],
            'evaluation_storage_path': eval_storage_dir,
            'evaluation_files': eval_files
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting think tank insights: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'think_tank_enabled': True,
            'timestamp': datetime.now().isoformat(),
            'total_evaluations': 0
        }), 500


# API endpoint to get available AI models
@app.route('/api/ai_models', methods=['GET'])
def get_ai_models():
    """Returns a list of all available AI models and their capabilities."""
    try:
        from multi_model_processor import get_model_processors
        processors = get_model_processors()
        
        available_models = []
        for name, processor in processors.items():
            if processor is not None:
                available_models.append({
                    "name": name,
                    "available": True,
                    "preferred_for": get_model_specializations(name)
                })
        
        # Also add direct model info
        if direct_huggingface_available and direct_huggingface_model is not None:
            available_models.append({
                "name": "direct_huggingface",
                "model_type": str(type(direct_huggingface_model).__name__),
                "available": True,
                "preferred_for": ["general", "text_generation"]
            })
            
        return jsonify({
            "success": True,
            "models": available_models,
            "count": len(available_models)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def get_model_specializations(model_name):
    """Returns the query types a model is specialized for."""
    specializations = {
        "huggingface": ["general", "text_generation", "question_answering"],
        "gpt4all": ["conversation", "chat", "reasoning"],
        "autogpt": ["complex_tasks", "planning", "code_generation"],
        "openai": ["conversation", "summarization", "creative_writing"],
        "claude": ["explanation", "analysis", "long_context"],
        "wolfram-alpha": ["math", "computation", "factual_queries"],
        "code-llama": ["code", "programming", "development"],
        "mistral-7b": ["finance", "business", "analysis"],
        "gpt-4": ["complex_reasoning", "expert_knowledge", "creative_tasks"],
        "llama-2-7b": ["general", "balanced_performance"]
    }
    return specializations.get(model_name, ["general"])

# Setup Flask-SocketIO with correct parameters
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    logger=True,
    async_mode='eventlet',
    engineio_logger=True
)

# Initialize Minerva
minerva = MinervaAI()
active_conversations = {}

# Initialize knowledge manager
knowledge_manager = KnowledgeManager()

# Ensure framework manager and HuggingFace integration are loaded
try:
    from integrations.framework_manager import framework_manager
    huggingface_loaded = framework_manager.ensure_huggingface_loaded()
    if huggingface_loaded:
        print("[FRAMEWORK] Successfully initialized HuggingFace in framework manager")
    else:
        print("[FRAMEWORK] Failed to initialize HuggingFace in framework manager")
except Exception as e:
    print(f"[FRAMEWORK] Error initializing framework manager: {str(e)}")

# Initialize plugin manager
plugin_manager = PluginManager()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Register error handlers
register_error_handlers(app)

# ===========================
# Direct AI Model Loading
# ===========================
print("\n[AI DEBUG] =================================================")
print("[AI DEBUG] Checking AI model availability directly...")
print("[AI DEBUG] =================================================\n")

# Initialize system capabilities detection
try:
    from system_capabilities import get_capabilities
    system_capabilities = get_capabilities()
    print(f"\n{system_capabilities}\n")
    
    # Get recommended settings based on the system
    ai_settings = system_capabilities.get_recommendations()
    print("[SYSTEM] Using recommended AI settings:")
    for key, value in ai_settings.items():
        print(f"[SYSTEM]   {key}: {value}")
    
    # Setup model according to capabilities
    huggingface_model_name = ai_settings["model"]
    use_8bit_quantization = ai_settings["use_8bit"]
    use_half_precision = ai_settings["use_half_precision"]
    device = ai_settings["device"]
    
except ImportError:
    print("[WARNING] Could not import system_capabilities module")
    huggingface_model_name = "distilgpt2"
    use_8bit_quantization = False
    use_half_precision = False
    device = "cpu"

# Initialize global AI model variables and availability flags
global direct_huggingface_model, direct_huggingface_tokenizer, direct_huggingface_available
direct_huggingface_model = None
direct_huggingface_tokenizer = None
direct_huggingface_available = False

# Attempt to load the appropriate AI model based on system capabilities
try:
    import torch
    import logging
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    print(f"[AI MODEL] Attempting to load {huggingface_model_name}")
    print("[INFO] Loading Hugging Face model...")
    
    # Initialize message tracking
    global processed_messages
    processed_messages = {}
    
    try:
        # Use our improved model loader that handles different model architectures
        from integrations.huggingface_integration import HuggingFaceIntegration
        
        # Create an instance of the integration class
        huggingface_integration = HuggingFaceIntegration()
        
        print(f"[INFO] Loading model using enhanced HuggingFace loader: {huggingface_model_name}")
        # Call our new improved model loader function
        direct_huggingface_model, direct_huggingface_tokenizer = huggingface_integration.load_huggingface_model(huggingface_model_name)
        
        if direct_huggingface_model is not None and direct_huggingface_tokenizer is not None:
            direct_huggingface_available = True
            print(f"[AI MODEL] Successfully loaded model: {huggingface_model_name}")
            print("[INFO] Hugging Face model successfully loaded!")
            logging.info("Hugging Face model successfully loaded!")
        else:
            raise Exception(f"Failed to load model {huggingface_model_name} - returned None")
        
    except Exception as e:
        print(f"[AI MODEL] Error loading model {huggingface_model_name}: {e}")
        logging.error(f"[ERROR] Failed to load Hugging Face model: {e}")
        print(f"[ERROR] Failed to load Hugging Face model: {e}")
        
        # Try to fall back to a simpler model
        if huggingface_model_name != "distilgpt2":
            print("[AI MODEL] Falling back to distilgpt2 model...")
            print("[INFO] Attempting to load fallback model: distilgpt2")
            try:
                # Use our improved model loader for the fallback model too
                from integrations.huggingface_integration import HuggingFaceIntegration
                huggingface_integration = HuggingFaceIntegration()
                
                huggingface_model_name = "distilgpt2"
                print(f"[INFO] Loading fallback model using enhanced loader: {huggingface_model_name}")
                
                # Use the improved loader
                direct_huggingface_model, direct_huggingface_tokenizer = huggingface_integration.load_huggingface_model(huggingface_model_name)
                
                if direct_huggingface_model is not None and direct_huggingface_tokenizer is not None:
                    direct_huggingface_available = True
                    print("[AI MODEL] Successfully loaded fallback model: distilgpt2")
                else:
                    raise Exception("Failed to load fallback model - returned None")
                    
            except Exception as e2:
                print(f"[AI MODEL] Error loading fallback model: {e2}")
                direct_huggingface_available = False
        else:
            direct_huggingface_available = False
    
except ImportError as e:
    print(f"[AI MODEL] Could not import required dependencies: {e}")
    print("[AI MODEL] AI model functionality will not be available")
    direct_huggingface_available = False
    
except Exception as e:
    print(f"[AI MODEL] Unexpected error: {e}")
    direct_huggingface_available = False

# Make sure the server runs even without AI models
print(f"\n[AI DEBUG] AI Model Direct Check Summary:")
print(f"[AI DEBUG] - Hugging Face: {direct_huggingface_available}")

if not direct_huggingface_available:
    print("\n[WARNING] Running in template-only mode. AI model responses will not be available.")
    print("[INFO] The system will fall back to template responses for all queries.")

# Load AI integrations
def load_integrations_from_config():
    """Load AI integrations from the configuration file."""
    from integrations.framework_manager import FrameworkManager
    
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config/integrations.json")
    if not os.path.exists(config_path):
        print(f"Integration configuration not found: {config_path}")
        return
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        manager = FrameworkManager()
        
        # Load configured integrations
        for integration_type, settings in config.get("integrations", {}).items():
            if settings.get("enabled", False):
                for path in settings.get("paths", []):
                    if os.path.exists(path):
                        manager.register_framework(integration_type, path)
        
        print(f"Loaded {len(manager.loaded_frameworks)} AI integrations")
    except Exception as e:
        print(f"Error loading integrations: {str(e)}")

def init_app(flask_app=None, socketio_instance=None):
    # Load AI integrations
    load_integrations_from_config()
    
    # Initialize global variables
    global app, socketio, direct_huggingface_model, direct_huggingface_tokenizer, direct_huggingface_available
    
    # Set the Flask and SocketIO instances
    if flask_app:
        app = flask_app
    if socketio_instance:
        socketio = socketio_instance
    
    # Initialize Hugging Face model
    initialize_huggingface_model()
    
    # Preload framework processors
    try:
        from multi_model_processor import get_model_processors
        processors = get_model_processors()
        available_models = [name for name, proc in processors.items() if proc is not None]
        if available_models:
            print(f"[STARTUP] Successfully loaded additional AI models: {', '.join(available_models)}")
            
            # Initialize our enhanced AI router
            try:
                # Always initialize multi_ai_coordinator to enable think tank mode
                coordinator = get_multi_ai_coordinator()
                if coordinator is None:
                    print("[ERROR] Failed to get MultiAICoordinator instance")
                else:
                    print("[STARTUP] Loaded MultiAICoordinator instance")
                
                # Initialize the AI router with our enhanced model selection
                if initialize_ai_router():
                    print("[STARTUP] Enhanced AI routing has been successfully initialized")
                else:
                    print("[WARNING] Failed to initialize enhanced AI routing")
            except Exception as router_error:
                print(f"[ERROR] Error initializing enhanced AI router: {router_error}")
        else:
            # Even when no additional models are available, we still need to initialize the coordinator
            # This ensures think tank mode can still be enabled, even if it will use the default model
            try:
                # Use the get function instead of redeclaring global
                coordinator = get_multi_ai_coordinator()
                if coordinator is None:
                    print("[ERROR] Failed to get MultiAICoordinator instance")
                else:
                    print("[STARTUP] Loaded MultiAICoordinator instance (fallback)")
                
                if initialize_ai_router():
                    print("[STARTUP] Basic AI routing initialized for think tank fallback")
            except Exception as fallback_error:
                print(f"[ERROR] Failed to initialize think tank fallback: {fallback_error}")
            
            print("[STARTUP] No additional AI models were loaded beyond HuggingFace")
    except ImportError as e:
        print(f"[STARTUP] Multi-model processor not available: {str(e)}")
    
    # Initialize Minerva system here if needed
    
    return app, socketio

@app.route('/')
def index():
    """Render the main dashboard page."""
    # Check if user is in session, if not create a user ID
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    # Get or create a conversation for this user
    user_id = session['user_id']
    if user_id not in active_conversations:
        result = minerva.start_conversation(user_id=user_id)
        active_conversations[user_id] = result['conversation_id']
    
    # Get frameworks for display
    frameworks = minerva.framework_manager.get_all_frameworks()
    framework_names = list(frameworks.keys()) if frameworks else []
    
    return render_template('index.html', 
                           user_id=user_id,
                           conversation_id=active_conversations[user_id],
                           frameworks=framework_names)

@app.route('/chat')
def chat():
    """Render the chat interface."""
    # Ensure user has an ID and conversation
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    if user_id not in active_conversations:
        result = minerva.start_conversation(user_id=user_id)
        active_conversations[user_id] = result['conversation_id']
    
    return render_template('chat.html', 
                           user_id=user_id,
                           conversation_id=active_conversations[user_id])

@app.route('/chat-test')
def chat_test():
    """Render the REST API-based chat test page."""
    return render_template('chat_test.html')

@app.route('/hybrid-chat-test')
def hybrid_chat_test():
    """Test page that offers both WebSocket and REST API chat options."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Minerva Hybrid Chat Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            margin-top: 0;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 400px;
        }
        .tabs {
            display: flex;
            margin-bottom: 10px;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            background-color: #e0e0e0;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
        }
        .tab.active {
            background-color: #4CAF50;
            color: white;
        }
        #chat-box {
            flex-grow: 1;
            border: 1px solid #ddd;
            padding: 10px;
            overflow-y: auto;
            background-color: #f9f9f9;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .message {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 5px;
            max-width: 70%;
            word-wrap: break-word;
        }
        .user {
            background-color: #DCF8C6;
            margin-left: auto;
            text-align: right;
        }
        .bot {
            background-color: #EAEAEA;
        }
        .controls {
            display: flex;
        }
        #message-input {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-right: 10px;
        }
        button {
            padding: 10px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .status {
            margin-top: 10px;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 5px;
            display: none;
        }
        .tech-details {
            margin-top: 20px;
            border-top: 1px solid #ddd;
            padding-top: 20px;
            font-size: 14px;
        }
        .tech-details h3 {
            margin-top: 0;
        }
        pre {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .setting {
            margin-bottom: 10px;
        }
        .setting label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Minerva Hybrid Chat Test</h1>
        
        <div class="setting">
            <label for="api-mode">Communication Mode:</label>
            <select id="api-mode">
                <option value="websocket">WebSocket (Real-time)</option>
                <option value="rest">REST API (HTTP)</option>
            </select>
        </div>
        
        <div class="chat-container">
            <div id="chat-box"></div>
            <div class="controls">
                <input type="text" id="message-input" placeholder="Type your message...">
                <button id="send-button">Send</button>
            </div>
        </div>
        
        <div id="status" class="status"></div>
        
        <div class="tech-details">
            <h3>Connection Details</h3>
            <div id="connection-status">Not connected</div>
            <div id="conversation-id">No active conversation</div>
            
            <h3>Debug Info</h3>
            <pre id="debug-log"></pre>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.1/socket.io.min.js"></script>
    <script>
        // DOM Elements
        const chatBox = document.getElementById('chat-box');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const statusDiv = document.getElementById('status');
        const apiModeSelect = document.getElementById('api-mode');
        const connectionStatus = document.getElementById('connection-status');
        const conversationIdDiv = document.getElementById('conversation-id');
        const debugLog = document.getElementById('debug-log');
        
        // State
        let socket = null;
        let conversationId = '';
        let isConnected = false;
        
        // Initialize
        function initialize() {
            if (apiModeSelect.value === 'websocket') {
                setupWebSocket();
            } else {
                disconnectWebSocket();
                connectionStatus.textContent = 'Using REST API (no persistent connection)';
            }
        }
        
        // Setup WebSocket
        function setupWebSocket() {
            if (socket) {
                return; // Already connected
            }
            
            addDebugMessage('Setting up WebSocket connection...');
            
            socket = io();
            
            socket.on('connect', () => {
                isConnected = true;
                connectionStatus.textContent = `Connected via WebSocket (ID: ${socket.id})`;
                addDebugMessage('WebSocket connected!');
                
                statusDiv.style.display = 'block';
                statusDiv.textContent = 'Connected to Minerva WebSocket Server';
                statusDiv.style.backgroundColor = '#d4edda';
                
                // Send a test message to verify connection
                socket.emit('test_message', { message: 'Test connection' });
            });
            
            socket.on('disconnect', () => {
                isConnected = false;
                connectionStatus.textContent = 'WebSocket disconnected';
                addDebugMessage('WebSocket disconnected');
                
                statusDiv.style.display = 'block';
                statusDiv.textContent = 'Disconnected from Minerva. Trying to reconnect...';
                statusDiv.style.backgroundColor = '#f8d7da';
            });
            
            socket.on('message_received', (data) => {
                addDebugMessage('Received message: ' + JSON.stringify(data));
                
                conversationId = data.conversation_id || conversationId;
                updateConversationId();
                
                addMessage(data.response, false);
            });
            
            socket.on('error', (data) => {
                addDebugMessage('Error: ' + JSON.stringify(data));
                
                statusDiv.style.display = 'block';
                statusDiv.textContent = 'Error: ' + (data.error || 'Unknown error');
                statusDiv.style.backgroundColor = '#f8d7da';
            });
            
            socket.on('test_response', (data) => {
                addDebugMessage('Test response: ' + JSON.stringify(data));
            });
        }
        
        // Disconnect WebSocket
        function disconnectWebSocket() {
            if (socket) {
                socket.disconnect();
                socket = null;
                isConnected = false;
                addDebugMessage('WebSocket manually disconnected');
            }
        }
        
        // Update conversation ID display
        function updateConversationId() {
            conversationIdDiv.textContent = conversationId 
                ? `Active conversation: ${conversationId}` 
                : 'No active conversation';
        }
        
        // Add debug message
        function addDebugMessage(message) {
            const timestamp = new Date().toISOString();
            debugLog.textContent = `[${timestamp}] ${message}\\n` + debugLog.textContent;
        }
        
        // Add a message to the chat box
        function addMessage(message, isUser) {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${isUser ? 'user' : 'bot'}`;
            messageElement.textContent = message;
            chatBox.appendChild(messageElement);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        // Send message via WebSocket
        function sendMessageWebSocket(message) {
            if (!socket || !isConnected) {
                addDebugMessage('WebSocket not connected, reconnecting...');
                setupWebSocket();
                setTimeout(() => sendMessageWebSocket(message), 1000);
                return;
            }
            
            addDebugMessage(`Sending via WebSocket: ${message}`);
            
            socket.emit('chat_message', {
                message: message,
                conversation_id: conversationId
            });
        }
        
        // Send message via REST API
        async function sendMessageREST(message) {
            addDebugMessage(`Sending via REST API: ${message}`);
            
            try {
                const response = await fetch('/api/chat/message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        conversation_id: conversationId
                    })
                });
                
                const data = await response.json();
                addDebugMessage('REST API response: ' + JSON.stringify(data));
                
                if (data.status === 'success') {
                    conversationId = data.conversation_id;
                    updateConversationId();
                    addMessage(data.response, false);
                } else {
                    statusDiv.style.display = 'block';
                    statusDiv.textContent = 'Error: ' + (data.message || 'Unknown error');
                    statusDiv.style.backgroundColor = '#f8d7da';
                }
            } catch (error) {
                addDebugMessage('REST API error: ' + error.message);
                statusDiv.style.display = 'block';
                statusDiv.textContent = 'Error: ' + error.message;
                statusDiv.style.backgroundColor = '#f8d7da';
            }
        }
        
        // Send a message using the selected method
        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            messageInput.value = '';
            
            if (apiModeSelect.value === 'websocket') {
                sendMessageWebSocket(message);
            } else {
                sendMessageREST(message);
            }
        }
        
        // Event Listeners
        sendButton.addEventListener('click', sendMessage);
        
        messageInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
        
        apiModeSelect.addEventListener('change', initialize);
        
        // Initialize the page
        initialize();
    </script>
</body>
</html>
    """

@app.route('/simple-chat')
def simple_chat():
    """Super simplified chat page for testing both WebSocket and REST API."""
    return render_template('simple_chat.html')

@app.route('/memories')
def memories():
    """Render the memories visualization page."""
    # Get all memories for display
    all_memories = minerva.search_memories(max_results=100)
    
    return render_template('memories.html', 
                           memories=all_memories.get('memories', []))

@app.route('/knowledge')
def knowledge():
    """Render the knowledge management page."""
    # Get list of documents
    documents = knowledge_manager.list_documents()
    return render_template('knowledge.html', documents=documents)

@app.route('/settings')
def settings():
    """Render the settings page."""
    return render_template('settings.html')


@app.route('/insights')
def model_insights():
    """Render the model insights dashboard."""
    # Get dashboard data from the insights manager
    dashboard_data = model_insights_manager.get_dashboard_data()
    return render_template('model_insights.html', **dashboard_data)


@app.route('/think-tank-insights')
def think_tank_insights():
    """Render the think tank insights dashboard."""
    # This will display the model comparisons and evaluations from the think tank approach
    return render_template('model_insights.html', 
                          page_title="Think Tank Insights",
                          dashboard_title="Minerva Think Tank Performance Dashboard")

# A/B testing dashboard removed - now admin-only functionality

@app.route('/plugins')
def plugins():
    """Render the plugin management page."""
    # Get all plugins and their metadata
    plugins_info = plugin_manager.get_plugin_metadata()
    
    # Discovery info - count of available vs loaded plugins
    discovered_plugins = len(plugin_manager.plugin_classes)
    loaded_plugins = len(plugin_manager.plugins)
    
    return render_template('plugins.html', 
                          plugins=plugins_info, 
                          discovered=discovered_plugins,
                          loaded=loaded_plugins)

# API Routes
@app.route('/api/chat/send', methods=['POST'])
@handle_api_error
def send_message():
    """API endpoint to send a message to Minerva."""
    data = request.json
    user_message = data.get('message', '')
    conversation_id = data.get('conversation_id', '')
    
    if not user_message or not conversation_id:
        raise InvalidRequestError("Missing required parameters")
    
    # Add user message to conversation
    minerva.add_message(
        conversation_id=conversation_id,
        role="user",
        content=user_message
    )
    
    # Process the message with Minerva (in a separate thread to not block)
    def process_and_respond():
        # Get the best framework for general chat
        framework_manager = minerva.framework_manager
        best_framework = framework_manager.get_best_framework_for_capability("text_generation")
        
        # If no framework is available, use a simple response
        if not best_framework:
            response = "I'm sorry, I don't have any AI frameworks available to process your request."
        else:
            try:
                # Try to execute with the best framework
                result = framework_manager.execute_with_framework(
                    best_framework, 
                    "execute_task", 
                    user_message
                )
                response = result.get('result', "I processed your request but couldn't generate a good response.")
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                response = f"I encountered an error while processing your request: {str(e)}"
        
        # Add assistant message to conversation
        minerva.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response
        )
        
        # Emit the response via Socket.IO
        socketio.emit('message_response', {
            'response': response,
            'conversation_id': conversation_id
        }, room=request.sid)
    
    # Start processing in a background thread
    threading.Thread(target=process_and_respond).start()
    
    return jsonify({'status': 'success', 'message': 'Processing your request'})

@app.route('/api/memories/add', methods=['POST'])
@handle_api_error
def add_memory():
    """API endpoint to add a memory."""
    data = request.json
    content = data.get('content', '')
    category = data.get('category', 'general')
    importance = int(data.get('importance', 5))
    tags = data.get('tags', [])
    
    if not content:
        raise InvalidRequestError("Missing required parameters")
    
    # Add memory
    result = minerva.add_memory(
        content=content,
        category=category,
        importance=importance,
        tags=tags
    )
    
    return jsonify(result)

@app.route('/api/memories/search', methods=['GET'])
@handle_api_error
def search_memories():
    """API endpoint to search memories."""
    query = request.args.get('query', '')
    category = request.args.get('category', '')
    tags = request.args.getlist('tag')
    max_results = int(request.args.get('max_results', 10))
    
    # Search memories
    result = minerva.search_memories(
        query=query if query else None,
        category=category if category else None,
        tags=tags if tags else None,
        max_results=max_results
    )
    
    return jsonify(result)

@app.route('/api/frameworks', methods=['GET'])
@handle_api_error
def get_frameworks():
    """API endpoint to get available frameworks."""
    framework_manager = minerva.framework_manager
    frameworks = framework_manager.get_all_frameworks()
    
    # Format the response
    result = {
        'status': 'success',
        'frameworks': []
    }
    
    for name, info in frameworks.items():
        if hasattr(info, 'to_dict'):
            framework_info = info.to_dict()
        elif isinstance(info, dict):
            framework_info = info
        else:
            # Handle the case where info is a BaseIntegration instance
            framework_info = {
                'name': name,
                'capabilities': getattr(info, 'capabilities', []),
                'version': getattr(info, 'version', 'unknown'),
                'description': getattr(info, 'description', '')
            }
        
        result['frameworks'].append(framework_info)
    
    return jsonify(result)

@app.route('/api/knowledge/search', methods=['POST'])
@handle_api_error
def knowledge_search():
    """API endpoint for searching knowledge."""
    data = request.json
    query = data.get('query', '')
    top_k = int(data.get('top_k', 5))
    filters = data.get('filters', None)
    
    # Search knowledge
    results = knowledge_manager.retrieve_knowledge(query, top_k, filters)
    
    return jsonify({"results": results})

@app.route('/api/knowledge/upload', methods=['POST'])
@handle_api_error
def knowledge_upload():
    """API endpoint for uploading documents."""
    if 'document' not in request.files:
        raise InvalidRequestError("No document provided")
    
    file = request.files['document']
    if file.filename == '':
        raise InvalidRequestError("No file selected")
    
    # Get metadata
    metadata = {}
    if 'metadata' in request.form:
        try:
            metadata = json.loads(request.form['metadata'])
        except json.JSONDecodeError:
            pass
    
    # Save file temporarily
    temp_dir = Path(app.instance_path) / "uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / file.filename
    file.save(temp_path)
    
    try:
        # Add document to knowledge system
        document_id = knowledge_manager.add_document(temp_path, metadata, move_to_storage=True)
        
        # Delete temporary file
        if temp_path.exists():
            temp_path.unlink()
        
        return jsonify({
            "success": True,
            "document_id": document_id,
            "message": f"Document '{file.filename}' uploaded successfully"
        })
    
    except Exception as e:
        # Delete temporary file
        if temp_path.exists():
            temp_path.unlink()
        
        raise MinervaError(f"Failed to upload document: {str(e)}")

@app.route('/api/knowledge/documents', methods=['GET'])
@handle_api_error
def knowledge_documents():
    """API endpoint for listing documents."""
    documents = knowledge_manager.list_documents()
    return jsonify({"documents": documents})

@app.route('/api/knowledge/documents/<document_id>', methods=['DELETE'])
@handle_api_error
def knowledge_delete_document(document_id):
    """API endpoint for deleting a document."""
    success = knowledge_manager.delete_document(document_id)
    if success:
        return jsonify({
            "success": True,
            "message": f"Document '{document_id}' deleted successfully"
        })
    else:
        raise MinervaError(f"Failed to delete document '{document_id}'")

@app.route('/api/knowledge/documents/<document_id>/metadata', methods=['PUT'])
@handle_api_error
def knowledge_update_metadata(document_id):
    """API endpoint for updating document metadata."""
    data = request.json
    metadata = data.get('metadata', {})
    
    success = knowledge_manager.update_document_metadata(document_id, metadata)
    if success:
        return jsonify({
            "success": True,
            "message": f"Metadata for document '{document_id}' updated successfully"
        })
    else:
        raise MinervaError(f"Failed to update metadata for document '{document_id}'")

@app.route('/api/search_knowledge', methods=['POST'])
@handle_api_error
def search_knowledge_api():
    """API endpoint for searching knowledge."""
    data = request.get_json()
    
    if not data or 'query' not in data:
        raise InvalidRequestError("Missing required parameter: query")
    
    query = data.get('query')
    top_k = data.get('top_k', 5)
    filters = data.get('filters', None)
    
    try:
        results = knowledge_manager.retrieve_knowledge(query, top_k, filters)
        return jsonify({"results": results})
    except Exception as e:
        log_error(e, {'query': query, 'top_k': top_k, 'filters': filters})
        raise MinervaError(f"Failed to search knowledge: {str(e)}")

@app.route('/api/upload_document', methods=['POST'])
@handle_api_error
def upload_document_api():
    """API endpoint for uploading documents."""
    if 'file' not in request.files:
        raise InvalidRequestError("No file part in the request")
    
    file = request.files['file']
    if file.filename == '':
        raise InvalidRequestError("No file selected")
    
    if file:
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract metadata from form
            metadata = {
                'title': request.form.get('title', filename),
                'author': request.form.get('author', ''),
                'category': request.form.get('category', ''),
                'tags': request.form.get('tags', '').split(',') if request.form.get('tags') else [],
                'description': request.form.get('description', ''),
                'upload_date': datetime.now().isoformat()
            }
            
            # Process document
            document_id = knowledge_manager.add_document(filepath, metadata)
            
            return jsonify({
                "success": True,
                "document_id": document_id,
                "message": f"Document '{filename}' uploaded and processed successfully"
            })
        
        except Exception as e:
            log_error(e, {'filename': file.filename})
            raise MinervaError(f"Failed to process document: {str(e)}")

@app.route('/api/list_documents')
@handle_api_error
def list_documents_api():
    """API endpoint for listing documents."""
    try:
        # Parse filter parameters from query string
        filters = {}
        for key in request.args:
            if key != 'page' and key != 'per_page':
                filters[key] = request.args.get(key)
        
        documents = knowledge_manager.list_documents(filters)
        
        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        start = (page - 1) * per_page
        end = start + per_page
        paginated_documents = documents[start:end]
        
        return jsonify({
            "documents": paginated_documents,
            "total": len(documents),
            "page": page,
            "per_page": per_page,
            "total_pages": (len(documents) + per_page - 1) // per_page
        })
    except Exception as e:
        log_error(e, {'filters': request.args})
        raise MinervaError(f"Failed to list documents: {str(e)}")

@app.route('/api/delete_document', methods=['POST'])
@handle_api_error
def delete_document_api():
    """API endpoint for deleting documents."""
    data = request.get_json()
    
    if not data or 'document_id' not in data:
        raise InvalidRequestError("Missing required parameter: document_id")
    
    document_id = data.get('document_id')
    
    try:
        success = knowledge_manager.delete_document(document_id)
        if not success:
            raise DocumentNotFoundError(document_id)
        
        return jsonify({
            "success": True,
            "message": f"Document '{document_id}' deleted successfully"
        })
    except DocumentNotFoundError as e:
        raise e
    except Exception as e:
        log_error(e, {'document_id': document_id})
        raise MinervaError(f"Failed to delete document: {str(e)}")

@app.route('/api/update_document_metadata', methods=['POST'])
@handle_api_error
def update_document_metadata_api():
    """API endpoint for updating document metadata."""
    data = request.get_json()
    
    if not data or 'document_id' not in data or 'metadata' not in data:
        raise InvalidRequestError(
            "Missing required parameters: document_id and metadata"
        )
    
    document_id = data.get('document_id')
    metadata = data.get('metadata')
    
    try:
        success = knowledge_manager.update_document_metadata(document_id, metadata)
        if not success:
            raise DocumentNotFoundError(document_id)
        
        return jsonify({
            "success": True,
            "message": f"Metadata for document '{document_id}' updated successfully"
        })
    except DocumentNotFoundError as e:
        raise e
    except Exception as e:
        log_error(e, {'document_id': document_id, 'metadata': metadata})
        raise MinervaError(f"Failed to update document metadata: {str(e)}")

@app.route('/api/plugins', methods=['GET'])
@handle_api_error
def list_plugins_api():
    """API endpoint for listing plugins."""
    plugins_info = plugin_manager.get_plugin_metadata()
    return jsonify({
        "success": True,
        "plugins": plugins_info
    })

@app.route('/api/plugins/<plugin_id>/enable', methods=['POST'])
@handle_api_error
def enable_plugin_api(plugin_id):
    """API endpoint for enabling a plugin."""
    result = plugin_manager.enable_plugin(plugin_id)
    if result:
        return jsonify({
            "success": True,
            "message": f"Plugin {plugin_id} enabled successfully"
        })
    else:
        raise MinervaError(f"Failed to enable plugin {plugin_id}")

@app.route('/api/plugins/<plugin_id>/disable', methods=['POST'])
@handle_api_error
def disable_plugin_api(plugin_id):
    """API endpoint for disabling a plugin."""
    result = plugin_manager.disable_plugin(plugin_id)
    if result:
        return jsonify({
            "success": True,
            "message": f"Plugin {plugin_id} disabled successfully"
        })
    else:
        raise MinervaError(f"Failed to disable plugin {plugin_id}")

@app.route('/api/plugins/<plugin_id>/configure', methods=['POST'])
@handle_api_error
def configure_plugin_api(plugin_id):
    """API endpoint for configuring a plugin."""
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise MinervaError(f"Plugin {plugin_id} not found", status_code=404)
    
    try:
        config_data = request.get_json()
        if not config_data:
            raise InvalidRequestError("No configuration data provided")
        
        # Check if plugin supports configuration
        if hasattr(plugin, 'configure'):
            result = plugin.configure(config_data)
            return jsonify({
                "success": result,
                "message": "Plugin configuration updated" if result else "Failed to update configuration"
            })
        else:
            raise MinervaError(f"Plugin {plugin_id} does not support configuration")
    except Exception as e:
        log_error(e, {"plugin_id": plugin_id})
        raise MinervaError(f"Error configuring plugin: {str(e)}")

@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """REST API endpoint for chat messages."""
    try:
        start_time = time.time()
        
        # Extract data from request
        data = request.json
        if not data:
            raise InvalidRequestError("No JSON data provided")
        
        message = data.get('message')
        if not message or not isinstance(message, str) or message.strip() == '':
            raise InvalidRequestError("Message is required and must be a non-empty string")
        
        session_id = data.get('session_id', str(uuid.uuid4()))
        user_id = data.get('user_id', session_id)  # Use session_id as user_id if not provided
        
        # Generate a message ID if not provided
        message_id = data.get('message_id', str(uuid.uuid4()))
        
        # Get the mode from the request (default to standard mode)
        mode = data.get('mode', 'standard')
        logger.info(f"[API DEBUG] Received chat message request with mode: {mode}, user_id: {user_id}")
        logger.info(f"[API DEBUG] Request data: {json.dumps({k: v for k, v in data.items() if k != 'api_key'}, indent=2)}")
        
        # Prevent duplicate processing
        if session_id in processed_messages and message_id in processed_messages[session_id]:
            logger.warning(f"Duplicate message {message_id} for session {session_id}, ignoring")
            return jsonify({
                'status': 'duplicate',
                'message': 'This message has already been processed'
            })
        
        # Add to processed messages
        if session_id not in processed_messages:
            processed_messages[session_id] = set()
        processed_messages[session_id].add(message_id)
        
        # Check for user preference commands
        preference_change = None
        preference_type = "retrieval"
        
        if message.lower() in ["concise mode", "/concise", "be concise"]:
            user_preference_manager.set_retrieval_depth(user_id, "concise")
            preference_change = "concise"
        elif message.lower() in ["standard mode", "/standard", "be standard"]:
            user_preference_manager.set_retrieval_depth(user_id, "standard")
            preference_change = "standard"
        elif message.lower() in ["deep dive mode", "/deep", "be detailed", "deep dive"]:
            user_preference_manager.set_retrieval_depth(user_id, "deep_dive")
            preference_change = "deep_dive"
        # Response tone commands
        elif message.lower() in ["/formal", "formal tone", "be formal"]:
            user_preference_manager.set_response_tone(user_id, "formal")
            preference_change = "formal"
            preference_type = "tone"
        elif message.lower() in ["/casual", "casual tone", "be casual"]:
            user_preference_manager.set_response_tone(user_id, "casual")
            preference_change = "casual"
            preference_type = "tone"
        elif message.lower() in ["/neutral", "neutral tone", "be neutral"]:
            user_preference_manager.set_response_tone(user_id, "neutral")
            preference_change = "neutral"
            preference_type = "tone"
        # Response structure commands
        elif message.lower() in ["/paragraph", "use paragraphs", "paragraph format"]:
            user_preference_manager.set_response_structure(user_id, "paragraph")
            preference_change = "paragraphs"
            preference_type = "structure"
        elif message.lower() in ["/bullets", "bullet points", "use bullet points"]:
            user_preference_manager.set_response_structure(user_id, "bullet_points")
            preference_change = "bullet points"
            preference_type = "structure"
        elif message.lower() in ["/numbered", "numbered list", "use numbered list"]:
            user_preference_manager.set_response_structure(user_id, "numbered_list")
            preference_change = "numbered list"
            preference_type = "structure"
        elif message.lower() in ["/summary", "just summarize", "use summary"]:
            user_preference_manager.set_response_structure(user_id, "summary")
            preference_change = "summary"
            preference_type = "structure"
        
        if preference_change:
            # Return immediate feedback about preference change
            feedback_message = ""
            if preference_type == "retrieval":
                feedback_message = f"I've switched to {preference_change.replace('_', ' ')} mode. I'll adjust my knowledge retrieval accordingly."
            elif preference_type == "tone":
                feedback_message = f"I'll now use a {preference_change} tone in my responses."
            elif preference_type == "structure":
                feedback_message = f"I'll now structure my responses as {preference_change}."
            
            return jsonify({
                'status': 'success',
                'session_id': session_id,
                'message_id': message_id,
                'response': feedback_message,
                'source': 'preferences',
                'processing_time': time.time() - start_time
            })
        
        # Process the message
        if mode == 'think_tank':
            logger.info(f"[API DEBUG] Processing message in think tank mode")
            # Get the multi_ai_coordinator, attempting recovery if needed
            coordinator = get_multi_ai_coordinator()
            logger.info(f"[API DEBUG] Coordinator retrieved: {coordinator is not None}")
            
            # Log coordinator details for debugging
            if coordinator:
                logger.info(f"[API DEBUG] Coordinator has {len(coordinator.model_processors) if hasattr(coordinator, 'model_processors') else 'unknown'} model processors")
                if hasattr(coordinator, 'model_processors'):
                    logger.info(f"[API DEBUG] Available models: {list(coordinator.model_processors.keys())}")
            else:
                logger.error(f"[API ERROR] Failed to get MultiAICoordinator instance!")
            
            if coordinator:
                try:
                    logger.info(f"[THINK TANK] MultiAICoordinator instance found, processing message with mode='think_tank'")
                    user_preferences = user_preference_manager.get_user_preferences(user_id)
                    
                    # Add debugging info to preferences
                    if not user_preferences:
                        user_preferences = {}
                    user_preferences['debug_mode'] = True
                    user_preferences['log_evaluations'] = True
                    
                    # Check if coordinator is fully initialized for think tank mode
                    if not hasattr(coordinator, 'model_processors') or len(coordinator.model_processors) == 0:
                        logger.error("[THINK TANK ERROR] Coordinator not fully initialized for think tank mode - missing model processors")
                        return jsonify({
                            'status': 'success',  # Don't expose error to user
                            'session_id': session_id,
                            'message_id': message_id,
                            'response': "Think tank mode is initializing. Please try again in a moment.",
                            'processing_time': time.time() - start_time
                        })
                    
                    response_data = asyncio.run(coordinator.process_message(
                        user_id=user_id,
                        message=message,
                        message_id=message_id,
                        user_preferences=user_preferences,
                        mode='think_tank'
                    ))
                    
                    response = response_data.get('response', 'No response generated in think tank mode')
                    logger.info(f"[API DEBUG] Think tank response generated successfully")
                    
                    # Log model evaluation information
                    if 'evaluations' in response_data:
                        logger.info(f"[THINK TANK] Evaluations recorded: {response_data['evaluations']}")
                    
                    # Return additional metadata in the response
                    return jsonify({
                        'status': 'success',
                        'session_id': session_id,
                        'message_id': message_id,
                        'response': response,
                        'processing_time': time.time() - start_time,
                        'mode': 'think_tank',
                        'models_used': response_data.get('models_used', []),
                        'evaluations_saved': response_data.get('evaluations_saved', False)
                    })
                except Exception as e:
                    logger.error(f"[API DEBUG] Error in think tank mode: {str(e)}", exc_info=True)
                    response = f"Error in think tank processing: {str(e)}"
            else:
                # Final attempt to initialize coordinator
                logger.error(f"[API DEBUG] Multi AI Coordinator not initialized, attempting emergency initialization")
                try:
                    from multi_ai_coordinator import MultiAICoordinator, multi_ai_coordinator as global_coordinator
                    global multi_ai_coordinator
                    multi_ai_coordinator = global_coordinator
                    
                    # Try to initialize the router
                    if initialize_ai_router():
                        logger.info("[RECOVERY] Emergency initialization of MultiAICoordinator successful")
                        # Recursive call to try again with the newly initialized coordinator
                        return chat_message()
                    else:
                        logger.error("[RECOVERY] Failed to initialize AI router during emergency recovery")
                except Exception as recovery_error:
                    logger.error(f"[CRITICAL] Failed during emergency coordinator initialization: {recovery_error}")
                
                response = "Think tank mode not available - coordinator not initialized"
        else:
            # Use the MultiAICoordinator for standard mode as well, if available
            coordinator = get_multi_ai_coordinator()
            if coordinator and hasattr(coordinator, 'model_processors') and len(coordinator.model_processors) > 0:
                logger.info(f"[STANDARD MODE] Using MultiAICoordinator for improved response quality")
                try:
                    user_preferences = user_preference_manager.get_user_preferences(user_id) or {}
                    response_data = asyncio.run(coordinator.process_message(
                        user_id=user_id,
                        message=message,
                        message_id=message_id,
                        user_preferences=user_preferences,
                        mode='standard'
                    ))
                    response = response_data.get('response', '')
                    if not response or len(response.strip()) < 10:
                        raise ValueError("Empty or very short response from coordinator")
                except Exception as coord_err:
                    logger.error(f"[ERROR] Failed to use coordinator in standard mode: {coord_err}")
                    # Fall back to the default processing methods
                    if huggingface_model_name and direct_huggingface_model and direct_huggingface_tokenizer:
                        response = process_gpt_response(message, user_id)
                    else:
                        response = process_huggingface_only(message)
            elif huggingface_model_name and direct_huggingface_model and direct_huggingface_tokenizer:
                response = process_gpt_response(message, user_id)
            else:
                response = process_huggingface_only(message)
        
        # Prepare the response
        result = {
            'status': 'success',
            'session_id': session_id,
            'message_id': message_id,
            'response': response,
            'processing_time': time.time() - start_time
        }
        
        logger.info(f"API chat response sent in {time.time() - start_time:.2f}s")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        error = MinervaError(
            "Error processing chat message", 
            details={"exception": str(e)}
        )
        return jsonify(error.to_dict()), error.status_code

@app.route('/api/test')
def test_route():
    """Simple test endpoint to verify the API is working."""
    return jsonify({
        'status': 'success',
        'message': 'Minerva API is working correctly',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/chat/send', methods=['POST'])
def api_send_chat_message():
    """API endpoint to manually send a chat message for testing."""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
            
        # Create test conversation if needed
        conversation_id = data.get('conversation_id', '')
        if not conversation_id:
            # Create a new conversation
            result = minerva.start_conversation()
            conversation_id = result.get('conversation_id')
            
        # Add message to conversation
        minerva.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message
        )
        
        # Generate response
        response = minerva.generate_response(conversation_id)
        
        return jsonify({
            'status': 'success',
            'conversation_id': conversation_id,
            'message': message,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in api_send_chat_message: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"Error processing request: {str(e)}"
        }), 500

@app.route('/send_chat_message', methods=['GET', 'POST'])
def send_chat_message():
    """Endpoint to manually send a chat message for testing."""
    # Get the message, user ID, and preferences
    message = None
    user_id = None
    retrieval_depth = None
    
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        user_id = request.form.get('user_id', '').strip() or str(uuid.uuid4())
        retrieval_depth = request.form.get('retrieval_depth')
        
        if retrieval_depth:
            user_preference_manager.set_retrieval_depth(user_id, retrieval_depth)
    
    # For GET requests or when no message is provided
    if not message:
        # Provide a form to enter the message
        return render_template(
            'chat_test_simple.html', 
            title="Test Chat Message", 
            content="""
            <form method="post" action="/send_chat_message">
                <div class="mb-3">
                    <label for="user_id" class="form-label">User ID (leave empty for auto-generated):</label>
                    <input type="text" class="form-control" id="user_id" name="user_id">
                </div>
                <div class="mb-3">
                    <label for="message" class="form-label">Enter your message:</label>
                    <textarea class="form-control" id="message" name="message" rows="3" required></textarea>
                </div>
                <div class="mb-3">
                    <label for="retrieval_depth" class="form-label">Retrieval Depth:</label>
                    <select class="form-select" id="retrieval_depth" name="retrieval_depth">
                        <option value="">Default (Standard)</option>
                        <option value="concise">Concise</option>
                        <option value="standard">Standard</option>
                        <option value="deep_dive">Deep Dive</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">Send Message</button>
            </form>
            """
        )
    
    # Process the message
    try:
        # Get user preferences for display
        preferences = user_preference_manager.get_user_preferences(user_id)
        retrieval_params = user_preference_manager.get_retrieval_params(user_id)
        
        # Process the message with AI model
        response = process_gpt_response(message, user_id)
        
        # Create a response to display
        result = f"""
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                Message Processed Successfully
            </div>
            <div class="card-body">
                <h5 class="card-title">User ID: {user_id}</h5>
                <div class="mb-3">
                    <strong>User Message:</strong>
                    <div class="p-2 bg-light">{message}</div>
                </div>
                <div class="mb-3">
                    <strong>User Preferences:</strong>
                    <pre class="p-2 bg-light">{json.dumps(preferences, indent=2)}</pre>
                    <strong>Retrieval Parameters:</strong>
                    <pre class="p-2 bg-light">{json.dumps(retrieval_params, indent=2)}</pre>
                </div>
                <div class="mb-3">
                    <strong>AI Response:</strong>
                    <div class="p-2 bg-light">{response}</div>
                </div>
            </div>
            <div class="card-footer">
                <a href="/send_chat_message" class="btn btn-primary">Send Another Message</a>
            </div>
        </div>
        """
        
        return render_template('chat_test_simple.html', title="Message Result", content=result)
    
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        
        # Display the error
        error_result = f"""
        <div class="card mb-4">
            <div class="card-header bg-danger text-white">
                Error Processing Message
            </div>
            <div class="card-body">
                <h5 class="card-title">Error: {str(e)}</h5>
                <div class="mb-3">
                    <strong>Message:</strong>
                    <div class="p-2 bg-light">{message}</div>
                </div>
                <div class="mb-3">
                    <strong>Traceback:</strong>
                    <pre class="p-2 bg-light">{error_traceback}</pre>
                </div>
            </div>
            <div class="card-footer">
                <a href="/send_chat_message" class="btn btn-primary">Try Again</a>
            </div>
        </div>
        """
        
        return render_template('chat_test_simple.html', title="Message Error", content=error_result)

# Global A/B Testing state
abtest_enabled = False
abtest_results = {
    "total_queries": 0,
    "model_a": {
        "uses": 0,
        "success": 0,
        "failure": 0,
        "avg_response_time": 0
    },
    "model_b": {
        "uses": 0,
        "success": 0,
        "failure": 0,
        "avg_response_time": 0
    }
}

# API Routes for A/B Testing

@app.route('/admin/abtest/toggle', methods=['POST'])
def admin_toggle_abtest_api():
    """
    API endpoint to enable or disable A/B testing experiments.
    
    Requires json body: {"enabled": true/false}
    Returns: {"status": "success", "enabled": true/false}
    """
    try:
        global abtest_enabled
        data = request.get_json()
        if 'enabled' not in data or not isinstance(data['enabled'], bool):
            return jsonify({"status": "error", "message": "Missing or invalid 'enabled' parameter"}), 400
        
        # Toggle experiment mode
        abtest_enabled = data['enabled']
        logger.info(f"A/B testing toggled to: {'enabled' if abtest_enabled else 'disabled'}")
        
        return jsonify({
            "status": "success", 
            "enabled": abtest_enabled,
            "message": f"A/B testing has been {'enabled' if abtest_enabled else 'disabled'}"
        })
    except Exception as e:
        logger.error(f"Error toggling A/B testing: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Preserve the old endpoint for backward compatibility
@app.route('/api/abtest/toggle', methods=['POST'])
def toggle_abtest_api():
    """Redirect to the main implementation"""
    return admin_toggle_abtest_api()

@app.route('/admin/abtest/results', methods=['GET'])
def admin_get_abtest_results_api():
    """
    API endpoint to retrieve A/B testing experiment results.
    
    Query params:
    - experiment_id (optional): Filter by specific experiment ID
    - user_id (optional): Filter by user ID
    - query_tags (optional): Comma-separated list of query tags to filter by
    - limit (optional): Maximum number of results to return (default: 50)
    
    Returns: {"status": "success", "results": [...], "statistics": {...}}
    """
    try:
        global abtest_results, abtest_enabled
        
        # Return simplified results from our global variable
        return jsonify({
            "status": "success",
            "enabled": abtest_enabled,
            "results": abtest_results
        })
    except Exception as e:
        logger.error(f"Error getting A/B test results: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
# Preserve the old endpoint for backward compatibility
@app.route('/api/abtest/results', methods=['GET'])
def get_abtest_results_api():
    """Redirect to the main implementation"""
    return admin_get_abtest_results_api()

@app.route('/api/abtest/feedback', methods=['POST'])
def record_abtest_feedback_api():
    """
    API endpoint to record user feedback for an A/B testing experiment.
    
    Requires json body: {
        "experiment_id": "uuid",
        "user_selected_winner": "model_name",
        "quality_rating": float,  # Optional, 0-10 scale
        "comment": "string"  # Optional
    }
    
    Returns: {"status": "success"}
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'experiment_id' not in data:
            return jsonify({"status": "error", "message": "Missing experiment_id"}), 400
            
        if 'user_selected_winner' not in data:
            return jsonify({"status": "error", "message": "Missing user_selected_winner"}), 400
            
        # Access the MultiAICoordinator instance
        coordinator = get_multi_ai_coordinator()
        if not coordinator:
            return jsonify({"status": "error", "message": "Multi-AI Coordinator not available"}), 500
            
        # Record the feedback
        success = coordinator.record_experiment_feedback(
            experiment_id=data['experiment_id'],
            user_feedback={
                "user_selected_winner": data['user_selected_winner'],
                "quality_rating": data.get('quality_rating'),
                "comment": data.get('comment'),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if success:
            return jsonify({"status": "success", "message": "Feedback recorded successfully"})
        else:
            return jsonify({"status": "error", "message": "Failed to record feedback"}), 400
    except Exception as e:
        logger.error(f"Error recording A/B test feedback: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API Routes for User Preferences
@app.route("/api/user/preferences", methods=["GET"])
def get_user_preferences_api():
    """API endpoint to get the current user preferences."""
    try:
        # Get the user ID from the session or request
        user_id = session.get("user_id") or request.args.get("user_id")
        
        if not user_id:
            return jsonify({
                "error": "User ID is required",
                "code": "missing_user_id"
            }), 400
        
        # Get user preferences
        preferences = user_preference_manager.get_user_preferences(user_id)
        
        return jsonify({
            "success": True,
            "preferences": preferences
        })
    
    except Exception as e:
        return handle_api_error(e, "Error retrieving user preferences")


@app.route("/api/user/preferences/retrieval_depth", methods=["POST"])
def set_retrieval_depth_api():
    """API endpoint to set the retrieval depth preference."""
    try:
        # Get the user ID and preference from the request
        user_id = session.get("user_id") or request.json.get("user_id")
        retrieval_depth = request.json.get("retrieval_depth")
        
        if not user_id:
            return jsonify({
                "error": "User ID is required",
                "code": "missing_user_id"
            }), 400
        
        if not retrieval_depth:
            return jsonify({
                "error": "Retrieval depth is required",
                "code": "missing_retrieval_depth"
            }), 400
        
        # Validate retrieval depth
        if retrieval_depth not in ["concise", "standard", "deep_dive"]:
            return jsonify({
                "error": f"Invalid retrieval depth: {retrieval_depth}. Must be one of: concise, standard, deep_dive",
                "code": "invalid_retrieval_depth"
            }), 400
        
        # Set the preference
        success = user_preference_manager.set_retrieval_depth(user_id, retrieval_depth)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Retrieval depth set to {retrieval_depth}",
                "preferences": user_preference_manager.get_user_preferences(user_id)
            })
        else:
            return jsonify({
                "error": "Failed to set retrieval depth",
                "code": "preference_update_failed"
            }), 500
    
    except Exception as e:
        return handle_api_error(e, "Error setting retrieval depth")


@app.route("/api/user/preferences/response_tone", methods=["POST"])
def set_response_tone_api():
    """API endpoint to set the response tone preference."""
    try:
        # Get the user ID and preference from the request
        user_id = session.get("user_id") or request.json.get("user_id")
        response_tone = request.json.get("response_tone")
        
        if not user_id:
            return jsonify({
                "error": "User ID is required",
                "code": "missing_user_id"
            }), 400
        
        if not response_tone:
            return jsonify({
                "error": "Response tone is required",
                "code": "missing_response_tone"
            }), 400
        
        # Validate response tone
        if response_tone not in ["formal", "casual", "neutral"]:
            return jsonify({
                "error": f"Invalid response tone: {response_tone}. Must be one of: formal, casual, neutral",
                "code": "invalid_response_tone"
            }), 400
        
        # Set the preference
        success = user_preference_manager.set_response_tone(user_id, response_tone)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Response tone set to {response_tone}",
                "preferences": user_preference_manager.get_user_preferences(user_id)
            })
        else:
            return jsonify({
                "error": "Failed to set response tone",
                "code": "preference_update_failed"
            }), 500
    
    except Exception as e:
        return handle_api_error(e, "Error setting response tone")


@app.route("/api/user/preferences/response_structure", methods=["POST"])
def set_response_structure_api():
    """API endpoint to set the response structure preference."""
    try:
        # Get the user ID and preference from the request
        user_id = session.get("user_id") or request.json.get("user_id")
        response_structure = request.json.get("response_structure")
        
        if not user_id:
            return jsonify({
                "error": "User ID is required",
                "code": "missing_user_id"
            }), 400
        
        if not response_structure:
            return jsonify({
                "error": "Response structure is required",
                "code": "missing_response_structure"
            }), 400
        
        # Validate response structure
        if response_structure not in ["paragraph", "bullet_points", "numbered_list", "summary"]:
            return jsonify({
                "error": f"Invalid response structure: {response_structure}. Must be one of: paragraph, bullet_points, numbered_list, summary",
                "code": "invalid_response_structure"
            }), 400
        
        # Set the preference
        success = user_preference_manager.set_response_structure(user_id, response_structure)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Response structure set to {response_structure}",
                "preferences": user_preference_manager.get_user_preferences(user_id)
            })
        else:
            return jsonify({
                "error": "Failed to set response structure",
                "code": "preference_update_failed"
            }), 500
    
    except Exception as e:
        return handle_api_error(e, "Error setting response structure")


@app.route("/api/user/preferences/response_length", methods=["POST"])
def set_response_length_api():
    """API endpoint to set the response length preference."""
    try:
        # Get the user ID and preference from the request
        user_id = session.get("user_id") or request.json.get("user_id")
        response_length = request.json.get("response_length")
        
        if not user_id:
            return jsonify({
                "error": "User ID is required",
                "code": "missing_user_id"
            }), 400
        
        if not response_length:
            return jsonify({
                "error": "Response length is required",
                "code": "missing_response_length"
            }), 400
        
        # Validate response length
        if response_length not in ["short", "medium", "long"]:
            return jsonify({
                "error": f"Invalid response length: {response_length}. Must be one of: short, medium, long",
                "code": "invalid_response_length"
            }), 400
        
        # Set the preference
        success = user_preference_manager.set_response_length(user_id, response_length)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Response length set to {response_length}",
                "preferences": user_preference_manager.get_user_preferences(user_id)
            })
        else:
            return jsonify({
                "error": "Failed to set response length",
                "code": "preference_update_failed"
            }), 500
    
    except Exception as e:
        return handle_api_error(e, "Error setting response length")


@app.route("/api/user/feedback", methods=["POST"])
def record_feedback_api():
    """API endpoint to record user feedback for a response."""
    try:
        # Get the user ID and feedback details from the request
        user_id = session.get("user_id") or request.json.get("user_id")
        message_id = request.json.get("message_id")
        feedback_type = request.json.get("feedback_type", "general")
        
        # Convert feedback_type to is_positive flag
        if feedback_type == "positive":
            is_positive = True
            feedback_type = "general"
        elif feedback_type == "negative":
            is_positive = False
            feedback_type = "general"
        else:
            # For backward compatibility
            is_positive = request.json.get("is_positive", True)
        
        if not user_id:
            return jsonify({
                "error": "User ID is required",
                "code": "missing_user_id"
            }), 400
        
        if not message_id:
            return jsonify({
                "error": "Message ID is required",
                "code": "missing_message_id"
            }), 400
        
        # Validate feedback type
        valid_feedback_types = ["general", "tone", "structure", "length"]
        if feedback_type not in valid_feedback_types:
            return jsonify({
                "error": f"Invalid feedback type: {feedback_type}. Must be one of: {', '.join(valid_feedback_types)}",
                "code": "invalid_feedback_type"
            }), 400
        
        # Get additional metadata
        model_used = request.json.get("model_used")
        query = request.json.get("query")
        response = request.json.get("response")
        complexity = request.json.get("complexity")
        tags = request.json.get("tags", [])
        
        # Estimate query complexity if not provided and query is available
        if not complexity and query:
            try:
                from ai_decision.scoring import estimate_query_complexity
                complexity = estimate_query_complexity(query)
                print(f"[FEEDBACK] Estimated query complexity: {complexity:.2f}/10.0")
            except Exception as e:
                print(f"[WARNING] Failed to estimate query complexity: {str(e)}")
                complexity = None
        
        # Record the feedback using the global feedback manager with enhanced context
        if hasattr(global_feedback_manager, 'record_enhanced_feedback') and query and response:
            # Use enhanced feedback recording if available and we have all context
            success = global_feedback_manager.record_enhanced_feedback(
                user_id=user_id, 
                message_id=message_id, 
                is_positive=is_positive, 
                feedback_type=feedback_type, 
                model_used=model_used,
                query=query,
                response=response,
                complexity=complexity,
                tags=tags
            )
        else:
            # Fall back to basic feedback recording
            success = global_feedback_manager.record_feedback(user_id, message_id, is_positive, feedback_type, model_used)
            
        # Record feedback in insights manager as well
        try:
            model_insights_manager.record_feedback(message_id, is_positive)
        except Exception as e:
            print(f"[WARNING] Failed to record feedback for insights: {str(e)}")
        
        if success:
            # Get updated preferences
            preferences = global_feedback_manager.get_user_preferences(user_id)
            
            # Check if any adjustments were made due to the feedback
            feedback_data = preferences.get("feedback", {})
            last_adjustments = feedback_data.get("last_adjustments", [])
            preference_updated = len(last_adjustments) > 0 and not last_adjustments[-1].get("is_positive", True) if last_adjustments else False
            
            return jsonify({
                "success": True,
                "message": "Feedback recorded successfully",
                "preference_updated": preference_updated,
                "preferences": preferences
            })
        else:
            return jsonify({
                "error": "Failed to record feedback",
                "code": "feedback_recording_failed"
            }), 500
    
    except Exception as e:
        return handle_api_error(e, "Error recording feedback")


@app.route("/api/user/preferences/update", methods=["POST"])
def update_multiple_preferences_api():
    """API endpoint to update multiple user preferences at once."""
    try:
        # Get the user ID and preferences from the request
        user_id = session.get("user_id") or request.json.get("user_id")
        preferences = request.json.get("preferences", {})
        
        if not user_id:
            return jsonify({
                "error": "User ID is required",
                "code": "missing_user_id"
            }), 400
        
        if not preferences:
            return jsonify({
                "error": "No preferences provided",
                "code": "missing_preferences"
            }), 400
        
        # Update each preference if provided
        success = True
        updated_preferences = []
        
        # Update retrieval depth if provided
        if "retrieval_depth" in preferences:
            retrieval_depth = preferences["retrieval_depth"]
            if retrieval_depth in ["concise", "standard", "deep_dive"]:
                if user_preference_manager.set_retrieval_depth(user_id, retrieval_depth):
                    updated_preferences.append("retrieval_depth")
                else:
                    success = False
        
        # Update response tone if provided
        if "response_tone" in preferences:
            response_tone = preferences["response_tone"]
            if response_tone in ["formal", "casual", "neutral"]:
                if user_preference_manager.set_response_tone(user_id, response_tone):
                    updated_preferences.append("response_tone")
                else:
                    success = False
        
        # Update response structure if provided
        if "response_structure" in preferences:
            response_structure = preferences["response_structure"]
            if response_structure in ["paragraph", "bullet_points", "numbered_list", "summary"]:
                if user_preference_manager.set_response_structure(user_id, response_structure):
                    updated_preferences.append("response_structure")
                else:
                    success = False
        
        if success and updated_preferences:
            return jsonify({
                "success": True,
                "message": f"Updated preferences: {', '.join(updated_preferences)}",
                "preferences": user_preference_manager.get_user_preferences(user_id)
            })
        elif not updated_preferences:
            return jsonify({
                "error": "No valid preferences to update",
                "code": "no_valid_preferences"
            }), 400
        else:
            return jsonify({
                "error": "Failed to update some preferences",
                "code": "preference_update_failed",
                "updated": updated_preferences
            }), 500
    
    except Exception as e:
        return handle_api_error(e, "Error updating user preferences")

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle a new client connection."""
    try:
        sid = request.sid if hasattr(request, 'sid') else 'unknown'
        print(f"[WEBSOCKET] Client connected: {sid}")
        
        # Send an immediate response on connection
        socketio.emit('response', {
            'status': 'connected', 
            'message': 'Connected to Minerva WebSocket Server',
            'server_time': datetime.now().isoformat()
        }, room=sid)
        
        print(f"[WEBSOCKET] Sent connection confirmation to {sid}")
    except Exception as e:
        print(f"[ERROR] Error in connect handler: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle a client disconnection."""
    try:
        sid = request.sid if hasattr(request, 'sid') else 'unknown'
        print(f"[WEBSOCKET] Client disconnected: {sid}")
    except Exception as e:
        print(f"[ERROR] Error in disconnect handler: {str(e)}")

@socketio.on('message')
def handle_message(message):
    """Handle a generic message from a client."""
    # Store sid before threading - ensure we have it even if request context changes
    sid = request.sid if hasattr(request, 'sid') else 'unknown'
    print(f"[SOCKETIO] Received message from {sid}: {message}")
    
    # Check for empty message
    if not message:
        print("[ERROR] Empty message received!")
        socketio.emit('error', {'message': 'Empty message received'}, room=sid)
        return {"status": "error", "message": "Empty message"}
    
    # Prevent duplicate message processing
    # Track message processing to avoid duplicate responses
    client_key = f"{sid}:{message}"
    if hasattr(handle_message, "processing_messages") and client_key in handle_message.processing_messages:
        print(f"[WARNING] Prevented duplicate WebSocket processing for message: {message}")
        return {"status": "already_processing"}
    
    # Initialize processing tracking set if it doesn't exist
    if not hasattr(handle_message, "processing_messages"):
        handle_message.processing_messages = set()
    
    # Add this message to the processing set
    handle_message.processing_messages.add(client_key)
    print(f"[SOCKETIO] Started tracking message: {client_key}")
    
    @copy_current_request_context
    def process_and_respond(sid, message):
        print(f"[SOCKETIO] Processing message: {message}")
        ai_response = "Minerva is thinking..."  # Default response
        
        try:
            # Send initial thinking response
            socketio.emit('response', {"message": ai_response}, room=sid)
            print(f"[SOCKETIO] Sent 'thinking' message to {sid}")
            
            # Process the message with GPT
            print(f"[GPT] Sending message to process_gpt_response")
            ai_response = process_gpt_response(message)
            
            if not ai_response:
                ai_response = "No AI models were able to generate a response."
                print("[GPT] No response generated from AI models")
                
        except Exception as e:
            print(f"[ERROR] AI processing failed: {str(e)}")
            import traceback
            traceback.print_exc()
            ai_response = f"Error processing message: {str(e)}"
        
        # Send the final response
        response_data = {
            'message': ai_response,
            'user_message': message,
            'timestamp': datetime.now().isoformat()
        }
        print(f"[SOCKETIO] Sending response to {sid}: {ai_response[:100]}...")
        try:
            # Use a small delay to ensure the response is sent after the thinking message
            eventlet.sleep(0.5)
            socketio.emit('response', response_data, room=sid)
            print(f"[SOCKETIO] Response sent successfully to {sid}")
        except Exception as e:
            print(f"[ERROR] Failed to send response to {sid}: {str(e)}")
        finally:
            # Remove the message from processing set when done
            handle_message.processing_messages.remove(client_key)
            print(f"[SOCKETIO] Finished processing message: {client_key}")
    
    # Start processing in a thread
    thread = threading.Thread(target=process_and_respond, args=(sid, message))
    thread.daemon = True
    thread.start()
    print(f"[SOCKETIO] Started processing thread for {sid}")
    
    return {"status": "processing"}

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle a chat message from a client."""
    start_time = time.time()
    
    # Ensure processed_messages is available globally
    global processed_messages
    if 'processed_messages' not in globals():
        processed_messages = {}
    
    try:
        # Get message content
        message = data.get('message', '').strip()
        session_id = data.get('session_id', request.sid)
        user_id = data.get('user_id', session_id)  # Use session_id as user_id if not provided
        
        if not message:
            emit('error', {
                'code': 'empty_message',
                'message': 'Message cannot be empty'
            })
            return
        
        # Track message to prevent duplicate processing
        message_id = data.get('message_id', str(uuid.uuid4()))
        
        if session_id in processed_messages and message_id in processed_messages[session_id]:
            logger.warning(f"Duplicate message {message_id} for session {session_id}, ignoring")
            return
        
        # Add to processed messages
        if session_id not in processed_messages:
            processed_messages[session_id] = set()
        processed_messages[session_id].add(message_id)
        
        # Check for user preference commands
        preference_change = None
        preference_type = "retrieval"
        
        if message.lower() in ["concise mode", "/concise", "be concise"]:
            user_preference_manager.set_retrieval_depth(user_id, "concise")
            preference_change = "concise"
        elif message.lower() in ["standard mode", "/standard", "be standard"]:
            user_preference_manager.set_retrieval_depth(user_id, "standard")
            preference_change = "standard"
        elif message.lower() in ["deep dive mode", "/deep", "be detailed", "deep dive"]:
            user_preference_manager.set_retrieval_depth(user_id, "deep_dive")
            preference_change = "deep_dive"
        # Response tone commands
        elif message.lower() in ["/formal", "formal tone", "be formal"]:
            user_preference_manager.set_response_tone(user_id, "formal")
            preference_change = "formal"
            preference_type = "tone"
        elif message.lower() in ["/casual", "casual tone", "be casual"]:
            user_preference_manager.set_response_tone(user_id, "casual")
            preference_change = "casual"
            preference_type = "tone"
        elif message.lower() in ["/neutral", "neutral tone", "be neutral"]:
            user_preference_manager.set_response_tone(user_id, "neutral")
            preference_change = "neutral"
            preference_type = "tone"
        # Response structure commands
        elif message.lower() in ["/paragraph", "use paragraphs", "paragraph format"]:
            user_preference_manager.set_response_structure(user_id, "paragraph")
            preference_change = "paragraphs"
            preference_type = "structure"
        elif message.lower() in ["/bullets", "bullet points", "use bullet points"]:
            user_preference_manager.set_response_structure(user_id, "bullet_points")
            preference_change = "bullet points"
            preference_type = "structure"
        elif message.lower() in ["/numbered", "numbered list", "use numbered list"]:
            user_preference_manager.set_response_structure(user_id, "numbered_list")
            preference_change = "numbered list"
            preference_type = "structure"
        elif message.lower() in ["/summary", "just summarize", "use summary"]:
            user_preference_manager.set_response_structure(user_id, "summary")
            preference_change = "summary"
            preference_type = "structure"
        
        if preference_change:
            # Return immediate feedback about preference change
            feedback_message = ""
            if preference_type == "retrieval":
                feedback_message = f"I've switched to {preference_change.replace('_', ' ')} mode. I'll adjust my knowledge retrieval accordingly."
            elif preference_type == "tone":
                feedback_message = f"I'll now use a {preference_change} tone in my responses."
            elif preference_type == "structure":
                feedback_message = f"I'll now structure my responses as {preference_change}."
            
            emit('response', {
                'session_id': session_id,
                'message_id': message_id,
                'response': feedback_message,
                'source': 'preferences',
                'time': time.time() - start_time
            })
            return
        
        # Get current user preferences for knowledge retrieval if user_id is provided
        user_preferences = None
        if user_id:
            try:
                user_preferences = user_preference_manager.get_retrieval_params(user_id)
                logger.info(f"Using retrieval parameters for user {user_id}: {user_preferences}")
            except Exception as e:
                logger.warning(f"Failed to get user preferences: {str(e)}")
        
        # Retrieve relevant knowledge if knowledge manager is available
        context = ""
        if 'knowledge_manager' in globals() and knowledge_manager and message:
            try:
                # Use the search part of the message to retrieve knowledge
                query = message
                
                # Perform knowledge retrieval with user preferences
                results = knowledge_manager.retrieve_knowledge(
                    query=query, 
                    top_k=user_preferences.get('top_k', 5) if user_preferences else 5,
                    user_id=user_id,
                    user_preferences=user_preferences
                )
                
                if results:
                    context = "\n\nRelevant information:\n"
                    for i, result in enumerate(results):
                        # Get content and source
                        content = result.get('text', '')
                        source = result.get('metadata', {}).get('source', 'Unknown source')
                        
                        # Limit context size based on user preference
                        max_context_chars = user_preferences.get('context_window', 1000) * 4 if user_preferences else 4000
                        
                        # Add content if there's room
                        if len(context) + len(content) < max_context_chars:
                            context += f"\n[{i+1}] {content}\n(Source: {source})\n"
                        else:
                            context += f"\n[{i+1}] (Additional information available but omitted for brevity)\n"
                            break
            except Exception as e:
                logger.error(f"Error retrieving knowledge: {str(e)}")
                # Continue without context
        
        # Process message in a separate thread to avoid blocking
        @copy_current_request_context
        def process_message_thread():
            try:
                # Process the message
                # Check if framework is available by trying to access it
                framework_available = False
                try:
                    from integrations.framework_manager import framework_manager
                    
                    # Actively try to load the HuggingFace framework
                    framework_manager.ensure_huggingface_loaded()
                    
                    # Now check if it's loaded
                    huggingface = framework_manager.get_framework_by_name("HuggingFace")
                    if huggingface:
                        framework_available = True
                        logger.info("Successfully loaded HuggingFace framework")
                except Exception as e:
                    logger.warning(f"Could not access HuggingFace framework: {str(e)}")
                    framework_available = False

                # Process based on available models
                try:
                    # First try using the direct model since we know it's more reliable
                    if direct_huggingface_available:
                        logger.info("Using direct HuggingFace model for processing")
                        response = process_huggingface_only(message)
                    # Only try the framework as a backup if direct fails
                    elif framework_available:
                        # Framework is available through the manager, use the GPT response processor
                        logger.info("Using framework manager for HuggingFace integration")
                        response = process_gpt_response(message, user_id)
                    else:
                        # No models available
                        logger.error("No AI models available for processing")
                        response = "I'm sorry, but I'm having trouble accessing my AI models right now. Please try again later."
                except Exception as e:
                    # Log any errors during processing
                    error_msg = str(e)
                    logger.error(f"Error processing message: {error_msg}", exc_info=True)
                    
                    # Try direct HuggingFace as a last resort
                    if direct_huggingface_available and ("Framework not loaded" in error_msg or "not defined" in error_msg):
                        try:
                            logger.warning("Trying direct HuggingFace as last resort after error")
                            response = process_huggingface_only(message)
                        except Exception as direct_error:
                            logger.error(f"Direct HuggingFace fallback also failed: {str(direct_error)}")
                            response = "I encountered an error while processing your request. Please try again with a simpler query."                    
                    else:
                        response = f"I encountered an error while processing your request. Please try again later."
                        
                # Final catchall for empty responses
                if not response or not response.strip():
                    response = "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
                
                # Send response
                response_id = str(uuid.uuid4())  # Generate unique ID for response
                emit('response', {
                    'session_id': session_id,
                    'message_id': message_id,
                    'response_id': response_id,  # Add response ID for feedback tracking
                    'response': response,
                    'time': time.time() - start_time
                })
                
                # Log success
                logger.info(f"Sent response to {session_id} in {time.time() - start_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                
                # Try to generate a fallback response
                try:
                    fallback = generate_fallback_response(message)
                    emit('response', {
                        'session_id': session_id,
                        'message_id': message_id,
                        'response': fallback,
                        'error': str(e),
                        'time': time.time() - start_time
                    })
                except Exception as e2:
                    # If even fallback fails, send a simple error
                    emit('error', {
                        'code': 'processing_error',
                        'message': f"Error processing your message: {str(e2)}"
                    })
        
        # Start processing thread
        processing_thread = threading.Thread(target=process_message_thread)
        processing_thread.daemon = True
        processing_thread.start()
        
        # Send immediate acknowledgment
        emit('message_received', {
            'session_id': session_id,
            'message_id': message_id
        })
        
    except Exception as e:
        # Handle any exceptions in the main thread
        logger.error(f"Error handling message: {str(e)}")
        error_handler(e)

@socketio.on('test_message')
def handle_test_message(data):
    """Handle a test message from a client."""
    print(f"[SOCKETIO] Received test message: {data}")
    socketio.emit('test_response', {'message': 'Test response received'}, room=request.sid)

@socketio.on_error()
def error_handler(e):
    """Global error handler for socketio"""
    print(f"[SOCKETIO ERROR] {e}")
    import traceback
    traceback.print_exc()
    
    try:
        # Try to notify the client if possible
        if hasattr(request, 'sid'):
            socketio.emit('error', {'message': f"Server error: {str(e)}"}, room=request.sid)
    except Exception as notify_err:
        print(f"[SOCKETIO] Failed to notify client of error: {notify_err}")

import re
from model_insights_manager import model_insights_manager

def clean_ai_response(response):
    """Wrapper around the imported clean_ai_response function with logging"""
    if not response or not isinstance(response, str):
        return ""
    
    print(f"[AI DEBUG] Cleaning response: {response[:100]}...")
    
    # Use our enhanced response handler module to clean the response
    from response_handler import clean_ai_response as enhanced_clean_response
    cleaned_response = enhanced_clean_response(response)
    
    # Log the change if significant
    if len(cleaned_response) < len(response) * 0.9:  # More than 10% reduction
        print(f"[AI DEBUG] Response significantly cleaned/filtered")
    
    return cleaned_response

def format_prompt(message, model_type="basic"):
    """Format a prompt for different model types.
    
    Args:
        message (str): The user message to format
        model_type (str): The type of model - "zephyr", "mistral", "basic", "code-llama", etc.
        
    Returns:
        str: Properly formatted prompt for the given model type
    """
    message = message.strip()
    
    # Define a comprehensive system prompt
    system_message = """You are Minerva, an advanced AI assistant designed to be helpful, harmless, and honest.
    
As Minerva, your responses should be:
1. ACCURATE - Provide factual information and admit when you don't know something
2. HELPFUL - Give thorough, thoughtful answers that address the user's question
3. BALANCED - Present multiple perspectives on controversial topics
4. ETHICAL - Refuse inappropriate requests for harmful content
5. ENGAGING - Be conversational and friendly, showing personality where appropriate

ALWAYS prioritize user safety and privacy. NEVER share or request personal information.
"""
    
    # Enhanced system prompts for specific model types
    model_specific_prompts = {
        "code-llama": """You are Minerva's code assistant. When answering programming questions:
1. Provide clear, working code examples
2. Explain the code functionality line by line
3. Highlight best practices and potential pitfalls
4. Consider performance, readability, and maintainability
5. Include proper error handling and edge cases
""",
        
        "wolfram-alpha": """You are Minerva's scientific and mathematical reasoning assistant. When answering:
1. Use precise scientific and mathematical terminology
2. Show step-by-step working for all calculations
3. Consider units, dimensions, and precision in your answers
4. Cite relevant formulas or theorems
5. Present results in a clear, structured format
""",
        
        "mistral-7b": """You are Minerva's analysis assistant. When providing analysis:
1. Consider multiple perspectives and interpretations
2. Organize information in a structured, logical manner
3. Identify patterns, relationships, and implications
4. Support claims with evidence and reasoning
5. Acknowledge limitations of your analysis
""",
        
        "gpt-4": """You are Minerva, powered by the most capable AI model. Your responses should be:
1. Comprehensive and nuanced, addressing complex aspects of the question
2. Highly accurate, with precise information and careful reasoning
3. Well-structured with clear organization and logical flow
4. Balanced, representing multiple perspectives fairly
5. Tailored to the specific context and details of the query
"""
    }
    
    # Get the appropriate system prompt based on model type
    enhanced_system = model_specific_prompts.get(model_type, system_message)
    
    # Format based on model architecture
    if model_type in ["zephyr", "mistral-7b"]:
        # Zephyr/Mistral specific format
        return f"<|system|>\n{enhanced_system}</s>\n<|assistant|>\nUser: {message}\nAssistant:"
    elif model_type in ["gpt-4", "claude"]:
        # ChatGPT/Claude format with system message
        return f"System: {enhanced_system}\n\nUser: {message}\n\nAssistant:"
    elif model_type == "code-llama":
        # Code Llama specific format
        return f"<s>[INST] {enhanced_system}\n\n{message} [/INST]\n"
    elif model_type == "basic":
        # Enhanced basic model format with explicit instructions for improved coherence
        return f"The following is a conversation with an AI assistant named Minerva. Minerva is helpful, harmless, and honest. Minerva gives direct, clear and concise answers.\n\nUser: {message}\nAssistant: I'll answer this question directly and clearly."
    else:
        # Default to a robust format for unknown model types
        return f"System: {enhanced_system}\n\nUser: {message}\n\nAssistant:"

def process_gpt_response(message, user_id=None):
    """
    Process a message and return a reliable AI response.
    
    Args:
        message: The user message to process
        user_id: Optional user ID for personalized settings
    
    Returns:
        str: The AI response
    """
    logger.info(f"Processing message with AI model: {huggingface_model_name}")
    
    # Try to get a template response first for common queries
    template_response = get_template_response(message)
    if template_response:
        logger.info("Using template response")
        return template_response
    
    # If no template match, proceed with the AI model
    if not direct_huggingface_model or not direct_huggingface_tokenizer:
        logger.warning("No AI model available, using fallback")
        return generate_fallback_response(message)
    
    # Get the model type (defaulting to huggingface_model_name)
    model_type = huggingface_model_name if huggingface_model_name else "distilgpt2"
    logger.info(f"Using model type: {model_type} for formatting prompt")
    
    # Format the prompt based on the model type
    prompt = format_prompt(message, model_type=model_type)
    
    # Get user preferences for knowledge retrieval if user_id is provided
    user_preferences = None
    if user_id:
        try:
            user_preferences = user_preference_manager.get_retrieval_params(user_id)
            logger.info(f"Using retrieval parameters for user {user_id}: {user_preferences}")
        except Exception as e:
            logger.warning(f"Failed to get user preferences: {str(e)}")
    
    # Retrieve relevant knowledge if knowledge manager is available
    context = ""
    if 'knowledge_manager' in globals() and knowledge_manager and message:
        try:
            # Use the search part of the message to retrieve knowledge
            query = message
            
            # Perform knowledge retrieval with user preferences
            results = knowledge_manager.retrieve_knowledge(
                query=query, 
                top_k=user_preferences.get('top_k', 5) if user_preferences else 5,
                user_id=user_id,
                user_preferences=user_preferences
            )
            
            if results:
                context = "\n\nRelevant information:\n"
                for i, result in enumerate(results):
                    # Get content and source
                    content = result.get('text', '')
                    source = result.get('metadata', {}).get('source', 'Unknown source')
                    
                    # Limit context size based on user preference
                    max_context_chars = user_preferences.get('context_window', 1000) * 4 if user_preferences else 4000
                    
                    # Add content if there's room
                    if len(context) + len(content) < max_context_chars:
                        context += f"\n[{i+1}] {content}\n(Source: {source})\n"
                    else:
                        context += f"\n[{i+1}] (Additional information available but omitted for brevity)\n"
                        break
        except Exception as e:
            logger.error(f"Error retrieving knowledge: {str(e)}")
            # Continue without context
    
    # Combine the prompt with context
    full_prompt = prompt
    if context:
        if model_type in ["zephyr", "mistral"]:
            # Insert context before user message in the prompt
            user_msg_start = full_prompt.find("User:")
            full_prompt = full_prompt[:user_msg_start] + context + full_prompt[user_msg_start:]
        else:
            full_prompt += context
    
    # Determine max tokens based on user preferences
    max_tokens = 150  # Default
    
    # Adjust token length based on user preferences if available
    if user_id:
        try:
            depth = user_preference_manager.get_retrieval_depth(user_id)
            if depth == "concise":
                max_tokens = 100  # Shorter responses
            elif depth == "deep_dive":
                max_tokens = 250  # Longer, more detailed responses
            logger.info(f"Adjusted token length based on user preference: {depth} -> {max_tokens}")
        except Exception as e:
            logger.warning(f"Failed to adjust token length: {str(e)}")
    
    # Get formatting parameters for response styling
    formatting_params = None
    if user_id:
        try:
            formatting_params = user_preference_manager.get_formatting_params(user_id)
            logger.info(f"Using formatting parameters for user {user_id}: {formatting_params}")
        except Exception as e:
            logger.warning(f"Failed to get formatting parameters: {str(e)}")
    
    # Import multi-AI coordinator for enhanced capabilities and feedback syncing
    try:
        import asyncio
        from multi_model_processor import get_model_processors, format_enhanced_prompt
        from multi_ai_coordinator import multi_ai_coordinator as imported_coordinator
        from users.global_feedback_manager import global_feedback_manager
        
        # Set the global reference
        global multi_ai_coordinator
        multi_ai_coordinator = imported_coordinator
        
        # Get available model processors
        model_processors = get_model_processors()
        
        # Check if at least one model is available (including HuggingFace)
        if any(model_processors.values()) or direct_huggingface_available:
            # Create a wrapper for HuggingFace model if available
            huggingface_func = None
            if direct_huggingface_available:
                def huggingface_wrapper(message, **kwargs):
                    try:
                        # Determine which model we're using to format the prompt
                        model_name = str(direct_huggingface_model)
                        is_advanced_model = "zephyr" in model_name.lower() or "mistral" in model_name.lower()
                        model_type = "zephyr" if is_advanced_model else "basic"
                        
                        # Use enhanced prompt formatting
                        formatted_prompt = format_enhanced_prompt(message, model_type=model_type)
                        
                        # Generate response
                        input_ids = direct_huggingface_tokenizer(formatted_prompt, return_tensors="pt").to(direct_huggingface_model.device)
                        
                        # Generate with parameters optimized for model type
                        if is_advanced_model:
                            generation_output = direct_huggingface_model.generate(
                                **input_ids,
                                max_new_tokens=max_tokens,  # Increased for more detailed answers
                                do_sample=True,
                                temperature=0.3,  # Slightly higher for more creative but still controlled
                                top_k=40,
                                top_p=0.9,
                                repetition_penalty=1.3  # Higher to further discourage repetitive text
                            )
                        else:
                            generation_output = direct_huggingface_model.generate(
                                **input_ids,
                                max_new_tokens=max_tokens,  # Slightly longer for more detail
                                do_sample=True,
                                temperature=0.2,  # Lower for consistency
                                top_k=30,
                                top_p=0.85
                            )
                        
                        # Decode the generated tokens to text
                        generated_text = direct_huggingface_tokenizer.decode(generation_output[0], skip_special_tokens=True)
                        
                        # Extract response based on model type
                        if is_advanced_model:
                            if "<|assistant|>" in generated_text:
                                assistant_text = generated_text.split("<|assistant|>")[1]
                                if "</s>" in assistant_text:
                                    assistant_text = assistant_text.split("</s>")[0]
                                response = assistant_text.strip()
                            elif "User:" in generated_text and "Assistant:" in generated_text:
                                response = generated_text.split("Assistant:")[1].strip()
                            else:
                                response = generated_text.replace(formatted_prompt, "").strip()
                        else:
                            if "Assistant:" in generated_text:
                                response = generated_text.split("Assistant:")[1].strip()
                            else:
                                response = generated_text.replace(formatted_prompt, "").strip()
                        
                        # Clean and validate the response
                        return clean_ai_response(response)
                    except Exception as e:
                        print(f"[ERROR] HuggingFace processing error: {str(e)}")
                        return f"Error processing with HuggingFace: {str(e)}"
                
                huggingface_func = huggingface_wrapper
            
            # Run the async function to get the best response from all available models
            try:
                # Register all available models with the coordinator
                if not hasattr(app, 'models_registered'):
                    # Register HuggingFace if available
                    if huggingface_func:
                        multi_ai_coordinator.register_model_processor('huggingface', huggingface_func)
                    
                    # Register other model processors
                    for model_name, processor_func in model_processors.items():
                        if processor_func:
                            multi_ai_coordinator.register_model_processor(model_name, processor_func)
                    
                    # Mark as registered to avoid re-registering
                    app.models_registered = True
                
                # Create an event loop if not exists
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                # Configure feedback manager to update AI Knowledge Repository
                # This ensures that the feedback system learns from each interaction
                try:
                    global_feedback_manager.update_interval = 1.0  # Fast updates for real-time learning
                except Exception as e:
                    print(f"[WARNING] Failed to configure feedback manager: {str(e)}")
                
                # Generate a message ID for tracking
                message_id = str(uuid.uuid4())
                
                # Estimate query complexity for more appropriate model selection
                try:
                    from ai_decision.scoring import estimate_query_complexity
                    query_complexity = estimate_query_complexity(message)
                    print(f"[AI DEBUG] Query complexity: {query_complexity:.2f}/10.0")
                except Exception as e:
                    print(f"[WARNING] Failed to estimate query complexity: {str(e)}")
                    query_complexity = None
                
                # Process with the multi-AI coordinator using enhanced model selection
                # Get user preferences for AI model selection
                user_prefs = None
                if user_id:
                    try:
                        user_prefs = user_preference_manager.get_user_preferences(user_id)
                    except Exception as e:
                        print(f"[WARNING] Failed to get user preferences: {str(e)}")
                
                # Import our enhanced model router from GPT AI Codes if available
                try:
                    # Add Minerva's path to sys.path
                    minerva_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
                    if minerva_path not in sys.path:
                        sys.path.insert(0, minerva_path)
                        
                    # Try to import the model_router
                    import importlib.util
                    # Use the correct folder name with spaces
                    spec = importlib.util.spec_from_file_location(
                        "model_router", 
                        os.path.join(minerva_path, "Gpt ai codes", "model_router.py")
                    )
                    model_router = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(model_router)
                    
                    # Log that we've loaded the model router
                    print(f"[AI DEBUG] Successfully imported enhanced model_router from 'Gpt ai codes'")
                    
                    # Route this request to determine the best model
                    best_model_name = model_router.route_request(message)
                    print(f"[AI DEBUG] Enhanced router suggests model: {best_model_name} for query: {message[:50]}...")
                    
                    # Register the router with the coordinator if not already done
                    model_router.register_with_coordinator()
                    print(f"[AI DEBUG] Enhanced router registered with coordinator")
                except Exception as e:
                    print(f"[WARNING] Could not import or use enhanced model_router: {str(e)}")
                    import traceback
                    traceback.print_exc()
                
                # Process the message with enhanced model selection
                result = loop.run_until_complete(
                    multi_ai_coordinator.process_message(
                        user_id=user_id or "anonymous", 
                        message=message, 
                        message_id=message_id,
                        user_preferences=user_prefs,
                        mode="think_tank"  # Force Think Tank mode for all messages
                    )
                )
                
                response = result["response"]
                best_model = result["model_used"]
                quality_score = result["quality_score"]
                message_id = result["message_id"]
                
                # Get additional information from the enhanced model selection
                complexity = result.get("complexity", 0)
                confidence = result.get("confidence", 0)
                considered_models = result.get("considered_models", [])
                
                print(f"[AI DEBUG] Best response from {best_model} with quality score {quality_score:.2f}")
                print(f"[AI DEBUG] Query complexity: {complexity:.2f}, confidence: {confidence:.2f}")
                print(f"[AI DEBUG] Models considered: {', '.join(considered_models)}")
                
                # Record selection in the insights manager for analytics
                try:
                    # Extract tags from the message using simple keyword detection
                    query_tags = []
                    if any(kw in message.lower() for kw in ["code", "program", "function", "class", "method"]):  
                        query_tags.append("code")
                    if any(kw in message.lower() for kw in ["explain", "how", "why", "what is"]):  
                        query_tags.append("explanation")
                    if any(kw in message.lower() for kw in ["compare", "difference", "versus", "vs"]):  
                        query_tags.append("comparison")
                    if len(message.split()) < 10:  
                        query_tags.append("short_query")
                    
                    # Create decision context data for more detailed insights
                    decision_context = {
                        "repository_guided": repository_guided,
                        "dashboard_guided": getattr(decision, 'dashboard_guided', False) if decision else False,
                        "priority": user_pref_manager.get_preference(user_id, "response_priority") or "balanced",
                        "processing_time": response_time if 'response_time' in locals() else None,
                        "response_formatting": {
                            "tone": user_pref_manager.get_preference(user_id, "response_tone"),
                            "structure": user_pref_manager.get_preference(user_id, "response_structure"),
                            "length": user_pref_manager.get_preference(user_id, "response_length")
                        }
                    }
                    
                    model_insights_manager.record_model_selection(
                        user_id=user_id or "anonymous",
                        message_id=message_id,
                        query=message,
                        selected_model=best_model,
                        considered_models=considered_models,
                        complexity=complexity,
                        quality_score=quality_score,
                        query_tags=query_tags,
                        decision_context=decision_context
                    )
                except Exception as e:
                    print(f"[WARNING] Failed to record model selection for insights: {str(e)}")
                
                # Check for empty or invalid responses
                if not response or response.strip() == "" or len(response) < 10:
                    print("[AI DEBUG] Response failed validation, falling back to template")
                    # Fall back to template or generic response
                    return get_template_response(message) or "I'd like to provide a more specific answer to your question. Could you please provide more details or rephrase your question?"
                
                print(f"[AI DEBUG] Final response: {response[:50]}...")
                
                # Apply response formatting using our enhanced response handler
                try:
                    # Use the imported format_response function 
                    from response_handler import format_response
                    
                    # Get desired formatting parameters
                    format_params = {}
                    if user_id and formatting_params:
                        format_params = formatting_params
                    
                    # Include model name as context to help with formatting
                    format_params['model_name'] = best_model
                    
                    # Format the response
                    formatted_response = format_response(response, format_params)
                    
                    print(f"[AI DEBUG] Applied enhanced formatting to response, original length: {len(response)}, formatted length: {len(formatted_response)}")
                    
                    response = formatted_response
                except Exception as e:
                    print(f"[ERROR] Error formatting response: {str(e)}")
                    # Continue with unformatted response
                
                return response
            except Exception as e:
                print(f"[ERROR] Error in multi-model processing: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Fall back to regular HuggingFace processing
                if direct_huggingface_available:
                    print("[AI DEBUG] Falling back to standard HuggingFace processing")
                    return process_huggingface_only(message)
    except ImportError as e:
        print(f"[WARNING] Multi-model processor not available: {str(e)}")
        # Continue with existing processing if multi-model is not available
        if direct_huggingface_available:
            return process_huggingface_only(message)
    
    # If no AI model is available, use a more comprehensive template fallback system
    if not direct_huggingface_available:
        print("[WARNING] No AI models available, using enhanced template fallback")
        
        # Try to generate a reasonable response based on the message content
        fallback_responses = [
            "I understand you're interested in this topic. Could you ask a more specific question?",
            "That's an interesting question. I'd need more specific details to provide a helpful answer.",
            "I'd like to help with that. Could you elaborate a bit more on what you're looking for?",
            "I'm not able to access my advanced thinking capabilities at the moment. Could we try a different topic?",
            "I'm currently operating in a simplified mode. I can answer basic questions about facts, jokes, or general knowledge."
        ]
        
        # Choose a response based on some simple rules
        if len(message) < 15:
            # Very short query
            return "I need a bit more context to give you a helpful answer. Could you provide more details?"
        elif "?" not in message:
            # Not a question
            return "I'm not sure if you're asking a question. Could you rephrase with a specific question?"
        elif any(keyword in message.lower() for keyword in ["how", "what", "why", "when", "where", "who"]):
            # It's a question but we don't have a template for it
            import random
            return random.choice(fallback_responses)
        else:
            # Default fallback
            return "I understand you're interested in this topic. To provide a more helpful response, could you rephrase your question or provide additional details about what you'd like to know?"
    
    # Default fallback
    return "I understand you're interested in this topic. To provide a more helpful response, could you rephrase your question or provide additional details about what you'd like to know?"

def process_huggingface_only(message):
    """Process a message using only the HuggingFace model (legacy approach)."""
    # Access these global variables
    global direct_huggingface_model, direct_huggingface_tokenizer, direct_huggingface_available
    
    # First, try to use the framework manager approach
    try:
        print("[INFO] Attempting to use framework_manager to get HuggingFace")
        from integrations.framework_manager import get_framework_by_name
        huggingface_framework = get_framework_by_name("HuggingFace")
        if huggingface_framework:
            print("[INFO] Successfully retrieved HuggingFace framework, using it for processing")
            # Use the framework's text generation capability
            try:
                response = huggingface_framework.generate_text(message, max_length=100)
                if response:
                    print("[SUCCESS] Successfully generated response using framework")
                    return response
            except Exception as fw_err:
                print(f"[WARNING] Error using framework for text generation: {str(fw_err)}")
        else:
            print("[WARNING] HuggingFace framework not found, falling back to direct model")
    except Exception as framework_err:
        print(f"[WARNING] Error accessing framework manager: {str(framework_err)}")
        
    # If we're here, we need to use the direct model approach as fallback
    print("[INFO] Falling back to direct HuggingFace model")
    try:
        # First, verify we have the direct model available
        if not direct_huggingface_model or not direct_huggingface_tokenizer or not direct_huggingface_available:
            logger.error("Direct HuggingFace model is not loaded or initialized properly")
            print("[ERROR] HuggingFace model not properly loaded. Attempting to initialize...")
            # Try to force-load the model again
            direct_huggingface_model = None
            direct_huggingface_tokenizer = None
            direct_huggingface_available = False
            
            try:
                print("[RECOVERY] Attempting to re-initialize HuggingFace model directly")
                import torch
                import logging
                from transformers import AutoModelForCausalLM, AutoTokenizer
                
                # Force clean cache to ensure fresh load
                print("[RECOVERY] Cleaning cache...")
                try:
                    import shutil
                    import os
                    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
                    if os.path.exists(cache_dir + "/models--distilgpt2"):
                        print(f"[RECOVERY] Removing cached model: {cache_dir}/models--distilgpt2")
                        shutil.rmtree(cache_dir + "/models--distilgpt2", ignore_errors=True)
                except Exception as cache_err:
                    print(f"[RECOVERY] Warning: Could not clean cache: {cache_err}")
                
                # First load the tokenizer
                print("[RECOVERY] Loading tokenizer...")
                direct_huggingface_tokenizer = AutoTokenizer.from_pretrained("distilgpt2", local_files_only=False)
                
                # Then load the model
                print("[RECOVERY] Loading model...")
                direct_huggingface_model = AutoModelForCausalLM.from_pretrained("distilgpt2", local_files_only=False)
                if torch.cuda.is_available():
                    device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    device = "mps"
                else:
                    device = "cpu"
                direct_huggingface_model = direct_huggingface_model.to(device)
                direct_huggingface_available = True
                print("[INFO] Hugging Face model successfully loaded!")
                print("[RECOVERY] Successfully re-initialized HuggingFace model")
            except Exception as re_init_error:
                print(f"[RECOVERY] Failed to re-initialize HuggingFace model: {str(re_init_error)}")
                return "I'm sorry, but I'm currently experiencing technical difficulties. My AI language model is not properly initialized. Please try again later."
        
        # Determine which model we're using to format the prompt appropriately
        model_name = str(direct_huggingface_model)
        is_advanced_model = "zephyr" in model_name.lower() or "mistral" in model_name.lower()
        print(f"[AI DEBUG] Using direct HuggingFace model: {model_name}")
        print(f"[AI DEBUG] Using advanced model format: {is_advanced_model}")
        
        # Format the prompt based on the model type
        try:
            # Try to use the enhanced formatter if available
            from multi_model_processor import format_enhanced_prompt
            formatted_prompt = format_enhanced_prompt(message, model_type="zephyr" if is_advanced_model else "basic", context={"is_greeting": any(word in message.lower() for word in ["hello", "hi", "hey", "greetings"])})
            print(f"[AI DEBUG] Using enhanced prompt formatter")
        except ImportError as e:
            # Fall back to basic formatting
            print(f"[AI DEBUG] Enhanced formatter not available: {str(e)}, falling back to basic formatting")
            formatted_prompt = format_prompt(message, model_type="zephyr" if is_advanced_model else "basic")
        
        print(f"[AI DEBUG] Using formatted prompt: {formatted_prompt}")
        
        # Generate response using the raw model instead of pipeline
        # Tokenize the input
        input_ids = direct_huggingface_tokenizer(formatted_prompt, return_tensors="pt").to(direct_huggingface_model.device)
        
        # Generate with parameters optimized for model type
        if is_advanced_model:
            # Advanced models need different parameters
            generation_output = direct_huggingface_model.generate(
                **input_ids,
                max_new_tokens=150,  # Generate more content for better answers
                do_sample=True,
                temperature=0.3,  # Slightly higher for more creative but still controlled
                top_k=40,
                top_p=0.9,
                repetition_penalty=1.2  # Higher to further discourage repetitive text
            )
        else:
            # Conservative parameters for smaller models
            generation_output = direct_huggingface_model.generate(
                **input_ids,
                max_new_tokens=40,  # Significantly shorter for better coherence on simple models
                do_sample=True,
                temperature=0.1,  # Much lower for improved consistency
                top_k=20,
                top_p=0.80,
                repetition_penalty=2.0  # Stronger repetition penalty to prevent nonsensical loops
            )
        
        # Decode the generated tokens to text
        generated_text = direct_huggingface_tokenizer.decode(generation_output[0], skip_special_tokens=True)
        
        print(f"[AI DEBUG] Model raw output: {generated_text}")
        
        # Extract response based on model type
        if is_advanced_model:
            # Advanced models might include special tokens
            if "<|assistant|>" in generated_text:
                # Extract everything after the assistant tag and before any closing tag
                assistant_text = generated_text.split("<|assistant|>")[1]
                # Remove any trailing tags if present
                if "</s>" in assistant_text:
                    assistant_text = assistant_text.split("</s>")[0]
                response = assistant_text.strip()
            elif "User:" in generated_text and "Assistant:" in generated_text:
                # Extract text between 'Assistant:' and the end
                response = generated_text.split("Assistant:")[1].strip()
            else:
                # Fallback extraction
                response = generated_text.replace(formatted_prompt, "").strip()
        else:
            # Enhanced response extraction for simpler models
            if "Assistant: I'll answer this question directly and clearly." in generated_text:
                # Extract only what comes after our explicit marker
                extracted = generated_text.split("Assistant: I'll answer this question directly and clearly.")[1].strip()
                # Limit to first 2-3 sentences for simple queries to avoid rambling
                sentences = re.split(r'[.!?]\s+', extracted)
                if len(message.split()) < 10 and len(sentences) > 3:
                    response = ". ".join(sentences[:3]) + "."
                else:
                    response = extracted
            elif "Assistant:" in generated_text:
                extracted = generated_text.split("Assistant:")[1].strip()
                # Limit sentences for simple messages
                sentences = re.split(r'[.!?]\s+', extracted)
                if len(message.split()) < 10 and len(sentences) > 3:
                    response = ". ".join(sentences[:3]) + "."
                else:
                    response = extracted
            else:
                response = generated_text.replace(formatted_prompt, "").strip()[:150]  # Hard limit length
            
            # Clean up any remaining garbage text
            response = re.sub(r'User:.*$', '', response, flags=re.DOTALL).strip()  # Remove any 'User:' and everything after
            response = re.sub(r'^I\'ll answer this question directly and clearly\.\s*', '', response).strip()  # Remove our special prompt if it's at the beginning
        
        # Clean and validate the response
        response = clean_ai_response(response)
        
        # Enhanced validation to detect low-quality or nonsensical responses
        is_invalid = False
        
        # Stricter validation for simple queries
        # Check for empty, short or echo responses
        if not response or response.strip() == "" or len(response) < 10 or message.lower() in response.lower() or "assistant" in response.lower()[0:20]:
            is_invalid = True
            print("[AI DEBUG] Response failed basic validation: empty, too short, or contains user message")
        
        # Check for nonsensical or repetitive text
        if not is_invalid:
            # Count word repetition - high repetition suggests a bad response
            words = response.lower().split()
            if len(words) > 10:  # Only check longer responses
                word_counts = {}
                for word in words:
                    if len(word) > 3:  # Only count substantive words
                        word_counts[word] = word_counts.get(word, 0) + 1
                
                # Calculate repetition ratio
                if len(word_counts) > 0:
                    max_repeats = max(word_counts.values())
                    unique_ratio = len(word_counts) / len(words)
                    
                    if max_repeats > 3 or unique_ratio < 0.5:  # Stricter thresholds for repetition detection
                        is_invalid = True
                        print(f"[AI DEBUG] Response failed repetition check: max_repeats={max_repeats}, unique_ratio={unique_ratio:.2f}")
        
        # Check coherence with sentence structure detection
        if not is_invalid:
            sentences = re.split(r'[.!?]\s+', response)
            if len(sentences) >= 3:  # Only analyze longer responses
                # Calculate average sentence length - abnormal length patterns indicate model confusion
                sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
                avg_length = sum(sentence_lengths) / max(1, len(sentence_lengths))
                
                # For simple queries, check for first sentence being too long
                if len(message.split()) < 7 and len(sentences) > 0 and len(sentences[0].split()) > 20:
                    is_invalid = True
                if sentence_lengths and (max(sentence_lengths) > 25 or min(sentence_lengths) < 2):
                    is_invalid = True
                    print(f"[AI DEBUG] Response failed sentence structure check: lengths={sentence_lengths}")
        
        if is_invalid:
            print("[AI DEBUG] Response failed enhanced validation, falling back to template")
            # Fall back to template or generic response
            return get_template_response(message) or "I'd like to provide a more specific answer to your question. Could you please provide more details or rephrase your question?"
        
        print(f"[AI DEBUG] Final response: {response[:50]}...")
        return response
    except Exception as e:
        print(f"[ERROR] Error processing response: {e}")
        import traceback
        traceback.print_exc()
    
    # Default fallback
    return "I understand you're interested in this topic. To provide a more helpful response, could you rephrase your question or provide additional details about what you'd like to know?"

def generate_fallback_response(message):
    """Generate a simple fallback response when AI models are unavailable."""
    print(f"[GPT] Using fallback response generator for: {message}")
    
    # Simple templated responses
    greetings = ["hello", "hi", "hey", "greetings", "howdy"]
    
    message_lower = message.lower()
    
    if any(greeting in message_lower for greeting in greetings):
        return "Hello! I'm Minerva, your AI assistant. How can I help you today?"
    
    elif "how are you" in message_lower:
        return "I'm functioning well, thank you for asking! How can I assist you?"
    
    elif any(q in message_lower for q in ["what can you do", "help", "capabilities"]):
        return "I'm Minerva, an AI assistant that can help answer questions, have conversations, and assist with various tasks. Currently, I'm in development mode."
    
    elif "thank" in message_lower:
        return "You're welcome! Feel free to ask if you need anything else."
    
    elif any(q in message_lower for q in ["bye", "goodbye", "see you"]):
        return "Goodbye! Feel free to chat again whenever you'd like."
        
    else:
        # Default response
        return f"I received your message: '{message}'. Currently, my AI models are unavailable, so I'm operating in a limited capacity. Please check back later when my full capabilities are online."

def get_template_response(message):
    """Generate a templated response for common question patterns."""
    message_lower = message.lower().strip()
    
    # Greeting patterns
    if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "greetings"]):
        return "Hello! I'm Minerva, your AI assistant. How can I help you today?"
    
    # Questions about capabilities
    if "what can you do" in message_lower or "your capabilities" in message_lower:
        return "I can answer questions, provide information, and assist with various tasks. Feel free to ask me anything, and I'll do my best to help!"
    
    # Time/date related
    if "what time" in message_lower or "current time" in message_lower or "what day" in message_lower:
        from datetime import datetime
        return f"I don't have access to real-time data, but I can tell you that when this response was generated, it was {datetime.now().strftime('%H:%M on %B %d, %Y')}."
    
    # Self-identity questions
    if "who are you" in message_lower or "your name" in message_lower:
        return "I am Minerva, an AI assistant designed to provide helpful information and engage in conversations."
    
    # Joke requests
    if "tell me a joke" in message_lower or "joke" in message_lower or "funny" in message_lower:
        import random
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "What do you call a fake noodle? An impasta!",
            "Why don't skeletons fight each other? They don't have the guts.",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus.",
            "I'm on a seafood diet. Every time I see food, I eat it.",
            "Why don't eggs tell jokes? They'd crack each other up.",
            "I used to play piano by ear, but now I use my hands.",
            "How do you organize a space party? You planet."
        ]
        return random.choice(jokes)
    
    # Fact requests
    if "tell me a fact" in message_lower or "interesting fact" in message_lower or "random fact" in message_lower:
        import random
        facts = [
            "The shortest war in history was between Britain and Zanzibar on August 27, 1896. Zanzibar surrendered after 38 minutes.",
            "A group of flamingos is called a 'flamboyance'.",
            "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
            "The average person walks the equivalent of five times around the world in a lifetime.",
            "A day on Venus is longer than a year on Venus. It takes 243 Earth days to rotate once on its axis, but only 225 Earth days to go around the Sun.",
            "Octopuses have three hearts: two pump blood through the gills, and one pumps it through the body.",
            "The first computer programmer was a woman named Ada Lovelace, who worked on Charles Babbage's Analytical Engine in the 1840s.",
            "Bananas are berries, but strawberries aren't.",
            "The world's oldest known living tree is over 5,000 years old.",
            "A bolt of lightning is about 54,000°F (30,000°C), which is six times hotter than the surface of the sun."
        ]
        return random.choice(facts)
    
    # Weather related
    if "weather" in message_lower or "temperature" in message_lower or "forecast" in message_lower:
        return "I don't have access to real-time weather data. To get the current weather or forecast, you could check a weather app or website with your location details."
    
    # Sports related
    if any(sport in message_lower for sport in ["football", "basketball", "baseball", "soccer", "hockey", "tennis", "golf", "sports"]):
        return "I don't have access to current sports information or scores. For the latest sports news, scores, and updates, you might want to check a dedicated sports website or app."
    
    # General knowledge
    if "what is" in message_lower:
        topic = message_lower.split("what is")[1].strip().rstrip("?")
        return f"{topic.capitalize()} refers to a concept or entity in our world. To provide you with accurate information about {topic}, I would need more specifics about what aspect you're interested in."
    
    # How-to questions
    if message_lower.startswith("how to"):
        topic = message_lower[7:].strip().rstrip("?")
        return f"To {topic}, you would typically follow a process that involves several steps. The specific approach depends on your exact goals and context. Could you provide more details about what you're trying to accomplish?"
    
    # Why questions
    if message_lower.startswith("why"):
        topic = message_lower[3:].strip().rstrip("?")
        return f"There are several possible reasons for {topic}. The most common explanations involve various factors including context, history, and specific circumstances. Would you like me to explore any particular aspect of this question?"
    
    # Very short queries
    if len(message_lower.split()) < 3:
        return "I need a bit more information to provide a helpful response. Could you please ask a more detailed question?"
    
    # No template matched
    return None

def run():
    """Run the Flask app."""
    # Initialize plugins
    logger.info("Discovering and loading plugins...")
    loaded_plugins = plugin_manager.load_plugins()
    logger.info(f"Loaded {len(loaded_plugins)} plugins: {', '.join(loaded_plugins)}")
    
    # Get port from environment or use default - use port 9876 by default to avoid conflict
    port = 9876  # Using high-numbered port to avoid conflicts
    
    # Run the app
    logger.info(f"Starting Minerva Web Interface on port {port}")
    
    # Make sure we're using eventlet with proper configuration
    socketio.init_app(app, async_mode='eventlet', cors_allowed_origins="*", 
                     ping_timeout=60, ping_interval=25)
    
    if os.environ.get('FLASK_ENV') == 'production':
        # In production, use a proper WSGI server
        logger.warning("Running in production mode. Using eventlet as WSGI server.")
        socketio.run(app, host='0.0.0.0', port=port)
    else:
        # In development, run with debug capabilities
        os.environ['FLASK_ENV'] = 'development'  # Ensure development mode
        logger.info("Running in development mode with eventlet.")
        socketio.run(app, host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    run()
