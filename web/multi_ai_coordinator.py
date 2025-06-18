"""
MultiAICoordinator Module

This module provides a unified interface to multiple AI models for the Minerva system.
It handles routing, API calls, and response blending from different AI models.
"""

import os
import sys
import json
import time
import logging
import requests
from pathlib import Path
import traceback
import re

# FIXED COORDINATOR EXPORTED HERE
coordinator = None  # Will be set to instance at end of file
Coordinator = None  # Compatibility alias
COORDINATOR = None  # Another compatibility alias

# Import AI API clients
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import mistralai
    from mistralai.client import MistralClient
    from mistralai.models.chat_completion import ChatMessage
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    logger.info("Coordinator process logger initialized")

# Global coordinator instances - these MUST be module-level variables
# They will be initialized after the MultiAICoordinator class is defined
coordinator = None
Coordinator = None
COORDINATOR = None
_instance = None

# API Key Utilities
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

class MultiAICoordinator:
    """
    Coordinates requests between multiple AI models and handles response blending.
    
    This class provides a unified interface for sending prompts to different AI models,
    tracking their performance, and optionally blending responses for optimal results.
    """
    
    _instance = None  # Class variable for singleton pattern
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance of MultiAICoordinator"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the coordinator with available AI models and configuration."""
        self.available_models = {}
        self.default_model = None
        
        # Initialize clients dictionary
        self.clients = {
            'openai': None,
            'anthropic': None, 
            'mistral': None,
            'huggingface': None
        }
        
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
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"MultiAICoordinator initialized with {len(self.available_models)} models")
        
        # Always add a fallback simulation model that doesn't require API keys
        if not self.available_models:
            self._add_simulation_models()
            self.logger.warning("No AI models available. Using simulation mode.")
            print("WARNING: Running in SIMULATION MODE - no valid API keys found!")
        
        # Set class instance for singleton pattern
        MultiAICoordinator._instance = self
        
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
                print("Set default model to GPT-4o (OpenAI)")
        elif openai_key:
            logger.warning("OpenAI API key format invalid - skipping OpenAI models")
        
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
                print("Set default model to Claude 3 Sonnet (Anthropic)")
        elif anthropic_key:
            logger.warning("Anthropic API key format invalid - skipping Anthropic models")
        
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
            
            self.available_models["mistral-small"] = {
                "name": "Mistral Small",
                "provider": "mistral",
                "max_tokens": 4000,
                "type": "chat",
                "context_window": 32000,
                "cost_per_1k_tokens": 0.003,
                "capabilities": ["reasoning", "writing"]
            }
            
            # Set a default model if none set yet
            if not self.default_model:
                self.default_model = "mistral-large"
                print("Set default model to Mistral Large")
        elif mistral_key:
            logger.warning("Mistral API key format invalid - skipping Mistral models")
        
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
                print("Set default model to Falcon 7B (HuggingFace)")
        elif huggingface_key:
            logger.warning("HuggingFace API key format invalid - skipping HuggingFace models")
    
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
        print("No API keys found - using Enhanced Simulation as default model")
    
    def generate_response(self, user_input, session_id=None, model_preference=None):
        """Generate a response to user input using the appropriate AI model.
        
        Args:
            user_input (str): The user's message
            session_id (str, optional): Session ID for context tracking
            model_preference (str, optional): Specific model to use
            
        Returns:
            str: The AI response
        """
        # Debug info for request
        print(f"[MultiAICoordinator] Generating response for input: '{user_input[:50]}...' with model preference: {model_preference}")
        print(f"[MultiAICoordinator] Session ID: {session_id}")
        print(f"[MultiAICoordinator] Available models: {list(self.available_models.keys()) if self.available_models else 'None'}")
        
        try:
            # If no models are available, use the simulation response
            if not self.available_models:
                print("[MultiAICoordinator] No AI models available - using simulated response")
                return self._generate_enhanced_response(user_input)
            
            # Determine which model to use
            chosen_model = model_preference if model_preference in self.available_models else self.default_model
            
            # If chosen model is not available, use the default model
            if not chosen_model or chosen_model not in self.available_models:
                # Make a list of available models for the error message
                model_list = ", ".join(self.available_models.keys())
                print(f"[MultiAICoordinator] Model '{model_preference}' not found. Available models: {model_list}")
                
                if self.default_model and self.default_model in self.available_models:
                    chosen_model = self.default_model
                    print(f"[MultiAICoordinator] Using default model: {chosen_model}")
                else:
                    # If default model is not set or not available, use first available model
                    chosen_model = list(self.available_models.keys())[0]
                    print(f"[MultiAICoordinator] Using first available model: {chosen_model}")
            
            print(f"[MultiAICoordinator] Selected model: {chosen_model} ({self.available_models[chosen_model]['name']})")
            
            # Check model type/provider and call appropriate API
            model_info = self.available_models[chosen_model]
            model_provider = model_info.get('provider', '').lower()
            print(f"[MultiAICoordinator] Model provider: {model_provider}")
            
            # Start timer for response generation
            start_time = time.time()
            
            # Generate response based on provider
            if model_provider == 'openai':
                print(f"[MultiAICoordinator] Calling OpenAI API with model {chosen_model}")
                response = self._call_openai_api(user_input, chosen_model, session_id)
            elif model_provider == 'anthropic':
                print(f"[MultiAICoordinator] Calling Anthropic API with model {chosen_model}")
                response = self._call_anthropic_api(user_input, chosen_model, session_id)
            elif model_provider == 'mistral':
                print(f"[MultiAICoordinator] Calling Mistral API with model {chosen_model}")
                response = self._call_mistral_api(user_input, chosen_model, session_id)
            elif model_provider == 'huggingface':
                print(f"[MultiAICoordinator] Calling Hugging Face API with model {chosen_model}")
                response = self._call_huggingface_api(user_input, chosen_model, session_id)
            elif model_provider in ['simulation', 'fallback']:
                print(f"[MultiAICoordinator] Using simulation mode")
                response = self._generate_enhanced_response(user_input)
            else:
                # Unknown provider - use enhanced response
                print(f"[MultiAICoordinator] Unknown provider '{model_provider}' - using enhanced simulation")
                response = self._generate_enhanced_response(user_input)
                
            # Calculate response time
            response_time = time.time() - start_time
            print(f"[MultiAICoordinator] Response generated in {response_time:.2f}s using {chosen_model}")
            print(f"[MultiAICoordinator] Response: {response[:100]}...")
            
            return response
        except Exception as e:
            # Log error and return a fallback response
            error_msg = f"[MultiAICoordinator] ERROR generating response with {chosen_model if 'chosen_model' in locals() else 'unknown model'}: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            
            # Return a user-friendly error message
            return f"I apologize, but I encountered an error while processing your request. Please try again later or try a different model. (Error: {str(e)})"
    
    def _call_openai_api(self, user_input, model_name='gpt-4o', session_id=None):
        """Call the OpenAI API to generate a response"""
        if 'openai' not in self.clients:
            raise ValueError("OpenAI client not initialized")
            
        try:
            # Validate API key before making request
            api_key = os.environ.get('OPENAI_API_KEY', '')
            if not api_key or len(api_key) < 20:  # OpenAI keys are at least 20 chars
                logger.warning("Missing or invalid OpenAI API key")
                raise ValueError("Missing or invalid OpenAI API key")
            
            client = self.clients['openai']
            
            # Format the messages
            messages = [{"role": "user", "content": user_input}]
            
            # Call the API
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            # Extract and return the response text
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise
    
    def _call_anthropic_api(self, user_input, model_name='claude-3-opus', session_id=None):
        """Call the Anthropic API to generate a response"""
        if 'anthropic' not in self.clients:
            raise ValueError("Anthropic client not initialized")
            
        try:
            # Validate API key before making request
            api_key = os.environ.get('ANTHROPIC_API_KEY', '')
            if not api_key or len(api_key) < 20:  # Anthropic keys are long
                logger.warning("Missing or invalid Anthropic API key")
                raise ValueError("Missing or invalid Anthropic API key")
            
            client = self.clients['anthropic']
            
            # Call the API
            response = client.messages.create(
                model=model_name,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": user_input}
                ]
            )
            
            # Extract and return the response text
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            raise
    
    def _call_mistral_api(self, user_input, model_name='mistral-large', session_id=None):
        """Call the Mistral API to generate a response"""
        if 'mistral' not in self.clients:
            raise ValueError("Mistral client not initialized")
            
        try:
            # Validate API key before making request
            api_key = os.environ.get('MISTRAL_API_KEY', '')
            if not api_key or len(api_key) < 20:  # Mistral keys are typically long
                logger.warning("Missing or invalid Mistral API key")
                raise ValueError("Missing or invalid Mistral API key")
            
            client = self.clients['mistral']
            
            # Map model names to Mistral model IDs
            model_map = {
                'mistral-large': 'mistral-large-latest',
                'mistral-medium': 'mistral-medium-latest',
                'mistral-small': 'mistral-small-latest'
            }
            
            # Get the actual model ID
            model_id = model_map.get(model_name, 'mistral-large-latest')
            
            # Create the messages
            messages = [ChatMessage(role="user", content=user_input)]
            
            # Call the API
            response = client.chat(
                model=model_id,
                messages=messages
            )
            
            # Extract and return the response text
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling Mistral API: {str(e)}")
            raise
    
    def _call_huggingface_api(self, user_input, model_name='gpt2', session_id=None):
        """Call the HuggingFace API to generate a response"""
        if 'huggingface' not in self.clients:
            raise ValueError("HuggingFace client not initialized")
            
        try:
            # Validate API key before making request
            api_key = os.environ.get('HUGGINGFACE_API_KEY', '')
            if not api_key or len(api_key) < 10:  # HuggingFace keys are typically longer
                logger.warning("Missing or invalid HuggingFace API key")
                raise ValueError("Missing or invalid HuggingFace API key")
            
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare the payload
            payload = {
                "inputs": user_input,
                "options": {
                    "use_cache": True,
                    "wait_for_model": True
                },
                "parameters": {
                    "max_new_tokens": 250,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True
                }
            }
            
            # Make the API call
            url = f"https://api-inference.huggingface.co/models/{model_name}"
            response = requests.post(url, headers=headers, json=payload)
            
            # Handle the response
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list) and len(data) > 0:
                    if 'generated_text' in data[0]:
                        return data[0]['generated_text']
                    else:
                        return str(data[0])
                elif isinstance(data, dict):
                    if 'generated_text' in data:
                        return data['generated_text']
                    else:
                        return str(data)
                else:
                    return str(data)
            else:
                error_msg = f"HuggingFace API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
        except Exception as e:
            logger.error(f"Error calling HuggingFace API: {str(e)}")
            raise
    
    def _generate_enhanced_response(self, user_input):
        """
        Generate enhanced simulated response when no real AI models are available.
        This provides more natural-sounding responses than a simple error message.
        
        Args:
            user_input (str): The user's message
            
        Returns:
            str: A simulated response
        """
        logger.info("Using enhanced simulation response for: %s", user_input[:50] + "..." if len(user_input) > 50 else user_input)
        
        # Extract potential topics from the input
        user_input_lower = user_input.lower()
        
        # Check for common greetings and respond appropriately
        greetings = ["hello", "hi", "hey", "greetings", "howdy"]
        if any(greeting in user_input_lower for greeting in greetings):
            return "Hello! I'm Minerva, your AI assistant. How can I help you today?"
        
        # Check for questions about the assistant
        if "who are you" in user_input_lower or "what are you" in user_input_lower:
            return "I'm Minerva, an AI assistant designed to help answer questions and have conversations on a wide range of topics."
        
        # Check for common topics
        if "minerva" in user_input_lower:
            return "Minerva is an advanced AI system designed to provide helpful information and assistance across a wide range of topics. While I'm currently running in simulation mode without connection to external AI APIs, I can still help with basic information and responses."
        
        if any(term in user_input_lower for term in ["ai", "artificial intelligence", "machine learning", "ml"]):
            return "Artificial Intelligence refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed."
        
        if "python" in user_input_lower or "code" in user_input_lower or "programming" in user_input_lower:
            return "Python is a high-level, interpreted programming language known for its readability and versatility. It's widely used in web development, data science, artificial intelligence, automation, and many other fields."
        
        # Default response based on the query type
        if user_input.endswith("?"):
            return f"That's an interesting question about '{user_input.rstrip('?')}'. When connected to real AI models, I could provide a more detailed response. Currently, I'm operating in simulation mode."
        
        # Generic response for other inputs
        return f"I understand you're asking about '{user_input}'. While I'm currently operating in simulation mode without connection to external AI APIs, I'd be happy to continue our conversation or try to help with something else."
            
    def get_available_models(self):
        """Return information about available AI models"""
        return {
            'models': list(self.available_models.keys()),
            'default': list(self.available_models.keys())[0] if self.available_models else None,
            'count': len(self.available_models)
        }

