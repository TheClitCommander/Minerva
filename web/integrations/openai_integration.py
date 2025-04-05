"""
OpenAI Integration Module

Provides integration with OpenAI API for Minerva's Think Tank.
Handles GPT-4, GPT-4o, and other OpenAI models.
"""

import json
import logging
import time
from typing import Optional, Dict, Any

import openai
from .config import OPENAI_API_KEY, OPENAI_ORG_ID

# Set up appropriate import for APIError
try:
    from openai.error import APIError
except ImportError:
    try:
        from openai.openai_object import OpenAIError as APIError
    except ImportError:
        # Generic fallback for newer versions
        APIError = Exception

logger = logging.getLogger(__name__)

# Model mapping (standardize model names to OpenAI's expected format)
MODEL_MAPPING = {
    "gpt-4": "gpt-4",
    "gpt-4-turbo": "gpt-4-0125-preview",
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini"
}

# Initialize OpenAI client
client = None

def init_openai_client():
    """Initialize or reinitialize the OpenAI client"""
    global client
    try:
        if OPENAI_API_KEY:
            # Set up client using either v1.0.0+ or fallback to v0.28.0 style
            try:
                # For v1.0.0+ OpenAI API
                client = openai.OpenAI(api_key=OPENAI_API_KEY, organization=OPENAI_ORG_ID if OPENAI_ORG_ID else None)
                logger.info("OpenAI client initialized successfully (v1.0.0+)")
            except (AttributeError, TypeError):
                # Fallback for older v0.28.0 API
                openai.api_key = OPENAI_API_KEY
                if OPENAI_ORG_ID:
                    openai.organization = OPENAI_ORG_ID
                client = openai
                logger.info("OpenAI client initialized successfully (v0.28.0)")
            
            # Log available models
            model_list = ", ".join(MODEL_MAPPING.values())
            logger.info(f"Available OpenAI models: {model_list}")
        else:
            client = None
            logger.warning("OpenAI API key not available - client not initialized")
    except Exception as e:
        client = None
        logger.error(f"Error initializing OpenAI client: {str(e)}")
        # Try to provide more helpful error diagnostics
        try:
            import pkg_resources
            openai_version = pkg_resources.get_distribution("openai").version
            logger.info(f"Installed OpenAI library version: {openai_version}")
        except Exception as pkg_error:
            logger.error(f"Could not determine OpenAI library version: {pkg_error}")
    return client

# Initialize the client on module load
init_openai_client()

# Model mapping (standardize model names to OpenAI's expected format)
MODEL_MAPPING = {
    'gpt-4': 'gpt-4',  # Using standard gpt-4 which should be available
    'gpt4': 'gpt-4',
    'gpt-4o': 'gpt-4o',
    'gpt-4o-mini': 'gpt-4o-mini',
}

