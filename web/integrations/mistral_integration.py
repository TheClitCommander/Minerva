"""
Mistral Integration Module

Provides integration with Mistral AI API for Minerva's Think Tank.
Handles Mistral and Llama models.
"""

import logging
import time
from typing import Optional, Dict, Any

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from .config import MISTRAL_API_KEY

logger = logging.getLogger(__name__)

# Initialize Mistral client
try:
    if MISTRAL_API_KEY:
        client = MistralClient(api_key=MISTRAL_API_KEY)
        logger.info("Mistral client initialized successfully")
    else:
        client = None
        logger.warning("Mistral API key not available - client not initialized")
except Exception as e:
    client = None
    logger.error(f"Error initializing Mistral client: {str(e)}")

# Model mapping (standardize model names to Mistral's expected format)
MODEL_MAPPING = {
    'mistral': 'mistral-large-latest',
    'mistral7b': 'mistral-small-latest',
    'mistral-large': 'mistral-large-latest',
    'mistral-small': 'mistral-small-latest',
    'llama': 'mistral-large-latest',  # Fallback to Mistral for Llama requests
    'llama2': 'mistral-large-latest', # Fallback to Mistral for Llama2 requests
}

def generate_response_with_usage(
    message: str, 
    system_prompt: str, 
    model_name: str = 'mistral',
    temperature: float = 0.7,
    max_tokens: Optional[int] = 4096
) -> tuple[str, Dict[str, Any]]:
    """
    Generate a response using Mistral AI API
    
    Args:
        message: User message to process
        system_prompt: System prompt to guide the model's response
        model_name: Name of the Mistral model to use
        temperature: Controls randomness (0 = deterministic, 1 = creative)
        max_tokens: Maximum number of tokens in the response
        
    Returns:
        Model's response text
        
    Raises:
        ImportError: If Mistral API key is not available
        Exception: For any errors during API call
    """
    if not client:
        raise ImportError("Mistral API key not available")
    
    # Map model name to Mistral format if needed
    mistral_model = MODEL_MAPPING.get(model_name, model_name)
    
    logger.info(f"Generating response with Mistral model: {mistral_model}")
    start_time = time.time()
    
    try:
        # Prepare the messages array with system prompt and user message
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=message)
        ]
        
        # Make the API call
        response = client.chat(
            model=mistral_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Extract the response content
        response_text = response.choices[0].message.content
        
        # Extract usage statistics from Mistral response
        usage_info = {
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
            'model': mistral_model
        }
        
        # Log success, timing, and token usage
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully generated response with {mistral_model} in {elapsed_time:.2f}s "  
                  f"({usage_info['input_tokens']} input / {usage_info['output_tokens']} output tokens)")
        
        return response_text, usage_info
        
    except Exception as e:
        # Handle general exceptions
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating Mistral response: {str(e)} (after {elapsed_time:.2f}s)")
        raise


# Backward compatibility wrapper
def generate_response(message: str, system_prompt: str, model_name: str = 'mistral',
                     temperature: float = 0.7, max_tokens: Optional[int] = 4096) -> str:
    """Legacy wrapper for generate_response_with_usage
    
    Returns just the response text for backward compatibility
    """
    response_text, _ = generate_response_with_usage(
        message, system_prompt, model_name, temperature, max_tokens
    )
    return response_text
