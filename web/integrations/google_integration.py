"""
Google AI Integration Module

Provides integration with Google's Gemini API for Minerva's Think Tank.
Handles Gemini models.
"""

import logging
import time
from typing import Optional, Dict, Any

import google.generativeai as genai
from .config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

# Initialize Google AI client
try:
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        logger.info("Google AI client initialized successfully")
        initialized = True
    else:
        logger.warning("Google API key not available - client not initialized")
        initialized = False
except Exception as e:
    logger.error(f"Error initializing Google AI client: {str(e)}")
    initialized = False

# Model mapping (standardize model names to Google's expected format)
MODEL_MAPPING = {
    'gemini': 'gemini-1.5-pro',
    'gemini-pro': 'gemini-1.5-pro',
}

def generate_response_with_usage(
    message: str, 
    system_prompt: str, 
    model_name: str = 'gemini',
    temperature: float = 0.7,
    max_tokens: Optional[int] = 4096
) -> tuple[str, Dict[str, Any]]:
    """
    Generate a response using Google's Gemini API
    
    Args:
        message: User message to process
        system_prompt: System prompt to guide the model's response
        model_name: Name of the Gemini model to use
        temperature: Controls randomness (0 = deterministic, 1 = creative)
        max_tokens: Maximum number of tokens in the response
        
    Returns:
        Model's response text
        
    Raises:
        ImportError: If Google API key is not available
        Exception: For any errors during API call
    """
    if not initialized:
        raise ImportError("Google API key not available")
    
    # Map model name to Google format if needed
    google_model = MODEL_MAPPING.get(model_name, model_name)
    
    logger.info(f"Generating response with Google model: {google_model}")
    start_time = time.time()
    
    try:
        # Configure the model
        model = genai.GenerativeModel(
            model_name=google_model,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        
        # Create the chat session with the system prompt
        chat = model.start_chat(history=[])
        
        # Combine system prompt and user message
        combined_message = f"{system_prompt}\n\nUser query: {message}"
        
        # Make the API call
        response = chat.send_message(combined_message)
        
        # Extract the response content
        response_text = response.text
        
        # Extract usage statistics - Gemini API doesn't provide token counts directly
        # but we can use the prompt and response lengths to estimate
        prompt_length = len(combined_message.split())
        response_length = len(response_text.split())
        
        # Estimate token counts - roughly 3/4 tokens per word for English text
        estimated_input_tokens = int(prompt_length * 1.33)
        estimated_output_tokens = int(response_length * 1.33)
        
        # Create usage info dictionary
        usage_info = {
            'input_tokens': estimated_input_tokens,
            'output_tokens': estimated_output_tokens,
            'total_tokens': estimated_input_tokens + estimated_output_tokens,
            'model': google_model,
            'estimated': True  # Flag to indicate these are estimates
        }
        
        # Log success, timing, and token usage
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully generated response with {google_model} in {elapsed_time:.2f}s "  
                  f"(~{usage_info['input_tokens']} input / ~{usage_info['output_tokens']} output tokens estimated)")
        
        return response_text, usage_info
        
    except Exception as e:
        # Handle general exceptions
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating Google response: {str(e)} (after {elapsed_time:.2f}s)")
        raise


# Backward compatibility wrapper
def generate_response(message: str, system_prompt: str, model_name: str = 'gemini',
                     temperature: float = 0.7, max_tokens: Optional[int] = 4096) -> str:
    """Legacy wrapper for generate_response_with_usage
    
    Returns just the response text for backward compatibility
    """
    response_text, _ = generate_response_with_usage(
        message, system_prompt, model_name, temperature, max_tokens
    )
    return response_text