def generate_response_with_usage(
    message: str, 
    system_prompt: str, 
    model_name: str = 'gpt-4',
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> tuple[str, Dict[str, Any]]:
    """
    Generate a response using OpenAI's API
    
    Args:
        message: User message to process
        system_prompt: System prompt to guide the model's response
        model_name: Name of the OpenAI model to use
        temperature: Controls randomness (0 = deterministic, 1 = creative)
        max_tokens: Maximum number of tokens in the response, or None for default
        
    Returns:
        Tuple of (response_text, usage_info)
        
    Raises:
        ImportError: If OpenAI API key is not available
        Exception: For any errors during API call
    """
    global client
    
    # Check if client exists, if not try to initialize it
    if not client:
        logger.warning("OpenAI client not initialized, attempting to initialize")
        client = init_openai_client()
        
    if not client:
        error_msg = "OpenAI API key not available or client initialization failed"
        logger.error(error_msg)
        raise ImportError(error_msg)
    
    # Map model name to OpenAI format if needed
    openai_model = MODEL_MAPPING.get(model_name, model_name)
    
    logger.info(f"Generating response with OpenAI model: {openai_model}")
    start_time = time.time()
    
    try:
        # Use a more direct approach to avoid potential import errors
        # Prepare the messages array with system prompt and user message
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Make the API call with error handling for different client implementations
        try:
            # For OpenAI version 0.28.0, use the module-level function
            params = {
                "model": openai_model,
                "messages": messages, 
                "temperature": temperature,
            }
            
            # Only add max_tokens if it's valid
            if max_tokens is not None and isinstance(max_tokens, int) and max_tokens > 0:
                params["max_tokens"] = max_tokens
                
            logger.info(f"OpenAI API parameters: {params}")
            # Detect which version of the OpenAI client we're using
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                # We're using v1.0.0+ client instance
                response = client.chat.completions.create(**params)
            else:
                # We're using legacy v0.28.0 API
                response = client.ChatCompletion.create(**params)
            
            # Extract the response content based on client version
            if hasattr(response, 'choices'):
                # v0.28.0 API response structure
                if len(response.choices) > 0:
                    if hasattr(response.choices[0], 'message'):
                        response_text = response.choices[0].message.content
                    else:
                        response_text = str(response.choices[0])
                else:
                    response_text = str(response)
            elif hasattr(response, 'model_dump'):
                # v1.0.0 API response structure
                try:
                    response_dict = response.model_dump()
                    response_text = response_dict['choices'][0]['message']['content']
                except (KeyError, IndexError, AttributeError):
                    response_text = str(response)
            else:
                # Fallback
                response_text = str(response)
                
            # Extract usage statistics
            usage_info = {
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'model': openai_model
            }
            
            # Try to extract usage based on client version
            if hasattr(response, 'usage'):
                # v0.28.0 API
                usage_info.update({
                    'input_tokens': getattr(response.usage, 'prompt_tokens', 0),
                    'output_tokens': getattr(response.usage, 'completion_tokens', 0),
                    'total_tokens': getattr(response.usage, 'total_tokens', 0),
                })
            elif hasattr(response, 'model_dump'):
                # v1.0.0 API
                try:
                    response_dict = response.model_dump()
                    usage = response_dict.get('usage', {})
                    usage_info.update({
                        'input_tokens': usage.get('prompt_tokens', 0),
                        'output_tokens': usage.get('completion_tokens', 0),
                        'total_tokens': usage.get('total_tokens', 0),
                    })
                except (AttributeError, TypeError):
                    pass
            
        except (AttributeError, ImportError) as api_struct_error:
            # Fallback for older OpenAI client versions or different structures
            logger.warning(f"Using fallback OpenAI client approach due to: {api_struct_error}")
            
            # Try direct API call without nested completions namespace
            try:
                # For older OpenAI API versions
                api_kwargs = {
                    "model": openai_model,
                    "messages": messages,
                    "temperature": temperature,
                }
                if max_tokens is not None:
                    api_kwargs["max_tokens"] = max_tokens
                    
                # Try different client structures based on OpenAI version
                if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                    # v1.0.0+ API
                    response = client.chat.completions.create(**api_kwargs)
                elif hasattr(client, 'chat') and hasattr(client.chat, 'create'):
                    # Some interim version
                    response = client.chat.create(**api_kwargs)
                elif hasattr(client, 'completions') and hasattr(client.completions, 'create'):
                    # Last resort - try completely different structure with completions
                    prompt_kwargs = api_kwargs.copy()
                    if 'messages' in prompt_kwargs:
                        del prompt_kwargs['messages']
                    
                    response = client.completions.create(
                        prompt=f"{system_prompt}\n\nUser: {message}\n\nAssistant:",
                        **prompt_kwargs
                    )
                else:
                    # Ultimate fallback for v0.28.0
                    response = client.ChatCompletion.create(**api_kwargs)
                
                # Basic extraction
                response_text = str(response)
                usage_info = {
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'total_tokens': 0,
                    'model': openai_model,
                    'fallback': True
                }
            except Exception as fallback_error:
                logger.error(f"Both OpenAI API approaches failed: {fallback_error}")
                raise
        
        # Log success, timing, and token usage
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully generated response with {openai_model} in {elapsed_time:.2f}s") 
        logger.info(f"Tokens: {usage_info.get('input_tokens', 0)} input / {usage_info.get('output_tokens', 0)} output")
        
        return response_text, usage_info
        
    except APIError as e:
        # Handle API-specific errors
        elapsed_time = time.time() - start_time
        logger.error(f"OpenAI API error after {elapsed_time:.2f}s: {str(e)}")
        error_details = f"OpenAI API error: {str(e)}"
        
        # Include rate limit information if available
        if hasattr(e, 'headers'):
            rate_limit_remaining = e.headers.get('x-ratelimit-remaining')
            if rate_limit_remaining:
                error_details += f" (Rate limit remaining: {rate_limit_remaining})"
                
        raise Exception(error_details)
        
    except Exception as e:
        # Handle general exceptions
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating OpenAI response: {str(e)} (after {elapsed_time:.2f}s)")
        raise


# Backward compatibility wrapper
def generate_response(message: str, system_prompt: str, model_name: str = 'gpt-4',
                     temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
    """Legacy wrapper for generate_response_with_usage
    
    Returns just the response text for backward compatibility
    """
    response_text, _ = generate_response_with_usage(
        message, system_prompt, model_name, temperature, max_tokens
    )
    return response_text


def generate_embedding_with_usage(text: str, model: str = 'text-embedding-ada-002') -> tuple[list[float], Dict[str, Any]]:
    """Generate an embedding vector for the provided text using OpenAI with usage tracking
    
    Args:
        text: Text to embed
        model: Embedding model to use
        
    Returns:
        Tuple containing:
            - List of floating point values representing the embedding vector
            - Usage information dict with input_tokens and model
        
    Raises:
        ImportError: If OpenAI API key is not available
        Exception: For any errors during API call
    """
    if not client:
        raise ImportError("OpenAI API key not available")
    
    logger.info(f"Generating embedding with model: {model}")
    start_time = time.time()
    
    try:
        # Make the API call
        response = client.embeddings.create(
            model=model,
            input=text
        )
        
        # Extract the embedding
        embedding = response.data[0].embedding
        
        # Construct usage info
        # For embeddings, OpenAI only provides input tokens
        usage_info = {
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': 0,  # Embeddings don't have output tokens
            'total_tokens': response.usage.prompt_tokens,
            'model': model
        }
        
        # Log success, timing, and token usage
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully generated embedding in {elapsed_time:.2f}s "  
                  f"({usage_info['input_tokens']} tokens)")
        
        return embedding, usage_info
        
    except APIError as e:
        # Handle API-specific errors
        logger.error(f"OpenAI API error: {str(e)}")
        error_details = f"OpenAI API error: {str(e)}"
        
        # Include rate limit information if available
        if hasattr(e, 'headers'):
            rate_limit_remaining = e.headers.get('x-ratelimit-remaining')
            if rate_limit_remaining:
                error_details += f" (Rate limit remaining: {rate_limit_remaining})"
                
        raise Exception(error_details)
        
    except Exception as e:
        # Handle general exceptions
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating OpenAI embedding: {str(e)} (after {elapsed_time:.2f}s)")
        raise


# Backward compatibility wrapper
def generate_embedding(text: str, model: str = 'text-embedding-ada-002') -> list[float]:
    """Legacy wrapper for generate_embedding_with_usage
    
    Returns just the embedding vector for backward compatibility
    """
    embedding, _ = generate_embedding_with_usage(text, model)
    return embedding