# Create the singleton coordinator instance
print("Initializing MultiAICoordinator singleton...")
coordinator = MultiAICoordinator()
Coordinator = coordinator  # Capital C alias for legacy imports
COORDINATOR = coordinator  # All-caps version for constant-style imports

# Ensure singleton pattern works
if hasattr(MultiAICoordinator, '_instance'):
    MultiAICoordinator._instance = coordinator

# Log initialization
print(f"Coordinator initialized with {len(coordinator.available_models) if hasattr(coordinator, 'available_models') else 0} models")

# Add to module globals directly to ensure they're accessible
globals()['coordinator'] = coordinator
globals()['Coordinator'] = Coordinator
globals()['COORDINATOR'] = COORDINATOR

# Make these available via from module import *
__all__ = ['MultiAICoordinator', 'coordinator', 'Coordinator', 'COORDINATOR']

# Print confirmation of initialization to help with debugging
print(f"MultiAICoordinator initialized and exported as Coordinator: {id(Coordinator)}")
print(f"Available models: {list(coordinator.available_models.keys())}")

# Create and export the coordinator instance for imports
coordinator = MultiAICoordinator()
Coordinator = coordinator  # Capital C for backward compatibility
print("✅ Coordinator properly exported and available for import")

# Add at the BOTTOM of the file
# Make coordinator available globally for imports
if coordinator is None:
    coordinator = MultiAICoordinator()
    Coordinator = coordinator  # Capital C version for imports
    _instance = coordinator
    # Add debug info
    print(f"✅ MultiAICoordinator global instance created: {id(coordinator)}")
    print(f"Available models: {list(coordinator.available_models.keys()) if hasattr(coordinator, 'available_models') else []}")

# IMPORTANT: Add this at the VERY END of the file
# Make the coordinator globally available with both naming conventions
coordinator = MultiAICoordinator()
Coordinator = coordinator  # Some imports look for capital C version

print(f"✅ MultiAICoordinator successfully initialized and exported globally as 'coordinator' and 'Coordinator'")
print(f"   Available models: {list(coordinator.available_models.keys()) if hasattr(coordinator, 'available_models') else []}")