"""
Anthropic Integration Module

Provides integration with Anthropic's Claude API for Minerva's Think Tank.
Handles Claude-3-Opus, Claude-3-Sonnet, and Claude-3-Haiku models.
"""

import logging
import time
from typing import Optional, Dict, Any

from anthropic import Anthropic, APIError
from .config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = None

def init_anthropic_client():
    """Initialize or reinitialize the Anthropic client"""
    global client
    try:
        if ANTHROPIC_API_KEY:
            # Simple, direct initialization with minimal parameters
            client = Anthropic(api_key=ANTHROPIC_API_KEY)
            logger.info("Anthropic client initialized successfully")
            # Log model versions available for debugging
            logger.info(f"Available Claude models: {', '.join(MODEL_MAPPING.values())}")
        else:
            client = None
            logger.warning("Anthropic API key not available - client not initialized")
    except Exception as e:
        client = None
        logger.error(f"Error initializing Anthropic client: {str(e)}")
        # Try to provide more helpful error diagnostics
        try:
            import pkg_resources
            anthropic_version = pkg_resources.get_distribution("anthropic").version
            logger.info(f"Installed Anthropic library version: {anthropic_version}")
        except Exception as pkg_error:
            logger.error(f"Could not determine Anthropic library version: {pkg_error}")
    return client

# Initialize the client on module load
init_anthropic_client()

# Model mapping (standardize model names to Anthropic's expected format)
MODEL_MAPPING = {
    'claude-3': 'claude-3-sonnet-20240229',
    'claude-3-opus': 'claude-3-opus-20240229',
    'claude-3-haiku': 'claude-3-haiku-20240307',
    'claude3': 'claude-3-sonnet-20240229',
}

def generate_response_with_usage(
    message: str, 
    system_prompt: str, 
    model_name: str = 'claude-3',
    temperature: float = 0.7,
    max_tokens: Optional[int] = 4096
) -> tuple[str, Dict[str, Any]]:
    """
    Generate a response using Anthropic's Claude API
    
    Args:
        message: User message to process
        system_prompt: System prompt to guide the model's response
        model_name: Name of the Claude model to use
        temperature: Controls randomness (0 = deterministic, 1 = creative)
        max_tokens: Maximum number of tokens in the response
        
    Returns:
        Model's response text and usage statistics
        
    Raises:
        ImportError: If Anthropic API key is not available
        Exception: For any errors during API call
    """
    global client
    
    # Check if client exists, if not try to initialize it
    if not client:
        logger.warning("Anthropic client not initialized, attempting to initialize")
        client = init_anthropic_client()
        
    if not client:
        error_msg = "Anthropic API key not available or client initialization failed"
        logger.error(error_msg)
        raise ImportError(error_msg)
    
    # Map model name to Anthropic format if needed
    anthropic_model = MODEL_MAPPING.get(model_name, model_name)
    
    logger.info(f"Generating response with Anthropic model: {anthropic_model}")
    start_time = time.time()
    
    try:
        # Make the API call with system prompt and user message
        logger.info(f"Making Anthropic API call with model {anthropic_model}")
        
        # For Anthropic v0.18.0, max_tokens is required and must be an integer
        # Set a default value if not provided or not valid
        if max_tokens is None or not isinstance(max_tokens, int) or max_tokens <= 0:
            max_tokens = 1000  # Default reasonable value
            
        # Build parameters dictionary with required max_tokens
        params = {
            "model": anthropic_model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": message}],
            "temperature": temperature,
            "max_tokens": max_tokens  # Always provide this for v0.18.0
        }
            
        logger.info(f"API parameters: {params}")
        response = client.messages.create(**params)
        
        # Extract the response content and handle potential structure changes
        try:
            # Standard extraction path
            if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 0:
                response_text = response.content[0].text
            # Alternate structure if content is not a list or is empty
            elif hasattr(response, 'content') and isinstance(response.content, dict):
                response_text = response.content.get('text', '')
            # Fall back to string conversion if we can't extract properly
            else:
                logger.warning(f"Unusual response structure from Anthropic API, attempting conversion: {type(response)}")
                response_text = str(response)
        except Exception as content_error:
            logger.error(f"Error extracting content from Anthropic response: {content_error}")
            # Fallback to string representation
            response_text = str(response)
        
        # Extract usage statistics with proper error handling
        try:
            if hasattr(response, 'usage'):
                usage_info = {
                    'input_tokens': getattr(response.usage, 'input_tokens', 0),
                    'output_tokens': getattr(response.usage, 'output_tokens', 0),
                    'total_tokens': getattr(response.usage, 'input_tokens', 0) + getattr(response.usage, 'output_tokens', 0),
                    'model': anthropic_model
                }
            else:
                # Default values if usage not available
                usage_info = {
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'total_tokens': 0,
                    'model': anthropic_model
                }
        except Exception as usage_error:
            logger.error(f"Error extracting usage from Anthropic response: {usage_error}")
            usage_info = {
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'model': anthropic_model,
                'error': str(usage_error)
            }
        
        # Log success, timing, and token usage
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully generated response with {anthropic_model} in {elapsed_time:.2f}s "  
                  f"({usage_info.get('input_tokens', 0)} input / {usage_info.get('output_tokens', 0)} output tokens)")
        
        return response_text, usage_info
        
    except APIError as e:
        # Handle API-specific errors
        elapsed_time = time.time() - start_time
        logger.error(f"Anthropic API error after {elapsed_time:.2f}s: {str(e)}")
        raise Exception(f"Anthropic API error: {str(e)}")
        
    except Exception as e:
        # Handle general exceptions
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating Anthropic response: {str(e)} (after {elapsed_time:.2f}s)")
        raise


# Backward compatibility wrapper
def generate_response(message: str, system_prompt: str, model_name: str = 'claude-3',
                     temperature: float = 0.7, max_tokens: Optional[int] = 4096) -> str:
    """Legacy wrapper for generate_response_with_usage
    
    Returns just the response text for backward compatibility
    """
    response_text, _ = generate_response_with_usage(
        message, system_prompt, model_name, temperature, max_tokens
    )
    return response_text
