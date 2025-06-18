#!/usr/bin/env python3
"""
Minerva Core Coordinator

Unified coordinator that manages all AI model interactions.
Merged from ai_coordinator_singleton.py and web/multi_ai_coordinator.py.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
import traceback

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    logger.info("Core coordinator logger initialized")


def validate_key_format(key_name, value):
    """Validate that an API key has the correct format."""
    if not value:
        return False
        
    # Define expected prefixes for different API keys
    expected_prefixes = {
        "OPENAI_API_KEY": "sk-",
        "ANTHROPIC_API_KEY": "sk-ant-",
        "HUGGINGFACE_API_KEY": "hf_",
        # Mistral doesn't have a required prefix pattern
        "MISTRAL_API_KEY": ""
    }
    
    prefix = expected_prefixes.get(key_name, "")
    if prefix and not value.startswith(prefix):
        return False
            
    # Basic length check - most API keys are longer than 8 chars
    if len(value) < 8:
        return False
            
    return True
        

def mask_key(value):
    """Mask an API key for safe logging by showing only first 7 chars and last 4."""
    if not value or len(value) < 8:
        return "INVALID_KEY"
    
    # Show prefix and last 4 chars
    return value[:7] + "..." + value[-4:]


class MinervaCoordinator:
    """
    Core coordinator for all AI model interactions in Minerva.
    
    This class provides a unified interface for sending prompts to different AI models,
    tracking their performance, and managing API interactions.
    """
    
    _instance = None  # Class variable for singleton pattern
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance of MinervaCoordinator"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the coordinator with available AI models and configuration."""
        self.available_models = {}
        self.default_model = None
        
        # Initialize model clients (will be loaded from models/ directory)
        self.model_clients = {}
        
        # Debug information for API keys with validation
        api_keys = {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
            "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY", ""),
            "HUGGINGFACE_API_KEY": os.getenv("HUGGINGFACE_API_KEY", "")
        }
        
        # Validate and log key status
        valid_keys = []
        for key_name, key_value in api_keys.items():
            if key_value:
                is_valid = validate_key_format(key_name, key_value)
                if is_valid:
                    valid_keys.append(key_name)
                    logger.info(f"{key_name}: Valid format - {mask_key(key_value)}")
                else:
                    logger.warning(f"{key_name}: Invalid format - {mask_key(key_value)}")
        
        if valid_keys:
            logger.info(f"Found {len(valid_keys)} valid API keys: {', '.join(valid_keys)}")
        else:
            logger.warning("No valid API keys found - will use simulation mode")
        
        # Initialize available models
        self._init_models(
            openai_key=api_keys["OPENAI_API_KEY"],
            anthropic_key=api_keys["ANTHROPIC_API_KEY"],
            mistral_key=api_keys["MISTRAL_API_KEY"],
            huggingface_key=api_keys["HUGGINGFACE_API_KEY"]
        )
        
        # Initialize model clients
        self._init_model_clients(api_keys)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"MinervaCoordinator initialized with {len(self.available_models)} models")
        
        # Always add a fallback simulation model that doesn't require API keys
        if not self.available_models:
            self._add_simulation_models()
            self.logger.warning("No AI models available. Using simulation mode.")
            print("WARNING: Running in SIMULATION MODE - no valid API keys found!")
        
        # Set class instance for singleton pattern
        MinervaCoordinator._instance = self
        
    def _init_model_clients(self, api_keys):
        """Initialize AI model clients by importing from models/ directory."""
        try:
            # Try to import model clients - they should be in models/ directory
            if api_keys["OPENAI_API_KEY"] and validate_key_format("OPENAI_API_KEY", api_keys["OPENAI_API_KEY"]):
                try:
                    from models.openai_client import OpenAIClient
                    self.model_clients['openai'] = OpenAIClient(api_keys["OPENAI_API_KEY"])
                    logger.info("✅ OpenAI client initialized")
                except ImportError:
                    logger.warning("OpenAI client not available - falling back to direct API calls")
            
            if api_keys["ANTHROPIC_API_KEY"] and validate_key_format("ANTHROPIC_API_KEY", api_keys["ANTHROPIC_API_KEY"]):
                try:
                    from models.anthropic_client import AnthropicClient
                    self.model_clients['anthropic'] = AnthropicClient(api_keys["ANTHROPIC_API_KEY"])
                    logger.info("✅ Anthropic client initialized")
                except ImportError:
                    logger.warning("Anthropic client not available - falling back to direct API calls")
            
            if api_keys["MISTRAL_API_KEY"] and validate_key_format("MISTRAL_API_KEY", api_keys["MISTRAL_API_KEY"]):
                try:
                    from models.mistral_client import MistralClient
                    self.model_clients['mistral'] = MistralClient(api_keys["MISTRAL_API_KEY"])
                    logger.info("✅ Mistral client initialized")
                except ImportError:
                    logger.warning("Mistral client not available - falling back to direct API calls")
            
            if api_keys["HUGGINGFACE_API_KEY"] and validate_key_format("HUGGINGFACE_API_KEY", api_keys["HUGGINGFACE_API_KEY"]):
                try:
                    from models.huggingface_client import HuggingFaceClient
                    self.model_clients['huggingface'] = HuggingFaceClient(api_keys["HUGGINGFACE_API_KEY"])
                    logger.info("✅ HuggingFace client initialized")
                except ImportError:
                    logger.warning("HuggingFace client not available - falling back to direct API calls")
                    
        except Exception as e:
            logger.warning(f"Error initializing model clients: {e}")
            logger.warning("Will fall back to legacy direct API calls")
    
    def _init_models(self, openai_key=None, anthropic_key=None, mistral_key=None, huggingface_key=None):
        """Initialize AI models based on available API keys with format validation."""
        # OpenAI models
        if openai_key and validate_key_format("OPENAI_API_KEY", openai_key):
            self.available_models["gpt-4o"] = {
                "name": "GPT-4o",
                "provider": "openai",
                "max_tokens": 8000,
                "type": "chat",
                "context_window": 128000,
                "cost_per_1k_tokens": 0.01,
                "capabilities": ["reasoning", "coding", "writing", "analysis"]
            }
            
            self.available_models["gpt-3.5-turbo"] = {
                "name": "GPT-3.5 Turbo",
                "provider": "openai",
                "max_tokens": 4000,
                "type": "chat",
                "context_window": 16000,
                "cost_per_1k_tokens": 0.002,
                "capabilities": ["reasoning", "coding", "writing"]
            }
            
            # Set a default model
            if not self.default_model:
                self.default_model = "gpt-4o"
                logger.info("Set default model to GPT-4o (OpenAI)")
        
        # Anthropic models
        if anthropic_key and validate_key_format("ANTHROPIC_API_KEY", anthropic_key):
            self.available_models["claude-3-opus"] = {
                "name": "Claude 3 Opus",
                "provider": "anthropic",
                "max_tokens": 4000,
                "type": "chat",
                "context_window": 200000,
                "cost_per_1k_tokens": 0.015,
                "capabilities": ["reasoning", "coding", "writing", "analysis", "creativity"]
            }
            
            self.available_models["claude-3-sonnet"] = {
                "name": "Claude 3 Sonnet",
                "provider": "anthropic",
                "max_tokens": 4000,
                "type": "chat",
                "context_window": 180000,
                "cost_per_1k_tokens": 0.008,
                "capabilities": ["reasoning", "coding", "writing", "analysis"]
            }
            
            # Set a default model if none set yet
            if not self.default_model:
                self.default_model = "claude-3-sonnet"
                logger.info("Set default model to Claude 3 Sonnet (Anthropic)")
        
        # Mistral models
        if mistral_key and validate_key_format("MISTRAL_API_KEY", mistral_key):
            self.available_models["mistral-large"] = {
                "name": "Mistral Large",
                "provider": "mistral",
                "max_tokens": 4000,
                "type": "chat",
                "context_window": 32000,
                "cost_per_1k_tokens": 0.008,
                "capabilities": ["reasoning", "coding", "writing"]
            }
            
            # Set a default model if none set yet
            if not self.default_model:
                self.default_model = "mistral-large"
                logger.info("Set default model to Mistral Large")
        
        # HuggingFace models
        if huggingface_key and validate_key_format("HUGGINGFACE_API_KEY", huggingface_key):
            self.available_models["falcon-7b"] = {
                "name": "Falcon 7B",
                "provider": "huggingface",
                "max_tokens": 2000,
                "type": "completion",
                "context_window": 4000,
                "cost_per_1k_tokens": 0.001,
                "capabilities": ["reasoning", "writing"]
            }
            
            # Set a default model if none set yet
            if not self.default_model:
                self.default_model = "falcon-7b"
                logger.info("Set default model to Falcon 7B (HuggingFace)")
    
    def _add_simulation_models(self):
        """Add simulation models when no API keys are available."""
        # Add the enhanced simulation model
        self.available_models["enhanced-simulation"] = {
            "name": "Enhanced Simulation",
            "provider": "simulation",
            "max_tokens": 2000,
            "type": "simulation",
            "context_window": 8000,
            "cost_per_1k_tokens": 0.0,
            "capabilities": ["basic-responses"]
        }
        
        # Add a fallback model
        self.available_models["fallback"] = {
            "name": "Fallback Model",
            "provider": "fallback",
            "max_tokens": 1000,
            "type": "fallback",
            "context_window": 4000,
            "cost_per_1k_tokens": 0.0,
            "capabilities": ["basic-responses"]
        }
        
        # Set the default model
        self.default_model = "enhanced-simulation"
        logger.info("No API keys found - using Enhanced Simulation as default model")
    
    def generate_response(self, user_input, session_id=None, model_preference=None):
        """Generate a response to user input using the appropriate AI model.
        
        Args:
            user_input (str): The user's message
            session_id (str, optional): Session ID for context tracking
            model_preference (str, optional): Specific model to use
            
        Returns:
            str: The AI response
        """
        logger.info(f"Generating response for input: '{user_input[:50]}...' with model: {model_preference}")
        
        try:
            # If no models are available, use the simulation response
            if not self.available_models:
                logger.info("No AI models available - using simulated response")
                return self._generate_enhanced_response(user_input)
            
            # Determine which model to use
            chosen_model = model_preference if model_preference in self.available_models else self.default_model
            
            # If chosen model is not available, use the default model
            if not chosen_model or chosen_model not in self.available_models:
                model_list = ", ".join(self.available_models.keys())
                logger.warning(f"Model '{model_preference}' not found. Available: {model_list}")
                
                if self.default_model and self.default_model in self.available_models:
                    chosen_model = self.default_model
                else:
                    chosen_model = list(self.available_models.keys())[0]
            
            logger.info(f"Selected model: {chosen_model} ({self.available_models[chosen_model]['name']})")
            
            # Get model info and provider
            model_info = self.available_models[chosen_model]
            model_provider = model_info.get('provider', '').lower()
            
            # Start timer for response generation
            start_time = time.time()
            
            # Generate response using appropriate client or fallback
            if model_provider in self.model_clients:
                # Use dedicated client
                client = self.model_clients[model_provider]
                response = client.generate_response(user_input, chosen_model, session_id)
            elif model_provider in ['simulation', 'fallback']:
                response = self._generate_enhanced_response(user_input)
            else:
                # Fall back to legacy direct API calls (to be moved to models/ later)
                response = self._legacy_api_call(user_input, chosen_model, model_provider, session_id)
                
            # Calculate response time
            response_time = time.time() - start_time
            logger.info(f"Response generated in {response_time:.2f}s using {chosen_model}")
            
            return response
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Return a user-friendly error message
            return f"I apologize, but I encountered an error while processing your request. Please try again later. (Error: {str(e)})"
    
    def _legacy_api_call(self, user_input, model_name, provider, session_id=None):
        """Legacy direct API calls - to be moved to models/ directory."""
        logger.warning(f"Using legacy API call for {provider} - consider moving to models/ directory")
        
        # Import the old implementation temporarily
        try:
            from web.multi_ai_coordinator import MultiAICoordinator
            legacy_coordinator = MultiAICoordinator()
            
            if provider == 'openai':
                return legacy_coordinator._call_openai_api(user_input, model_name, session_id)
            elif provider == 'anthropic':
                return legacy_coordinator._call_anthropic_api(user_input, model_name, session_id)
            elif provider == 'mistral':
                return legacy_coordinator._call_mistral_api(user_input, model_name, session_id)
            elif provider == 'huggingface':
                return legacy_coordinator._call_huggingface_api(user_input, model_name, session_id)
            else:
                return self._generate_enhanced_response(user_input)
                
        except Exception as e:
            logger.error(f"Legacy API call failed: {e}")
            return self._generate_enhanced_response(user_input)
    
    def _generate_enhanced_response(self, user_input):
        """
        Generate enhanced simulated response when no real AI models are available.
        """
        logger.info(f"Using enhanced simulation for: {user_input[:50]}...")
        
        user_input_lower = user_input.lower()
        
        # Check for common greetings
        greetings = ["hello", "hi", "hey", "greetings", "howdy"]
        if any(greeting in user_input_lower for greeting in greetings):
            return "Hello! I'm Minerva, your AI assistant. How can I help you today?"
        
        # Check for questions about the assistant
        if "who are you" in user_input_lower or "what are you" in user_input_lower:
            return "I'm Minerva, an AI assistant designed to help answer questions and have conversations on a wide range of topics."
        
        # Check for common topics
        if "minerva" in user_input_lower:
            return "Minerva is an advanced AI system designed to provide helpful information and assistance. While I'm currently running in simulation mode, I can still help with basic information and responses."
        
        if any(term in user_input_lower for term in ["ai", "artificial intelligence", "machine learning", "ml"]):
            return "Artificial Intelligence refers to the simulation of human intelligence in machines. Machine Learning is a subset of AI that enables systems to learn from experience."
        
        if "python" in user_input_lower or "code" in user_input_lower or "programming" in user_input_lower:
            return "Python is a high-level programming language known for its readability and versatility. It's widely used in web development, data science, AI, and automation."
        
        # Default responses
        if user_input.endswith("?"):
            return f"That's an interesting question about '{user_input.rstrip('?')}'. When connected to real AI models, I could provide a more detailed response."
        
        return f"I understand you're asking about '{user_input}'. I'd be happy to continue our conversation or help with something else."
            
    def get_available_models(self):
        """Return information about available AI models"""
        return {
            'models': list(self.available_models.keys()),
            'default': self.default_model,
            'count': len(self.available_models)
        }


# Create the singleton coordinator instance
coordinator = MinervaCoordinator()

# Legacy compatibility aliases
Coordinator = coordinator  # Capital C alias for legacy imports
MultiAICoordinator = MinervaCoordinator  # For backward compatibility

# Module exports
__all__ = ['MinervaCoordinator', 'coordinator', 'Coordinator', 'MultiAICoordinator']

logger.info(f"✅ Core coordinator initialized with {len(coordinator.available_models)} models")
logger.info(f"Available models: {list(coordinator.available_models.keys())}") 