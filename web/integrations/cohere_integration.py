"""
Cohere Integration Module

Provides integration with Cohere API for Minerva's Think Tank.
Handles Cohere models.
"""

import logging
import time
from typing import Optional, Dict, Any

import cohere
from .config import COHERE_API_KEY

logger = logging.getLogger(__name__)

# Initialize Cohere client
try:
    if COHERE_API_KEY:
        client = cohere.Client(api_key=COHERE_API_KEY)
        logger.info("Cohere client initialized successfully")
    else:
        client = None
        logger.warning("Cohere API key not available - client not initialized")
except Exception as e:
    client = None
    logger.error(f"Error initializing Cohere client: {str(e)}")

# Model mapping (standardize model names to Cohere's expected format)
MODEL_MAPPING = {
    'cohere': 'command',
    'cohere-command': 'command',
}

def generate_response_with_usage(
    message: str, 
    system_prompt: str, 
    model_name: str = 'cohere',
    temperature: float = 0.7,
    max_tokens: Optional[int] = 4096
) -> tuple[str, Dict[str, Any]]:
    """
    Generate a response using Cohere's API
    
    Args:
        message: User message to process
        system_prompt: System prompt to guide the model's response
        model_name: Name of the Cohere model to use
        temperature: Controls randomness (0 = deterministic, 1 = creative)
        max_tokens: Maximum number of tokens in the response
        
    Returns:
        Model's response text
        
    Raises:
        ImportError: If Cohere API key is not available
        Exception: For any errors during API call
    """
    if not client:
        raise ImportError("Cohere API key not available")
    
    # Map model name to Cohere format if needed
    cohere_model = MODEL_MAPPING.get(model_name, model_name)
    
    logger.info(f"Generating response with Cohere model: {cohere_model}")
    start_time = time.time()
    
    try:
        # Make the API call
        response = client.chat(
            model=cohere_model,
            message=message,
            preamble=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Extract the response content
        response_text = response.text
        
        # Extract token usage from response
        # Note: Cohere provides token counts in response.meta
        usage_info = {
            'input_tokens': response.meta.prompt_tokens,
            'output_tokens': response.meta.completion_tokens,
            'total_tokens': response.meta.prompt_tokens + response.meta.completion_tokens,
            'model': cohere_model
        }
        
        # Log success, timing, and token usage
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully generated response with {cohere_model} in {elapsed_time:.2f}s "  
                  f"({usage_info['input_tokens']} input / {usage_info['output_tokens']} output tokens)")
        
        return response_text, usage_info
        
    except Exception as e:
        # Handle general exceptions
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating Cohere response: {str(e)} (after {elapsed_time:.2f}s)")
        raise


# Backward compatibility wrapper
def generate_response(message: str, system_prompt: str, model_name: str = 'cohere',
                     temperature: float = 0.7, max_tokens: Optional[int] = 4096) -> str:
    """Legacy wrapper for generate_response_with_usage
    
    Returns just the response text for backward compatibility
    """
    response_text, _ = generate_response_with_usage(
        message, system_prompt, model_name, temperature, max_tokens
    )
    return response_text
